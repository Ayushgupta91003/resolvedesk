"""Tenant-scoped retrieval. Keyless lexical search; optional Postgres/pgvector semantic search."""
import re
from sqlalchemy import select, text
from .models import Document, SessionLocal, engine
from .config import EMBEDDINGS_ENABLED

def words(value):
    return set(re.findall(r"[a-z0-9]+", value.lower())) - {"the", "a", "is", "and", "to", "my", "i", "for", "it", "of", "in", "can"}

def retrieve(org_id: str, query: str, limit=3):
    with SessionLocal() as db:
        docs = db.scalars(select(Document).where(Document.org_id == org_id)).all()
        semantic = {}
        if EMBEDDINGS_ENABLED and engine.dialect.name == "postgresql":
            from langchain_openai import OpenAIEmbeddings
            embedding = OpenAIEmbeddings(model="text-embedding-3-small").embed_query(query)
            rows = db.execute(text("SELECT document_id, 1 - (embedding <=> CAST(:vector AS vector)) AS score FROM document_vectors WHERE org_id=:org ORDER BY embedding <=> CAST(:vector AS vector) LIMIT :limit"), {"vector": str(embedding), "org": org_id, "limit": limit}).all()
            semantic = {row.document_id: float(row.score) for row in rows}
        scored = []
        for doc in docs:
            overlap = len(words(query) & words(doc.title + " " + doc.body))
            score = overlap + semantic.get(doc.id, 0) * 5
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [{"id": d.id, "title": d.title, "excerpt": d.body[:3500], "score": round(s, 3)} for s, d in scored[:limit]]

def setup_vectors():
    if EMBEDDINGS_ENABLED:
        if engine.dialect.name != "postgresql":
            raise RuntimeError("EMBEDDINGS_ENABLED requires PostgreSQL with pgvector.")
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(text("CREATE TABLE IF NOT EXISTS document_vectors (document_id VARCHAR(36) PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE, org_id VARCHAR(36) NOT NULL, embedding vector(1536) NOT NULL)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS document_vectors_org_idx ON document_vectors(org_id)"))

def index_document(doc_id):
    if not EMBEDDINGS_ENABLED:
        return
    from langchain_openai import OpenAIEmbeddings
    with SessionLocal() as db:
        doc = db.get(Document, doc_id)
        if not doc:
            return
        vector = OpenAIEmbeddings(model="text-embedding-3-small").embed_query(doc.title + "\n" + doc.body)
        db.execute(text("INSERT INTO document_vectors(document_id,org_id,embedding) VALUES (:id,:org,CAST(:vector AS vector)) ON CONFLICT(document_id) DO UPDATE SET embedding=excluded.embedding"), {"id": doc.id, "org": doc.org_id, "vector": str(vector)})
        db.commit()
