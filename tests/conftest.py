import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from main import app
from src.database.db import get_db
from src.entity.base import Base

# Важливо імпортувати всі ORM-моделі до Base.metadata.create_all().
# Інакше SQLAlchemy не знатиме про частину таблиць.
from src.entity.blacklist import TokenBlacklist  # noqa: F401
from src.entity.comment import Comment  # noqa: F401
from src.entity.photo import Photo  # noqa: F401
from src.entity.photo_transform import PhotoTransform  # noqa: F401
from src.entity.rating import Rating  # noqa: F401
from src.entity.tag import Tag  # noqa: F401
from src.entity.user import User  # noqa: F401


TEST_PASSWORD = "Password123!"


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield factory

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(session_factory):
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(session_factory):
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def register_user():
    async def _register(
        client: AsyncClient,
        username: str,
        email: str,
        password: str = TEST_PASSWORD,
    ):
        return await client.post(
            "/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
            },
        )

    return _register


@pytest.fixture
def login_user():
    async def _login(
        client: AsyncClient,
        identity: str,
        password: str = TEST_PASSWORD,
    ):
        return await client.post(
            "/api/auth/login",
            data={
                "username": identity,
                "password": password,
            },
        )

    return _login


@pytest_asyncio.fixture
async def admin(client, register_user):
    response = await register_user(
        client,
        username="admin",
        email="admin@example.com",
    )

    assert response.status_code == 201, response.text

    return response.json()


@pytest_asyncio.fixture
async def admin_headers(client, admin, login_user):
    response = await login_user(
        client,
        identity=admin["username"],
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest_asyncio.fixture
async def user(client, admin, register_user):
    response = await register_user(
        client,
        username="user",
        email="user@example.com",
    )

    assert response.status_code == 201, response.text

    return response.json()


@pytest_asyncio.fixture
async def user_headers(client, user, login_user):
    response = await login_user(
        client,
        identity=user["username"],
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest_asyncio.fixture
async def other_user(client, user, register_user):
    response = await register_user(
        client,
        username="other",
        email="other@example.com",
    )

    assert response.status_code == 201, response.text

    return response.json()


@pytest_asyncio.fixture
async def other_user_headers(client, other_user, login_user):
    response = await login_user(
        client,
        identity=other_user["username"],
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest_asyncio.fixture
async def moderator(
    client,
    user,
    admin_headers,
    register_user,
    login_user,
):
    response = await register_user(
        client,
        username="moderator",
        email="moderator@example.com",
    )

    assert response.status_code == 201, response.text

    moderator_data = response.json()

    response = await client.patch(
        f"/api/users/{moderator_data['id']}/role",
        json={
            "role": "moderator",
        },
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text

    moderator_data = response.json()

    login_response = await login_user(
        client,
        identity=moderator_data["username"],
    )

    assert login_response.status_code == 200, login_response.text

    token = login_response.json()["access_token"]

    return {
        "data": moderator_data,
        "headers": {
            "Authorization": f"Bearer {token}",
        },
    }


@pytest.fixture
def mock_cloudinary(monkeypatch):
    state = {
        "uploaded": [],
        "deleted": [],
    }

    async def fake_upload(file):
        number = len(state["uploaded"]) + 1
        public_id = f"photoshare/test-{number}"
        image_url = f"https://example.com/photo-{number}.jpg"

        state["uploaded"].append(public_id)

        return {
            "image_url": image_url,
            "public_id": public_id,
        }

    async def fake_delete(public_id):
        state["deleted"].append(public_id)

    monkeypatch.setattr(
        "src.routes.photos.upload_photo",
        fake_upload,
    )
    monkeypatch.setattr(
        "src.routes.photos.delete_cloudinary_photo",
        fake_delete,
    )

    return state


@pytest.fixture
def create_photo(mock_cloudinary):
    async def _create(
        client: AsyncClient,
        headers: dict[str, str],
        description: str = "Test photo",
        tag: str | None = None,
    ):
        data = {
            "description": description,
        }

        if tag is not None:
            data["tags"] = tag

        response = await client.post(
            "/api/photos",
            headers=headers,
            data=data,
            files={
                "file": (
                    "photo.jpg",
                    b"fake-image-content",
                    "image/jpeg",
                ),
            },
        )

        assert response.status_code == 201, response.text

        return response.json()

    return _create