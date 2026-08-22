from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.entity.role import Role
from src.routes import (
    auth,
    comments,
    photos,
    ratings,
    transforms,
    users,
)
from src.schemas.comment import CommentCreate, CommentUpdate
from src.schemas.photo import PhotoUpdate
from src.schemas.photo_transform import TransformRequest
from src.schemas.rating import RatingCreate
from src.schemas.user import UserRoleUpdate, UserUpdate


NOW = datetime.now(timezone.utc)


def make_db():
    return SimpleNamespace(
        commit=AsyncMock(),
        rollback=AsyncMock(),
        refresh=AsyncMock(),
    )


def make_user(
    *,
    user_id=1,
    username="user",
    email="user@example.com",
    role=Role.USER,
    is_active=True,
):
    return SimpleNamespace(
        id=user_id,
        username=username,
        email=email,
        avatar_url=None,
        role=role,
        is_active=is_active,
        password_hash="hashed-password",
        created_at=NOW,
        updated_at=NOW,
    )


def make_photo(
    *,
    photo_id=1,
    user_id=1,
    description="photo",
):
    return SimpleNamespace(
        id=photo_id,
        user_id=user_id,
        description=description,
        image_url="https://example.com/photo.jpg",
        public_id="photo-public-id",
        created_at=NOW,
        updated_at=NOW,
        tags=[],
        comments=[],
        ratings=[],
        transformed_photos=[],
    )


def make_comment(
    *,
    comment_id=1,
    photo_id=1,
    user_id=1,
    text="comment",
):
    return SimpleNamespace(
        id=comment_id,
        photo_id=photo_id,
        user_id=user_id,
        text=text,
        created_at=NOW,
        updated_at=NOW,
    )


def make_rating(
    *,
    rating_id=1,
    photo_id=1,
    user_id=2,
    value=5,
):
    return SimpleNamespace(
        id=rating_id,
        photo_id=photo_id,
        user_id=user_id,
        value=value,
        created_at=NOW,
    )


def make_transform(
    *,
    transform_id=1,
    photo_id=1,
):
    return SimpleNamespace(
        id=transform_id,
        photo_id=photo_id,
        transformation_type="w_300",
        transformed_url="https://example.com/transformed.jpg",
        qr_code_url="https://example.com/qr.png",
        created_at=NOW,
    )


def test_build_photo_detail_with_rating():
    photo = make_photo()

    photo.ratings = [
        SimpleNamespace(value=5),
        SimpleNamespace(value=3),
    ]

    result = photos.build_detail(photo)

    assert result.id == photo.id
    assert result.rating_summary is not None
    assert result.rating_summary.average_rating == 4
    assert result.rating_summary.ratings_count == 2


async def test_direct_upload_photo_success(monkeypatch):
    db = make_db()
    user = make_user()
    photo = make_photo()

    file = SimpleNamespace(
        content_type="image/jpeg",
    )

    upload_mock = AsyncMock(
        return_value={
            "image_url": photo.image_url,
            "public_id": photo.public_id,
        }
    )

    create_mock = AsyncMock(
        return_value=photo,
    )

    tag = SimpleNamespace(
        id=1,
        name="nature",
    )

    get_tags_mock = AsyncMock(
        return_value=[tag],
    )

    set_tags_mock = AsyncMock(
        return_value=photo,
    )

    monkeypatch.setattr(
        photos,
        "upload_photo",
        upload_mock,
    )
    monkeypatch.setattr(
        photos,
        "create_photo",
        create_mock,
    )
    monkeypatch.setattr(
        photos,
        "get_or_create_tags",
        get_tags_mock,
    )
    monkeypatch.setattr(
        photos,
        "set_photo_tags",
        set_tags_mock,
    )

    result = await photos.upload_user_photo(
        file=file,
        description="Test photo",
        tags=["Nature"],
        db=db,
        user=user,
    )

    assert result is photo

    upload_mock.assert_awaited_once()
    create_mock.assert_awaited_once()

    get_tags_mock.assert_awaited_once_with(
        db,
        ["nature"],
    )

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


