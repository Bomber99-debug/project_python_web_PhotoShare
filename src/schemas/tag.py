"""Pydantic schemas for photo tags."""

from pydantic import BaseModel, ConfigDict, Field


class TagResponse( BaseModel ):
	model_config = ConfigDict( from_attributes=True )

	id: int
	name: str = Field( min_length=1, max_length=100 )
