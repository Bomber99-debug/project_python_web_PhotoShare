from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.entity.role import Role
from src.schemas.auth import UserRegister
from src.services import auth as auth_service


def make_db():
    return SimpleNamespace(
        commit=AsyncMock(),
    )


def make_user(
    *,
    user_id=1,
    role=Role.USER,
    is_active=True,
):
    return SimpleNamespace(
        id=user_id,
        username="user",
        email="user@example.com",
        password_hash="stored-hash",
        role=role,
        is_active=is_active,
    )


def register_data():
    return UserRegister(
        username="newuser",
        email="newuser@example.com",
        password="Password123!",
    )


async def test_register_first_user_becomes_admin(
    monkeypatch,
):
    db = make_db()
    data = register_data()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        AsyncMock(
            return_value=None
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        AsyncMock(
            return_value=None
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "count_users",
        AsyncMock(
            return_value=0
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "hash_password",
        lambda password: "hashed-password",
    )

    created_user = make_user(
        role=Role.ADMIN,
    )

    create_mock = AsyncMock(
        return_value=created_user,
    )

    monkeypatch.setattr(
        auth_service,
        "create_user",
        create_mock,
    )

    result = await auth_service.register_user(
        db,
        data,
    )

    assert result is created_user

    kwargs = create_mock.await_args.kwargs

    assert kwargs["username"] == data.username
    assert kwargs["email"] == data.email
    assert kwargs["password_hash"] == "hashed-password"
    assert kwargs["role"] == Role.ADMIN
    assert kwargs["is_active"] is True

    db.commit.assert_awaited_once()


async def test_register_non_first_user_becomes_user(
    monkeypatch,
):
    db = make_db()
    data = register_data()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        AsyncMock(
            return_value=None
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        AsyncMock(
            return_value=None
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "count_users",
        AsyncMock(
            return_value=5
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "hash_password",
        lambda password: "hashed",
    )

    create_mock = AsyncMock(
        return_value=make_user()
    )

    monkeypatch.setattr(
        auth_service,
        "create_user",
        create_mock,
    )

    await auth_service.register_user(
        db,
        data,
    )

    assert (
        create_mock.await_args.kwargs["role"]
        == Role.USER
    )


async def test_register_duplicate_email(
    monkeypatch,
):
    db = make_db()
    data = register_data()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        AsyncMock(
            return_value=make_user()
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.register_user(
            db,
            data,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "Email already registered"
    )


async def test_register_duplicate_username(
    monkeypatch,
):
    db = make_db()
    data = register_data()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        AsyncMock(
            return_value=None
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        AsyncMock(
            return_value=make_user()
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.register_user(
            db,
            data,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "Username already taken"
    )


async def test_authenticate_by_email(
    monkeypatch,
):
    db = make_db()
    user = make_user()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        AsyncMock(
            return_value=user
        ),
    )

    username_mock = AsyncMock()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        username_mock,
    )

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed: True,
    )

    result = await auth_service.authenticate_user(
        db,
        "user@example.com",
        "Password123!",
    )

    assert result is user

    username_mock.assert_not_awaited()


async def test_authenticate_by_username_fallback(
    monkeypatch,
):
    db = make_db()
    user = make_user()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        AsyncMock(
            return_value=None
        ),
    )

    username_mock = AsyncMock(
        return_value=user,
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        username_mock,
    )

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed: True,
    )

    result = await auth_service.authenticate_user(
        db,
        "user",
        "Password123!",
    )

    assert result is user

    username_mock.assert_awaited_once_with(
        db,
        "user",
    )


async def test_authenticate_unknown_user(
    monkeypatch,
):
    db = make_db()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        AsyncMock(
            return_value=None
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        AsyncMock(
            return_value=None
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.authenticate_user(
            db,
            "missing",
            "Password123!",
        )

    assert exc.value.status_code == 401
    assert (
        exc.value.detail
        == "Invalid username/email or password"
    )


async def test_authenticate_wrong_password(
    monkeypatch,
):
    db = make_db()
    user = make_user()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        AsyncMock(
            return_value=user
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed: False,
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.authenticate_user(
            db,
            "user@example.com",
            "WrongPassword",
        )

    assert exc.value.status_code == 401


async def test_authenticate_inactive_user(
    monkeypatch,
):
    db = make_db()

    user = make_user(
        is_active=False,
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        AsyncMock(
            return_value=user
        ),
    )

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed: True,
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.authenticate_user(
            db,
            "user@example.com",
            "Password123!",
        )

    assert exc.value.status_code == 401
    assert (
        exc.value.detail
        == "Inactive user account"
    )


async def test_logout_adds_token_to_blacklist(
    monkeypatch,
):
    db = make_db()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(hours=1)
    )

    monkeypatch.setattr(
        auth_service,
        "is_blacklisted",
        AsyncMock(
            return_value=False
        ),
    )

    add_mock = AsyncMock()

    monkeypatch.setattr(
        auth_service,
        "add_to_blacklist",
        add_mock,
    )

    await auth_service.logout_user(
        db,
        "access-token",
        expires_at,
    )

    add_mock.assert_awaited_once_with(
        db,
        "access-token",
        expires_at,
    )

    db.commit.assert_awaited_once()


async def test_logout_does_not_add_duplicate_token(
    monkeypatch,
):
    db = make_db()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(hours=1)
    )

    monkeypatch.setattr(
        auth_service,
        "is_blacklisted",
        AsyncMock(
            return_value=True
        ),
    )

    add_mock = AsyncMock()

    monkeypatch.setattr(
        auth_service,
        "add_to_blacklist",
        add_mock,
    )

    await auth_service.logout_user(
        db,
        "already-blacklisted",
        expires_at,
    )

    add_mock.assert_not_awaited()
    db.commit.assert_not_awaited()