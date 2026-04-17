"""Valence Diagnostics — Web Application.

FastAPI app: marketing site + authenticated diagnostic engine.
Persists jobs, users, and contact inquiries in SQLite (swap to Postgres
via DATABASE_URL). All config comes from env vars — see app/config.py.
"""
from __future__ import annotations

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI, UploadFile, File, Form, BackgroundTasks,
    HTTPException, Request, Depends,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import (
    APP_ENV, IS_PRODUCTION,
    UPLOAD_DIR, RESULTS_DIR, TEMPLATES_DIR, STATIC_DIR,
    MAX_UPLOAD_BYTES,
)
from app.db import init_db, get_session, User, Job, ContactInquiry
from app.auth import (
    hash_password, verify_password,
    validate_email, validate_password,
    set_session_cookie, clear_session_cookie,
    current_user, require_user,
)
from app.inference import analyze_image
from app.motility import analyze_video
from app.report import (
    generate_pdf_report, generate_csv_export, generate_json_export,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO if IS_PRODUCTION else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("valence")


# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Valence Diagnostics",
    description="AI-powered computer vision for real-time bovine sperm quality.",
    version="0.2.0",
)

STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.on_event("startup")
def _startup() -> None:
    init_db()
    log.info("Valence Diagnostics started · env=%s", APP_ENV)


# ── Security headers ─────────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ── HTML-aware auth redirect ─────────────────────────────────────────────────
# For pages (not APIs), a 401 should redirect to /login with ?next=

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401 and request.url.path.startswith("/app"):
        return RedirectResponse(url=f"/login?next={request.url.path}", status_code=303)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_sample_info(**kwargs) -> dict:
    return {k: (v or "").strip()[:200] for k, v in kwargs.items()}


# ── Analysis jobs (background) ───────────────────────────────────────────────

def run_image_job(job_id: str, image_path: str, sample_info: dict) -> None:
    """Background task — image morphology."""
    from app.db import SessionLocal  # late import to dodge circularity
    db = SessionLocal()
    try:
        job = db.scalar(select(Job).where(Job.job_id == job_id))
        if not job:
            return
        job.status = "processing"
        db.commit()

        result_dir = RESULTS_DIR / job_id
        result_dir.mkdir(parents=True, exist_ok=True)

        result = analyze_image(image_path, output_dir=str(result_dir))
        pdf_path = generate_pdf_report(result, sample_info, str(result_dir / "report.pdf"))
        json_data = generate_json_export(result, sample_info)
        csv_data = generate_csv_export(result)

        (result_dir / "report.json").write_text(json.dumps(json_data, indent=2))
        (result_dir / "report.csv").write_text(csv_data)

        job.status = "completed"
        job.result_json = json.dumps(json_data)
        job.pdf_path = pdf_path
        job.csv_path = str(result_dir / "report.csv")
        job.completed_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        log.exception("image job %s failed", job_id)
        job = db.scalar(select(Job).where(Job.job_id == job_id))
        if job:
            job.status = "failed"
            job.error = str(e)[:4000]
            db.commit()
    finally:
        db.close()


def run_video_job(job_id: str, video_path: str, sample_info: dict) -> None:
    """Background task — motility analysis."""
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        job = db.scalar(select(Job).where(Job.job_id == job_id))
        if not job:
            return
        job.status = "processing"
        db.commit()

        result_dir = RESULTS_DIR / job_id
        result_dir.mkdir(parents=True, exist_ok=True)

        result = analyze_video(video_path, output_dir=str(result_dir), max_frames=300)

        motility_data = {
            "type": "motility",
            "summary": {
                "total_tracks": result.total_tracks,
                "total_motility_pct": result.total_motility_pct,
                "progressive_motility_pct": result.progressive_motility_pct,
                "rapid_pct": result.rapid_pct, "medium_pct": result.medium_pct,
                "slow_pct": result.slow_pct, "static_pct": result.static_pct,
                "mass_motility_score": result.mass_motility_score,
                "quality_class": result.quality_class,
                "estimated_concentration": result.estimated_concentration,
                "concentration_note": result.concentration_note,
            },
            "kinematics": {
                "mean_vcl": result.mean_vcl, "mean_vsl": result.mean_vsl,
                "mean_vap": result.mean_vap, "mean_lin": result.mean_lin,
                "mean_str": result.mean_str, "mean_wob": result.mean_wob,
                "mean_alh": result.mean_alh, "mean_bcf": result.mean_bcf,
            },
            "metadata": {
                "fps": result.fps, "frames_analyzed": result.frames_analyzed,
                "processing_time_s": result.processing_time_s,
            },
            "tracks": [
                {
                    "track_id": t.track_id, "motility_class": t.motility_class,
                    "is_progressive": t.is_progressive,
                    "vcl": t.vcl, "vsl": t.vsl, "vap": t.vap,
                    "lin": t.lin, "str": t.str_, "wob": t.wob,
                    "alh": t.alh, "bcf": t.bcf, "n_frames": len(t.frames),
                }
                for t in result.tracks
            ],
            "sample_info": sample_info,
        }

        (result_dir / "motility_report.json").write_text(json.dumps(motility_data, indent=2))

        job.status = "completed"
        job.result_json = json.dumps(motility_data)
        job.track_overlay_path = result.track_overlay_path or ""
        job.completed_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        log.exception("video job %s failed", job_id)
        job = db.scalar(select(Job).where(Job.job_id == job_id))
        if job:
            job.status = "failed"
            job.error = str(e)[:4000]
            db.commit()
    finally:
        db.close()


