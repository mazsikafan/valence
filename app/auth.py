"""Valence Diagnostics — authentication.

Minimal, dependency-light auth:
  * bcrypt password hashing
  * itsdangerous signed session cookie carrying just the user_id
  * FastAPI dependency `current_user` / `require_user`

Deliberately NOT a JWT system — session cookies are simpler, revocable
at any time by rotating SESSION_SECRET, and good enough for a SaaS
app behind HTTPS.
"""
from __future__ import annotations

import re
from typing import Optional

import bcrypt
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import (
    SESSION_SECRET,
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    IS_PRODUCTION,
)
from app.db import User, get_session


_serializer = URLSafeSerializer(SESSION_SECRET, salt="valence.session.v1")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── Password hashing ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ── Input validation ─────────────────────────────────────────────────────────

def validate_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not email or len(email) > 320 or not _EMAIL_RE.match(email):
        raise HTTPException(400, "Please enter a valid email address.")
    return email


def validate_password(password: str) -> str:
    if not password or len(password) < 10:
        raise HTTPException(400, "Password must be at least 10 characters.")
    if len(password) > 256:
        raise HTTPException(400, "Password is too long.")
    return password


# ── Session cookie ───────────────────────────────────────────────────────────

def set_session_cookie(response, user_id: int) -> None:
    token = _serializer.dumps({"uid": user_id})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


def _read_session_user_id(request: Request) -> Optional[int]:
    raw = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw:
        return None
    try:
        payload = _serializer.loads(raw)
    except BadSignature:
        return None
    uid = payload.get("uid") if isinstance(payload, dict) else None
    return int(uid) if isinstance(uid, int) else None


# ── FastAPI dependencies ─────────────────────────────────────────────────────

def current_user(
    request: Request, db: Session = Depends(get_session)
) -> Optional[User]:
    uid = _read_session_user_id(request)
    if uid is None:
        return None
    user = db.get(User, uid)
    if user is None or not user.is_active:
        return None
    return user


def require_user(user: Optional[User] = Depends(current_user)) -> User:
    if user is None:
        # API callers get 401; HTML pages handle redirect themselves
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_user_or_redirect(
    request: Request, user: Optional[User] = Depends(current_user)
):
    """For HTML pages: return the user, or raise a RedirectResponse to /login."""
    if user is None:
        raise HTTPException(
            status_code=307,
            detail="redirect",
            headers={"Location": f"/login?next={request.url.path}"},
        )
    return user
