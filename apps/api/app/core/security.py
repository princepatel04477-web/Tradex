"""Security utilities: password hashing, JWT generation & decoding."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import hashlib
import hmac
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.errors import AuthenticationError

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, email: str, extra: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expires,
        "iat": now,
        "role": "authenticated",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise AuthenticationError("Invalid or expired token") from e