async def test_direct_upload_photo_cleanup(monkeypatch):
    db = make_db()
    user = make_user()

    file = SimpleNamespace(
        content_type="image/jpeg",
    )

    monkeypatch.setattr(
        photos,
        "upload_photo",
        AsyncMock(
            return_value={
                "image_url": "https://example.com/photo.jpg",
                "public_id": "uploaded-photo",
            }
        ),
    )

    monkeypatch.setattr(
        photos,
        "create_photo",
        AsyncMock(
            side_effect=RuntimeError("database failure")
        ),
    )

    delete_mock = AsyncMock(
        side_effect=RuntimeError("cloudinary failure")
    )

    monkeypatch.setattr(
        photos,
        "delete_cloudinary_photo",
        delete_mock,
    )

    with pytest.raises(
        RuntimeError,
        match="database failure",
    ):
        await photos.upload_user_photo(
            file=file,
            description=None,
            tags=None,
            db=db,
            user=user,
        )

    db.rollback.assert_awaited_once()

    delete_mock.assert_awaited_once_with(
        "uploaded-photo"
    )


async def test_direct_get_photo(monkeypatch):
    db = make_db()
    photo = make_photo()

    get_mock = AsyncMock(
        return_value=photo,
    )

    monkeypatch.setattr(
        photos,
        "get_photo_detail",
        get_mock,
    )

    result = await photos.get_photo(
        photo_id=1,
        db=db,
    )

    assert result.id == 1

    get_mock.return_value = None

    with pytest.raises(HTTPException) as exc:
        await photos.get_photo(
            photo_id=999,
            db=db,
        )

    assert exc.value.status_code == 404


async def test_direct_update_photo(monkeypatch):
    db = make_db()
    user = make_user()
    photo = make_photo()

    monkeypatch.setattr(
        photos,
        "get_photo_by_id",
        AsyncMock(
            return_value=photo
        ),
    )

    monkeypatch.setattr(
        photos,
        "can_modify_photo",
        lambda photo_user_id, current_user: True,
    )

    update_mock = AsyncMock(
        return_value=photo,
    )

    tag = SimpleNamespace(
        id=1,
        name="nature",
    )

    get_tags_mock = AsyncMock(
        return_value=[tag],
    )

    set_tags_mock = AsyncMock(
        return_value=photo,
    )

    monkeypatch.setattr(
        photos,
        "update_photo",
        update_mock,
    )
    monkeypatch.setattr(
        photos,
        "get_or_create_tags",
        get_tags_mock,
    )
    monkeypatch.setattr(
        photos,
        "set_photo_tags",
        set_tags_mock,
    )

    result = await photos.update_user_photo(
        photo_id=1,
        data=PhotoUpdate(
            description="Changed",
            tags=["Nature"],
        ),
        db=db,
        user=user,
    )

    assert result is photo

    update_mock.assert_awaited_once()
    get_tags_mock.assert_awaited_once()
    set_tags_mock.assert_awaited_once()

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


