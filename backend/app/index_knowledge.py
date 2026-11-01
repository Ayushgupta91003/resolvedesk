from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from sqlalchemy import select
from .models import SessionLocal, Document
from .knowledge import setup_vectors, index_document
from .config import EMBEDDINGS_ENABLED

if __name__ == "__main__":
    if not EMBEDDINGS_ENABLED:
        raise SystemExit("Set EMBEDDINGS_ENABLED=true and use PostgreSQL before indexing.")
    setup_vectors()
    with SessionLocal() as db:
        ids = list(db.scalars(select(Document.id)))
    for doc_id in ids:
        index_document(doc_id)
        print(f"Indexed {doc_id}")
    print(f"Indexed {len(ids)} documents.")
