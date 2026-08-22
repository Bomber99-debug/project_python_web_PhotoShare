"""Database operations for JWT blacklist entries."""

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.blacklist import TokenBlacklist


async def is_blacklisted(db: AsyncSession, token: str) -> bool:
    stmt = select(TokenBlacklist.id).where(TokenBlacklist.token == token)
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def add_to_blacklist(db: AsyncSession, token: str, expires_at: datetime) -> None:
    db.add(TokenBlacklist(token=token, expires_at=expires_at))
    await db.flush()


async def delete_expired(db: AsyncSession, now: datetime) -> None:
    await db.execute(delete(TokenBlacklist).where(TokenBlacklist.expires_at <= now))
