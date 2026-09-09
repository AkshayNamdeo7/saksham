from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

_BCRYPT_MAX = 72


def hash_password(password: str) -> str:
    data = password.encode("utf-8")[:_BCRYPT_MAX]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(data, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        data = plain.encode("utf-8")[:_BCRYPT_MAX]
        return bcrypt.checkpw(data, hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None