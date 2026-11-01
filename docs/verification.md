# Verification record

Build date: 1 November 2026 (Asia/Calcutta).

| Check | Result |
|---|---|
| FastAPI integration suite | **33 passed** on SQLite; PostgreSQL suite also exercised in isolated resolvedesk_test |
| Deterministic evaluation set | **86/86 passed**; category examples and refund boundary cases |
| Live Gemini agent | Free-tier synthetic-only end-to-end pass; native LangChain Gemini tool calling, 2 verified citations, approved sandbox refund, idempotent resume |
| Semantic retrieval | Gemini embedding-001, 768 dimensions, 3 synthetic chunks in PostgreSQL pgvector; tenant-scoped query passed |
| LLM financial-policy boundary | Mocked unsafe recommendation blocked; tenant-scoped tools checked |
| Durable checkpoint read | Verified from a separate Python process |
| Approved job restart recovery | Fresh process resumed persisted approval and executed exactly one action |
| AWS S3 archival adapter | Stubbed SDK request verified object scope and server-side encryption |
| Docker Compose configuration | `docker compose config --quiet` passed |
| Terraform source syntax | Four `.tf` files parsed with python-hcl2 |
| TypeScript | `tsc --noEmit` passed |
| Next.js production build | Passed: compiled, type checked and prerendered |
| Frontend lockfile consistency | `npm ci --dry-run --ignore-scripts --offline` passed |
| Python dependency consistency | `pip check` passed |
| Final-folder HTTP checks | API health and frontend HTTP 200 from the requested D: folder |
| Browser workflow | Owner login, investigation, checkpoint pause, server restart, approval, resolved response and customer order status verified |
| Customer portal | Customer saw only their three requests and their own orders; reviewed response visible |
| Windows launchers | Started and stopped the owned API/frontend process trees; startup readiness check added |
| Polling regression | Typed review text and keyboard focus remained intact across refresh cycles in the browser |
| Short-screen layout | Final stylesheet verified at a 720px-high desktop viewport; sidebar footer accessible |

Browser QA found and fixed a proposal panel remount during polling and a sidebar footer overflow on short screens. The production build was rerun after the fixes. Browser-test data is archived locally under `data/`; the morning demo starts with fresh seeded data. Screenshots are under `docs/screenshots/`.

These checks do not establish general LLM answer quality, retrieval recall, load capacity or production readiness. The evaluation suite is deterministic and is not a benchmark of a language model. The live smoke test establishes one synthetic refund workflow, not broad model quality. See live-verification.json for tokens, citations and isolation details. Terraform provider validation/plan/apply requires Terraform and the user's AWS configuration; HCL parsing alone does not verify cloud resources or provider compatibility. AWS was not provisioned. The combined Render Dockerfile is prepared but has not been built or deployed; Render/Neon account setup and hosted verification remain.

Docker Desktop's Linux engine is now running. The dedicated PostgreSQL container is healthy; all 33 integration tests passed against both SQLite and the isolated PostgreSQL test database. The regular app now uses PostgreSQL with approved Gemini cloud processing and four indexed policies. The one-click launcher starts its database service automatically. Hosted deployment is deferred at the user's request.
