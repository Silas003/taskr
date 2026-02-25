from datetime import datetime, timedelta, timezone
import os
from typing import Optional

# Pull secret and expiry from env; provide a sensible dev default
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    try:
        from jose import jwt
    except Exception:
        raise RuntimeError("python-jose is required for JWT support. Install 'python-jose[cryptography]'.")

    to_encode = {"sub": str(subject)}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        from jose import JWTError, jwt
    except Exception:
        raise RuntimeError("python-jose is required for JWT support. Install 'python-jose[cryptography]'.")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
