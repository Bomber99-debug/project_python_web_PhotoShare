"""Authentication HTTP endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.user import User
from src.schemas.auth import Token, UserRegister
from src.schemas.user import UserResponse
from src.services.auth import authenticate_user, logout_user, register_user
from src.services.dependencies import get_current_active_user, oauth2_scheme
from src.services.security import create_access_token, decode_access_token

router = APIRouter()


@router.post( "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register user" )
async def register( data: UserRegister, db: AsyncSession = Depends( get_db ) ) -> User:
	"""Register a user; the first account automatically becomes admin."""
	return await register_user( db, data )


@router.post( "/login", response_model=Token, summary="Login and get JWT" )
async def login( form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends( get_db ) ) -> Token:
	"""Use username or email in the OAuth2 `username` field."""
	user = await authenticate_user( db, form.username, form.password )
	token = create_access_token( { "sub": str( user.id ), "role": user.role.value } )
	return Token( access_token=token )


@router.post( "/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Blacklist current JWT" )
async def logout( token: str = Depends( oauth2_scheme ),
		db: AsyncSession = Depends( get_db ),
		_: User = Depends( get_current_active_user ), ) -> None:
	payload = decode_access_token( token )
	expires_at = datetime.fromtimestamp( payload[ "exp" ], tz=timezone.utc )
	await logout_user( db, token, expires_at )
