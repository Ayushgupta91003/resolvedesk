from sqlalchemy import select
from app.models import SessionLocal, Document
from app.knowledge import retrieve, chunks

def test_retrieval_returns_matching_tail_chunk():
    with SessionLocal() as db:
        doc = Document(org_id="org-orbit", title="Detailed reference", body=("Background material. " * 400) + "\nUniquecondition734 qualifies for specialist escalation.")
        db.add(doc)
        db.commit()
        doc_id = doc.id
    results = retrieve("org-orbit", "uniquecondition734")
    assert results and results[0]["document_id"] == doc_id
    assert "Uniquecondition734" in results[0]["excerpt"]
    assert results[0]["chunk"] > 1

def test_chunks_preserve_evidence_across_boundaries():
    body = ("context " * 135) + "boundary_evidence" + (" continuation" * 200)
    pieces = list(chunks(body))
    assert any("boundary_evidence" in piece for piece in pieces)
    assert all(len(piece) <= 1100 for piece in pieces)

def test_retrieval_never_includes_other_tenant():
    results = retrieve("org-orbit", "private Northstar policy")
    assert all(result["document_id"] != "doc-north" for result in results)

def test_unrelated_query_returns_no_sources():
    assert retrieve("org-orbit", "unmatchabletoken987654") == []
