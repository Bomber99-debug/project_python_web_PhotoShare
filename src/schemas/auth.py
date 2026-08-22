"""Pydantic schemas used by authentication endpoints."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.entity.role import Role


class UserRegister( BaseModel ):
	model_config = ConfigDict( from_attributes=True )

	username: str = Field( min_length=3, max_length=50 )
	email: EmailStr
	password: str = Field( min_length=6, max_length=128 )


class Token( BaseModel ):
	access_token: str
	token_type: str = "bearer"


class TokenPayload( BaseModel ):
	sub: str
	exp: int
	role: Role
