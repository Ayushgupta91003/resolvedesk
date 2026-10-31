"""Environment configuration. Defaults deliberately support a keyless local demo."""
import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'resolvedesk.db'}")
CHECKPOINT_URL = os.getenv("CHECKPOINT_URL", "")
APP_ENV = os.getenv("APP_ENV", "development")
SEED_DEMO = os.getenv("SEED_DEMO", "true").lower() == "true"
AGENT_MODE = os.getenv("AGENT_MODE", "demo")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
EMBEDDINGS_ENABLED = os.getenv("EMBEDDINGS_ENABLED", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
COOKIE_SECURE = APP_ENV == "production"
SESSION_HOURS = 24
MAX_UPLOAD_BYTES = 512_000
