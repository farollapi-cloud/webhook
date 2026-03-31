import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import Base, get_engine, reset_engine_for_tests


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    reset_engine_for_tests()
    get_settings.cache_clear()

    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["SECRET_KEY"] = "test-secret-key-for-jwt-must-be-long-enough-32"
    os.environ["AUTH_CLIENT_ID"] = "admin"
    os.environ["AUTH_CLIENT_SECRET"] = "testsecret"
    os.environ["BACKEND_PUBLIC_URL"] = "http://test.example"

    get_settings.cache_clear()

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    from app.main import app

    return TestClient(app)


@pytest.fixture
def admin_token(client: TestClient) -> str:
    r = client.post(
        "/api/v1/auth/token",
        json={"client_id": "admin", "client_secret": "testsecret"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}
