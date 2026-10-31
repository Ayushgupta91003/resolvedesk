import logging
import secrets
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Response, Request, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session
from . import config
from .models import Base, engine, get_db, SessionLocal, Organization, User, Ticket, Message, Order, Document, Run, RunEvent, Approval, Action, Audit, AuthSession, now
from .auth import current_user, staff, owner, hash_password, verify_password, new_session, token_hash
from .agent import run_job, recover_jobs, workflow_lock
from .knowledge import setup_vectors, index_document
from .storage import archive_document
from .seed import seed_demo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
queue_lock = threading.Lock()
login_attempts = defaultdict(deque)

@asynccontextmanager
async def lifespan(app):
    if config.APP_ENV == "production" and config.SEED_DEMO:
        raise RuntimeError("Disable SEED_DEMO before production startup.")
    Base.metadata.create_all(engine)
    setup_vectors()
    if config.SEED_DEMO:
        seed_demo()
    threading.Thread(target=recover_jobs, daemon=True, name="resolvedesk-recovery").start()
    yield

app = FastAPI(title="ResolveDesk API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"])

@app.middleware("http")
async def browser_security(request, call_next):
    origin = request.headers.get("origin")
    if request.method not in ("GET", "HEAD", "OPTIONS") and origin and origin not in config.CORS_ORIGINS:
        return JSONResponse({"detail": "Request origin is not allowed."}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response

def dump(row, exclude=()):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns if column.name not in exclude}

def public_user(user):
    return dump(user, ("password_hash",))

def audit(db, user, action, resource):
    db.add(Audit(org_id=user.org_id, actor=user.name, action=action, resource=resource))

def ticket_for(db, id_, user):
    ticket = db.get(Ticket, id_)
    if not ticket or ticket.org_id != user.org_id or (user.role == "customer" and ticket.customer_id != user.id):
        raise HTTPException(404, "Ticket not found.")
    return ticket

def run_for(db, id_, user):
    run = db.get(Run, id_)
    if not run or run.org_id != user.org_id:
        raise HTTPException(404, "Run not found.")
    ticket_for(db, run.ticket_id, user)
    return run

class Login(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)
    workspace: str = Field(default="", max_length=100)

class Register(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    organization: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=200)

    @field_validator("email")
    @classmethod
    def email_valid(cls, value):
        value = value.strip().lower()
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("A valid email address is required")
        return value

class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=200)
    role: Literal["agent", "customer"] = "agent"

class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=12000)
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    order_reference: str = Field(default="", max_length=50)
    customer_id: str = Field(default="", max_length=36)

class Reply(BaseModel):
    body: str = Field(min_length=1, max_length=8000)

class Decision(BaseModel):
    approved: bool
    note: str = Field(default="", max_length=1000)

class DocumentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=20, max_length=50000)

def set_cookie(response, token):
    response.set_cookie("resolvedesk_session", token, httponly=True, secure=config.COOKIE_SECURE, samesite="lax", max_age=config.SESSION_HOURS * 3600, path="/")

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "agent_mode": config.AGENT_MODE, "sandbox": True, "demo_available": config.SEED_DEMO}

@app.post("/api/auth/login")
def login(body: Login, request: Request, response: Response, db: Session = Depends(get_db)):
    key = request.client.host if request.client else "local"
    with queue_lock:
        times = login_attempts[key]
        current = time.monotonic()
        while times and current - times[0] > 60:
            times.popleft()
        if len(times) >= 20:
            raise HTTPException(429, "Too many attempts. Try again in one minute.")
        times.append(current)
    query = select(User).where(User.email == body.email.strip().lower())
    if body.workspace:
        query = query.where(User.org_id == body.workspace)
    users = db.scalars(query).all()
    if len(users) != 1 or not verify_password(body.password, users[0].password_hash):
        raise HTTPException(401, "Invalid credentials. If your email belongs to multiple workspaces, provide your workspace ID.")
    user = users[0]
    db.execute(delete(AuthSession).where(AuthSession.expires_at < now()))
    set_cookie(response, new_session(db, user))
    return public_user(user)

