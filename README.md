# PhotoShare API

PhotoShare API — REST API для зберігання та керування фотографіями, користувачами, тегами, коментарями, рейтингами й трансформаціями зображень.

Застосунок побудований на FastAPI, використовує PostgreSQL через асинхронний SQLAlchemy, JWT для автентифікації та Cloudinary для зберігання й трансформації зображень.

API підтримує систему ролей, керування доступом, блокування користувачів, коментарі, рейтинги, пошук і фільтрацію фотографій, генерацію QR-кодів для трансформованих зображень.

---

## Основні можливості

### Користувачі та автентифікація

- реєстрація користувачів;
- автентифікація за `username` або `email`;
- JWT Bearer authentication;
- перший зареєстрований користувач автоматично отримує роль `admin`;
- наступні користувачі отримують роль `user`;
- підтримуються ролі:
  - `user`;
  - `moderator`;
  - `admin`;
- редагування власного профілю;
- перегляд публічного профілю користувача;
- блокування та розблокування користувачів адміністратором;
- зміна ролі користувача адміністратором;
- заблокований користувач не може авторизуватися;
- logout із додаванням JWT до blacklist.

### Фотографії

- завантаження фотографій у Cloudinary;
- зберігання URL, `public_id` та метаданих у PostgreSQL;
- підтримка JPEG, PNG, GIF та WebP;
- перегляд фотографії;
- редагування опису;
- редагування тегів;
- видалення фотографії;
- користувач керує власними фотографіями;
- адміністратор може редагувати та видаляти фотографії інших користувачів.

### Теги

- до 5 тегів на одну фотографію;
- автоматична нормалізація тегів;
- теги зберігаються в нижньому регістрі;
- дублікати тегів для однієї фотографії видаляються;
- однакові теги глобально не дублюються в базі даних.

### Коментарі

- створення коментарів до фотографій;
- перегляд коментарів;
- автор може редагувати власний коментар;
- `moderator` та `admin` можуть видаляти коментарі;
- зберігається час створення та редагування коментаря.

### Рейтинги

- оцінка фотографії від 1 до 5;
- користувач може оцінити фотографію лише один раз;
- власну фотографію оцінювати не можна;
- розрахунок середнього рейтингу;
- підрахунок кількості оцінок;
- `moderator` та `admin` можуть переглядати детальні оцінки;
- `moderator` та `admin` можуть видаляти оцінки.

### Пошук і фільтрація

Підтримується:

- пошук за текстом в описі;
- пошук за тегом;
- фільтрація за мінімальним рейтингом;
- фільтрація за датою;
- сортування за датою;
- сортування за рейтингом;
- сортування за зростанням або спаданням;
- фільтрація за користувачем для `moderator` та `admin`.

### Трансформації зображень

Cloudinary використовується для створення трансформованих URL.

Підтримуються:

- зміна ширини;
- зміна висоти;
- crop-режими;
- обертання;
- ефекти;
- зміна формату.

Доступні crop-режими:

- `scale`;
- `fit`;
- `fill`;
- `crop`;
- `thumb`;
- `pad`;
- `limit`.

Доступні ефекти:

- `grayscale`;
- `sepia`;
- `blur`;
- `sharpen`;
- `pixelate`;
- `oil_paint`;
- `cartoonify`.

Доступні формати:

- `jpg`;
- `png`;
- `webp`;
- `gif`;
- `auto`.

Для трансформованого зображення:

1. генерується Cloudinary URL;
2. створюється QR-код;
3. QR-код завантажується в Cloudinary;
4. URL трансформованого зображення та QR-коду зберігаються в PostgreSQL.

---

## Технології

- Python 3.13;
- FastAPI;
- Uvicorn;
- SQLAlchemy 2;
- AsyncPG;
- PostgreSQL 17;
- Alembic;
- Pydantic 2;
- Pydantic Settings;
- JWT (`python-jose`);
- Argon2 / `pwdlib`;
- Cloudinary;
- QRCode;
- Docker;
- Docker Compose;
- Poetry;
- pytest;
- pytest-asyncio;
- pytest-cov;
- HTTPX;
- SQLite / aiosqlite для тестового середовища.

Проєкт вимагає Python:

```text
>=3.13,<3.14
```

