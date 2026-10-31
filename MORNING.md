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

## Verified

**25 backend tests**, **86 deterministic evaluation cases**, TypeScript, production build, dependency checks and an actual browser owner → investigation → restart → approval → customer walkthrough.

## What we can do together next

- Add your GitHub remote and push the existing local commits.
- Test live LLM mode using your own API key, if you want it.
- Run PostgreSQL containers once Docker Desktop's Linux engine is available.
- Review and provision AWS in your account only when ready.
- Choose the next product feature from `docs/roadmap.md`.

Cloud is not deployed, LLM calls have not been paid for/tested, and payments remain simulated. The keyless demo is deterministic and clearly labeled. Detailed evidence and remaining limits are in `docs/verification.md`.

Use **STOP.cmd** to stop the owned servers. For editing with hot reload, stop them first, then run `scripts/start.ps1 -Dev`. After edits, `scripts/build.ps1` packages a fresh production version for START.cmd.
