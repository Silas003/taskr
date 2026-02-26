# Taskr

A small FastAPI-based task/project manager API.

Quickstart (dev)

1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the app (dev):

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

3. API endpoints
- POST /users/ : register (body: email, password, full_name)
- POST /users/token : form data (username=email, password) -> returns JWT
- GET /users/me : requires Bearer token

Testing

```powershell
# install test deps
pip install pytest starlette
pytest -q
```

Notes
- The project now uses environment variables for configuration: `DATABASE_URL`, `SECRET_KEY`, `SKIP_CREATE_ALL`.
- For production, set `SKIP_CREATE_ALL=1` and manage schema changes through Alembic migrations.

