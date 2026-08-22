"""Optional rating endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.user import User
from src.repository.photos import get_photo_by_id
from src.repository.ratings import (create_rating,
                                    delete_rating,
                                    get_average,
                                    get_rating,
                                    get_user_photo_rating,
                                    list_photo_ratings,
                                    )
from src.schemas.rating import RatingAverageResponse, RatingCreate, RatingResponse
from src.services.dependencies import get_current_active_user
from src.services.permissions import can_manage_rating, require_moderator_or_admin

router = APIRouter()


@router.post( "/photos/{photo_id}/ratings",
              response_model=RatingResponse,
              status_code=status.HTTP_201_CREATED,
              summary="Rate a photo",
              description=("Add a rating from 1 to 5 to a photo. "
                           "A user cannot rate their own photo and may rate each photo only once."),
              responses={
		              400: { "description": "Cannot rate own photo or photo has already been rated by this user.", },
		              401: { "description": "Authentication required or user account is inactive.", },
		              404: { "description": "Photo not found.", },
		              }, )
async def rate_photo( photo_id: int,
                      data: RatingCreate,
                      db: AsyncSession = Depends( get_db ),
                      user: User = Depends( get_current_active_user ), ):
	photo = await get_photo_by_id( db, photo_id )
	if photo is None:
		raise HTTPException( status_code=404, detail="Photo not found" )
	if photo.user_id == user.id:
		raise HTTPException( status_code=400, detail="You cannot rate your own photo" )
	if await get_user_photo_rating( db, photo_id, user.id ):
		raise HTTPException( status_code=400, detail="You have already rated this photo" )
	rating = await create_rating( db, photo_id=photo_id, user_id=user.id, value=data.value )
	await db.commit()
	return rating


@router.get( "/photos/{photo_id}/ratings",
             response_model=RatingAverageResponse,
             summary="Get photo rating summary",
             description="Return the average rating and total number of ratings for a photo.",
             responses={ 404: { "description": "Photo not found.", },
                         }, )
async def rating_summary( photo_id: int, db: AsyncSession = Depends( get_db ) ):
	if await get_photo_by_id( db, photo_id ) is None:
		raise HTTPException( status_code=404, detail="Photo not found" )
	average, count = await get_average( db, photo_id )
	return RatingAverageResponse( photo_id=photo_id, average_rating=average, ratings_count=count )


@router.get( "/photos/{photo_id}/ratings/details",
             response_model=list[ RatingResponse ],
             summary="Get detailed photo ratings",
             description=("Return individual ratings for a photo. "
                          "Only moderators and administrators may access rating details."),
             responses={
		             401: { "description": "Authentication required or user account is inactive.", },
		             403: { "description": "Moderator or administrator role required.", },
		             }, )
async def rating_details( photo_id: int,
                          db: AsyncSession = Depends( get_db ),
                          _: User = Depends( require_moderator_or_admin ), ):
	return await list_photo_ratings( db, photo_id )


@router.delete( "/ratings/{rating_id}",
                summary="Delete a rating",
                description="Delete an existing rating. Only moderators and administrators may remove ratings.",
                responses={
		                401: { "description": "Authentication required or user account is inactive.", },
		                403: { "description": "Moderator or administrator role required.", },
		                404: { "description": "Rating not found.", },
		                }, )
async def remove_rating( rating_id: int,
                         db: AsyncSession = Depends( get_db ),
                         user: User = Depends( get_current_active_user ), ):
	rating = await get_rating( db, rating_id )
	if rating is None:
		raise HTTPException( status_code=404, detail="Rating not found" )
	if not can_manage_rating( user ):
		raise HTTPException( status_code=403, detail="Only moderator or admin can delete ratings" )
	await delete_rating( db, rating )
	await db.commit()
	return { "message": "Rating deleted successfully" }
