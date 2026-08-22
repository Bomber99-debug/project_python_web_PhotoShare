"""SQLAlchemy ORM model for photo comments."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.entity.base import Base
from src.entity.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.entity.photo import Photo
    from src.entity.user import User


class Comment(TimestampMixin, Base):
    """Comment created by a user under a photo."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)

    photo: Mapped["Photo"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment id={self.id} photo_id={self.photo_id} user_id={self.user_id}>"
