"""Tag entity and photo-to-tag association table."""

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.entity.base import Base

if TYPE_CHECKING:
	from src.entity.photo import Photo

photo_tags = Table( "photo_tags",
		Base.metadata,
		Column( "photo_id", Integer, ForeignKey( "photos.id", ondelete="CASCADE" ), primary_key=True ),
		Column( "tag_id", Integer, ForeignKey( "tags.id", ondelete="CASCADE" ), primary_key=True ), )


class Tag( Base ):
	"""Globally unique normalized photo tag."""

	__tablename__ = "tags"

	id: Mapped[ int ] = mapped_column( primary_key=True )
	name: Mapped[ str ] = mapped_column( String( 100 ), unique=True, index=True, nullable=False )

	photos: Mapped[ list[ "Photo" ] ] = relationship( secondary=photo_tags, back_populates="tags" )

	def __repr__( self ) -> str:
		return f"<Tag id={self.id} name={self.name!r}>"
