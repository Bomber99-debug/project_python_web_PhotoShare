"""Photo comment endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.user import User
from src.repository.comments import create_comment, delete_comment, get_comment, list_photo_comments, update_comment
from src.repository.photos import get_photo_by_id
from src.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from src.services.dependencies import get_current_active_user
from src.services.permissions import can_delete_comment, can_edit_comment

router = APIRouter()


@router.post("/photos/{photo_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_photo_comment(
    photo_id: int, data: CommentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)
):
    if await get_photo_by_id(db, photo_id) is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    comment = await create_comment(db, photo_id=photo_id, user_id=user.id, text=data.text)
    await db.commit()
    return comment


@router.get("/photos/{photo_id}/comments", response_model=list[CommentResponse])
async def get_comments(photo_id: int, db: AsyncSession = Depends(get_db)):
    if await get_photo_by_id(db, photo_id) is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return await list_photo_comments(db, photo_id)


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def edit_comment(
    comment_id: int, data: CommentUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)
):
    comment = await get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if not can_edit_comment(comment.user_id, user):
        raise HTTPException(status_code=403, detail="You can edit only your own comments")
    comment = await update_comment(db, comment, data.text)
    await db.commit()
    return comment


@router.delete("/comments/{comment_id}")
async def remove_comment(
    comment_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)
):
    comment = await get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if not can_delete_comment(user):
        raise HTTPException(status_code=403, detail="Only moderator or admin can delete comments")
    await delete_comment(db, comment)
    await db.commit()
    return {"message": "Comment deleted successfully"}
