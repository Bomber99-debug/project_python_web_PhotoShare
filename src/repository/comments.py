"""Database operations for photo comments."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.comment import Comment


async def create_comment(db: AsyncSession, *, photo_id: int, user_id: int, text: str) -> Comment:
    comment = Comment(photo_id=photo_id, user_id=user_id, text=text)
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    return comment


async def get_comment(db: AsyncSession, comment_id: int) -> Comment | None:
    return (await db.execute(select(Comment).where(Comment.id == comment_id))).scalar_one_or_none()


async def update_comment(db: AsyncSession, comment: Comment, text: str) -> Comment:
    comment.text = text
    comment.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(comment)
    return comment


async def delete_comment(db: AsyncSession, comment: Comment) -> None:
    await db.delete(comment)
    await db.flush()


async def list_photo_comments(db: AsyncSession, photo_id: int) -> list[Comment]:
    stmt = select(Comment).where(Comment.photo_id == photo_id).order_by(Comment.created_at.asc())
    return list((await db.execute(stmt)).scalars().all())
