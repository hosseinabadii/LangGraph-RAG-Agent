from fastapi import APIRouter, HTTPException, status

from app.db.main import SessionDep
from app.users import service as user_service
from app.users.schemas import UserCreate

from .dependencies import AccessTokenBearerDep, OAuth2PasswordRequestFormDep, RefreshTokenBearerDep
from .schemas import LoginResponse, LogoutResponse, RefreshTokenResponse, SignupResponse
from .utils import create_jwt_token, verify_password

auth_router = APIRouter()


@auth_router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def create_user_Account(user_data: UserCreate, session: SessionDep):
    new_user = await user_service.create_user(user_data, session)

    return {"message": "Account Created!", "user": new_user}


@auth_router.post("/login", response_model=LoginResponse)
async def login_users(form_data: OAuth2PasswordRequestFormDep, session: SessionDep):
    email = form_data.username
    password = form_data.password

    user = await user_service.get_user_by_email(email, session)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Your account is not active")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Your account is not verified")

    is_password_valid = verify_password(password, user.password_hash)
    if not is_password_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_jwt_token(
        user_data={"email": user.email, "id": str(user.id)},
        refresh=False,
    )

    refresh_token = create_jwt_token(
        user_data={"email": user.email, "id": str(user.id)},
        refresh=True,
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {"email": user.email, "id": str(user.id), "username": user.username},
    }


@auth_router.get("/logout", response_model=LogoutResponse)
async def revoke_token(token_data: AccessTokenBearerDep):
    return {"message": "Logged out successfully"}


@auth_router.get("/refresh-token", response_model=RefreshTokenResponse)
async def get_new_access_token(token_data: RefreshTokenBearerDep):
    user = token_data.user
    user_data = {"email": user.email, "id": str(user.id)}
    new_access_token = create_jwt_token(user_data=user_data, refresh=False)

    return {"access_token": new_access_token}
