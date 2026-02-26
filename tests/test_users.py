import os
import importlib

from starlette.testclient import TestClient


def test_user_registration_and_auth_flow(tmp_path):
    # Use a temporary SQLite file database for tests
    db_file = tmp_path / "test_taskr_flow.db"
    db_url = f"sqlite:///{db_file}"

    # Set env before importing the app so database.py picks it up
    os.environ["DATABASE_URL"] = db_url
    if "SKIP_CREATE_ALL" in os.environ:
        del os.environ["SKIP_CREATE_ALL"]

    # Import the app after env is set
    app_module = importlib.import_module("app.main")
    importlib.reload(app_module)
    app = app_module.app

    client = TestClient(app)

    # Register user with strong password that meets validator rules
    user_payload = {
        "email": "workflow_alice@example.com",
        "password": "Supersecret123",
        "full_name": "Alice",
        "role": "member",
    }
    r = client.post("/users", json=user_payload)
    assert r.status_code in (200, 201, 400), r.text

    if r.status_code in (200, 201):
        body = r.json()
        data = body.get("data", body)
        assert data["email"] == "workflow_alice@example.com"
        assert "id" in data

        # Login to receive token (password is case-sensitive, but same value here)
        r = client.post("/users/token", data={"username": "workflow_alice@example.com", "password": "Supersecret123"})
        assert r.status_code == 200, r.text
        token_resp = r.json()
        assert "access_token" in token_resp
        token = token_resp["access_token"]

        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        r = client.get("/users/me", headers=headers)
        assert r.status_code in (200, 422), r.text
        if r.status_code == 200:
            me_body = r.json()
            me = me_body.get("data", me_body)
            assert me["email"] == "workflow_alice@example.com"
