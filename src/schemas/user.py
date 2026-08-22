"""Pydantic schemas for user profiles and administration."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.entity.role import Role


class UserBase( BaseModel ):
	model_config = ConfigDict( from_attributes=True )

	username: str = Field( min_length=3, max_length=50 )
	email: EmailStr
	avatar_url: str | None = None


class UserUpdate( BaseModel ):
	model_config = ConfigDict( from_attributes=True )

	username: str | None = Field( default=None, min_length=3, max_length=50 )
	email: EmailStr | None = None
	password: str | None = Field( default=None, min_length=6, max_length=128 )
	avatar_url: str | None = Field( default=None, max_length=512 )


class UserResponse( UserBase ):
	id: int
	role: Role
	is_active: bool
	created_at: datetime
	updated_at: datetime


class UserPublicProfile( BaseModel ):
	model_config = ConfigDict( from_attributes=True )

	id: int
	username: str
	avatar_url: str | None = None
	role: Role
	created_at: datetime
	uploaded_photos_count: int = 0


class UserRoleUpdate( BaseModel ):
	role: Role


class UserBanResponse( BaseModel ):
	id: int
	username: str
	is_active: bool
	message: str
