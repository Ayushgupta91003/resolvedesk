# Verification record

Build date: 1 November 2026 (Asia/Calcutta).

| Check | Result |
|---|---|
| FastAPI integration suite | **25 passed**, Python 3.12.6, keyless demo mode |
| Deterministic evaluation set | **86/86 passed**; category examples and refund boundary cases |
| LangChain live adapter construction | Compiled with a placeholder key; no provider request |
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

These checks do not establish LLM answer quality, retrieval recall, load capacity or production readiness. The evaluation suite is deterministic and is not a benchmark of a language model. Terraform provider validation/plan/apply requires Terraform and the user's AWS configuration; HCL parsing alone does not verify cloud resources or provider compatibility. AWS was not provisioned. Live LLM calls and semantic embeddings require the user's API key and remain unverified.

Docker Desktop was installed, but its Linux engine was unavailable during this session. PostgreSQL/container runtime checks therefore remain pending; native SQLite integration checks passed.