У `.python-version` використовується:

```text
3.13.7
```

---

## Структура проєкту

```text
project_python_web_PhotoShare/
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── scripts/
│   └── docker-entrypoint.sh
│
├── src/
│   ├── conf/
│   │   └── config.py
│   │
│   ├── database/
│   │   └── db.py
│   │
│   ├── entity/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── blacklist.py
│   │   ├── comment.py
│   │   ├── mixins.py
│   │   ├── photo.py
│   │   ├── photo_transform.py
│   │   ├── rating.py
│   │   ├── role.py
│   │   ├── tag.py
│   │   └── user.py
│   │
│   ├── repository/
│   │   ├── blacklist.py
│   │   ├── comments.py
│   │   ├── photos.py
│   │   ├── ratings.py
│   │   └── users.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── comments.py
│   │   ├── photos.py
│   │   ├── ratings.py
│   │   ├── search.py
│   │   ├── transforms.py
│   │   └── users.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── comment.py
│   │   ├── photo.py
│   │   ├── photo_transform.py
│   │   ├── rating.py
│   │   ├── tag.py
│   │   └── user.py
│   │
│   └── services/
│       ├── auth.py
│       ├── cloudinary.py
│       ├── dependencies.py
│       ├── permissions.py
│       ├── qr.py
│       ├── security.py
│       └── tags.py
│
├── tests/
├── .dockerignore
├── .env.example
├── .gitignore
├── .python-version
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── main.py
├── poetry.lock
├── pyproject.toml
└── README.md
```

Основні шари застосунку:

```text
routes
   ↓
services
   ↓
repository
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL
```

- `routes` — HTTP endpoints FastAPI;
- `schemas` — Pydantic-моделі запитів та відповідей;
- `services` — бізнес-логіка, авторизація, Cloudinary, QR-коди;
- `repository` — запити до бази даних;
- `entity` — SQLAlchemy ORM-моделі;
- `database` — асинхронний engine та сесії;
- `conf` — конфігурація застосунку.

---

## Клонування репозиторію

```bash
git clone https://github.com/Bomber99-debug/project_python_web_PhotoShare.git
cd project_python_web_PhotoShare
```

---

## Налаштування середовища

Створити `.env` на основі прикладу:

```bash
cp .env.example .env
```

Приклад:

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST_IP=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_CONTAINER_PORT=5432
POSTGRES_DB=photoshare

# Local database URL
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST_IP}:${POSTGRES_PORT}/${POSTGRES_DB}

# Application
APP_ENV=development
DEBUG=false

# JWT
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cloudinary
CLOUDINARY_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

Перед запуском необхідно вказати власні Cloudinary credentials:

```env
CLOUDINARY_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

Також необхідно замінити:

```env
SECRET_KEY=replace-with-a-long-random-secret
```

на випадковий секретний ключ.

Для production `SECRET_KEY` повинен містити щонайменше 32 символи.

---

## Змінні середовища

| Змінна | Призначення |
|---|---|
| `POSTGRES_USER` | користувач PostgreSQL |
| `POSTGRES_PASSWORD` | пароль PostgreSQL |
| `POSTGRES_HOST_IP` | адреса PostgreSQL для локального запуску |
| `POSTGRES_PORT` | порт PostgreSQL на хості |
| `POSTGRES_CONTAINER_PORT` | порт PostgreSQL усередині Docker |
| `POSTGRES_DB` | назва бази даних |
| `DATABASE_URL` | SQLAlchemy URL для підключення до PostgreSQL |
| `APP_ENV` | середовище застосунку: `development` або `production` |
| `DEBUG` | увімкнення SQLAlchemy debug logging |
| `SECRET_KEY` | секретний ключ для підпису JWT |
| `ALGORITHM` | алгоритм JWT, за замовчуванням `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | час життя JWT у хвилинах |
| `CLOUDINARY_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |

---

## Встановлення через Poetry

Перевірити версію Python:

```bash
python --version
```

Для pyenv:

```bash
pyenv local 3.13.7
```

Встановити залежності:

```bash
poetry install
```

Активувати середовище можна стандартним способом Poetry або запускати команди через:

```bash
poetry run <команда>
```

---

## Локальний запуск

### 1. Запустити PostgreSQL

PostgreSQL можна запустити окремо через Docker Compose:

```bash
docker compose up -d db
```

Перевірити стан:

```bash
docker compose ps
```

PostgreSQL повинен перейти у стан:

```text
healthy
```

### 2. Застосувати міграції

```bash
poetry run alembic upgrade head
```

Перевірити поточну міграцію:

```bash
poetry run alembic current
```

Перевірити відповідність ORM-моделей схемі бази:

```bash
poetry run alembic check
```

Нормальний результат:

```text
No new upgrade operations detected.
```

### 3. Запустити FastAPI

```bash
poetry run uvicorn main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## Запуск через Docker Compose

