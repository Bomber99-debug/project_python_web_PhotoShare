"""Database operations for ratings."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.rating import Rating


async def create_rating(db: AsyncSession, *, photo_id: int, user_id: int, value: int) -> Rating:
    rating = Rating(photo_id=photo_id, user_id=user_id, value=value)
    db.add(rating)
    await db.flush()
    await db.refresh(rating)
    return rating


async def get_rating(db: AsyncSession, rating_id: int) -> Rating | None:
    return (await db.execute(select(Rating).where(Rating.id == rating_id))).scalar_one_or_none()


async def get_user_photo_rating(db: AsyncSession, photo_id: int, user_id: int) -> Rating | None:
    stmt = select(Rating).where(Rating.photo_id == photo_id, Rating.user_id == user_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_photo_ratings(db: AsyncSession, photo_id: int) -> list[Rating]:
    stmt = select(Rating).where(Rating.photo_id == photo_id).order_by(Rating.created_at.asc())
    return list((await db.execute(stmt)).scalars().all())


async def get_average(db: AsyncSession, photo_id: int) -> tuple[float, int]:
    stmt = select(func.avg(Rating.value), func.count(Rating.id)).where(Rating.photo_id == photo_id)
    average, count = (await db.execute(stmt)).one()
    return float(average or 0), int(count or 0)


async def delete_rating(db: AsyncSession, rating: Rating) -> None:
    await db.delete(rating)
    await db.flush()
