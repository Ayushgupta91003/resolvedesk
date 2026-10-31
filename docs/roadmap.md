# Next steps

## First morning

- Run the local demo and choose the product/design changes you want.
- Create an empty GitHub repository and add it as the local Git remote.
- Supply an API key if you want to test paid LLM mode; keep it in backend/.env.
- Start Docker Desktop and verify the PostgreSQL/pgvector Compose profile.

## Next implementation milestones

1. Alembic schema migrations and integration tests against PostgreSQL in CI.
2. Real store adapter using a sandbox order/payment provider. Preserve amount/ownership/idempotency checks.
3. Chunked PDF ingestion, evidence coverage tests and retrieval benchmarks.
4. SSE updates, paginated APIs and data fetching with cancellation/cache.
5. A separate SQS worker, transactional outbox and distributed leases. Then permit multiple API replicas.
6. Password reset, verified email/invitations, stronger session lifecycle and shared rate limits.
7. An LLM evaluation set with known tool trajectories and human-rated answer/evidence quality. Track task success, unsafe action attempts, latency and actual provider cost.
8. Configure and validate cloud infrastructure in your AWS account, then provision only after cost review.
9. Per-tenant configurable policy with versioning and a strict server-side policy engine.
10. Real customer feedback and usability iteration.

## Resume evidence to collect

Use measured values, not invented impact. Record the integration test count, evaluation scope, deployed environment, number of real user trials, observed completion rate and processing latency. Clearly label synthetic data, deterministic demo mode and simulated payments.

Suggested bullet after completing/validating the applicable parts:

> Built a multi-tenant support SaaS with Next.js, FastAPI and PostgreSQL; implemented LangGraph checkpoint recovery, role-controlled human approvals and idempotent sandbox actions, validated through [N] integration scenarios.

Add LangChain tool calling, pgvector and AWS deployment to the bullet only after testing those modes in the environment you will demonstrate.
