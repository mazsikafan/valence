# BovineVision AI

**Automated bovine semen morphology analysis powered by deep learning.**

Upload a microscopy image of a bull semen sample. Get back a professional quality report with per-cell morphology classification, defect breakdown, and a pass/review/reject decision — in seconds.

---

## What It Does

BovineVision AI replaces manual sperm morphology counting with computer vision. A veterinarian, lab technician, or AI station operator uploads a microscopy image, and the system:

1. **Detects** every sperm cell in the field (YOLOv8 object detection)
2. **Classifies** each cell into one of 8 morphology categories
3. **Aggregates** results into a sample-level quality assessment
4. **Generates** a downloadable report (PDF, JSON, CSV)

### Morphology Classes

| Class | Category | Severity | What It Means |
|-------|----------|----------|---------------|
| Normal | Normal | -- | Healthy, morphologically correct sperm |
| Agglutination | Head Defect | Major | Cells clumped together; may indicate immune response |
| Loose-head | Head Defect | Major | Detached or poorly attached head; non-functional |
| Coiled-tail | Tail Defect | Major | Tightly coiled flagellum; cannot swim |
| Folded-tail | Tail Defect | Minor | Bent tail; impaired motility |
| Proximal droplet | Cytoplasmic Droplet | Minor | Droplet near head; immature cell |
| Distal droplet | Cytoplasmic Droplet | Minor | Droplet near tail; minor immaturity |
| Others | Other Abnormality | Minor | Miscellaneous defects |

### Quality Decision

