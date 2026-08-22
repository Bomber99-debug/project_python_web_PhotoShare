"""Database operations for users."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.photo import Photo
from src.entity.role import Role
from src.entity.user import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    return (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()


async def count_users(db: AsyncSession) -> int:
    return int((await db.execute(select(func.count()).select_from(User))).scalar_one())


async def count_user_photos(db: AsyncSession, user_id: int) -> int:
    stmt = select(func.count()).select_from(Photo).where(Photo.user_id == user_id)
    return int((await db.execute(stmt)).scalar_one())


async def create_user(db: AsyncSession, **data) -> User:
    user = User(**data)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, data: dict) -> User:
    for field, value in data.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


async def set_user_active(db: AsyncSession, user_id: int, is_active: bool) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user is None:
        return None
    user.is_active = is_active
    await db.flush()
    await db.refresh(user)
    return user


async def set_user_role(db: AsyncSession, user_id: int, role: Role) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user is None:
        return None
    user.role = role
    await db.flush()
    await db.refresh(user)
    return user
