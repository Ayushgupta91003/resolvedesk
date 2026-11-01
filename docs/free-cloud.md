# Free cloud deployment preparation

Status: configuration prepared, not deployed or container-build verified yet.

The root Dockerfile packages Next.js and FastAPI behind one origin. Render runs this web image; Neon supplies PostgreSQL with pgvector. Both business records and LangGraph checkpoints live in PostgreSQL. Local container files are ephemeral, so do not rely on them for durable data.

1. Push this repository to your own private GitHub repository. Never commit backend/.env or database backups.
2. Create a Neon Free project. In its SQL editor execute `CREATE EXTENSION IF NOT EXISTS vector;`. Copy the direct PostgreSQL connection string, including SSL settings, into Render's secret DATABASE_URL field. Do not post it in chat. The application derives CHECKPOINT_URL automatically. Use a direct connection rather than a transaction-pooled connection for checkpoints.
3. Connect the GitHub repository to a Render Blueprint using render.yaml. Confirm the service plan is Free. Enter DATABASE_URL and LLM_API_KEY only through secret environment fields. Leave tracing disabled and SEED_DEMO=false. Never add a payment method or upgrade on this project's behalf.
4. Render builds the root Dockerfile. After deployment, open the HTTPS URL and register a new owner workspace. The local demo accounts are deliberately absent in production.
5. Upload only non-sensitive sample policies and create a sample customer/ticket. Cloud indexing and investigation send relevant text to Google; Free-tier data terms apply. Review the owner approval before sandbox execution.
6. Verify /api/health reports PostgreSQL and hybrid retrieval, then test sign-in, ticket investigation, approval, restart recovery and tenant isolation on the hosted instance.

Free instances have resource and idle limits; this is a portfolio deployment, not an availability guarantee. A combined Node/Python process may exceed the free service memory allowance under load. Measure before claiming the deployment works. If the build or service exceeds limits, keep the proven local setup and revisit hosting rather than silently selecting a paid plan.

Official plan details: https://render.com/docs/free and https://neon.com/docs/introduction/plans. Gemini billing: https://ai.google.dev/gemini-api/docs/billing.
