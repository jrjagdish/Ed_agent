from datetime import datetime
import secrets
import uuid
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    Request,
    Response,
    UploadFile,
    HTTPException,
    status,
)
import pdfplumber
from app import start_process
from db.base import get_db
from db.models import APIKey, Files, User
from schemas import UserCreate, UserLogin, UserResponse
from sqlalchemy.orm import Session
from utils.security import create_access_token, create_refresh_token, verify_token
import hashlib
from fastapi import Security, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import redis.asyncio as redis
from sqlalchemy import func, cast, Date
from datetime import timedelta

security = HTTPBearer()
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
COOKIE_SETTINGS = {
    "httponly": True,
    "samesite": "lax",
    "secure": False,  # Set to True in production (HTTPS)
    "path": "/",
}

cloudinary.config(
    cloud_name="dviu4sdd9",
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)


async def track_usage(user_id: str):
    """Handles the incrementing and limit checking in Redis"""
    MONTHLY_LIMIT = 1000  # Set your limit here
    current_month = datetime.utcnow().strftime("%Y-%m")
    usage_key = f"usage:{user_id}:{current_month}"

    # Increment request count
    request_count = await redis_client.incr(usage_key)

    if request_count == 1:
        await redis_client.expire(usage_key, 2764800)

    if request_count > MONTHLY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly limit of {MONTHLY_LIMIT} requests exceeded.",
        )

    return request_count


def get_text_from_pdf(file: UploadFile):
    file.file.seek(0)
    with pdfplumber.open(file.file) as pdf:
        if len(pdf.pages) > 3:
            return {"ERROR: Please provide the pdf which has less than 3 pages"}
        else:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

    if not text.strip():
        return {"ERROR : No data to extract"}

    return text


@app.post("/register")
def register_user(user: UserCreate, response: Response, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered.")

    new_user = User(email=user.email, username=user.username)
    new_user.hash_password(user.password)

    db.add(new_user)
    db.commit()
    db.flush()
    token = create_access_token(str(new_user.id))
    refresh = create_refresh_token(str(new_user.id))

    response.set_cookie(
        key="access_token", value=token, **COOKIE_SETTINGS, max_age=3600
    )
    response.set_cookie(
        key="refresh_token", value=refresh, **COOKIE_SETTINGS, max_age=604800
    )
    return {"message": "registered", "token": token}


@app.post("/login")
def user_authentication_system(
    user: UserLogin, response: Response, db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.verify_password(user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(db_user.id))
    refresh = create_refresh_token(str(db_user.id))
   
    response.set_cookie(
        key="access_token", value=token, **COOKIE_SETTINGS, max_age=3600
    )
    response.set_cookie(
        key="refresh_token", value=refresh, **COOKIE_SETTINGS, max_age=604800
    )

    return {"id": db_user.id, "email": db_user.email, "token": token}


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    token = request.cookies.get("access_token")
   
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.get("/api_key/")
def genrate_api_key(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = "sk_live_" + secrets.token_hex(32)
    hashed_key = hash_api_key(token)
    api_key = APIKey(user_id=current_user.id, key_hash=hashed_key, name=name)

    db.add(api_key)
    db.commit()
    return {"api_key": token, "warning": "Copy this key . You won’t see it again."}


@app.get("/usage-stats/")
async def get_usage_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # 1. Real Real-time Count (Redis)
    current_month = datetime.utcnow().strftime("%Y-%m")
    usage_key = f"usage:{current_user.id}:{current_month}"
    redis_count = await redis_client.get(usage_key) or 0

    # 2. Real Total Spend (Sum of all costs in DB)
    total_cost = (
        db.query(func.sum(Files.cost)).filter(Files.user_id == current_user.id).scalar()
        or 0
    )

    # 3. Real History (Usage over the last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Query: Count files uploaded per day for this user
    history_query = (
        db.query(
            cast(Files.uploaded_at, Date).label("day"),
            func.count(Files.id).label("count"),
        )
        .filter(Files.user_id == current_user.id, Files.uploaded_at >= seven_days_ago)
        .group_by(cast(Files.uploaded_at, Date))
        .all()
    )

    # Format history for Recharts
    real_history = [{"name": str(day), "usage": count} for day, count in history_query]

    # Fallback if history is empty (new users)
    if not real_history:
        real_history = [{"name": "No Data", "usage": 0}]

    return {
        "total_requests": int(redis_count),
        "total_spend": round(float(total_cost), 4),
        "limit": 1000,
        "history": real_history,  # <--- Now 100% Real
    }


async def verify_api_key(credentials=Security(security), db: Session = Depends(get_db)):
    raw_key = credentials.credentials
    key_hash = hash_api_key(raw_key)

    api_key = (
        db.query(APIKey)
        .filter(APIKey.key_hash == key_hash, APIKey.is_active == True)
        .first()
    )

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    request_count = await track_usage(str(api_key.user_id))

    api_key.last_used_at = datetime.utcnow()
    db.commit()

    return {"user": api_key.user, "request_count": request_count}


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


@app.post("/upload")
async def upload_file(
    file: UploadFile,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    data = get_text_from_pdf(file)
    if isinstance(data, dict) and "error" in data:
        return data

    result = await start_process({"input_text": data})
    file.file.seek(0)

    upload_result = cloudinary.uploader.upload(
        file.file, resource_type="raw", folder="pdfs", public_id=file.filename
    )
    data = Files(
        user_id=user["user"].id,
        uploaded_file_url=upload_result["secure_url"],
        summary=result.get("Summary"),
        mcq=result.get("MCQs"),
        cost=result.get("Estimated Cost"),
    )
    db.add(data)
    db.commit()
    message = "Successful!"

    return {
        "Message": message,
        "Secure_url": upload_result["secure_url"],
        "Summary": result.get("Summary"),
        "MCQs": result.get("MCQs"),
        "Token Cost": f"{result.get("Estimated Cost")}$",
    }
