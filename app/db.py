"""Valence Diagnostics — database layer.

SQLAlchemy 2.0 ORM. SQLite by default; swap DATABASE_URL for Postgres in prod.
Tables: users, jobs, contact_inquiries.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

from app.config import (
    DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, IS_PRODUCTION,
)


# ── Engine / session ─────────────────────────────────────────────────────────
# Backend-specific engine kwargs:
#   SQLite needs check_same_thread=False when FastAPI uses threads, and
#   doesn't use a real connection pool.
#   Postgres benefits from pool_pre_ping (dead-connection detection across
#   container restarts) and explicit pool sizing under concurrent load.
_engine_kwargs: dict = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(
        pool_pre_ping=True,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
        pool_recycle=1800,  # recycle connections after 30 min
    )

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    pass


# ── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    organization: Mapped[str] = mapped_column(String(200), default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    jobs: Mapped[list["Job"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    # image | motility
    job_type: Mapped[str] = mapped_column(String(20), default="image")
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)  # queued|processing|completed|failed

    filename: Mapped[str] = mapped_column(String(500), default="")
    sample_info_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")

    pdf_path: Mapped[str] = mapped_column(String(500), default="")
    csv_path: Mapped[str] = mapped_column(String(500), default="")
    track_overlay_path: Mapped[str] = mapped_column(String(500), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped[Optional[User]] = relationship(back_populates="jobs")

    # ── Convenience: render as the dict shape the JS / templates expect ────
    def to_dict(self) -> dict:
        try:
            sample_info = json.loads(self.sample_info_json or "{}")
        except Exception:
            sample_info = {}
        try:
            result = json.loads(self.result_json) if self.result_json else None
        except Exception:
            result = None

        d = {
            "job_id": self.job_id,
            "status": self.status,
            "type": self.job_type,
            "filename": self.filename,
            "sample_info": sample_info,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else "",
        }
        if result is not None:
            d["result"] = result
        if self.error:
            d["error"] = self.error
        if self.pdf_path:
            d["pdf_path"] = self.pdf_path
        if self.csv_path:
            d["csv_path"] = self.csv_path
        if self.track_overlay_path:
            d["track_overlay_path"] = self.track_overlay_path
        return d


class ContactInquiry(Base):
    __tablename__ = "contact_inquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    name: Mapped[str] = mapped_column(String(200), default="")
    organization: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(320), index=True, default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    interest: Mapped[str] = mapped_column(String(50), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    ip: Mapped[str] = mapped_column(String(64), default="")


# ── Init / session helper ────────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they do not exist. Called at app startup."""
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """FastAPI dependency: per-request DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
