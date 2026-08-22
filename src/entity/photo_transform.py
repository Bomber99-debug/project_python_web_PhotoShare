"""Stored Cloudinary transformation URLs and their QR codes."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.entity.base import Base

if TYPE_CHECKING:
	from src.entity.photo import Photo


class PhotoTransform( Base ):
	"""A persisted transformed photo URL and QR code URL."""

	__tablename__ = "photo_transforms"

	id: Mapped[ int ] = mapped_column( primary_key=True )
	photo_id: Mapped[ int ] = mapped_column( ForeignKey( "photos.id", ondelete="CASCADE" ), index=True )
	transformation_type: Mapped[ str ] = mapped_column( String( 100 ), nullable=False )
	transformed_url: Mapped[ str ] = mapped_column( String( 512 ), nullable=False )
	qr_code_url: Mapped[ str | None ] = mapped_column( String( 512 ), nullable=True )
	created_at: Mapped[ datetime ] = mapped_column( DateTime( timezone=True ),
			default=lambda: datetime.now( timezone.utc ),
			server_default=func.now(),
			nullable=False, )

	photo: Mapped[ "Photo" ] = relationship( back_populates="transformed_photos" )

	def __repr__( self ) -> str:
		return f"<PhotoTransform id={self.id} photo_id={self.photo_id} type={self.transformation_type!r}>"
