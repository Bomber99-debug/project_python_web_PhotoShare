"""Authentication business logic."""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.role import Role
from src.entity.user import User
from src.repository.blacklist import add_to_blacklist, is_blacklisted
from src.repository.users import count_users, create_user, get_user_by_email, get_user_by_username
from src.schemas.auth import UserRegister
from src.services.security import hash_password, verify_password


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    if await get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    role = Role.ADMIN if await count_users(db) == 0 else Role.USER
    user = await create_user(
        db,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role=role,
        is_active=True,
    )
    await db.commit()
    return user


async def authenticate_user(db: AsyncSession, identity: str, password: str) -> User:
    user = await get_user_by_email(db, identity)
    if user is None:
        user = await get_user_by_username(db, identity)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def logout_user(db: AsyncSession, token: str, expires_at: datetime) -> None:
    if not await is_blacklisted(db, token):
        await add_to_blacklist(db, token, expires_at)
        await db.commit()
