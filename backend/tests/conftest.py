import os
import tempfile
from pathlib import Path

TEST_DIR = Path(tempfile.mkdtemp(prefix="resolvedesk-tests-"))
os.environ["DATA_DIR"] = str(TEST_DIR)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DIR / 'test.db'}"
os.environ["AGENT_MODE"] = "demo"
os.environ["SEED_DEMO"] = "true"
os.environ["APP_ENV"] = "test"
os.environ["EMBEDDINGS_ENABLED"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Base, engine
from app.seed import seed_demo
from app.main import login_attempts

@pytest.fixture(autouse=True)
def reset_database():
    login_attempts.clear()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed_demo()
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def owner(client):
    r = client.post("/api/auth/login", json={"email": "owner@orbit.demo", "password": "DemoPass123!"})
    assert r.status_code == 200
    return client

def login(client, email):
    assert client.post("/api/auth/login", json={"email": email, "password": "DemoPass123!"}).status_code == 200