@app.post("/api/auth/register", status_code=201)
def register(body: Register, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "This email is already registered. Sign in or use another email.")
    org = Organization(name=body.organization.strip())
    db.add(org)
    db.flush()
    user = User(org_id=org.id, email=body.email, name=body.name.strip(), role="owner", password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    audit(db, user, "workspace.created", org.name)
    db.commit()
    set_cookie(response, new_session(db, user))
    return public_user(user)

@app.post("/api/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("resolvedesk_session", "")
    if token:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(token)))
        db.commit()
    response.delete_cookie("resolvedesk_session", path="/")
    return {"ok": True}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {**public_user(user), "organization": dump(db.get(Organization, user.org_id)), "agent_mode": config.AGENT_MODE}

@app.get("/api/dashboard")
def dashboard(user: User = Depends(staff), db: Session = Depends(get_db)):
    tickets = db.scalars(select(Ticket).where(Ticket.org_id == user.org_id)).all()
    runs = db.scalars(select(Run).where(Run.org_id == user.org_id)).all()
    approvals = db.scalars(select(Approval).where(Approval.org_id == user.org_id, Approval.status == "pending")).all()
    actions = db.scalars(select(Action).where(Action.org_id == user.org_id)).all()
    return {"tickets": len(tickets), "open": sum(t.status in ("open", "investigating", "escalated") for t in tickets), "resolved": sum(t.status == "resolved" for t in tickets), "pending_approvals": len(approvals), "runs": len(runs), "completed_runs": sum(r.status == "completed" for r in runs), "refunds": sum(a.kind == "refund" for a in actions), "avg_latency_ms": round(sum(r.latency_ms for r in runs) / len(runs)) if runs else 0, "input_tokens": sum(r.input_tokens for r in runs), "output_tokens": sum(r.output_tokens for r in runs), "categories": {k: sum(t.category == k for t in tickets) for k in ("delivery", "refund", "account", "billing", "general")}, "recent_activity": [dump(a) for a in db.scalars(select(Audit).where(Audit.org_id == user.org_id).order_by(Audit.created_at.desc()).limit(8))]}

@app.get("/api/tickets")
def tickets(status: str = "", q: str = "", user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Ticket).where(Ticket.org_id == user.org_id)
    if user.role == "customer":
        query = query.where(Ticket.customer_id == user.id)
    if status:
        query = query.where(Ticket.status == status)
    if q:
        query = query.where(Ticket.subject.ilike(f"%{q[:100]}%") | Ticket.number.ilike(f"%{q[:100]}%"))
    rows = db.scalars(query.order_by(Ticket.created_at.desc()).limit(200)).all()
    customers = {u.id: u for u in db.scalars(select(User).where(User.org_id == user.org_id))}
    return [{**dump(t), "customer_name": customers[t.customer_id].name, "customer_email": customers[t.customer_id].email} for t in rows]

