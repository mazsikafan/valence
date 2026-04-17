"""Valence Diagnostics — runtime configuration.

All tunables come from environment variables with sane defaults, so
deployment is a matter of setting env vars — nothing is hard-coded.
Loads `.env` from project root in development.
"""
from __future__ import annotations

import os
from pathlib import Path

# ── .env loading (no extra dep needed) ───────────────────────────────────────
_PROJECT_ROOT = Path(__file__).parent.parent
_env_path = _PROJECT_ROOT / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _env_path(key: str, default: Path) -> Path:
    raw = os.getenv(key)
    if not raw:
        return default
    p = Path(raw)
    return p if p.is_absolute() else (_PROJECT_ROOT / p).resolve()


# ── App ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = _PROJECT_ROOT
APP_ENV = _env("APP_ENV", "development")
IS_PRODUCTION = APP_ENV == "production"
APP_HOST = _env("APP_HOST", "127.0.0.1")
APP_PORT = _env_int("APP_PORT", 8765)
APP_BASE_URL = _env("APP_BASE_URL", f"http://{APP_HOST}:{APP_PORT}")

# ── Security ─────────────────────────────────────────────────────────────────
SESSION_SECRET = _env(
    "SESSION_SECRET",
    "dev-insecure-change-me-dev-insecure-change-me-dev-insecure-change-me",
)
SESSION_COOKIE_NAME = _env("SESSION_COOKIE_NAME", "valence_session")
SESSION_MAX_AGE_SECONDS = _env_int("SESSION_MAX_AGE_SECONDS", 60 * 60 * 24 * 14)

if IS_PRODUCTION and SESSION_SECRET.startswith("dev-"):
    raise RuntimeError(
        "SESSION_SECRET must be set in production — refusing to start with the dev default."
    )

CORS_ORIGINS = [
    o.strip() for o in _env("CORS_ORIGINS", APP_BASE_URL).split(",") if o.strip()
]

# ── Paths ────────────────────────────────────────────────────────────────────
UPLOAD_DIR = _env_path("UPLOAD_DIR", PROJECT_ROOT / "uploads")
RESULTS_DIR = _env_path("RESULTS_DIR", PROJECT_ROOT / "results")
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL = _env("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'valence.db'}")
DB_POOL_SIZE = _env_int("DB_POOL_SIZE", 10)
DB_MAX_OVERFLOW = _env_int("DB_MAX_OVERFLOW", 20)
DB_POOL_TIMEOUT = _env_int("DB_POOL_TIMEOUT", 30)

if IS_PRODUCTION and DATABASE_URL.startswith("sqlite"):
    import warnings
    warnings.warn(
        "Running in production with SQLite. Set DATABASE_URL to a Postgres URL "
        "(postgresql+psycopg://...) before serving real traffic.",
        stacklevel=2,
    )

# ── Uploads ──────────────────────────────────────────────────────────────────
MAX_UPLOAD_MB = _env_int("MAX_UPLOAD_MB", 500)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# ── Model weights ────────────────────────────────────────────────────────────
YOLO_WEIGHTS = _env_path(
    "YOLO_WEIGHTS",
    PROJECT_ROOT / "runs" / "detect" / "models" / "yolo_runs"
    / "yolov8n_bovine" / "weights" / "best.pt",
)
CNN_WEIGHTS = _env_path("CNN_WEIGHTS", MODELS_DIR / "cnn_efficientnet_b0_best.pt")
YOLO_PRETRAINED = "yolov8n.pt"

# ── Detection params ─────────────────────────────────────────────────────────
DETECTION_CONF = 0.25
DETECTION_IOU = 0.45
IMAGE_SIZE = 640
CROP_SIZE = 128

# ── Classes (Roboflow bovine dataset) ────────────────────────────────────────
CLASS_NAMES = [
    "agglutination", "coiled-tail", "distal-droplet", "folded-tail",
    "loose-head", "normal", "others", "proximal-droplet",
]

DEFECT_CATEGORIES = {
    "normal": {"category": "Normal", "severity": "none"},
    "agglutination": {"category": "Head Defect", "severity": "major"},
    "loose-head": {"category": "Head Defect", "severity": "major"},
    "coiled-tail": {"category": "Tail Defect", "severity": "major"},
    "folded-tail": {"category": "Tail Defect", "severity": "minor"},
    "mitocondria": {"category": "Midpiece Defect", "severity": "minor"},
    "proximal-droplet": {"category": "Cytoplasmic Droplet", "severity": "minor"},
    "distal-droplet": {"category": "Cytoplasmic Droplet", "severity": "minor"},
    "error": {"category": "Artifact", "severity": "exclude"},
    "others": {"category": "Other Abnormality", "severity": "minor"},
}

# Society for Theriogenology BSE thresholds
QUALITY_THRESHOLDS = {"satisfactory": 70, "deferred": 50}

# ── Contact form relay ───────────────────────────────────────────────────────
SMTP_HOST = _env("SMTP_HOST", "")
SMTP_PORT = _env_int("SMTP_PORT", 587)
SMTP_USER = _env("SMTP_USER", "")
SMTP_PASSWORD = _env("SMTP_PASSWORD", "")
SMTP_FROM = _env("SMTP_FROM", "no-reply@valence-diagnostics.ai")
CONTACT_FORWARD_TO = _env("CONTACT_FORWARD_TO", "")

# ── Observability ────────────────────────────────────────────────────────────
SENTRY_DSN = _env("SENTRY_DSN", "")

# ── Ensure dirs exist ────────────────────────────────────────────────────────
for d in [UPLOAD_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
