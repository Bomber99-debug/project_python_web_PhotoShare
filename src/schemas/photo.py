"""Pydantic schemas for photo API responses and updates."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.comment import CommentResponse
from src.schemas.photo_transform import PhotoTransformResponse
from src.schemas.rating import RatingAverageResponse
from src.schemas.tag import TagResponse


def _normalize_tags( tags: list[ str ] | None ) -> list[ str ] | None:
	if tags is None:
		return None
	if len( tags ) > 5:
		raise ValueError( "A photo can have at most 5 tags" )
	normalized: list[ str ] = [ ]
	for tag in tags:
		cleaned = tag.strip().lower()
		if not cleaned:
			raise ValueError( "Tags cannot be empty" )
		if len( cleaned ) > 100:
			raise ValueError( "Each tag must be at most 100 characters" )
		if cleaned not in normalized:
			normalized.append( cleaned )
	return normalized


class PhotoUpdate( BaseModel ):
	description: str | None = Field( default=None, max_length=2000 )
	tags: list[ str ] | None = Field( default=None, max_length=5 )

	@field_validator( "tags" )
	@classmethod
	def validate_tags( cls, value: list[ str ] | None ) -> list[ str ] | None:
		return _normalize_tags( value )


class PhotoResponse( BaseModel ):
	model_config = ConfigDict( from_attributes=True )

	id: int
	user_id: int
	description: str | None
	image_url: str
	public_id: str
	created_at: datetime
	updated_at: datetime
	tags: list[ TagResponse ] = Field( default_factory=list )


class PhotoDetailResponse( PhotoResponse ):
	comments: list[ CommentResponse ] = Field( default_factory=list )
	rating_summary: RatingAverageResponse | None = None
	transformed_photos: list[ PhotoTransformResponse ] = Field( default_factory=list )
