from uuid import UUID

from fastapi import APIRouter, status

from app.auth.dependencies import CurrentUserDep
from app.db.main import SessionDep

from . import service as user_service
from .schemas import UserPublic, UserUpdate

user_router = APIRouter()


@user_router.get("/me", response_model=UserPublic)
async def get_current_user(user: CurrentUserDep):
    return user


@user_router.put("/user-profile/{user_id}", response_model=UserPublic)
async def update_user_profile(
    user_id: UUID, update_data: UserUpdate, current_user: CurrentUserDep, session: SessionDep
):
    return await user_service.update_user_profile(user_id, update_data, current_user, session)


@user_router.delete("/user-profile/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(user_id: UUID, current_user: CurrentUserDep, session: SessionDep):
    return await user_service.delete_user_profile(user_id, current_user, session)