async def test_direct_update_photo_errors(monkeypatch):
    db = make_db()
    user = make_user()
    photo = make_photo()

    get_mock = AsyncMock(
        return_value=None,
    )

    monkeypatch.setattr(
        photos,
        "get_photo_by_id",
        get_mock,
    )

    with pytest.raises(HTTPException) as exc:
        await photos.update_user_photo(
            photo_id=999,
            data=PhotoUpdate(
                description="Changed",
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 404

    get_mock.return_value = photo

    monkeypatch.setattr(
        photos,
        "can_modify_photo",
        lambda photo_user_id, current_user: False,
    )

    with pytest.raises(HTTPException) as exc:
        await photos.update_user_photo(
            photo_id=1,
            data=PhotoUpdate(
                description="Changed",
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 403

    monkeypatch.setattr(
        photos,
        "can_modify_photo",
        lambda photo_user_id, current_user: True,
    )

    def broken_normalizer(_):
        raise ValueError("Invalid tags")

    monkeypatch.setattr(
        photos,
        "normalize_tag_names",
        broken_normalizer,
    )

    with pytest.raises(HTTPException) as exc:
        await photos.update_user_photo(
            photo_id=1,
            data=PhotoUpdate(
                tags=["valid"],
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid tags"


async def test_direct_delete_photo(monkeypatch):
    db = make_db()
    user = make_user()
    photo = make_photo()

    get_mock = AsyncMock(
        return_value=photo,
    )

    delete_cloud_mock = AsyncMock()
    delete_db_mock = AsyncMock()

    monkeypatch.setattr(
        photos,
        "get_photo_by_id",
        get_mock,
    )

    monkeypatch.setattr(
        photos,
        "can_modify_photo",
        lambda photo_user_id, current_user: True,
    )

    monkeypatch.setattr(
        photos,
        "delete_cloudinary_photo",
        delete_cloud_mock,
    )

    monkeypatch.setattr(
        photos,
        "delete_photo",
        delete_db_mock,
    )

    result = await photos.delete_user_photo(
        photo_id=1,
        db=db,
        user=user,
    )

    assert result == {
        "message": "Photo deleted successfully",
    }

    delete_cloud_mock.assert_awaited_once_with(
        photo.public_id
    )

    delete_db_mock.assert_awaited_once_with(
        db,
        photo,
    )

    db.commit.assert_awaited_once()


async def test_direct_delete_photo_errors(monkeypatch):
    db = make_db()
    user = make_user()
    photo = make_photo()

    get_mock = AsyncMock(
        return_value=None,
    )

    monkeypatch.setattr(
        photos,
        "get_photo_by_id",
        get_mock,
    )

    with pytest.raises(HTTPException) as exc:
        await photos.delete_user_photo(
            photo_id=999,
            db=db,
            user=user,
        )

    assert exc.value.status_code == 404

    get_mock.return_value = photo

    monkeypatch.setattr(
        photos,
        "can_modify_photo",
        lambda photo_user_id, current_user: False,
    )

    with pytest.raises(HTTPException) as exc:
        await photos.delete_user_photo(
            photo_id=1,
            db=db,
            user=user,
        )

    assert exc.value.status_code == 403


async def test_direct_comment_crud(monkeypatch):
    db = make_db()
    user = make_user()
    photo = make_photo()
    comment = make_comment()

    monkeypatch.setattr(
        comments,
        "get_photo_by_id",
        AsyncMock(
            return_value=photo
        ),
    )

    create_mock = AsyncMock(
        return_value=comment,
    )

    monkeypatch.setattr(
        comments,
        "create_comment",
        create_mock,
    )

    result = await comments.create_photo_comment(
        photo_id=1,
        data=CommentCreate(
            text="Comment",
        ),
        db=db,
        user=user,
    )

    assert result is comment

    list_mock = AsyncMock(
        return_value=[comment],
    )

    monkeypatch.setattr(
        comments,
        "list_photo_comments",
        list_mock,
    )

    result = await comments.get_comments(
        photo_id=1,
        db=db,
    )

    assert result == [comment]

    monkeypatch.setattr(
        comments,
        "get_comment",
        AsyncMock(
            return_value=comment
        ),
    )

    monkeypatch.setattr(
        comments,
        "can_edit_comment",
        lambda comment_user_id, current_user: True,
    )

    updated_comment = make_comment(
        text="Updated",
    )

    update_mock = AsyncMock(
        return_value=updated_comment,
    )

    monkeypatch.setattr(
        comments,
        "update_comment",
        update_mock,
    )

    result = await comments.edit_comment(
        comment_id=1,
        data=CommentUpdate(
            text="Updated",
        ),
        db=db,
        user=user,
    )

    assert result.text == "Updated"

    monkeypatch.setattr(
        comments,
        "can_delete_comment",
        lambda current_user: True,
    )

    delete_mock = AsyncMock()

    monkeypatch.setattr(
        comments,
        "delete_comment",
        delete_mock,
    )

    result = await comments.remove_comment(
        comment_id=1,
        db=db,
        user=user,
    )

    assert result == {
        "message": "Comment deleted successfully",
    }


async def test_direct_comment_errors(monkeypatch):
    db = make_db()
    user = make_user()
    comment = make_comment()

    get_photo_mock = AsyncMock(
        return_value=None,
    )

    monkeypatch.setattr(
        comments,
        "get_photo_by_id",
        get_photo_mock,
    )

    with pytest.raises(HTTPException) as exc:
        await comments.create_photo_comment(
            photo_id=999,
            data=CommentCreate(
                text="Comment",
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        await comments.get_comments(
            photo_id=999,
            db=db,
        )

    assert exc.value.status_code == 404

    get_comment_mock = AsyncMock(
        return_value=None,
    )

    monkeypatch.setattr(
        comments,
        "get_comment",
        get_comment_mock,
    )

    with pytest.raises(HTTPException) as exc:
        await comments.edit_comment(
            comment_id=999,
            data=CommentUpdate(
                text="Changed",
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 404

    get_comment_mock.return_value = comment

    monkeypatch.setattr(
        comments,
        "can_edit_comment",
        lambda comment_user_id, current_user: False,
    )

    with pytest.raises(HTTPException) as exc:
        await comments.edit_comment(
            comment_id=1,
            data=CommentUpdate(
                text="Changed",
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 403

    get_comment_mock.return_value = None

    with pytest.raises(HTTPException) as exc:
        await comments.remove_comment(
            comment_id=999,
            db=db,
            user=user,
        )

    assert exc.value.status_code == 404

    get_comment_mock.return_value = comment

    monkeypatch.setattr(
        comments,
        "can_delete_comment",
        lambda current_user: False,
    )

    with pytest.raises(HTTPException) as exc:
        await comments.remove_comment(
            comment_id=1,
            db=db,
            user=user,
        )

    assert exc.value.status_code == 403


async def test_direct_rating_crud(monkeypatch):
    db = make_db()

    owner = make_user(
        user_id=1,
    )

    rater = make_user(
        user_id=2,
    )

    photo = make_photo(
        user_id=owner.id,
    )

    rating = make_rating(
        user_id=rater.id,
    )

    monkeypatch.setattr(
        ratings,
        "get_photo_by_id",
        AsyncMock(
            return_value=photo
        ),
    )

    monkeypatch.setattr(
        ratings,
        "get_user_photo_rating",
        AsyncMock(
            return_value=None
        ),
    )

    create_mock = AsyncMock(
        return_value=rating,
    )

    monkeypatch.setattr(
        ratings,
        "create_rating",
        create_mock,
    )

    result = await ratings.rate_photo(
        photo_id=1,
        data=RatingCreate(
            value=5,
        ),
        db=db,
        user=rater,
    )

    assert result is rating

    monkeypatch.setattr(
        ratings,
        "get_average",
        AsyncMock(
            return_value=(4.5, 2)
        ),
    )

    summary = await ratings.rating_summary(
        photo_id=1,
        db=db,
    )

    assert summary.average_rating == 4.5
    assert summary.ratings_count == 2

    monkeypatch.setattr(
        ratings,
        "list_photo_ratings",
        AsyncMock(
            return_value=[rating]
        ),
    )

    details = await ratings.rating_details(
        photo_id=1,
        db=db,
        _=rater,
    )

    assert details == [rating]

    monkeypatch.setattr(
        ratings,
        "get_rating",
        AsyncMock(
            return_value=rating
        ),
    )

    monkeypatch.setattr(
        ratings,
        "can_manage_rating",
        lambda current_user: True,
    )

    delete_mock = AsyncMock()

    monkeypatch.setattr(
        ratings,
        "delete_rating",
        delete_mock,
    )

    result = await ratings.remove_rating(
        rating_id=1,
        db=db,
        user=rater,
    )

    assert result == {
        "message": "Rating deleted successfully",
    }


async def test_direct_rating_errors(monkeypatch):
    db = make_db()

    owner = make_user(
        user_id=1,
    )

    other = make_user(
        user_id=2,
    )

    photo = make_photo(
        user_id=owner.id,
    )

    get_photo_mock = AsyncMock(
        return_value=None,
    )

    monkeypatch.setattr(
        ratings,
        "get_photo_by_id",
        get_photo_mock,
    )

    with pytest.raises(HTTPException) as exc:
        await ratings.rate_photo(
            photo_id=999,
            data=RatingCreate(
                value=5,
            ),
            db=db,
            user=other,
        )

    assert exc.value.status_code == 404

    get_photo_mock.return_value = photo

    with pytest.raises(HTTPException) as exc:
        await ratings.rate_photo(
            photo_id=1,
            data=RatingCreate(
                value=5,
            ),
            db=db,
            user=owner,
        )

    assert exc.value.status_code == 400

    monkeypatch.setattr(
        ratings,
        "get_user_photo_rating",
        AsyncMock(
            return_value=make_rating()
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await ratings.rate_photo(
            photo_id=1,
            data=RatingCreate(
                value=5,
            ),
            db=db,
            user=other,
        )

    assert exc.value.status_code == 400

    get_photo_mock.return_value = None

    with pytest.raises(HTTPException) as exc:
        await ratings.rating_summary(
            photo_id=999,
            db=db,
        )

    assert exc.value.status_code == 404

    get_rating_mock = AsyncMock(
        return_value=None,
    )

    monkeypatch.setattr(
        ratings,
        "get_rating",
        get_rating_mock,
    )

    with pytest.raises(HTTPException) as exc:
        await ratings.remove_rating(
            rating_id=999,
            db=db,
            user=other,
        )

    assert exc.value.status_code == 404

    get_rating_mock.return_value = make_rating()

    monkeypatch.setattr(
        ratings,
        "can_manage_rating",
        lambda current_user: False,
    )

    with pytest.raises(HTTPException) as exc:
        await ratings.remove_rating(
            rating_id=1,
            db=db,
            user=other,
        )

    assert exc.value.status_code == 403


async def test_direct_transform_crud(monkeypatch):
    db = make_db()
    user = make_user()
    photo = make_photo()
    transform = make_transform()

    monkeypatch.setattr(
        transforms,
        "get_photo_by_id",
        AsyncMock(
            return_value=photo
        ),
    )

    monkeypatch.setattr(
        transforms,
        "can_modify_photo",
        lambda photo_user_id, current_user: True,
    )

    monkeypatch.setattr(
        transforms,
        "validate_transformation",
        lambda data: None,
    )

    monkeypatch.setattr(
        transforms,
        "transformed_url",
        lambda public_id, data:
        "https://example.com/transformed.jpg",
    )

    monkeypatch.setattr(
        transforms,
        "generate_qr_code",
        AsyncMock(
            return_value="https://example.com/qr.png"
        ),
    )

    monkeypatch.setattr(
        transforms,
        "transformation_type",
        lambda data: "w_300",
    )

    create_mock = AsyncMock(
        return_value=transform,
    )

    monkeypatch.setattr(
        transforms,
        "create_transform",
        create_mock,
    )

    result = await transforms.create_photo_transform(
        photo_id=1,
        data=TransformRequest(
            width=300,
        ),
        db=db,
        user=user,
    )

    assert result is transform

    monkeypatch.setattr(
        transforms,
        "list_transforms",
        AsyncMock(
            return_value=[transform]
        ),
    )

    result = await transforms.get_photo_transforms(
        photo_id=1,
        db=db,
    )

    assert result == [transform]

    monkeypatch.setattr(
        transforms,
        "get_transform",
        AsyncMock(
            return_value=transform
        ),
    )

    result = await transforms.get_transform_by_id(
        transform_id=1,
        db=db,
    )

    assert result is transform


async def test_direct_transform_errors(monkeypatch):
    db = make_db()
    user = make_user()
    photo = make_photo()

    get_photo_mock = AsyncMock(
        return_value=None,
    )

    monkeypatch.setattr(
        transforms,
        "get_photo_by_id",
        get_photo_mock,
    )

    with pytest.raises(HTTPException) as exc:
        await transforms.create_photo_transform(
            photo_id=999,
            data=TransformRequest(
                width=300,
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 404

    get_photo_mock.return_value = photo

    monkeypatch.setattr(
        transforms,
        "can_modify_photo",
        lambda photo_user_id, current_user: False,
    )

    with pytest.raises(HTTPException) as exc:
        await transforms.create_photo_transform(
            photo_id=1,
            data=TransformRequest(
                width=300,
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 403

    monkeypatch.setattr(
        transforms,
        "can_modify_photo",
        lambda photo_user_id, current_user: True,
    )

    def invalid_transform(_):
        raise ValueError(
            "At least one transformation option is required"
        )

    monkeypatch.setattr(
        transforms,
        "validate_transformation",
        invalid_transform,
    )

    with pytest.raises(HTTPException) as exc:
        await transforms.create_photo_transform(
            photo_id=1,
            data=TransformRequest(
                width=300,
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 400

    get_photo_mock.return_value = None

    with pytest.raises(HTTPException) as exc:
        await transforms.get_photo_transforms(
            photo_id=999,
            db=db,
        )

    assert exc.value.status_code == 404

    monkeypatch.setattr(
        transforms,
        "get_transform",
        AsyncMock(
            return_value=None
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await transforms.get_transform_by_id(
            transform_id=999,
            db=db,
        )

    assert exc.value.status_code == 404


async def test_direct_user_routes(monkeypatch):
    db = make_db()

    user = make_user()

    result = await users.get_me(
        user=user,
    )

    assert result is user

    monkeypatch.setattr(
        users,
        "get_user_by_email",
        AsyncMock(
            return_value=None
        ),
    )

    monkeypatch.setattr(
        users,
        "get_user_by_username",
        AsyncMock(
            return_value=None
        ),
    )

    monkeypatch.setattr(
        users,
        "hash_password",
        lambda password: "new-hash",
    )

    update_mock = AsyncMock(
        return_value=user,
    )

    monkeypatch.setattr(
        users,
        "update_user",
        update_mock,
    )

    result = await users.update_me(
        data=UserUpdate(
            username="changed",
            email="changed@example.com",
            password="NewPassword123!",
        ),
        db=db,
        user=user,
    )

    assert result is user

    changes = update_mock.await_args.args[2]

    assert changes["username"] == "changed"
    assert changes["email"] == "changed@example.com"
    assert changes["password_hash"] == "new-hash"
    assert "password" not in changes


async def test_direct_user_update_errors(monkeypatch):
    db = make_db()
    user = make_user()

    with pytest.raises(HTTPException) as exc:
        await users.update_me(
            data=UserUpdate(),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 400

    monkeypatch.setattr(
        users,
        "get_user_by_email",
        AsyncMock(
            return_value=make_user(
                user_id=2,
                email="used@example.com",
            )
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await users.update_me(
            data=UserUpdate(
                email="used@example.com",
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 400

    monkeypatch.setattr(
        users,
        "get_user_by_email",
        AsyncMock(
            return_value=None
        ),
    )

    monkeypatch.setattr(
        users,
        "get_user_by_username",
        AsyncMock(
            return_value=make_user(
                user_id=2,
                username="taken",
            )
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await users.update_me(
            data=UserUpdate(
                username="taken",
            ),
            db=db,
            user=user,
        )

    assert exc.value.status_code == 400


async def test_direct_public_profile(monkeypatch):
    db = make_db()
    user = make_user()

    get_mock = AsyncMock(
        return_value=user,
    )

    monkeypatch.setattr(
        users,
        "get_user_by_username",
        get_mock,
    )

    monkeypatch.setattr(
        users,
        "count_user_photos",
        AsyncMock(
            return_value=7
        ),
    )

    result = await users.public_profile(
        username=user.username,
        db=db,
    )

    assert result.id == user.id
    assert result.username == user.username
    assert result.uploaded_photos_count == 7

    get_mock.return_value = None

    with pytest.raises(HTTPException) as exc:
        await users.public_profile(
            username="missing",
            db=db,
        )

    assert exc.value.status_code == 404


async def test_direct_admin_user_routes(monkeypatch):
    db = make_db()

    admin_user = make_user(
        role=Role.ADMIN,
    )

    target = make_user(
        user_id=2,
        username="target",
        email="target@example.com",
    )

    active_mock = AsyncMock(
        return_value=target,
    )

    monkeypatch.setattr(
        users,
        "set_user_active",
        active_mock,
    )

    result = await users.ban_user(
        user_id=target.id,
        db=db,
        _=admin_user,
    )

    assert result.is_active is False

    result = await users.unban_user(
        user_id=target.id,
        db=db,
        _=admin_user,
    )

    assert result.is_active is True

    role_mock = AsyncMock(
        return_value=target,
    )

    monkeypatch.setattr(
        users,
        "set_user_role",
        role_mock,
    )

    result = await users.change_role(
        user_id=target.id,
        data=UserRoleUpdate(
            role=Role.MODERATOR,
        ),
        db=db,
        _=admin_user,
    )

    assert result is target


async def test_direct_admin_user_routes_not_found(
    monkeypatch,
):
    db = make_db()

    admin_user = make_user(
        role=Role.ADMIN,
    )

    monkeypatch.setattr(
        users,
        "set_user_active",
        AsyncMock(
            return_value=None
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await users.ban_user(
            user_id=999,
            db=db,
            _=admin_user,
        )

    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        await users.unban_user(
            user_id=999,
            db=db,
            _=admin_user,
        )

    assert exc.value.status_code == 404

    monkeypatch.setattr(
        users,
        "set_user_role",
        AsyncMock(
            return_value=None
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await users.change_role(
            user_id=999,
            data=UserRoleUpdate(
                role=Role.MODERATOR,
            ),
            db=db,
            _=admin_user,
        )

    assert exc.value.status_code == 404


async def test_direct_logout_route(monkeypatch):
    db = make_db()
    user = make_user()

    expiration = int(
        NOW.timestamp()
    )

    monkeypatch.setattr(
        auth,
        "decode_access_token",
        lambda token: {
            "sub": "1",
            "role": "user",
            "exp": expiration,
        },
    )

    logout_mock = AsyncMock()

    monkeypatch.setattr(
        auth,
        "logout_user",
        logout_mock,
    )

    await auth.logout(
        token="token",
        db=db,
        _=user,
    )

    logout_mock.assert_awaited_once()

    args = logout_mock.await_args.args

    assert args[0] is db
    assert args[1] == "token"
    assert args[2].tzinfo is not None