# ── Public / marketing pages ─────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request, user: Optional[User] = Depends(current_user)):
    return templates.TemplateResponse("landing.html", {"request": request, "user": user})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request, user: Optional[User] = Depends(current_user)):
    return templates.TemplateResponse("pricing.html", {"request": request, "user": user})


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, user: Optional[User] = Depends(current_user)):
    return templates.TemplateResponse("contact.html", {"request": request, "user": user})


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("legal.html", {
        "request": request,
        "title": "Privacy Policy",
        "body_template": "privacy_body.html",
    })


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("legal.html", {
        "request": request,
        "title": "Terms of Service",
        "body_template": "terms_body.html",
    })


# ── Auth pages ───────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: str = "/app",
    user: Optional[User] = Depends(current_user),
):
    if user:
        return RedirectResponse(next, status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "next": next})


@app.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    next: str = "/app",
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session),
):
    email_clean = (email or "").strip().lower()
    user = db.scalar(select(User).where(User.email == email_clean))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        # Deliberately generic error (don't leak which field failed)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "next": next, "email": email_clean,
             "error": "Invalid email or password."},
            status_code=401,
        )
    # Safe redirect: reject absolute URLs / protocol-relative
    target = next if next.startswith("/") and not next.startswith("//") else "/app"
    response = RedirectResponse(target, status_code=303)
    set_session_cookie(response, user.id)
    return response


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(
    request: Request,
    next: str = "/app",
    user: Optional[User] = Depends(current_user),
):
    if user:
        return RedirectResponse(next, status_code=303)
    return templates.TemplateResponse("signup.html", {"request": request, "next": next})


