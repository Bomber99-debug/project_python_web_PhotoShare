"""Password hashing and JWT helpers."""

from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from pwdlib import PasswordHash

from src.conf.config import settings

password_hasher = PasswordHash.recommended()


def hash_password( password: str ) -> str:
	return password_hasher.hash( password )


def verify_password( password: str, hashed_password: str ) -> bool:
	return password_hasher.verify( password, hashed_password )


def create_access_token( data: dict, expires_delta: timedelta | None = None ) -> str:
	payload = data.copy()
	payload[ "exp" ] = datetime.now( timezone.utc ) + (
			expires_delta or timedelta( minutes=settings.access_token_expire_minutes ))
	return jwt.encode( payload, settings.secret_key, algorithm=settings.algorithm )


def decode_access_token( token: str ) -> dict:
	try:
		return jwt.decode( token, settings.secret_key, algorithms=[ settings.algorithm ] )
	except JWTError as exc:
		raise ValueError( "Invalid or expired token" ) from exc
