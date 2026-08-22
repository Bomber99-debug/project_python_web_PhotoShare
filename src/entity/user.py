"""SQLAlchemy ORM model for application users."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.entity.base import Base
from src.entity.mixins import TimestampMixin
from src.entity.role import Role

if TYPE_CHECKING:
	from src.entity.comment import Comment
	from src.entity.photo import Photo
	from src.entity.rating import Rating


class User( TimestampMixin, Base ):
	"""Registered PhotoShare user."""

	__tablename__ = "users"

	id: Mapped[ int ] = mapped_column( primary_key=True )
	username: Mapped[ str ] = mapped_column( String( 50 ), unique=True, index=True, nullable=False )
	email: Mapped[ str ] = mapped_column( String( 255 ), unique=True, index=True, nullable=False )
	password_hash: Mapped[ str ] = mapped_column( String( 255 ), nullable=False )
	avatar_url: Mapped[ str | None ] = mapped_column( String( 512 ), nullable=True )
	role: Mapped[ Role ] = mapped_column( SAEnum( Role,
			name="user_role",
			native_enum=False,
			values_callable=lambda enum_cls: [ member.value for member in enum_cls ], ),
			default=Role.USER,
			nullable=False, )
	is_active: Mapped[ bool ] = mapped_column( Boolean, default=True, nullable=False )

	photos: Mapped[ list[ "Photo" ] ] = relationship( back_populates="owner", cascade="all, delete-orphan" )
	comments: Mapped[ list[ "Comment" ] ] = relationship( back_populates="user", cascade="all, delete-orphan" )
	ratings: Mapped[ list[ "Rating" ] ] = relationship( back_populates="user", cascade="all, delete-orphan" )

	def __repr__( self ) -> str:
		return f"<User id={self.id} username={self.username!r} role={self.role.value}>"
