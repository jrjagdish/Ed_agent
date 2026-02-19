from fastapi import HTTPException
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # default to HS256

# Helper for consistent timezone-aware "now"
def get_now() -> datetime:
    return datetime.now(timezone.utc)

# -------------------------------
# Access Token
# -------------------------------
def create_access_token(user_id: str, expires_delta: timedelta = None) -> str:
    """
    Create a JWT access token for a user.
    """
    expire = get_now() + (expires_delta or timedelta(minutes=10))
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# -------------------------------
# Refresh Token
# -------------------------------
def create_refresh_token(user_id: str) -> str:
    """
    Create a refresh token for session rotation.
    """
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": get_now() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# -------------------------------
# Token Verification
# -------------------------------
def verify_token(token: str, expected_type: str = "access") -> dict:
    """
    Verify a JWT token, check signature and 'type' claim.
    Raises HTTPException if invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(status_code=401, detail=f"Invalid token type: expected '{expected_type}'")

    return payload
