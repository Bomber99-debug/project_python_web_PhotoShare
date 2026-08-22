"""SQLAlchemy ORM model for user photos."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.entity.base import Base
from src.entity.mixins import TimestampMixin
from src.entity.tag import photo_tags

if TYPE_CHECKING:
    from src.entity.comment import Comment
    from src.entity.photo_transform import PhotoTransform
    from src.entity.rating import Rating
    from src.entity.tag import Tag
    from src.entity.user import User


class Photo(TimestampMixin, Base):
    """Photo metadata stored in PostgreSQL; image bytes live in Cloudinary."""

    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    public_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="photos")
    tags: Mapped[list["Tag"]] = relationship(secondary=photo_tags, back_populates="photos")
    comments: Mapped[list["Comment"]] = relationship(back_populates="photo", cascade="all, delete-orphan")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="photo", cascade="all, delete-orphan")
    transformed_photos: Mapped[list["PhotoTransform"]] = relationship(
        back_populates="photo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Photo id={self.id} user_id={self.user_id} public_id={self.public_id!r}>"