Для повного запуску API та PostgreSQL:

```bash
docker compose up --build
```

Або у фоновому режимі:

```bash
docker compose up -d --build
```

Перевірити контейнери:

```bash
docker compose ps
```

Переглянути логи API:

```bash
docker compose logs api
```

Переглянути логи PostgreSQL:

```bash
docker compose logs db
```

Зупинити сервіси:

```bash
docker compose down
```

Зупинити сервіси та видалити PostgreSQL volume:

```bash
docker compose down -v
```

> `docker compose down -v` видаляє дані PostgreSQL, що зберігаються в Docker volume.

При запуску API-контейнера автоматично виконується:

```bash
alembic upgrade head
```

Після успішного застосування міграцій запускається Uvicorn.

API доступний за адресою:

```text
http://localhost:8000
```

---

## PostgreSQL у локальному середовищі та Docker

При локальному запуску застосунок підключається до:

```text
127.0.0.1:5432
```

Наприклад:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/photoshare
```

У Docker Compose API підключається до PostgreSQL через ім'я Docker-сервісу:

```text
db:5432
```

Compose автоматично перевизначає `DATABASE_URL` для контейнера API.

---

## Міграції Alembic

Створити нову автоматичну міграцію:

```bash
poetry run alembic revision --autogenerate -m "назва міграції"
```

Застосувати всі міграції:

```bash
poetry run alembic upgrade head
```

Відкотити останню:

```bash
poetry run alembic downgrade -1
```

Відкотити всі:

```bash
poetry run alembic downgrade base
```

Перевірити поточну revision:

```bash
poetry run alembic current
```

Перевірити head:

```bash
poetry run alembic heads
```

Перевірити, чи ORM-моделі відповідають схемі БД:

```bash
poetry run alembic check
```

---

## Ролі та права доступу

| Дія | `user` | `moderator` | `admin` |
|---|:---:|:---:|:---:|
| Реєстрація та login | ✅ | ✅ | ✅ |
| Редагування власного профілю | ✅ | ✅ | ✅ |
| Завантаження фото | ✅ | ✅ | ✅ |
| Редагування власного фото | ✅ | ✅ | ✅ |
| Видалення власного фото | ✅ | ✅ | ✅ |
| Редагування чужого фото | ❌ | ❌ | ✅ |
| Видалення чужого фото | ❌ | ❌ | ✅ |
| Створення коментарів | ✅ | ✅ | ✅ |
| Редагування власного коментаря | ✅ | ✅ | ✅ |
| Видалення коментарів | ❌ | ✅ | ✅ |
| Створення рейтингу | ✅ | ✅ | ✅ |
| Перегляд детальних рейтингів | ❌ | ✅ | ✅ |
| Видалення рейтингів | ❌ | ✅ | ✅ |
| Фільтрація фото за `user_id` | ❌ | ✅ | ✅ |
| Бан користувачів | ❌ | ❌ | ✅ |
| Розбан користувачів | ❌ | ❌ | ✅ |
| Зміна ролей | ❌ | ❌ | ✅ |
| Трансформація власного фото | ✅ | ✅ | ✅ |
| Трансформація чужого фото | ❌ | ❌ | ✅ |

---

## Автентифікація

### Реєстрація

```http
POST /api/auth/register
```

Перший зареєстрований користувач автоматично отримує:

```text
admin
```

Усі наступні:

```text
user
```

### Login

```http
POST /api/auth/login
```

Endpoint використовує `OAuth2PasswordRequestForm`.

У поле:

```text
username
```

можна передати:

- username;
- email.

У відповідь повертається JWT Bearer token.

### Авторизація у Swagger

1. Відкрити:

```text
http://localhost:8000/docs
```

2. Виконати `/api/auth/login`.
3. Скопіювати `access_token`.
4. Натиснути **Authorize**.
5. Вставити Bearer token.

### Logout

```http
POST /api/auth/logout
```

Поточний JWT додається до blacklist і більше не може використовуватися для авторизованих запитів.

---

## API endpoints

### Стан застосунку

| Метод | Endpoint | Опис |
|---|---|---|
| `GET` | `/` | базова інформація про API |
| `GET` | `/health` | health check |

### Автентифікація

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `POST` | `/api/auth/register` | публічний | реєстрація |
| `POST` | `/api/auth/login` | публічний | отримання JWT |
| `POST` | `/api/auth/logout` | авторизований | blacklist поточного JWT |

### Користувачі

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `GET` | `/api/users/me` | авторизований | власний профіль |
| `PUT` | `/api/users/me` | авторизований | редагування власного профілю |
| `GET` | `/api/users/{username}` | публічний | публічний профіль |
| `PATCH` | `/api/users/{user_id}/ban` | admin | блокування користувача |
| `PATCH` | `/api/users/{user_id}/unban` | admin | розблокування користувача |
| `PATCH` | `/api/users/{user_id}/role` | admin | зміна ролі |

### Фотографії

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `POST` | `/api/photos` | авторизований | завантаження фото |
| `GET` | `/api/photos/{photo_id}` | публічний | детальна інформація |
| `PUT` | `/api/photos/{photo_id}` | owner/admin | редагування |
| `DELETE` | `/api/photos/{photo_id}` | owner/admin | видалення |

### Коментарі

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `POST` | `/api/photos/{photo_id}/comments` | авторизований | створення коментаря |
| `GET` | `/api/photos/{photo_id}/comments` | публічний | список коментарів |
| `PUT` | `/api/comments/{comment_id}` | автор | редагування коментаря |
| `DELETE` | `/api/comments/{comment_id}` | moderator/admin | видалення коментаря |

### Рейтинги

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `POST` | `/api/photos/{photo_id}/ratings` | авторизований | оцінити фотографію |
| `GET` | `/api/photos/{photo_id}/ratings` | публічний | середній рейтинг |
| `GET` | `/api/photos/{photo_id}/ratings/details` | moderator/admin | детальні рейтинги |
| `DELETE` | `/api/ratings/{rating_id}` | moderator/admin | видалення рейтингу |

### Пошук

```http
GET /api/photos/search
```

Параметри:

| Параметр | Опис |
|---|---|
| `keyword` | пошук у тексті опису |
| `tag` | фільтр за тегом |
| `min_rating` | мінімальний середній рейтинг від 1 до 5 |
| `sort_by` | `date` або `rating` |
| `order` | `asc` або `desc` |
| `user_id` | фільтр за автором, тільки moderator/admin |
| `date_from` | початкова дата |
| `date_to` | кінцева дата |

Приклад:

```http
GET /api/photos/search?tag=nature&min_rating=4&sort_by=rating&order=desc
```

### Трансформації

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `POST` | `/api/photos/{photo_id}/transform` | owner/admin | створення трансформації |
| `GET` | `/api/photos/{photo_id}/transforms` | публічний | список трансформацій |
| `GET` | `/api/transforms/{transform_id}` | публічний | одна трансформація |

Приклад тіла запиту:

```json
{
  "width": 800,
  "height": 600,
  "crop": "fill",
  "angle": 0,
  "effect": "grayscale",
  "format": "webp"
}
```

Необхідно передати щонайменше один параметр трансформації.

---

## Swagger та ReDoc

FastAPI автоматично генерує OpenAPI-документацію.

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

Для основних endpoint-ів документація містить:

- короткий опис операції;
- детальний опис;
- request/response schemas;
- HTTP status codes;
- `400 Bad Request`;
- `401 Unauthorized`;
- `403 Forbidden`;
- `404 Not Found`;
- автоматичну документацію `422 Validation Error`, де вона застосовується.

---

## HTTP статуси

Основні статуси API:

| Код | Значення |
|---|---|
| `200` | успішний запит |
| `201` | ресурс створено |
| `204` | успішна операція без response body |
| `400` | некоректний запит або порушення бізнес-правил |
| `401` | необхідна автентифікація або токен недійсний |
| `403` | недостатньо прав |
| `404` | ресурс не знайдено |
| `422` | помилка валідації FastAPI/Pydantic |
| `500` | внутрішня помилка або проблема зовнішнього сервісу |

---

## Cloudinary

Бінарні файли фотографій у PostgreSQL не зберігаються.

Cloudinary зберігає:

- завантажені фотографії;
- згенеровані QR-коди.

PostgreSQL зберігає:

- URL фотографії;
- Cloudinary `public_id`;
- опис;
- власника;
- теги;
- коментарі;
- рейтинги;
- URL трансформованих фотографій;
- URL QR-кодів.

---

## Тестування

Тести використовують:

- pytest;
- pytest-asyncio;
- HTTPX;
- SQLite через `aiosqlite`;
- mock для Cloudinary;
- unit tests;
- API integration tests;
- прямі тести route/service функцій.

Запустити всі тести:

```bash
poetry run pytest -v
```

Або всередині активованого Poetry environment:

```bash
pytest -v
```

Поточний набір:

```text
119 тестів
119 успішно
0 помилок
```

---

## Покриття тестами

Перевірити coverage:

```bash
poetry run pytest --cov=src --cov=main --cov-report=term-missing
```

Або:

```bash
pytest --cov=src --cov=main --cov-report=term-missing
```

Поточне покриття application-коду:

```text
93%
```

Таким чином виконується вимога про покриття тестами понад 90%.

---

## Перевірка перед запуском або здачею

Рекомендована послідовність:

```bash
poetry install

