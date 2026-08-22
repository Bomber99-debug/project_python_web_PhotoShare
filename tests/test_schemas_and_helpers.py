from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.entity.role import Role
from src.schemas.comment import CommentCreate
from src.schemas.photo import PhotoUpdate
from src.schemas.photo_transform import TransformRequest
from src.schemas.rating import RatingCreate
from src.services.permissions import can_delete_comment, can_edit_comment, can_manage_rating, can_modify_photo
from src.services.tags import normalize_tag_name, normalize_tag_names


def test_tag_normalization():
    assert normalize_tag_name("  Cats ") == "cats"
    assert normalize_tag_names([" Cats ", "cats", "DOGS"]) == ["cats", "dogs"]


def test_invalid_tag():
    with pytest.raises(ValueError):
        normalize_tag_name("   ")


def test_photo_schema_normalizes_tags():
    data = PhotoUpdate(tags=[" One ", "TWO", "one"])
    assert data.tags == ["one", "two"]


def test_comment_schema_strips_text():
    assert CommentCreate(text=" hi ").text == "hi"


def test_rating_range():
    assert RatingCreate(value=5).value == 5
    with pytest.raises(ValidationError):
        RatingCreate(value=6)


def test_transform_effect_validation():
    assert TransformRequest(effect=" Sepia ").effect == "sepia"
    with pytest.raises(ValidationError):
        TransformRequest(effect="explode")


def test_permission_matrix():
    owner = SimpleNamespace(id=1, role=Role.USER)
    other = SimpleNamespace(id=2, role=Role.USER)
    mod = SimpleNamespace(id=3, role=Role.MODERATOR)
    admin = SimpleNamespace(id=4, role=Role.ADMIN)
    assert can_modify_photo(1, owner)
    assert not can_modify_photo(1, other)
    assert can_modify_photo(1, admin)
    assert can_edit_comment(1, owner)
    assert not can_edit_comment(1, other)
    assert not can_delete_comment(owner)
    assert can_delete_comment(mod)
    assert can_delete_comment(admin)
    assert can_manage_rating(mod)
