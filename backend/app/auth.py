import hashlib
import hmac
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .models import AuthSession, User, get_db, now
from .config import SESSION_HOURS

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"

def verify_password(password: str, value: str) -> bool:
    try:
        _, salt, digest = value.split("$")
        return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000).hex(), digest)
    except ValueError:
        return False

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def new_session(db: Session, user: User):
    token = secrets.token_urlsafe(48)
    db.add(AuthSession(token_hash=token_hash(token), user_id=user.id, expires_at=now() + timedelta(hours=SESSION_HOURS)))
    db.commit()
    return token

def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("resolvedesk_session", "")
    session = db.get(AuthSession, token_hash(token)) if token else None
    if not session or session.expires_at < now():
        raise HTTPException(401, "Please sign in to your workspace.")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Account not found.")
    return user

def staff(user: User = Depends(current_user)):
    if user.role not in ("owner", "agent"):
        raise HTTPException(403, "A support team role is required.")
    return user

def owner(user: User = Depends(current_user)):
    if user.role != "owner":
        raise HTTPException(403, "Only workspace owners can approve actions or manage teammates.")
    return user