poetry run alembic upgrade head
poetry run alembic check

poetry run pytest -v

poetry run pytest \
  --cov=src \
  --cov=main \
  --cov-report=term-missing
```

Для Docker:

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs api
```

Перевірка API:

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

---

## Production

Для production необхідно:

```env
APP_ENV=production
```

Також необхідно встановити безпечний:

```env
SECRET_KEY=<випадковий_секретний_ключ>
```

Production-запуск не дозволяє використовувати:

```text
change-me
```

або:

```text
replace-with-a-long-random-secret
```

Секретний ключ повинен містити щонайменше 32 символи.

Також необхідно налаштувати:

```env
DATABASE_URL=...
CLOUDINARY_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

---

## Розгортання

Проєкт підготовлений до контейнерного розгортання через `Dockerfile`.

Контейнер:

1. встановлює production-залежності через Poetry;
2. використовує зафіксовані версії з `poetry.lock`;
3. запускає `alembic upgrade head`;
4. після успішних міграцій запускає Uvicorn;
5. слухає порт `8000`.

Публічна адреса застосунку буде додана після розгортання.

Після deployment у цьому розділі необхідно додати:

```text
API: https://<deployment-url>
Swagger: https://<deployment-url>/docs
ReDoc: https://<deployment-url>/redoc
Health: https://<deployment-url>/health
```

---

## Безпека

- паролі не зберігаються у відкритому вигляді;
- для хешування використовується сучасний password hashing через `pwdlib`;
- авторизація виконується через JWT Bearer token;
- JWT має обмежений термін життя;
- logout блокує поточний токен;
- права доступу перевіряються на рівні FastAPI dependencies та бізнес-логіки;
- production не запускається з небезпечним placeholder `SECRET_KEY`;
- секрети зберігаються в `.env`;
- `.env` виключений із Git через `.gitignore`;
- Cloudinary credentials не повинні зберігатися в репозиторії.

---

## Особливості бази даних

PostgreSQL використовується як основна база даних.

SQLAlchemy працює в асинхронному режимі через:

```text
postgresql+asyncpg
```

Для рейтингів на рівні бази встановлені обмеження:

```text
1 <= rating <= 5
```

та унікальність:

```text
(photo_id, user_id)
```

Тому один користувач не може створити декілька рейтингів для однієї фотографії.

Каскадне видалення використовується для пов'язаних записів фотографій, коментарів, рейтингів та інших залежних сутностей.

---

## Ліцензія

Умови використання проєкту наведені у файлі:

```text
LICENSE
```