@app.post("/signup", response_class=HTMLResponse)
async def signup_submit(
    request: Request,
    next: str = "/app",
    full_name: str = Form(""),
    organization: str = Form(""),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session),
):
    form_state = {
        "request": request, "next": next,
        "full_name": full_name.strip()[:200],
        "organization": organization.strip()[:200],
        "email": email.strip().lower()[:320],
    }
    try:
        email_clean = validate_email(email)
        validate_password(password)
    except HTTPException as exc:
        return templates.TemplateResponse(
            "signup.html", {**form_state, "error": exc.detail}, status_code=400
        )

    existing = db.scalar(select(User).where(User.email == email_clean))
    if existing:
        return templates.TemplateResponse(
            "signup.html",
            {**form_state, "error": "An account with that email already exists."},
            status_code=409,
        )

    user = User(
        email=email_clean,
        password_hash=hash_password(password),
        full_name=form_state["full_name"],
        organization=form_state["organization"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    target = next if next.startswith("/") and not next.startswith("//") else "/app"
    response = RedirectResponse(target, status_code=303)
    set_session_cookie(response, user.id)
    return response


@app.post("/logout")
async def logout_submit():
    response = RedirectResponse("/", status_code=303)
    clear_session_cookie(response)
    return response


@app.get("/logout")
async def logout_get():
    return await logout_submit()


# ── Diagnostic engine (auth-gated) ───────────────────────────────────────────

@app.get("/app", response_class=HTMLResponse)
async def engine(
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    recent = db.scalars(
        select(Job)
        .where(Job.user_id == user.id, Job.status == "completed")
        .order_by(Job.completed_at.desc())
        .limit(10)
    ).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "recent_jobs": [j.to_dict() for j in recent],
    })


# ── Upload endpoints ─────────────────────────────────────────────────────────

_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp")
_VIDEO_EXTS = (".mp4", ".avi", ".mov", ".mkv")


def _save_upload(upload: UploadFile, job_id: str, allowed_exts: tuple) -> Path:
    name = upload.filename or ""
    if not name.lower().endswith(allowed_exts):
        raise HTTPException(400, f"Unsupported file type. Allowed: {', '.join(allowed_exts)}")

    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    # Strip any path components a client might smuggle in
    safe_name = Path(name).name
    target = job_dir / safe_name

    total = 0
    with open(target, "wb") as f:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                f.close()
                target.unlink(missing_ok=True)
                raise HTTPException(413, f"File exceeds {MAX_UPLOAD_BYTES // 1024 // 1024} MB limit.")
            f.write(chunk)
    return target


@app.post("/api/upload")
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sample_id: str = Form(""), bull_id: str = Form(""),
    breed: str = Form(""), collection_date: str = Form(""),
    fresh_thawed: str = Form(""), lab_name: str = Form(""),
    operator: str = Form(""), magnification: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    job_id = uuid.uuid4().hex[:8]
    image_path = _save_upload(file, job_id, _IMAGE_EXTS)

    sample_info = _safe_sample_info(
        sample_id=sample_id or job_id, bull_id=bull_id, breed=breed,
        collection_date=collection_date, fresh_thawed=fresh_thawed,
        lab_name=lab_name, operator=operator, magnification=magnification,
    )

    job = Job(
        job_id=job_id, user_id=user.id, job_type="image",
        status="queued", filename=Path(image_path).name,
        sample_info_json=json.dumps(sample_info),
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(run_image_job, job_id, str(image_path), sample_info)
    return {"job_id": job_id, "status": "queued", "message": "Analysis started"}


@app.post("/api/upload/video")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sample_id: str = Form(""), bull_id: str = Form(""),
    breed: str = Form(""), collection_date: str = Form(""),
    fresh_thawed: str = Form(""), lab_name: str = Form(""),
    operator: str = Form(""), magnification: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    job_id = uuid.uuid4().hex[:8]
    video_path = _save_upload(file, job_id, _VIDEO_EXTS)

    sample_info = _safe_sample_info(
        sample_id=sample_id or job_id, bull_id=bull_id, breed=breed,
        collection_date=collection_date, fresh_thawed=fresh_thawed,
        lab_name=lab_name, operator=operator, magnification=magnification,
    )

    job = Job(
        job_id=job_id, user_id=user.id, job_type="motility",
        status="queued", filename=Path(video_path).name,
        sample_info_json=json.dumps(sample_info),
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(run_video_job, job_id, str(video_path), sample_info)
    return {"job_id": job_id, "status": "queued", "message": "Video motility analysis started"}


# ── Batch upload (folders / multi-file) ──────────────────────────────────────
#
# The engine accepts a list of files — typically from an HTML folder picker
# (<input webkitdirectory>). Each file is classified by extension, routed to
# the right pipeline, and gets its own Job row so status/reports per file
# remain independent. The response includes a batch_id the client uses to
# display per-file progress.

def _classify_upload(filename: str) -> str:
    name = (filename or "").lower()
    if name.endswith(_IMAGE_EXTS):
        return "image"
    if name.endswith(_VIDEO_EXTS):
        return "motility"
    return "unsupported"


@app.post("/api/upload/batch")
async def upload_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    sample_id: str = Form(""), bull_id: str = Form(""),
    breed: str = Form(""), collection_date: str = Form(""),
    fresh_thawed: str = Form(""), lab_name: str = Form(""),
    operator: str = Form(""), magnification: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    if not files:
        raise HTTPException(400, "No files provided")

    batch_id = uuid.uuid4().hex[:10]
    shared_info = _safe_sample_info(
        sample_id=sample_id, bull_id=bull_id, breed=breed,
        collection_date=collection_date, fresh_thawed=fresh_thawed,
        lab_name=lab_name, operator=operator, magnification=magnification,
    )

    accepted: list[dict] = []
    skipped: list[dict] = []

    for upload in files:
        raw_name = upload.filename or ""
        # Folder uploads set `webkitRelativePath` which the browser puts in
        # the filename; take the basename so we don't smuggle paths.
        basename = Path(raw_name).name
        job_type = _classify_upload(basename)

        if job_type == "unsupported":
            skipped.append({"filename": basename or "(unnamed)", "reason": "unsupported file type"})
            continue

        job_id = uuid.uuid4().hex[:8]
        allowed = _IMAGE_EXTS if job_type == "image" else _VIDEO_EXTS
        try:
            saved_path = _save_upload(upload, job_id, allowed)
        except HTTPException as exc:
            skipped.append({"filename": basename, "reason": exc.detail})
            continue

        per_file_info = {**shared_info, "sample_id": shared_info["sample_id"] or basename or job_id}

        job = Job(
            job_id=job_id,
            user_id=user.id,
            job_type=job_type,
            status="queued",
            filename=basename,
            sample_info_json=json.dumps(per_file_info),
        )
        db.add(job)
        db.flush()

        runner = run_image_job if job_type == "image" else run_video_job
        background_tasks.add_task(runner, job_id, str(saved_path), per_file_info)

        accepted.append({
            "job_id": job_id,
            "filename": basename,
            "type": job_type,
            "status": "queued",
        })

    db.commit()

    if not accepted:
        raise HTTPException(400, "No supported files in batch. Allowed: "
                                  f"{', '.join(_IMAGE_EXTS + _VIDEO_EXTS)}")

    return {
        "batch_id": batch_id,
        "accepted": accepted,
        "skipped": skipped,
        "counts": {
            "total": len(files),
            "accepted": len(accepted),
            "skipped": len(skipped),
            "images": sum(1 for j in accepted if j["type"] == "image"),
            "videos": sum(1 for j in accepted if j["type"] == "motility"),
        },
    }


# ── Job / report endpoints ───────────────────────────────────────────────────

def _get_job_for_user(job_id: str, user: User, db: Session) -> Job:
    job = db.scalar(select(Job).where(Job.job_id == job_id))
    if not job:
        raise HTTPException(404, "Analysis not found")
    if job.user_id != user.id and not user.is_admin:
        raise HTTPException(404, "Analysis not found")
    return job


@app.get("/api/analysis/{job_id}")
async def get_analysis(
    job_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    return _get_job_for_user(job_id, user, db).to_dict()


@app.get("/api/report/{job_id}/json")
async def get_json_report(
    job_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    job = _get_job_for_user(job_id, user, db)
    if job.status != "completed" or not job.result_json:
        raise HTTPException(404, "Report not ready")
    return JSONResponse(json.loads(job.result_json))


@app.get("/api/report/{job_id}/pdf")
async def get_pdf_report(
    job_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    job = _get_job_for_user(job_id, user, db)
    if job.status != "completed" or not job.pdf_path or not Path(job.pdf_path).exists():
        raise HTTPException(404, "PDF not ready")
    return FileResponse(job.pdf_path, media_type="application/pdf",
                        filename=f"Valence_Report_{job_id}.pdf")


@app.get("/api/report/{job_id}/csv")
async def get_csv_report(
    job_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    job = _get_job_for_user(job_id, user, db)
    if job.status != "completed" or not job.csv_path or not Path(job.csv_path).exists():
        raise HTTPException(404, "CSV not ready")
    return FileResponse(job.csv_path, media_type="text/csv",
                        filename=f"Valence_Cells_{job_id}.csv")


@app.get("/api/report/{job_id}/html", response_class=HTMLResponse)
async def get_html_report(
    job_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    job = _get_job_for_user(job_id, user, db)
    if job.status != "completed":
        raise HTTPException(404, "Report not ready")
    html_path = RESULTS_DIR / job_id / "report.html"
    if not html_path.exists():
        raise HTTPException(404, "HTML report not found")
    return HTMLResponse(html_path.read_text())


@app.get("/api/report/{job_id}/tracks")
async def get_track_overlay(
    job_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    job = _get_job_for_user(job_id, user, db)
    if job.status != "completed" or not job.track_overlay_path or not Path(job.track_overlay_path).exists():
        raise HTTPException(404, "Track overlay not found")
    return FileResponse(job.track_overlay_path, media_type="image/jpeg",
                        filename=f"Valence_Tracks_{job_id}.jpg")


@app.get("/report/{job_id}", response_class=HTMLResponse)
async def view_report(
    request: Request, job_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    job = _get_job_for_user(job_id, user, db)
    return templates.TemplateResponse("analysis.html", {
        "request": request, "user": user, "job": job.to_dict(),
    })


@app.get("/api/history")
async def get_history(
    user: User = Depends(require_user),
    db: Session = Depends(get_session),
):
    rows = db.scalars(
        select(Job).where(Job.user_id == user.id).order_by(Job.created_at.desc()).limit(100)
    ).all()
    return [
        {
            "job_id": j.job_id, "status": j.status,
            "type": j.job_type, "filename": j.filename,
            "created_at": j.created_at.isoformat() if j.created_at else "",
            "completed_at": j.completed_at.isoformat() if j.completed_at else "",
        }
        for j in rows
    ]


# ── Contact form ─────────────────────────────────────────────────────────────

@app.post("/api/contact")
async def submit_contact(request: Request, db: Session = Depends(get_session)):
    data = await request.json()
    name = (data.get("name") or "").strip()[:200]
    email = (data.get("email") or "").strip().lower()[:320]
    if not name or not email:
        raise HTTPException(400, "Name and email are required")

    inquiry = ContactInquiry(
        name=name, email=email,
        organization=(data.get("organization") or "").strip()[:200],
        phone=(data.get("phone") or "").strip()[:50],
        interest=(data.get("interest") or "").strip()[:50],
        message=(data.get("message") or "").strip()[:4000],
        ip=(request.client.host if request.client else "")[:64],
    )
    db.add(inquiry)
    db.commit()
    log.info("contact inquiry from %s <%s> interest=%s", name, email, inquiry.interest)
    return {"ok": True}


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/healthz")
async def healthz():
    """Liveness + basic readiness probe."""
    return {"status": "ok", "env": APP_ENV, "version": app.version}
