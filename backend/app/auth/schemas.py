from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.users.schemas import UserPublic


class SignupResponse(BaseModel):
    message: str
    user: UserPublic


class LoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    user: dict[str, str]


class LogoutResponse(BaseModel):
    message: str


class RefreshTokenResponse(BaseModel):
    access_token: str


class UserTokenData(BaseModel):
    email: EmailStr
    id: UUID


class TokenData(BaseModel):
    user: UserTokenData
    exp: int
    jti: UUID
    refresh: bool


class VerifyEmailResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr


class PasswordResetResponse(BaseModel):
    message: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    new_password: Annotated[str, Field(min_length=8, max_length=32)]
    confirm_password: Annotated[str, Field(min_length=8, max_length=32)]
