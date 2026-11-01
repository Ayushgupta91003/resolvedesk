"""Tenant-scoped chunk retrieval with optional OpenAI or local Ollama embeddings."""
import math
import os
import re
import httpx
from sqlalchemy import select, text
from .models import Document, SessionLocal, engine
from .config import EMBEDDINGS_ENABLED, EMBEDDING_PROVIDER, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, OLLAMA_BASE_URL, CLOUD_API_ENABLED

CHUNK_SIZE = 1100
CHUNK_OVERLAP = 150

def words(value):
    return set(re.findall(r"[a-z0-9]+", value.lower())) - {"the", "a", "is", "and", "to", "my", "i", "for", "it", "of", "in", "can"}

def chunks(body):
    start = 0
    while start < len(body):
        end = min(start + CHUNK_SIZE, len(body))
        if end < len(body):
            boundary = body.rfind(" ", start + CHUNK_SIZE // 2, end)
            if boundary > start:
                end = boundary
        excerpt = body[start:end].strip()
        if excerpt:
            yield excerpt
        if end >= len(body):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)

def embed_texts(values, query=False):
    if EMBEDDING_PROVIDER != "ollama" and not CLOUD_API_ENABLED:
        raise RuntimeError("Cloud embeddings are disabled until CLOUD_API_ENABLED=true.")
    if EMBEDDING_PROVIDER == "ollama":
        prefix = "search_query: " if query else "search_document: "
        response = httpx.post(f"{OLLAMA_BASE_URL}/api/embed", json={"model": EMBEDDING_MODEL, "input": [prefix + value for value in values], "truncate": False, "keep_alive": "0"}, timeout=180)
        response.raise_for_status()
        embeddings = response.json()["embeddings"]
    elif EMBEDDING_PROVIDER == "gemini":
        key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("Gemini embeddings require a configured provider key.")
        model = EMBEDDING_MODEL.removeprefix("models/")
        if not re.fullmatch(r"[a-zA-Z0-9._-]+", model):
            raise ValueError("Invalid embedding model name.")
        requests = [{"model": f"models/{model}", "content": {"parts": [{"text": value}]}, "taskType": "RETRIEVAL_QUERY" if query else "RETRIEVAL_DOCUMENT", "outputDimensionality": EMBEDDING_DIMENSIONS} for value in values]
        response = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents", headers={"x-goog-api-key": key}, json={"requests": requests}, timeout=60)
        response.raise_for_status()
        embeddings = [item["values"] for item in response.json()["embeddings"]]
    elif EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        client = OpenAIEmbeddings(model=EMBEDDING_MODEL, dimensions=EMBEDDING_DIMENSIONS)
        embeddings = [client.embed_query(values[0])] if query else client.embed_documents(values)
    else:
        raise RuntimeError("EMBEDDING_PROVIDER must be openai, gemini or ollama.")
    if len(embeddings) != len(values) or any(len(v) != EMBEDDING_DIMENSIONS or not all(math.isfinite(x) for x in v) for v in embeddings):
        raise ValueError("Embedding provider returned unexpected vector dimensions or non-finite values.")
    normalized = []
    for vector in embeddings:
        norm = math.sqrt(sum(value * value for value in vector))
        if not norm:
            raise ValueError("Embedding provider returned a zero vector.")
        normalized.append([value / norm for value in vector])
    return normalized

def retrieve(org_id: str, query: str, limit=3):
    with SessionLocal() as db:
        docs = db.scalars(select(Document).where(Document.org_id == org_id)).all()
        semantic = {}
        if EMBEDDINGS_ENABLED and engine.dialect.name == "postgresql":
            vector = embed_texts([query[:6000]], query=True)[0]
            rows = db.execute(text("SELECT id, 1 - (embedding <=> CAST(:vector AS vector)) AS score FROM document_chunks WHERE org_id=:org ORDER BY embedding <=> CAST(:vector AS vector) LIMIT :limit"), {"vector": str(vector), "org": org_id, "limit": max(limit * 3, 10)}).all()
            semantic = {row.id: float(row.score) for row in rows}
        scored = []
        for doc in docs:
            for index, excerpt in enumerate(chunks(doc.body)):
                source_id = f"{doc.id}:{index}"
                overlap = len(words(query) & words(doc.title + " " + excerpt))
                semantic_score = semantic.get(source_id, 0)
                if not overlap and semantic_score < .35:
                    continue
                score = overlap + max(0, semantic_score) * 5
                scored.append({"id": source_id, "document_id": doc.id, "chunk": index + 1, "title": doc.title, "excerpt": excerpt, "score": round(score, 3)})
        scored.sort(key=lambda source: source["score"], reverse=True)
        return scored[:limit]

def setup_vectors():
    if not EMBEDDINGS_ENABLED:
        return
    if engine.dialect.name != "postgresql":
        raise RuntimeError("EMBEDDINGS_ENABLED requires PostgreSQL with pgvector.")
    if not 1 <= EMBEDDING_DIMENSIONS <= 4096:
        raise RuntimeError("Embedding dimensions must be in the range 1–4096.")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text(f"CREATE TABLE IF NOT EXISTS document_chunks (id VARCHAR(64) PRIMARY KEY, document_id VARCHAR(36) NOT NULL REFERENCES documents(id) ON DELETE CASCADE, org_id VARCHAR(36) NOT NULL, chunk_index INTEGER NOT NULL, body TEXT NOT NULL, embedding vector({EMBEDDING_DIMENSIONS}) NOT NULL)"))
        column_type = conn.execute(text("SELECT format_type(a.atttypid,a.atttypmod) FROM pg_attribute a WHERE a.attrelid='document_chunks'::regclass AND a.attname='embedding' AND NOT a.attisdropped")).scalar_one()
        if column_type != f"vector({EMBEDDING_DIMENSIONS})":
            raise RuntimeError(f"Existing chunks use {column_type}; match dimensions or explicitly reindex into a new database.")
        conn.execute(text("CREATE INDEX IF NOT EXISTS document_chunks_org_idx ON document_chunks(org_id)"))

def index_document(doc_id):
    if not EMBEDDINGS_ENABLED:
        return
    with SessionLocal() as db:
        doc = db.get(Document, doc_id)
        if not doc:
            return
        pieces = list(chunks(doc.body))
        vectors = embed_texts([doc.title + "\n" + body for body in pieces])
        db.execute(text("DELETE FROM document_chunks WHERE document_id=:id AND org_id=:org"), {"id": doc.id, "org": doc.org_id})
        for index, (body, vector) in enumerate(zip(pieces, vectors)):
            db.execute(text("INSERT INTO document_chunks(id,document_id,org_id,chunk_index,body,embedding) VALUES (:id,:doc,:org,:index,:body,CAST(:vector AS vector))"), {"id": f"{doc.id}:{index}", "doc": doc.id, "org": doc.org_id, "index": index, "body": body, "vector": str(vector)})
        db.commit()
