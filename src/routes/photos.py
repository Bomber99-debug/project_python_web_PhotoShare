"""Photo CRUD endpoints."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.photo import Photo
from src.entity.user import User
from src.repository.photos import (create_photo,
                                   delete_photo,
                                   get_or_create_tags,
                                   get_photo_by_id,
                                   get_photo_detail,
                                   set_photo_tags,
                                   update_photo,
                                   )
from src.schemas.photo import PhotoDetailResponse, PhotoResponse, PhotoUpdate
from src.schemas.rating import RatingAverageResponse
from src.services.cloudinary import delete_photo as delete_cloudinary_photo, upload_photo
from src.services.dependencies import get_current_active_user
from src.services.permissions import can_modify_photo
from src.services.tags import normalize_tag_names

router = APIRouter()
ALLOWED_IMAGE_CONTENT_TYPES = { "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp" }


def validate_image_file( file: UploadFile ) -> None:
	if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
		raise HTTPException( status_code=400, detail="Only jpeg, png, gif and webp images are allowed" )


def build_detail( photo: Photo ) -> PhotoDetailResponse:
	summary = None
	if photo.ratings:
		summary = RatingAverageResponse( photo_id=photo.id,
		                                 average_rating=sum(
				                                 item.value for item in photo.ratings, ) / len( photo.ratings ),
		                                 ratings_count=len( photo.ratings ), )
	base = PhotoResponse.model_validate( photo )
	return PhotoDetailResponse( **base.model_dump(),
	                            comments=photo.comments,
	                            rating_summary=summary,
	                            transformed_photos=photo.transformed_photos, )


@router.post( "",
              response_model=PhotoResponse,
              status_code=status.HTTP_201_CREATED,
              summary="Upload a photo",
              description=("Upload an image to Cloudinary and save its metadata in PhotoShare. "
                           "Supported formats: JPEG, PNG, GIF and WebP. "
                           "A photo can contain at most five unique normalized tags."),
              responses={
		              400: { "description": "Unsupported image type or invalid tags.", },
		              401: { "description": "Authentication required or user account is inactive.", },
		              }, )
async def upload_user_photo( file: UploadFile = File( ... ),
                             description: str | None = Form( default=None ),
                             tags: list[ str ] | None = Form( default=None ),
                             db: AsyncSession = Depends( get_db ),
                             user: User = Depends( get_current_active_user ), ) -> Photo:
	validate_image_file( file )
	try:
		normalized_tags = normalize_tag_names( tags )
	except ValueError as exc:
		raise HTTPException( status_code=400, detail=str( exc ) ) from exc

	uploaded: dict[ str, str ] | None = None
	try:
		uploaded = await upload_photo( file )
		photo = await create_photo( db,
		                            user_id=user.id,
		                            description=description,
		                            image_url=uploaded[ "image_url" ],
		                            public_id=uploaded[ "public_id" ], )
		if normalized_tags:
			photo = await set_photo_tags( db, photo, await get_or_create_tags( db, normalized_tags ) )
		await db.commit()
		await db.refresh( photo, attribute_names=[ "tags" ] )
		return photo
	except Exception:
		await db.rollback()
		if uploaded is not None:
			try:
				await delete_cloudinary_photo( uploaded[ "public_id" ] )
			except Exception:
				pass
		raise


@router.get( "/{photo_id}",
             response_model=PhotoDetailResponse,
             summary="Get photo details",
             description=("Return a photo with its tags, comments, rating summary "
                          "and saved transformed versions."),
             responses={ 404: { "description": "Photo not found.", },
                         }, )
async def get_photo( photo_id: int, db: AsyncSession = Depends( get_db ) ) -> PhotoDetailResponse:
	photo = await get_photo_detail( db, photo_id )
	if photo is None:
		raise HTTPException( status_code=404, detail="Photo not found" )
	return build_detail( photo )


@router.put( "/{photo_id}",
             response_model=PhotoResponse,
             summary="Update a photo",
             description=("Update the photo description and/or tags. "
                          "The photo owner may edit their own photo; an admin may edit any photo."),
             responses={
		             400: { "description": "Invalid tags.", },
		             401: { "description": "Authentication required or user account is inactive.", },
		             403: { "description": "The current user is not allowed to modify this photo.", },
		             404: { "description": "Photo not found.", },
		             }, )
async def update_user_photo( photo_id: int,
                             data: PhotoUpdate,
                             db: AsyncSession = Depends( get_db ),
                             user: User = Depends( get_current_active_user ), ) -> Photo:
	photo = await get_photo_by_id( db, photo_id )
	if photo is None:
		raise HTTPException( status_code=404, detail="Photo not found" )
	if not can_modify_photo( photo.user_id, user ):
		raise HTTPException( status_code=403, detail="Insufficient permissions" )
	changes = data.model_dump( exclude_unset=True )
	tags = changes.pop( "tags", None )
	if changes:
		photo = await update_photo( db, photo, changes )
	if tags is not None:
		try:
			normalized = normalize_tag_names( tags )
		except ValueError as exc:
			raise HTTPException( status_code=400, detail=str( exc ) ) from exc
		photo = await set_photo_tags( db, photo, await get_or_create_tags( db, normalized ) )
	await db.commit()
	await db.refresh( photo, attribute_names=[ "tags" ] )
	return photo


@router.delete( "/{photo_id}",
                summary="Delete a photo",
                description=("Delete a photo from Cloudinary and PhotoShare. "
                             "The owner may delete their own photo; an admin may delete any photo."),
                responses={
		                401: { "description": "Authentication required or user account is inactive.", },
		                403: { "description": "The current user is not allowed to delete this photo.", },
		                404: { "description": "Photo not found.", },
		                }, )
async def delete_user_photo( photo_id: int,
                             db: AsyncSession = Depends( get_db ),
                             user: User = Depends( get_current_active_user ), ) -> dict[ str, str ]:
	photo = await get_photo_by_id( db, photo_id )
	if photo is None:
		raise HTTPException( status_code=404, detail="Photo not found" )
	if not can_modify_photo( photo.user_id, user ):
		raise HTTPException( status_code=403, detail="Insufficient permissions" )
	await delete_cloudinary_photo( photo.public_id )
	await delete_photo( db, photo )
	await db.commit()
	return { "message": "Photo deleted successfully" }
