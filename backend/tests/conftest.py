import os
import tempfile
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parents[1] / "data" / "tests"
TEST_ROOT.mkdir(parents=True, exist_ok=True)
TEST_DIR = Path(tempfile.mkdtemp(prefix="resolvedesk-tests-", dir=TEST_ROOT))
os.environ["DATA_DIR"] = str(TEST_DIR)
test_database = os.getenv("TEST_DATABASE_URL", "")
if test_database:
    from sqlalchemy.engine import make_url
    if make_url(test_database).database != "resolvedesk_test":
        raise RuntimeError("Destructive test setup only accepts the dedicated resolvedesk_test database.")
    os.environ["DATABASE_URL"] = test_database
    os.environ["CHECKPOINT_URL"] = os.getenv("TEST_CHECKPOINT_URL", test_database.replace("postgresql+psycopg://", "postgresql://"))
else:
    os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_DIR / 'test.db').as_posix()}"
    os.environ["CHECKPOINT_URL"] = ""
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
