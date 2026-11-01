"""Opt-in real-provider smoke test using a separate, synthetic-only database.

Never reads the runtime app database. Requires explicit --confirm-free-tier and
only uses fixed sample data created by app.seed in localhost's dedicated DB.
"""
import argparse
import ast
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-free-tier", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    if not args.confirm_free_tier:
        raise SystemExit("Verify your provider project is Free tier before explicitly opting in.")
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / "backend" / ".env")
    target = os.getenv("LIVE_TEST_DATABASE_URL", "postgresql+psycopg://resolvedesk:resolvedesk-local-only@127.0.0.1:55432/resolvedesk_live_test")
    url = make_url(target)
    if url.host not in ("localhost", "127.0.0.1") or url.port != 55432 or url.database != "resolvedesk_live_test":
        raise SystemExit("Smoke tests only accept the dedicated local resolvedesk_live_test database.")
    os.environ.update(DATABASE_URL=target, CHECKPOINT_URL=target.replace("postgresql+psycopg://", "postgresql://"), AGENT_MODE="llm", LLM_PROVIDER="gemini", OPENAI_MODEL="gemini-3.5-flash-lite", LLM_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/", CLOUD_API_ENABLED="true", EMBEDDINGS_ENABLED="true", EMBEDDING_PROVIDER="gemini", EMBEDDING_MODEL="gemini-embedding-001", EMBEDDING_DIMENSIONS="768", LANGSMITH_TRACING="false", DATA_DIR=str(root / "data" / "live-smoke"))
    from sqlalchemy import select, func, text
    from .models import Base, engine, SessionLocal, Document, Ticket, Run, Approval, Action, Order
    from .seed import seed_demo
    from .knowledge import setup_vectors, index_document, retrieve
    from .agent import run_job
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Ticket)) and not args.retry_failed:
            raise SystemExit("Smoke database is not empty. Use a fresh dedicated test database; existing data was not changed.")
    seed_demo()
    expected_docs = {}
    expected_tickets = {}
    for node in ast.walk(ast.parse(Path(__file__).with_name("seed.py").read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Document":
            fields = {item.arg: ast.literal_eval(item.value) for item in node.keywords}
            expected_docs[fields["id"]] = fields
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "samples" for target in node.targets):
            expected_tickets = {row[0]: row for row in ast.literal_eval(node.value)}
    with SessionLocal() as db:
        docs = db.scalars(select(Document)).all()
        assert len(docs) == len(expected_docs)
        for doc in docs:
            expected = expected_docs[doc.id]
            assert all(getattr(doc, key) == value for key, value in expected.items())
        assert db.scalar(select(func.count()).select_from(Ticket)) == 6
        for ticket_id, row in expected_tickets.items():
            ticket = db.get(Ticket, ticket_id)
            assert ticket.subject == row[3] and ticket.description == row[4] and ticket.customer_id == row[2]
    setup_vectors()
    # Only these three repository-defined sample policies go to Google.
    for doc_id in ("doc-refund", "doc-shipping", "doc-account"):
        with engine.connect() as connection:
            indexed = connection.execute(text("SELECT count(*) FROM document_chunks WHERE document_id=:id"), {"id": doc_id}).scalar_one()
        if not indexed:
            index_document(doc_id)
        print(f"Indexed synthetic source {doc_id}", flush=True)
    sources = retrieve("org-orbit", "Can I get my money back for an undelivered purchase?")
    if not sources or any(source["document_id"] == "doc-north" for source in sources):
        raise AssertionError("Tenant-scoped semantic retrieval failed.")
    with SessionLocal() as db:
        run = db.scalar(select(Run).where(Run.ticket_id == "ticket-1", Run.status == "failed")) if args.retry_failed else None
        if args.retry_failed and not run:
            old = db.scalar(select(Run).where(Run.ticket_id == "ticket-1", Run.status == "awaiting_approval"))
            if old:
                old.status = "rejected"
                for pending in db.scalars(select(Approval).where(Approval.run_id == old.id, Approval.status == "pending")):
                    pending.status = "rejected"
                db.commit()
                run = Run(org_id="org-orbit", ticket_id="ticket-1", mode="llm")
                db.add(run)
                db.commit()
        if not run:
            if args.retry_failed:
                raise SystemExit("There is no failed synthetic run to retry.")
            run = Run(org_id="org-orbit", ticket_id="ticket-1", mode="llm")
            db.add(run)
            db.commit()
        run_id = run.id
    run_job(run_id, recover=args.retry_failed)
    with SessionLocal() as db:
        run = db.get(Run, run_id)
        if run.status != "awaiting_approval" or run.proposal.get("action") != "refund":
            raise AssertionError(f"Live investigation did not propose the expected reviewed refund: status={run.status}, action={run.proposal.get('action')}, error={run.error}")
        if not run.proposal.get("citations"):
            raise AssertionError("Live recommendation has no verified citations.")
        approval = db.scalar(select(Approval).where(Approval.run_id == run_id))
        approval.status, approval.decided_by = "approved", "user-owner"
        db.commit()
    run_job(run_id, resume=True)
    run_job(run_id, resume=True)
    with SessionLocal() as db:
        run = db.get(Run, run_id)
        assert run.status == "completed"
        assert db.get(Order, "order-1").payment_status == "refunded"
        assert db.scalar(select(func.count()).select_from(Action)) == 1
        vector_count = db.execute(text("SELECT count(*) FROM document_chunks")).scalar_one()
        report = {"provider": "gemini", "model": "gemini-3.5-flash-lite", "database": "postgresql", "vector_store": "pgvector", "embedding_model": "gemini-embedding-001", "embedding_dimensions": 768, "indexed_sample_chunks": vector_count, "workflow": run.status, "citations": len(run.proposal["citations"]), "input_tokens": run.input_tokens, "output_tokens": run.output_tokens, "sandbox_actions": 1, "idempotency": "passed", "data": "repository-defined synthetic fixtures in separate local test database", "runtime_user_data_read": False}
    output = root / "docs" / "live-verification.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)

if __name__ == "__main__":
    main()
