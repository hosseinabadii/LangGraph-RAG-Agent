import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from loguru import logger

from app.config import settings

from .schemas import TokenData


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password_byte_enc = plain_password.encode("utf-8")
    hash_password_byte_enc = hashed_password.encode("utf-8")

    return bcrypt.checkpw(password=plain_password_byte_enc, hashed_password=hash_password_byte_enc)


def create_jwt_token(user_data: dict, refresh: bool = False) -> str:
    if refresh:
        expiry = timedelta(days=settings.refresh_token_expiry_days)
    else:
        expiry = timedelta(minutes=settings.access_token_expiry_mins)

    payload = {
        "user": user_data,
        "exp": datetime.now(tz=UTC) + expiry,
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
    }
    token = jwt.encode(payload=payload, key=settings.jwt_secret, algorithm=settings.jwt_algorithm)

    return token


def decode_token(token: str) -> TokenData | None:
    try:
        token_data = jwt.decode(jwt=token, key=settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenData(**token_data)
    except jwt.PyJWTError as e:
        logger.error(f"Error decoding jwt token: {e}")
        return None
