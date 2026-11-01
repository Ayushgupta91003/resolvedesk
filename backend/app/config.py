"""Environment configuration. Defaults deliberately support a keyless local demo."""
import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'resolvedesk.db').as_posix()}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
CHECKPOINT_URL = os.getenv("CHECKPOINT_URL", "") or (DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1) if DATABASE_URL.startswith("postgresql+psycopg://") else "")
APP_ENV = os.getenv("APP_ENV", "development")
SEED_DEMO = os.getenv("SEED_DEMO", "true").lower() == "true"
AGENT_MODE = os.getenv("AGENT_MODE", "demo")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
CLOUD_API_ENABLED = os.getenv("CLOUD_API_ENABLED", "false").lower() == "true"
LLM_BASE_URL = os.getenv("LLM_BASE_URL", {"ollama": "http://127.0.0.1:11434/v1", "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/"}.get(LLM_PROVIDER, ""))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "180" if LLM_PROVIDER == "ollama" else "40"))
EMBEDDINGS_ENABLED = os.getenv("EMBEDDINGS_ENABLED", "false").lower() == "true"
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", {"ollama": "nomic-embed-text", "gemini": "gemini-embedding-001"}.get(EMBEDDING_PROVIDER, "text-embedding-3-small"))
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "768" if EMBEDDING_PROVIDER in ("ollama", "gemini") else "1536"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
if os.getenv("RENDER_EXTERNAL_URL"):
    CORS_ORIGINS.append(os.environ["RENDER_EXTERNAL_URL"].rstrip("/"))
COOKIE_SECURE = APP_ENV == "production"
SESSION_HOURS = 24
MAX_UPLOAD_BYTES = 512_000