@app.post("/api/tickets", status_code=201)
def create_ticket(body: TicketCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    customer_id = user.id if user.role == "customer" else body.customer_id or user.id
    customer = db.get(User, customer_id)
    if not customer or customer.org_id != user.org_id:
        raise HTTPException(400, "Customer must belong to this workspace.")
    if body.order_reference:
        order = db.scalar(select(Order).where(Order.org_id == user.org_id, Order.customer_id == customer_id, Order.reference == body.order_reference))
        if not order:
            raise HTTPException(400, "Order reference does not belong to this customer.")
    ticket = Ticket(org_id=user.org_id, customer_id=customer_id, number=f"RD-{secrets.token_hex(4).upper()}", subject=body.subject.strip(), description=body.description.strip(), priority=body.priority, order_reference=body.order_reference)
    db.add(ticket)
    db.flush()
    db.add(Message(ticket_id=ticket.id, author=customer.name, kind="customer", body=ticket.description))
    audit(db, user, "ticket.created", ticket.number)
    db.commit()
    return dump(ticket)

@app.get("/api/tickets/{ticket_id}")
def ticket_detail(ticket_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ticket = ticket_for(db, ticket_id, user)
    customer = db.get(User, ticket.customer_id)
    messages = db.scalars(select(Message).where(Message.ticket_id == ticket.id).order_by(Message.created_at)).all()
    runs = db.scalars(select(Run).where(Run.ticket_id == ticket.id).order_by(Run.created_at.desc())).all()
    # Internal proposals/traces are restricted to support staff.
    return {**dump(ticket), "customer_name": customer.name, "customer_email": customer.email, "messages": [dump(m) for m in messages], "runs": [dump(r) for r in runs] if user.role != "customer" else []}

@app.post("/api/tickets/{ticket_id}/messages", status_code=201)
def reply(ticket_id: str, body: Reply, user: User = Depends(current_user), db: Session = Depends(get_db)):
    with queue_lock:
        ticket = ticket_for(db, ticket_id, user)
        active = db.scalar(select(Run).where(Run.ticket_id == ticket_id, Run.status.in_(["queued", "running", "awaiting_approval"])))
        if active:
            raise HTTPException(409, "An investigation is active. Finish or decline its proposal before changing the conversation.")
        message = Message(ticket_id=ticket.id, author=user.name, kind="customer" if user.role == "customer" else "support", body=body.body.strip())
        db.add(message)
        ticket.updated_at = now()
        if user.role == "customer":
            ticket.status = "open"
        audit(db, user, "ticket.replied", ticket.number)
        db.commit()
    return dump(message)

@app.post("/api/tickets/{ticket_id}/investigate", status_code=202)
def investigate(ticket_id: str, tasks: BackgroundTasks, user: User = Depends(staff), db: Session = Depends(get_db)):
    with queue_lock:
        ticket = ticket_for(db, ticket_id, user)
        active = db.scalar(select(Run).where(Run.ticket_id == ticket_id, Run.status.in_(["queued", "running", "awaiting_approval"])))
        if active:
            raise HTTPException(409, "This ticket already has an active investigation.")
        if ticket.status == "resolved":
            raise HTTPException(409, "A resolved ticket needs a new customer reply before another investigation.")
        run = Run(org_id=user.org_id, ticket_id=ticket_id, mode=config.AGENT_MODE)
        db.add(run)
        ticket.status = "investigating"
        db.flush()
        audit(db, user, "agent.started", ticket.number)
        db.commit()
        tasks.add_task(run_job, run.id)
        return dump(run)

@app.get("/api/runs")
def runs(user: User = Depends(staff), db: Session = Depends(get_db)):
    return [dump(r) for r in db.scalars(select(Run).where(Run.org_id == user.org_id).order_by(Run.created_at.desc()).limit(100))]

@app.get("/api/runs/{run_id}")
def run_detail(run_id: str, user: User = Depends(staff), db: Session = Depends(get_db)):
    run = run_for(db, run_id, user)
    approval = db.scalar(select(Approval).where(Approval.run_id == run.id))
    return {**dump(run), "events": [dump(e) for e in db.scalars(select(RunEvent).where(RunEvent.run_id == run.id).order_by(RunEvent.created_at))], "approval": dump(approval) if approval else None}

@app.post("/api/runs/{run_id}/retry", status_code=202)
def retry_run(run_id: str, tasks: BackgroundTasks, user: User = Depends(staff), db: Session = Depends(get_db)):
    with queue_lock:
        run = run_for(db, run_id, user)
        if run.status != "failed":
            raise HTTPException(409, "Only failed runs can be retried.")
        other = db.scalar(select(Run).where(Run.ticket_id == run.ticket_id, Run.id != run.id, Run.status.in_(["queued", "running", "awaiting_approval"])))
        if other:
            raise HTTPException(409, "Another investigation is active for this ticket.")
        approval = db.scalar(select(Approval).where(Approval.run_id == run.id))
        decision = approval.status == "approved" if approval and approval.status in ("approved", "rejected") else None
        run.status, run.error = "queued", ""
        db.commit()
        tasks.add_task(run_job, run.id, resume=decision, recover=True)
        return dump(run)

@app.get("/api/approvals")
def approvals(user: User = Depends(staff), db: Session = Depends(get_db)):
    rows = db.scalars(select(Approval).where(Approval.org_id == user.org_id).order_by(Approval.created_at.desc()).limit(100)).all()
    return [{**dump(a), "run": dump(db.get(Run, a.run_id)), "ticket": dump(db.get(Ticket, db.get(Run, a.run_id).ticket_id))} for a in rows]

@app.post("/api/approvals/{approval_id}/decide", status_code=202)
def decide(approval_id: str, body: Decision, tasks: BackgroundTasks, user: User = Depends(owner), db: Session = Depends(get_db)):
    with queue_lock:
        approval = db.scalar(select(Approval).where(Approval.id == approval_id, Approval.org_id == user.org_id).with_for_update())
        if not approval:
            raise HTTPException(404, "Approval not found.")
        if approval.status != "pending":
            raise HTTPException(409, "This proposal already has a decision.")
        run = db.get(Run, approval.run_id)
        if run.status != "awaiting_approval":
            raise HTTPException(409, "This workflow is not ready for approval.")
        approval.status = "approved" if body.approved else "rejected"
        approval.decided_by, approval.note = user.id, body.note
        run.status = "queued"
        audit(db, user, f"proposal.{approval.status}", run.ticket_id)
        db.commit()
        tasks.add_task(run_job, run.id, resume=body.approved)
        return dump(approval)

@app.get("/api/knowledge")
def knowledge(user: User = Depends(staff), db: Session = Depends(get_db)):
    return [dump(d) for d in db.scalars(select(Document).where(Document.org_id == user.org_id).order_by(Document.created_at.desc()))]

@app.post("/api/knowledge", status_code=201)
def add_document(body: DocumentCreate, tasks: BackgroundTasks, user: User = Depends(staff), db: Session = Depends(get_db)):
    doc = Document(org_id=user.org_id, title=body.title.strip(), body=body.body.strip())
    db.add(doc)
    db.flush()
    archive_document(user.org_id, doc.id, doc.title, doc.body)
    audit(db, user, "knowledge.created", doc.title)
    db.commit()
    tasks.add_task(index_document, doc.id)
    return dump(doc)

@app.post("/api/knowledge/upload", status_code=201)
async def upload_document(tasks: BackgroundTasks, file: UploadFile = File(...), user: User = Depends(staff), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith((".txt", ".md")):
        raise HTTPException(400, "Upload a UTF-8 .txt or .md document.")
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Maximum file size is 500 KB.")
    try:
        content = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "File must contain UTF-8 text.")
    if len(content.strip()) < 20 or len(content) > 50000:
        raise HTTPException(400, "Document must contain 20–50,000 characters.")
    return add_document(DocumentCreate(title=file.filename[:160], body=content), tasks, user, db)

@app.delete("/api/knowledge/{document_id}")
def remove_document(document_id: str, user: User = Depends(owner), db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc or doc.org_id != user.org_id:
        raise HTTPException(404, "Document not found.")
    audit(db, user, "knowledge.deleted", doc.title)
    db.delete(doc)
    db.commit()
    return {"ok": True}

@app.get("/api/orders")
def orders(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Order).where(Order.org_id == user.org_id)
    if user.role == "customer":
        query = query.where(Order.customer_id == user.id)
    return [dump(o) for o in db.scalars(query)]

@app.get("/api/team")
def team(user: User = Depends(staff), db: Session = Depends(get_db)):
    return [public_user(u) for u in db.scalars(select(User).where(User.org_id == user.org_id))]

@app.post("/api/team", status_code=201)
def add_teammate(body: TeamCreate, user: User = Depends(owner), db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(422, "A valid email is required.")
    if db.scalar(select(User).where(User.org_id == user.org_id, User.email == email)):
        raise HTTPException(409, "This workspace already has a user with this email.")
    teammate = User(org_id=user.org_id, name=body.name.strip(), email=email, role=body.role, password_hash=hash_password(body.password))
    db.add(teammate)
    audit(db, user, "team.member_created", email)
    db.commit()
    return public_user(teammate)

@app.get("/api/audit")
def audit_logs(user: User = Depends(owner), db: Session = Depends(get_db)):
    return [dump(a) for a in db.scalars(select(Audit).where(Audit.org_id == user.org_id).order_by(Audit.created_at.desc()).limit(200))]