Based on the [Society for Theriogenology BSE](https://www.therio.org/) classification:

- **Satisfactory** — >= 70% morphologically normal
- **Deferred** — 50-70% normal (re-evaluate later)
- **Unsatisfactory** — < 50% normal

---

## The Report

Each analysis produces a professional semen quality report containing:

- **Sample metadata** — Bull ID, breed, collection date, lab, operator, magnification
- **Summary statistics** — Total cells, % normal, % abnormal
- **Defect breakdown table** — Count and percentage per defect type, categorized by severity
- **Morphology distribution pie chart**
- **Detection confidence bar chart**
- **Annotated microscopy image** — Original image with color-coded bounding boxes per class
- **Quality classification** — Satisfactory / Deferred / Unsatisfactory with color badge
- **Disclaimer** — Results are decision support, not a replacement for expert assessment

Available in three formats:
- **PDF / HTML** — printable, archivable, matches CASA report style
- **JSON** — structured data for integration with lab information systems (LIMS)
- **CSV** — per-cell data (cell ID, class, confidence, bounding box) for researchers

---

## Quick Start

### Install

```bash
git clone <repo-url>
cd bull_sperm
pip install -r requirements.txt
```

Requires Python 3.9+ and ~2GB disk for model weights.

### Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Use

1. Drag and drop a microscopy image (JPG, PNG, TIFF, BMP)
2. Fill in sample metadata (optional but recommended)
3. Click **Analyze Sample**
4. Wait a few seconds for processing
5. View results and download PDF/JSON/CSV report

### API

```bash
# Upload and analyze
curl -X POST http://localhost:8000/api/upload \
  -F "file=@sample.jpg" \
  -F "bull_id=BULL-042" \
  -F "breed=Holstein"

# Returns: {"job_id": "abc123", "status": "queued"}

# Check status
curl http://localhost:8000/api/analysis/abc123

# Download reports
curl -O http://localhost:8000/api/report/abc123/pdf
curl http://localhost:8000/api/report/abc123/json
curl -O http://localhost:8000/api/report/abc123/csv

# History
curl http://localhost:8000/api/history
```

Full API docs at [http://localhost:8000/docs](http://localhost:8000/docs) (auto-generated Swagger UI).

---

## How It Works

```
Microscopy Image (any resolution)
        |
        v
  +-----------+
  | YOLOv8n   |  Detects all sperm cells with bounding boxes
  | 640x640   |  ~15ms per image (GPU), ~4s (CPU)
  +-----------+
        |
        v
  +-----------+
  | Per-cell  |  Classifies each detection into 8 morphology types
  | CNN       |  EfficientNet-B0 with ImageNet transfer learning
  +-----------+
        |
        v
  +-----------+
  | Aggregate |  Counts normal/abnormal, computes percentages,
  |           |  applies BSE quality thresholds
  +-----------+
        |
        v
  +-----------+
  | Report    |  Generates HTML/PDF with charts, annotated image,
  | Generator |  defect table, quality decision
  +-----------+
```

### Models

| Model | Architecture | Training Data | Performance | Purpose |
|-------|-------------|---------------|-------------|---------|
| Sperm Detector | YOLOv8n (nano) | 699 bovine images | 20% mAP@50, 60.9% on normals | Locates cells |
| Binary Classifier | Random Forest | 12,242 cell crops | **86% acc, 0.92 AUC** | Normal vs abnormal |
| Multiclass Classifier | LightGBM | 12,242 cell crops (10 classes) | **75% acc, 47% F1 macro** | Defect type |
| Quality Classifier | Random Forest | CASA parameters | 94% acc (synthetic data) | Sample pass/fail |

### Training Data

- **699 real bovine microscopy images** from 2 Roboflow datasets (CC BY 4.0)
- **12,297 bounding box annotations** across 8 morphology classes
- **12,242 cell crops** extracted for CNN classification training
- Image-level splits to prevent data leakage (no crops from the same image in train and test)

---

## Project Structure

```
bull_sperm/
  app/
    main.py           Web app (FastAPI endpoints, job management)
    inference.py       ML pipeline (YOLOv8 detect -> classify -> aggregate)
    report.py          Report generation (HTML/PDF/JSON/CSV)
    config.py          Settings (classes, thresholds, paths)
    templates/
      index.html       Upload interface (drag-drop, metadata form)
      analysis.html    Report viewer
  models/              Trained model weights (.pt, .pkl)
  data/
    raw/bovine/        Real Roboflow bovine images + YOLO annotations
    processed/         Cell crops for classification
    manifests/         Data tracking CSVs
  configs/             Label schema, YOLO training config
  reports/             Generated analysis reports
  results/             Per-analysis output (reports, annotated images)
  uploads/             Uploaded image staging
  notebooks/           Research notebook (full pipeline)
  requirements.txt
  train_cnn.py         CNN training script
```

---

## Who Is This For

| User | Use Case |
|------|----------|
| **AI station technician** | Quick pass/fail on ejaculates before processing into doses |
| **Veterinarian** | Breeding soundness exam (BSE) morphology component |
| **Breeding company** | Quality monitoring across bulls and over time |
| **Semen processing lab** | QC check on thawed semen samples |
| **Researcher** | Per-cell morphology data export for studies |

---

## Limitations

**This is a research prototype, not a certified diagnostic tool.**

- **Morphology only** — no motility, concentration, or viability assessment (yet)
- **699 training images** — small dataset; performance may vary on different microscopes, staining protocols, or magnifications
- **Community annotations** — training labels from Roboflow community, not certified veterinary andrologists
- **No clinical validation** — not tested in a prospective study against expert assessment or CASA ground truth
- **Single modality** — darkfield/phase contrast microscopy images only; no video analysis
- **No regulatory approval** — not CE marked or OIE compliant

Use as **decision support**, not as a sole basis for breeding decisions.

---

## Roadmap

### Module 2: Video Motility Analysis (planned, see MODULE_2_MOTILITY_PLAN.md)
- [ ] Video upload + frame extraction (50+ fps)
- [ ] YOLOv8 per-frame detection (pretrained on HSTLI 1.49M annotations)
- [ ] DeepSORT multi-object tracking (pretrained on VISEM-Tracking)
- [ ] Kinematic parameter computation (VCL, VSL, VAP, ALH, BCF, LIN, STR, WOB)
- [ ] Motility classification (rapid / medium / slow / static / progressive)
- [ ] Concentration estimation
- [ ] Track overlay visualization (color-coded by velocity class)
- [ ] Combined morphology + motility report

### Infrastructure
- [ ] Docker containerization
- [ ] PDF export via WeasyPrint
- [ ] User accounts and data isolation
- [ ] Edge deployment (Raspberry Pi 5 + USB microscope)

### Data & Validation
- [ ] Hungarian university partnership (real bovine videos + CASA ground truth)
- [ ] Multi-lab validation study
- [ ] Breed-specific model fine-tuning
- [ ] Fertility outcome correlation

---

## Tech Stack

- **Backend:** FastAPI + Uvicorn
- **Detection:** YOLOv8 (ultralytics)
- **Classification:** PyTorch + torchvision (EfficientNet-B0, ResNet50)
- **Image processing:** OpenCV
- **Reports:** Matplotlib + HTML/CSS (WeasyPrint for PDF)
- **Frontend:** Vanilla HTML/CSS/JS with Jinja2 templates

---

## License

Training data: CC BY 4.0 (Roboflow community datasets).
Software: Proprietary.

---

## Quick Start — Local Development

```bash
# 1. Clone + install
git clone https://github.com/mazsikafan/valence.git
cd valence
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # paste into SESSION_SECRET

# 3. Run
uvicorn app.main:app --reload --port 8765
# → http://127.0.0.1:8765
```

First visit `/signup` to create an account. The diagnostic engine at `/app` is
auth-gated; the marketing site at `/`, `/pricing`, `/contact`, `/privacy`, and
`/terms` is public.

## Quick Start — Docker (single-container, SQLite)

```bash
cp .env.example .env     # edit SESSION_SECRET
docker compose up --build
```

## Production — app + Postgres

`docker-compose.prod.yml` brings up the app alongside a managed Postgres.
Create a `.env.prod` file with at least these two variables, then bring
the stack up:

```bash
cat > .env.prod <<EOF
SESSION_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
POSTGRES_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
APP_BASE_URL=https://valence-diagnostics.ai
CORS_ORIGINS=https://valence-diagnostics.ai
EOF

docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml logs -f valence
```

The compose file pins `postgres:16-alpine`, puts data on a named volume
(`pgdata`), and gates the app's startup on a Postgres healthcheck so the
first `create_all()` succeeds. Mount a TLS-terminating reverse proxy
(Caddy, Nginx, or Cloudflare) in front — the app only speaks HTTP.

### Migrating an existing SQLite DB to Postgres

Ad-hoc is fine for the first few users:

```bash
sqlite3 valence.db .dump | \
  sed -e 's/AUTOINCREMENT/GENERATED ALWAYS AS IDENTITY/g' \
      -e 's/PRAGMA.*;//' | \
  psql "postgresql://valence:PW@host:5432/valence"
```

For anything bigger, use [pgloader](https://pgloader.io) — one command
and it handles schema, types, and indexes.

### Volumes

The compose files mount `uploads/`, `results/`, `models/`, and `runs/` as
volumes so data survives rebuilds. `models/` and `runs/` are read-only at
runtime — build-time artifacts should not be written from the app.

## Environment Variables

See `.env.example` for the full list. The important ones:

| Var | Purpose |
|-----|---------|
| `SESSION_SECRET` | Signs session cookies. Rotate to invalidate every session. |
| `DATABASE_URL` | SQLite by default; use `postgresql+psycopg://…` in prod. |
| `YOLO_WEIGHTS`, `CNN_WEIGHTS` | Paths to trained model weights. |
| `MAX_UPLOAD_MB` | Hard upload size cap. |
| `CORS_ORIGINS` | Comma-separated list of allowed origins. |
| `SENTRY_DSN` | Optional error tracking. |

Never commit `.env`. The app refuses to start in `APP_ENV=production` if
`SESSION_SECRET` still has the dev default.

## Routes

Public:
- `GET /` — marketing landing
- `GET /pricing`, `/contact`, `/privacy`, `/terms`
- `POST /api/contact` — stores an inquiry in the `contact_inquiries` table
- `GET /healthz` — liveness/readiness probe

Auth:
- `GET/POST /signup`, `/login`, `POST /logout`

Authenticated engine:
- `GET /app` — upload UI + recent jobs (per-user)
- `POST /api/upload`, `/api/upload/video` — submit a single sample
- `POST /api/upload/batch` — submit many files (folder upload, mixed images + videos). Server auto-classifies by extension, routes images → morphology pipeline and videos → motility pipeline, and returns one job_id per accepted file + a list of skipped files with reasons.
- `GET /api/analysis/{job_id}` — poll status
- `GET /api/report/{job_id}/{pdf|json|csv|html|tracks}` — exports
- `GET /api/history` — user's job history

## Production Checklist

Before the first paid user, confirm:

- [ ] `SESSION_SECRET` rotated to a fresh 48-byte random string
- [ ] `APP_ENV=production`, HTTPS in front of the app (Caddy / Nginx / Cloudflare)
- [ ] `DATABASE_URL` pointing at managed Postgres, not SQLite
- [ ] Volume-mount `uploads/` and `results/` on durable storage with backups
- [ ] Rate limiting at the reverse-proxy layer on `/api/upload*` and `/login`
- [ ] Sentry DSN set
- [ ] Privacy/terms reviewed by counsel and real contact details filled in
- [ ] Motility pipeline validated on a real bovine video dataset with
      ground-truth CASA labels (this is the biggest remaining ML risk)
