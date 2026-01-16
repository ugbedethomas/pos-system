from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
from app.database import SessionLocal
import app.models as models
import app.schemas as schemas

# Secret key for token
SECRET_KEY = "pos-system-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Simple password hashing (for development only - use bcrypt in production)
def get_password_hash(password: str) -> str:
    # Simple SHA256 hash for development
    salt = "pos-system-salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    # Simple JWT token (for development)
    import json
    import base64
    import hmac

    header = json.dumps({"alg": "HS256", "typ": "JWT"})
    payload = json.dumps(to_encode)

    header_b64 = base64.urlsafe_b64encode(header.encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")

    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def authenticate_user(db, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(token: str):
    try:
        import base64
        import json

        parts = token.split(".")
        if len(parts) != 3:
            return None

        payload_b64 = parts[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())

        username = payload.get("sub")
        if not username:
            return None

        db = SessionLocal()
        user = db.query(models.User).filter(models.User.username == username).first()
        db.close()
        return user
    except:
        return None