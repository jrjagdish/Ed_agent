from datetime import datetime
import secrets
import uuid
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, UploadFile, HTTPException, status
import pdfplumber
from app import start_process
from db.base import get_db
from db.models import APIKey, Files, User
from schemas import UserCreate, UserLogin, UserResponse
from sqlalchemy.orm import Session
from utils.security import create_access_token, create_refresh_token, verify_token
import hashlib
from fastapi import Security, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()
load_dotenv()

app = FastAPI()

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


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
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    print(user.email)
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered.")

    new_user = User(email=user.email, username=user.username)
    new_user.hash_password(user.password)

    db.add(new_user)
    db.commit() 
    db.flush()
    token = create_access_token(str(new_user.id))
    return {"message": "registered", "token": token}


@app.post("/login", response_model=UserResponse)
def user_authentication_system(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.verify_password(user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(db_user.id))

    return {"id": db_user.id, "email": db_user.email, "token": token}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")

    user = db.query(User).filter(User.id == uuid.UUID(user_id) ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.get("/api_key")
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


def verify_api_key(credentials=Security(security), db: Session = Depends(get_db)):
    raw_key = credentials.credentials
    key_hash = hash_api_key(raw_key)

    api_key = (
        db.query(APIKey)
        .filter(APIKey.key_hash == key_hash, APIKey.is_active == True)
        .first()
    )

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    api_key.last_used_at = datetime.utcnow()
    db.commit()

    return api_key.user


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
    data = Files(user_id=user.id, uploaded_file_url=upload_result["secure_url"])
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
