"""Database operations for photos, tags, transformations and search."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.entity.photo import Photo
from src.entity.photo_transform import PhotoTransform
from src.entity.rating import Rating
from src.entity.tag import Tag


async def create_photo( db: AsyncSession,
                        *,
                        user_id: int,
                        description: str | None,
                        image_url: str,
                        public_id: str, ) -> Photo:
	photo = Photo( user_id=user_id, description=description, image_url=image_url, public_id=public_id )
	db.add( photo )
	await db.flush()
	await db.refresh( photo )
	return photo


async def get_photo_by_id( db: AsyncSession, photo_id: int ) -> Photo | None:
	stmt = select( Photo ).where( Photo.id == photo_id ).options( selectinload( Photo.tags ) )
	return (await db.execute( stmt )).scalar_one_or_none()


async def get_photo_detail( db: AsyncSession, photo_id: int ) -> Photo | None:
	stmt = (select( Photo ).where( Photo.id == photo_id ).options( selectinload( Photo.tags ),
			selectinload( Photo.comments ),
			selectinload( Photo.ratings ),
			selectinload( Photo.transformed_photos ), ))
	return (await db.execute( stmt )).scalar_one_or_none()


async def update_photo( db: AsyncSession, photo: Photo, data: dict ) -> Photo:
	for field, value in data.items():
		setattr( photo, field, value )
	await db.flush()
	await db.refresh( photo, attribute_names=[ "tags" ] )
	return photo


async def delete_photo( db: AsyncSession, photo: Photo ) -> None:
	await db.delete( photo )
	await db.flush()


async def get_or_create_tags( db: AsyncSession, names: list[ str ] ) -> list[ Tag ]:
	result: list[ Tag ] = [ ]
	for name in names:
		tag = (await db.execute( select( Tag ).where( Tag.name == name ) )).scalar_one_or_none()
		if tag is None:
			tag = Tag( name=name )
			db.add( tag )
			await db.flush()
		result.append( tag )
	return result


async def set_photo_tags( db: AsyncSession, photo: Photo, tags: list[ Tag ] ) -> Photo:
	await db.refresh( photo, attribute_names=[ "tags" ] )
	photo.tags = tags
	await db.flush()
	await db.refresh( photo, attribute_names=[ "tags" ] )
	return photo


async def create_transform( db: AsyncSession,
                            *,
                            photo_id: int,
                            transformation_type: str,
                            transformed_url: str,
                            qr_code_url: str | None, ) -> PhotoTransform:
	item = PhotoTransform( photo_id=photo_id,
			transformation_type=transformation_type,
			transformed_url=transformed_url,
			qr_code_url=qr_code_url, )
	db.add( item )
	await db.flush()
	await db.refresh( item )
	return item


async def get_transform( db: AsyncSession, transform_id: int ) -> PhotoTransform | None:
	return (
		await db.execute( select( PhotoTransform ).where( PhotoTransform.id == transform_id ) )).scalar_one_or_none()


async def list_transforms( db: AsyncSession, photo_id: int ) -> list[ PhotoTransform ]:
	stmt = select( PhotoTransform ).where( PhotoTransform.photo_id == photo_id ).order_by(
			PhotoTransform.created_at.asc() )
	return list( (await db.execute( stmt )).scalars().all() )


async def search_photos( db: AsyncSession,
		*,
		keyword: str | None = None,
		tag: str | None = None,
		min_rating: float | None = None,
		sort_by: str = "date",
		order: str = "desc",
		user_id: int | None = None,
		date_from: datetime | None = None,
		date_to: datetime | None = None, ) -> list[ Photo ]:
	stats = (select( Rating.photo_id.label( "photo_id" ), func.avg( Rating.value ).label( "avg_rating" ) ).group_by(
		Rating.photo_id, ).subquery())
	stmt = select( Photo ).options( selectinload( Photo.tags ) )
	if keyword:
		stmt = stmt.where( Photo.description.ilike( f"%{keyword}%" ) )
	if tag:
		stmt = stmt.join( Photo.tags ).where( Tag.name == tag )
	if user_id is not None:
		stmt = stmt.where( Photo.user_id == user_id )
	if date_from is not None:
		stmt = stmt.where( Photo.created_at >= date_from )
	if date_to is not None:
		stmt = stmt.where( Photo.created_at <= date_to )
	if min_rating is not None or sort_by == "rating":
		stmt = stmt.outerjoin( stats, Photo.id == stats.c.photo_id )
	if min_rating is not None:
		stmt = stmt.where( func.coalesce( stats.c.avg_rating, 0 ) >= min_rating )
	sort_column = func.coalesce( stats.c.avg_rating, 0 ) if sort_by == "rating" else Photo.created_at
	stmt = stmt.order_by( sort_column.asc() if order == "asc" else sort_column.desc() )
	return list( (await db.execute( stmt )).scalars().unique().all() )
