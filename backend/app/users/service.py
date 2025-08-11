from uuid import UUID

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import hash_password
from app.db.models import User

from .schemas import UserCreate, UserUpdate


async def _check_permission(user_id: UUID, currenrt_user: User) -> None:
    if user_id != currenrt_user.id:
        raise HTTPException(status_code=403, detail="Not enough permission")


async def get_user_by_email(email: EmailStr, session: AsyncSession) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def get_user_by_username(username: str, session: AsyncSession) -> User | None:
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def create_user(user_data: UserCreate, session: AsyncSession) -> User:
    if await get_user_by_email(user_data.email, session):
        raise HTTPException(status_code=403, detail="Email already exists.")

    if await get_user_by_username(user_data.username, session):
        raise HTTPException(status_code=403, detail="Username already exists.")

    new_user = User(**user_data.model_dump(exclude={"password"}))
    new_user.password_hash = hash_password(user_data.password)
    session.add(new_user)
    await session.commit()

    return new_user


async def update_user_profile(
    user_id: UUID, update_data: UserUpdate, current_user: User, session: AsyncSession
) -> User:
    await _check_permission(user_id, current_user)
    update_data_dict = update_data.model_dump(exclude_none=True)

    email = update_data_dict.get("email")
    if email and email != current_user.email and await get_user_by_email(email, session):
        raise HTTPException(status_code=403, detail="Email already exists.")

    username = update_data_dict.get("username")
    if username and username != current_user.username and await get_user_by_username(username, session):
        raise HTTPException(status_code=403, detail="Username already exists.")

    for key, value in update_data_dict.items():
        setattr(current_user, key, value)
    await session.commit()
    await session.refresh(current_user)

    return current_user


async def delete_user_profile(user_id: UUID, current_user: User, session: AsyncSession) -> None:
    await _check_permission(user_id, current_user)
    await session.delete(current_user)
    await session.commit()
