# PhotoShare API

PhotoShare is a FastAPI REST API for uploading and managing photos, tags, comments, user profiles, Cloudinary transformations and QR codes.

## Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2 async
- PostgreSQL 17
- Alembic
- Pydantic 2
- JWT authentication
- Cloudinary
- Docker Compose
- pytest

## Project structure

```text
src/
├── conf/        # application settings
├── database/    # SQLAlchemy engine and sessions
├── entity/      # ORM entities
├── repository/  # database queries only
├── routes/      # FastAPI HTTP endpoints
├── schemas/     # Pydantic request/response models
└── services/    # auth, permissions, Cloudinary, QR and helpers
```

## Local setup

```bash
pyenv local 3.13.7
poetry install
cp .env.example .env
```

Set Cloudinary credentials in `.env`, then start PostgreSQL locally or use Docker.

### Run with Docker Compose

```bash
docker compose up --build
```

The API will be available at:

- `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

The container applies `alembic upgrade head` before starting Uvicorn.

## Run without Docker

Start PostgreSQL and configure `DATABASE_URL`, then:

```bash
poetry run alembic upgrade head
poetry run uvicorn main:app --reload
```

## Authentication

The first registered account receives the `admin` role. Later users receive the `user` role.

Register:

```http
POST /api/auth/register
```

Login uses OAuth2 form fields. Put either username or email into the `username` field:

```http
POST /api/auth/login
```

Use the returned Bearer token in Swagger **Authorize**.

## Main endpoints

- `POST /api/photos` upload photo, description and up to five tags
- `GET /api/photos/{photo_id}` get photo details
- `PUT /api/photos/{photo_id}` edit description/tags
- `DELETE /api/photos/{photo_id}` delete own photo; admin may delete any
- `POST /api/photos/{photo_id}/comments` comment on a photo
- `PUT /api/comments/{comment_id}` edit own comment
- `DELETE /api/comments/{comment_id}` moderator/admin only
- `GET /api/users/{username}` public profile
- `GET|PUT /api/users/me` own profile
- `PATCH /api/users/{id}/ban` admin ban
- `PATCH /api/users/{id}/role` admin role change
- `POST /api/photos/{photo_id}/transform` save transformed URL and QR code
- `POST /api/photos/{photo_id}/ratings` optional rating
- `GET /api/photos/search` optional search/filtering

## Tests

```bash
poetry run pytest -v
poetry run pytest --cov=src --cov=main --cov-report=term-missing
```

The included tests are a starter suite for helpers and health endpoints. Expand API/repository integration tests before claiming the assignment's >90% coverage target.

## Notes

Image binary data is not stored in PostgreSQL. Cloudinary stores the media; PostgreSQL stores URLs, public IDs and metadata.
