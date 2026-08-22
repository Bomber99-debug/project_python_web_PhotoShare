"""Import all ORM entities so Alembic can discover their metadata."""

from src.entity.base import Base
from src.entity.blacklist import TokenBlacklist
from src.entity.comment import Comment
from src.entity.photo import Photo
from src.entity.photo_transform import PhotoTransform
from src.entity.rating import Rating
from src.entity.tag import Tag, photo_tags
from src.entity.user import User

__all__ = [
    "Base",
    "TokenBlacklist",
    "Comment",
    "Photo",
    "PhotoTransform",
    "Rating",
    "Tag",
    "User",
    "photo_tags",
]
