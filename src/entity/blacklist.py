"""Server-side blacklist for logged-out access tokens."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, func, String
from sqlalchemy.orm import Mapped, mapped_column

from src.entity.base import Base


class TokenBlacklist( Base ):
	"""JWT blocked until its original expiration time."""

	__tablename__ = "token_blacklist"

	id: Mapped[ int ] = mapped_column( primary_key=True )
	token: Mapped[ str ] = mapped_column( String( 1024 ), unique=True, index=True, nullable=False )
	expires_at: Mapped[ datetime ] = mapped_column( DateTime( timezone=True ), nullable=False )
	created_at: Mapped[ datetime ] = mapped_column( DateTime( timezone=True ),
			default=lambda: datetime.now( timezone.utc ),
			server_default=func.now(),
			nullable=False, )
