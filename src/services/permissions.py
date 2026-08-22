"""Small authorization predicates shared by routes."""

from src.entity.role import Role
from src.entity.user import User
from src.services.dependencies import require_roles

require_admin = require_roles(Role.ADMIN)
require_moderator_or_admin = require_roles(Role.MODERATOR, Role.ADMIN)


def can_modify_photo(photo_user_id: int, user: User) -> bool:
    return user.role == Role.ADMIN or user.id == photo_user_id


def can_edit_comment(comment_user_id: int, user: User) -> bool:
    return user.id == comment_user_id


def can_delete_comment(user: User) -> bool:
    return user.role in {Role.MODERATOR, Role.ADMIN}


def can_manage_rating(user: User) -> bool:
    return user.role in {Role.MODERATOR, Role.ADMIN}
