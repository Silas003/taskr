# Taskr

Taskr is a FastAPI-based backend for managing users, projects, and tasks.

It implements a realistic user workflow (registration, authentication, roles), project and task management, and a layered architecture suitable for production-style services.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Domain Model](#domain-model)
- [Requirements](#requirements)
- [Configuration | Environment Variables](#configuration--environment-variables)
- [Local Development Setup](#local-development-setup)
- [Running with Docker](#running-with-docker)
- [Database & Migrations](#database--migrations)
- [Testing](#testing)
- [API Overview](#api-overview)
  - [Auth & Users](#auth--users)
  - [Projects](#projects)
  - [Tasks](#tasks)
  - [Health](#health)
- [Error Handling & Response Shape](#error-handling--response-shape)
- [Security Notes](#security-notes)

---

## Architecture Overview

The codebase follows a clean, layered architecture:

- **Routers** (`app/routers/v1/*.py`)
  - FastAPI routing layer.
  - HTTP concerns (paths, status codes, query params, response models, security dependencies).

- **Services** (`app/services/**`)
  - Domain logic: validation, orchestration, enforcing business rules.
  - Example: `UserService`, `ProjectService`, `TaskService`.

- **Repositories** (`app/repositories/**`)
  - Persistence abstractions, implemented with SQLAlchemy.
  - Provide CRUD and query methods used by services.

- **Models** (`app/models/**`)
  - SQLAlchemy ORM entities for `User`, `Project`, `Task`, `ProjectMember`, etc.

- **Schemas / DTOs** (`app/schemas/dto.py`, `app/schemas/response.py`)
  - Pydantic v2 models for request/response payloads.
  - `ResponseBase[T]` wraps all successful responses with a consistent envelope.

- **Security & Validation** (`app/core`, `app/security`, `app/validators`)
  - JWT creation/verification.
  - Password hashing (bcrypt) and strength rules.
  - Email/full-name validation.

- **Exceptions** (`app/exceptions/CustomExceptions.py`)
  - Domain-specific errors mapped to HTTP exceptions via `to_http_exception`.

- **Application entrypoint** (`app/main.py`)
  - Creates the `FastAPI` app instance.
  - Loads environment variables.
  - Configures CORS.
  - Registers global exception handlers.
  - Includes all versioned routers under `/api/v1/...`.
  - Optionally auto-creates tables on startup.

---

## Domain Model

At a high level, the system has the following core entities:

- **User**
  - Fields: `id`, `email`, `full_name` (optional), `password` (hashed), system `role` (e.g. `admin`, `member`).
  - Capabilities depend on role:
    - `admin`: can list and manage users, manage project membership.
    - `member`: can own/join projects and manage tasks as allowed by project roles.

- **Project**
  - Fields: `id`, `name`, `description`, `owner_id`, `created_at`.
  - Relationships:
    - Owned by a `User`.
    - Has many `Task` items.
    - Has many `ProjectMember` records.

- **ProjectMember**
  - Fields: `project_id`, `user_id`, `role` (`owner`, `editor`, `viewer`).
  - Controls access level within a project:
    - `owner`: full control, including membership management.
    - `editor`: can modify project details and tasks.
    - `viewer`: read access; when assigned to a task, can update its status.

- **Task**
  - Fields: `id`, `title`, `description`, `project_id`, `assigned_to` (nullable), `status`, `due_date`, `created_at`.
  - `status` is an enum (e.g. `pending`, `in_progress`, `done`).
  - Assignment is optional; tasks can exist unassigned.

---

## Requirements

- Python **3.11+** (project has been developed and tested with Python >= 3.11).
- PostgreSQL **13+** (or any version supported by SQLAlchemy + psycopg2).
- pip / virtualenv.

For containerized environments:

- Docker **20+**.
- Docker Compose **v2+**.

---

## Configuration  Environment Variables

Configuration is primarily driven by environment variables. They are loaded via `python-dotenv` in both `app/database.py` and `app/main.py`.

### Database (`app/database.py`)

The database URL is constructed via `sqlalchemy.engine.URL.create` using:

- `DB_DRIVER` (default: `postgresql+psycopg2`)
- `DB_USER` (default: `postgres`)
- `DB_PASS` (default: `password`)
- `DB_HOST` (default: `127.0.0.1`)
- `DB_PORT` (default: `5432`)
- `DB_NAME` (default: `taskr`)

Example `.env` snippet:

```env
DB_DRIVER=postgresql+psycopg2
DB_USER=postgres
DB_PASS=password
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=taskr
```

### Application / Security (`app/main.py`, security modules)

Commonly used env vars:

- `ENV`  environment name (`development`, `production`, etc.).
- `SKIP_CREATE_ALL`  if unset/falsey, SQLAlchemy will auto-create tables at startup:
  - For dev: leave unset or set to `0`.
  - For production: set to `1` and use Alembic migrations instead.
- `SECRET_KEY`  secret used for signing JWTs.
- `ACCESS_TOKEN_EXPIRE_MINUTES`  access token lifetime.
- `REFRESH_TOKEN_EXPIRE_MINUTES`  refresh token lifetime.

### CORS (`app/main.py`)

CORS is configured via:

- `CORS_ALLOWED_ORIGINS` (default: `*`)
- `CORS_ALLOWED_METHODS` (default: `*`)
- `CORS_ALLOWED_HEADERS` (default: `*`)
- `CORS_ALLOW_CREDENTIALS` (default: `true`)

For production, tighten `CORS_ALLOWED_ORIGINS` to your frontend origins (e.g. `https://app.example.com`).

---

## Local Development Setup

### 1. Create and activate a virtual environment (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root (alongside `requirements.txt`) with at least:

```env
DB_USER=postgres
DB_PASS=password
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=taskr

SECRET_KEY=dev-secret-key-change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_MINUTES=43200

ENV=development
SKIP_CREATE_ALL=0

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOWED_METHODS=*
CORS_ALLOWED_HEADERS=*
CORS_ALLOW_CREDENTIALS=true
```

Make sure a local PostgreSQL instance is running and accessible with these credentials.

### 3. Run the app (dev)

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Versioned paths: `http://127.0.0.1:8000/api/v1/...`

---

## Running with Docker

A typical container setup for this project looks like:

### Dockerfile (summary)

- Based on `python:3.11-slim`.
- Installs dependencies from `requirements.txt`.
- Copies the app code into `/app`.
- Exposes port `8000`.
- Runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

### docker-compose.yml (summary)

- `db` service: Postgres 15 (e.g. `postgres:15-alpine`) with a `taskr` database.
- `app` service: builds from the repo Dockerfile, depends on `db`, and binds `8000:8000`.

Example (abridged):

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: taskr
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5433:5432"

  app:
    build: .
    environment:
      DB_USER: postgres
      DB_PASS: password
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: taskr
      SECRET_KEY: dev-secret-key-change-me
      ENV: production
      SKIP_CREATE_ALL: "0"
    ports:
      - "8000:8000"
    depends_on:
      - db
```

Run with:

```bash
docker compose build
docker compose up
```

Then open `http://localhost:8000/docs`.

---

## Database & Migrations

SQLAlchemy is configured in `app/database.py`:

- Uses `declarative_base()` to define ORM models.
- Provides `SessionLocal` and `get_db()` for dependency-injected DB sessions.

On startup, `app/main.py` performs:

```python
if not os.getenv("SKIP_CREATE_ALL"):
    Base.metadata.create_all(bind=engine)
```

For development, this auto-creates tables.

For production, you should:

1. Set `SKIP_CREATE_ALL=1`.
2. Use **Alembic** migrations (configured under `alembic/`):
   - `alembic.ini` at the project root.
   - Versioned migration scripts under `alembic/versions/`.

Typical Alembic commands:

```bash
alembic revision -m "describe change"
alembic upgrade head
```

---

## Testing

Pytest-based tests live under `tests/` and are organized by domain (`users`, `project`, `task`, etc.). They cover:

- User registration & auth workflow.
- Permission checks and role behavior.
- Project and task endpoints and services.

To run tests locally:

```powershell
pip install -r requirements.txt  # includes pytest
pytest
```

In a containerized environment, after `docker compose up`:

```bash
docker compose exec app pytest
```

The test configuration (`tests/conftest.py`) sets up a test database and overrides dependencies to isolate tests from production data.

---

## API Overview

The API is versioned under `/api/v1`. The main routers are:

- `app/routers/v1/users.py`  `/api/v1/users/...`
- `app/routers/v1/project.py`  `/api/v1/project/...`
- `app/routers/v1/task.py`  `/api/v1/task/...`
- `app/routers/v1/health.py`  `/api/v1/health` (simple readiness probe).

The OpenAPI docs (`/docs`) provide full request/response schemas. Below is a high-level summary.

### Auth & Users

Base path: `/api/v1/users`

- **POST `/users`**  Register user
  - Request body: `UserCreate` (email, password, optional full_name).
  - Response: `ResponseBase[UserRead]`, HTTP 201.
  - Errors:
    - 400/422 if validation fails or password is too weak.
    - 400 if email already exists.

- **POST `/users/token`**  Login
  - Request: `application/x-www-form-urlencoded` (`username` = email, `password`).
  - Response: `Token` (`access_token`, `token_type`).
  - Errors: 401 for invalid credentials.

- **GET `/users/me`**  Current user
  - Auth: `Authorization: Bearer <access_token>`.
  - Response: `ResponseBase[UserRead]`.

- **POST `/users/refresh`**  Refresh access token
  - Reads a refresh token from a `refresh` cookie, issues a new access token.

- **GET `/users/logout`**  Logout
  - Clears the `refresh` cookie.

- **GET `/users`**  List users (admin only)
  - Auth: admin role required.
  - Query params:
    - `skip` (int, default 0)  offset for pagination.
    - `limit` (int, default 10)  page size.
    - `email_contains` (optional str)  case-insensitive substring match on email.
    - `role` (optional str)  filter by exact system role.
  - Response: `ResponseBase[List[UserRead]]`.

- **GET `/users/{id}`**  Get user by ID
  - Access: user may read their own profile; admins may read any.

- **PUT `/users/{id}`**  Update user
  - Allows updating `full_name` and/or `password` with validation.

- **DELETE `/users/{id}`**  Delete user
  - Access: user themselves or admin, according to access control.

### Projects

Base path: `/api/v1/project`

- **POST `/project`**  Create project
  - Auth: authenticated user.
  - Body: `ProjectCreate`.
  - The creator becomes the `owner` and is added as a `ProjectMember`.

- **GET `/project/all`**  List projects
  - Auth: authenticated user.
  - Query params:
    - `skip`, `limit` for pagination.
    - `name_contains` (optional) for case-insensitive partial name search.

- **GET `/project/{id}`**  Get project by ID
  - Access: owner, editor, or viewer member.

- **PUT `/project/{id}`**  Update project
  - Access: project `owner` or `editor`.

- **DELETE `/project/{id}`**  Delete project
  - Access: project `owner`.

- **GET `/project/user/{user_id}`**  List projects by user
  - Auth: authenticated user.
  - Query params: `skip`, `limit` for pagination.

- **GET `/project/by-name`**  Get project by name
  - Auth: authenticated user.

- **Project membership**
  - **POST `/project/{id}/members`**  Add member
    - Access: project `owner` or system `admin`.
    - Body: `ProjectMemberAdd` (`user_id`, `role`).
  - **PATCH `/project/{id}/members/{user_id}`**  Change member role
    - Access: project `owner` or system `admin`.
  - **DELETE `/project/{id}/members/{user_id}`**  Remove member
    - Access: project `owner` or system `admin`.

### Tasks

Base path: `/api/v1/task`

- **POST `/task`**  Create task
  - Access: project `owner` or `editor`.
  - Body: `TaskCreate`.
  - `assigned_to` is optional (nullable).

- **GET `/task`**  List tasks
  - Access: must be at least `viewer` on relevant projects.
  - Query params:
    - `skip`, `limit` for pagination.
    - `status` (optional) to filter by exact status.

- **GET `/task/{id}`**  Get task by ID
  - Access: member of the project (`owner`, `editor`, or `viewer`).

- **PUT `/task/{id}`**  Update task
  - Access rules:
    - `owner` / `editor`: can update all fields.
    - `viewer` assigned to the task: can update **status only**.

- **DELETE `/task/{id}`**  Delete task
  - Access: project `owner` or `editor`.

- **GET `/task/user/{id}`**  List tasks by user
  - Auth: authenticated user.
  - Query params: `skip`, `limit` for pagination.

- **GET `/task/project/{id}`**  List tasks by project
  - Auth: authenticated user.
  - Query params: `skip`, `limit` for pagination.

### Health

- **GET `/api/v1/health`**
  - Simple liveness/health endpoint.
  - Can be used by orchestrators or load balancers.

---

## Error Handling & Response Shape

Errors are raised using FastAPI `HTTPException` or custom domain exceptions mapped via `to_http_exception`.

Successful responses generally follow the generic `ResponseBase[T]` envelope:

```json
{
  "code": 200,
  "message": "Human-readable summary",
  "data": { /* or a list, or null */ }
}
```

Examples:

- 200 OK response with data:

```json
{
  "code": 200,
  "message": "User profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Example User",
    "role": "member"
  }
}
```

- 4xx/5xx error (standard FastAPI style):

```json
{
  "detail": "Invalid authentication credentials"
}
```

Project-specific errors may include structured `detail` objects with `code` and `message` fields for better client handling.

---

## Security Notes

- **Authentication**: JWT-based using `Authorization: Bearer <token>`.
- **Password storage**: hashed using bcrypt via `PasswordManager`.
- **Authorization**:
  - System-level roles (`SystemRole`) for admin vs. regular user.
  - Project-level roles (`ProjectRole`) for owner/editor/viewer distinctions.
  - Access is enforced in router dependencies and services.
- **CORS**: enabled and configurable via env; restrict origins in production.
- **CSRF**:
  - The API is stateless and primarily uses Bearer tokens, so CSRF risk is low compared to cookie-based auth.
  - If you introduce cookie-based session auth in the future, add explicit CSRF protection (double-submit token or SameSite+origin checks).

---

This README is intended as both a quickstart guide and a technical reference for developers extending or integrating with Taskr. For the most accurate and detailed API contract, always refer to the generated OpenAPI docs at `/docs`.
