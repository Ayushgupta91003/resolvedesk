# Good morning — ResolveDesk is ready to explore

Project: `D:\06_All_Coding_Related_Stuff\03_Personal_Projects\06_ResolveDesk`

1. Open **http://127.0.0.1:3000**. If it is not running, double-click **START.cmd**.
2. Click **Step into Orbit Commerce** on the sign-in screen. The browser may already be signed in as the owner.
3. Open **Support inbox → Payment went through, but my order never arrived**.
4. Click **Run investigation**. Review the policy sources and verified order.
5. Approve the **sandbox** refund. The ticket resolves and a reviewed response appears.
6. Sign out and use **Try customer portal** to see Priya's own requests and order status.

Manual owner login: `owner@orbit.demo` / `DemoPass123!`.

## What's built

- Next.js/TypeScript dashboard, inbox, approvals, knowledge base, agent activity, settings/team and customer portal.
- FastAPI with real sessions, owner/agent/customer roles, organization isolation and customer ownership checks.
- SQLite local demo; PostgreSQL + pgvector Docker configuration and optional semantic retrieval.
- Real LangGraph checkpoints, approval interrupts, restart recovery and idempotent sandbox actions.
- Optional LangChain tool-calling model adapter and LangSmith tracing.
- Dockerfiles, CI workflow and AWS Terraform scaffold.
- Windows setup/build/start/stop scripts and installed local dependencies.

## Latest local verification

Docker PostgreSQL is running on localhost:55432. Existing SQLite records were migrated without deleting the original database. Gemini Free-tier testing passed in a separate synthetic-only database: native LangChain Gemini agent, LangGraph approval, pgvector semantic retrieval, two verified citations, sandbox refund and duplicate-execution prevention. See `docs/live-verification.json`.

The regular app now uses Gemini with hybrid retrieval after your explicit opt-in. Its four policies were indexed successfully. Investigation and indexing send relevant ticket/policy text to Google. Your key is stored only in ignored `backend/.env`. Gemini Pro and API billing are separate; leave the API project on Free tier and do not enable paid billing.

Keep Docker Desktop running. START.cmd now starts this project's PostgreSQL service automatically when backend/.env selects the local database on port 55432. It leaves other projects alone.

## Previous verification

**25 backend tests**, **86 deterministic evaluation cases**, TypeScript, production build, dependency checks and an actual browser owner → investigation → restart → approval → customer walkthrough.

## What we can do together next

- Existing Git history is pushed to https://github.com/Ayushgupta91003/resolvedesk (public repository).
- Hosting is deferred at your request. When ready, create free Render and Neon projects using docs/free-cloud.md.
- Review and provision AWS in your account only when ready.
- Choose the next product feature from `docs/roadmap.md`.

Cloud is not deployed. Live Gemini has been tested using Free-tier synthetic fixtures; payments remain simulated. Detailed evidence and remaining limits are in `docs/verification.md`.

Use **STOP.cmd** to stop the owned servers. For editing with hot reload, stop them first, then run `scripts/start.ps1 -Dev`. After edits, `scripts/build.ps1` packages a fresh production version for START.cmd.
