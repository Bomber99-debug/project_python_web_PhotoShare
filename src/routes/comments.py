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


@router.post( "/photos/{photo_id}/comments",
              response_model=CommentResponse,
              status_code=status.HTTP_201_CREATED,
              summary="Add a comment to a photo",
              description=("Create a comment under an existing photo. "
                           "Only authenticated active users may add comments."),
              responses={
		              401: { "description": "Authentication required or user account is inactive.", },
		              404: { "description": "Photo not found.", },
		              }, )
async def create_photo_comment( photo_id: int,
                                data: CommentCreate,
                                db: AsyncSession = Depends( get_db ),
                                user: User = Depends( get_current_active_user ), ):
	if await get_photo_by_id( db, photo_id ) is None:
		raise HTTPException( status_code=404, detail="Photo not found" )
	comment = await create_comment( db, photo_id=photo_id, user_id=user.id, text=data.text )
	await db.commit()
	return comment


@router.get( "/photos/{photo_id}/comments",
             response_model=list[ CommentResponse ],
             summary="Get photo comments",
             description="Return all comments associated with the specified photo.",
             responses={ 404: { "description": "Photo not found.", },
                         }, )
async def get_comments( photo_id: int, db: AsyncSession = Depends( get_db ) ):
	if await get_photo_by_id( db, photo_id ) is None:
		raise HTTPException( status_code=404, detail="Photo not found" )
	return await list_photo_comments( db, photo_id )


@router.put( "/comments/{comment_id}",
             response_model=CommentResponse,
             summary="Edit a comment",
             description="Update a comment. A user may edit only their own comments.",
             responses={
		             401: { "description": "Authentication required or user account is inactive.", },
		             403: { "description": "The current user is not the author of this comment.", },
		             404: { "description": "Comment not found.", },
		             }, )
async def edit_comment( comment_id: int,
                        data: CommentUpdate,
                        db: AsyncSession = Depends( get_db ),
                        user: User = Depends( get_current_active_user ), ):
	comment = await get_comment( db, comment_id )
	if comment is None:
		raise HTTPException( status_code=404, detail="Comment not found" )
	if not can_edit_comment( comment.user_id, user ):
		raise HTTPException( status_code=403, detail="You can edit only your own comments" )
	comment = await update_comment( db, comment, data.text )
	await db.commit()
	return comment


@router.delete( "/comments/{comment_id}",
                summary="Delete a comment",
                description="Delete a comment. Only moderators and administrators may delete comments.",
                responses={
		                401: { "description": "Authentication required or user account is inactive.", },
		                403: { "description": "Moderator or administrator role required.", },
		                404: { "description": "Comment not found.", },
		                }, )
async def remove_comment( comment_id: int,
                          db: AsyncSession = Depends( get_db ),
                          user: User = Depends( get_current_active_user ), ):
	comment = await get_comment( db, comment_id )
	if comment is None:
		raise HTTPException( status_code=404, detail="Comment not found" )
	if not can_delete_comment( user ):
		raise HTTPException( status_code=403, detail="Only moderator or admin can delete comments" )
	await delete_comment( db, comment )
	await db.commit()
	return { "message": "Comment deleted successfully" }
