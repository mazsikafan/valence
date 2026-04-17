# Module 2: Video-Based Motility Analysis — Implementation Plan

## What The User Sees

### Quick View (Field Mode)
The technician uploads a 30-second video. After ~30 seconds of processing, they see:

```
┌─────────────────────────────────────────────────┐
│                                                 │
│   TOTAL MOTILITY          PROGRESSIVE           │
│   ██████████ 72%          ██████░░░░ 48%        │
│                                                 │
│   CONCENTRATION           QUALITY               │
│   1,240 M/mL              ████ SATISFACTORY     │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│   [Annotated frame with color-coded tracks]     │
│   ● Rapid (green)  ● Medium (yellow)            │
│   ● Slow (red)     ● Static (blue)              │
│                                                 │
├─────────────────────────────────────────────────┤
│   Rapid: 38%  Medium: 22%  Slow: 12%  Static: 28% │
│                                                 │
│   [Download PDF]  [Download JSON]  [Download CSV]│
└─────────────────────────────────────────────────┘
```

### Detailed View (Lab Mode)
Expandable sections below the quick view:

**Kinematic Parameters Table:**
```
Parameter    Mean ± SD       Min    Max    Unit
─────────────────────────────────────────────────
VCL          118.3 ± 42.1   12.4   287.6  μm/s
VSL           68.7 ± 31.2    4.1   198.3  μm/s
VAP           89.4 ± 35.8    8.2   234.1  μm/s
LIN           58.1 ± 18.3   11.2    94.7  %
STR           76.9 ± 14.1   22.8    98.1  %
WOB           75.6 ± 12.4   31.5    96.3  %
ALH            4.8 ± 2.1     0.8    14.2  μm
BCF           24.3 ± 8.7     3.2    48.1  Hz
```

**Velocity Distribution Histogram:**
- X-axis: velocity bins (0-300 μm/s)
- Y-axis: number of cells
- Color bands: rapid (green) / medium (yellow) / slow (red)

**Track Visualization:**
- Single frame from video with all tracked trajectories overlaid
- Color-coded by motility class
- Toggle: show all / rapid only / progressive only

**Per-Cell Data Table (expandable):**
- Cell ID, VCL, VSL, VAP, LIN, STR, WOB, ALH, BCF, motility class, track duration

---

## Combined Report (Module 1 + Module 2)

When both an image AND video are uploaded for the same sample, the report merges:

```
┌─────────────────────────────────────────────────┐
│  BovineVision AI — Complete Semen Analysis      │
│  Bull: HU-BULL-042 | Holstein | 2026-03-28      │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─── MORPHOLOGY (from image) ──────────────┐  │
│  │  Normal: 74%  Abnormal: 26%              │  │
│  │  Head defects: 8%  Tail defects: 12%     │  │
│  │  Droplets: 4%  Other: 2%                 │  │
│  │  [pie chart]  [annotated image]          │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌─── MOTILITY (from video) ────────────────┐  │
│  │  Total motility: 72%  Progressive: 48%   │  │
│  │  Concentration: 1,240 M/mL               │  │
│  │  VCL: 118 μm/s  VSL: 69 μm/s            │  │
│  │  [velocity histogram] [track overlay]    │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌─── OVERALL ASSESSMENT ───────────────────┐  │
│  │                                          │  │
│  │          ██ SATISFACTORY ██              │  │
│  │                                          │  │
│  │  Morphology: PASS (74% normal >= 70%)    │  │
│  │  Motility:   PASS (72% motile >= 30%)    │  │
│  │  Combined quality score: 8.2 / 10        │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  [Download PDF]  [JSON]  [CSV]                  │
└─────────────────────────────────────────────────┘
```

---

## Technical Architecture

### Pipeline

```
Video Upload (MP4/AVI, 50+ fps)
        │
        ▼
  Frame Extraction (OpenCV, every frame or every Nth)
        │
        ▼
  YOLOv8 Detection per frame (pretrained on HSTLI 1.49M annotations)
        │  Output: bounding boxes + confidence per frame
        ▼
  DeepSORT Tracking (associate detections across frames)
        │  Output: track_id → list of (frame, x, y) positions
        ▼
  Kinematic Computation (pure math, no ML)
        │  VCL = sum of frame-to-frame distances / time
        │  VSL = straight-line distance(start, end) / time
        │  VAP = smoothed path distance / time (5-point moving avg)
        │  ALH = max perpendicular distance from VAP line
        │  BCF = count of VAP-line crossings / time
        │  LIN = VSL / VCL
        │  STR = VSL / VAP
        │  WOB = VAP / VCL
        ▼
  Motility Classification per track
        │  Rapid:    VCL > 100 μm/s (or pixels scaled)
        │  Medium:   VCL 50-100 μm/s
        │  Slow:     VCL 20-50 μm/s
        │  Static:   VCL < 20 μm/s
        │  Progressive: STR > 70% AND VCL > 50 μm/s
        ▼
  Concentration Estimation
        │  Count unique tracks / (chamber_depth × field_area × dilution)
        │  Requires: known magnification + chamber specs
        ▼
  Aggregation
        │  Total motility % = (rapid + medium + slow) / total
        │  Progressive % = progressive / total
        │  Mean ± SD for each kinematic parameter
        ▼
  Report Generation
```

### Training Data

| Dataset | Annotations | Use |
|---------|-------------|-----|
| **HSTLI** | 1.49M bbox, CASA ground truth | Train YOLO detector, validate kinematics |
| **VISEM-Tracking** | 29K frames, tracking IDs | Train DeepSORT tracker |
| **Hungarian university videos** | TBD | Fine-tune for bovine |

### Calibration Requirement

Kinematic parameters in μm/s require pixel-to-micron conversion:
- User inputs magnification (20x, 40x, etc.) and camera sensor size
- OR system calibrates from a stage micrometer image
- OR parameters reported in pixels/frame with a note

### Key Dependencies

```
# Additional packages needed
pip install deep-sort-realtime   # DeepSORT tracking
# ultralytics already installed (YOLOv8)
# opencv already installed (frame extraction)
# numpy/scipy already installed (kinematic math)
```

---

## Implementation Steps

### Step 1: Download HSTLI + VISEM-Tracking
- HSTLI from HuggingFace (~27 hours of video, 1.49M annotations)
- VISEM-Tracking from Zenodo (6.3 GB, 29K annotated frames)

### Step 2: Train Video Detection Model
- YOLOv8s (small, not nano — video needs more accuracy)
- Train on HSTLI annotations (YOLO format already)
- Validate detection mAP on VISEM-Tracking held-out frames

### Step 3: Build Tracking Pipeline
- Integrate DeepSORT with YOLOv8 detections
- Track sperm heads across frames → trajectory per cell
- Validate track continuity (min track length, handle occlusions)

### Step 4: Implement Kinematic Calculations
- Pure Python/NumPy — no ML needed
- VCL, VSL, VAP from position sequences
- ALH, BCF from trajectory geometry
- Validate against HSTLI CASA ground truth (they have real VCL/VSL/VAP values)

### Step 5: Build Motility Classification
- Apply WHO-standard thresholds to kinematic values
- Rapid / medium / slow / static / progressive categories
- Compute sample-level percentages

### Step 6: Concentration Estimation
- Count unique tracked cells per field
- Scale by chamber volume and dilution
- Requires user-provided magnification input

### Step 7: Integrate into Web App
- New upload endpoint: `/api/upload/video`
- Video processing as background task (30-60 sec)
- New report sections: kinematics table, velocity histogram, track overlay
- Combined report when both image + video provided

### Step 8: Track Overlay Visualization
- Draw color-coded trajectories on a single reference frame
- Green = rapid, yellow = medium, red = slow, blue = static
- Save as annotated frame image for the report

---

## Timeline Estimate

| Step | Effort | Blocked by |
|------|--------|-----------|
| Download data | 1 day | Nothing |
| Train YOLO on HSTLI | 2-3 days | Data download |
| DeepSORT integration | 2-3 days | YOLO trained |
| Kinematic math | 1 day | DeepSORT working |
| Motility classification | 0.5 day | Kinematics |
| Concentration estimation | 0.5 day | YOLO detection count |
| Web app integration | 1-2 days | Pipeline working |
| Track visualization | 1 day | Tracking working |
| **Total** | **~10-12 days** | |

---

## Validation Strategy

1. **Detection:** mAP@50 > 80% on VISEM-Tracking test set
2. **Tracking:** Track continuity > 90% (cells tracked for >80% of their visible frames)
3. **Kinematics:** VCL/VSL/VAP within ±15% of HSTLI CASA ground truth
4. **Motility %:** Within ±5% of HSTLI reported motility
5. **Concentration:** Within ±20% of known standard (acceptable for CASA systems)

---

## What This Unlocks

With Module 2 complete, BovineVision covers:

| CASA Function | Module | Status |
|---|---|---|
| Morphology (8 classes) | Module 1 | Done (86% AUC) |
| Motility (total, progressive) | Module 2 | Planned |
| Kinematics (VCL, VSL, VAP, ALH, BCF, LIN, STR, WOB) | Module 2 | Planned |
| Concentration | Module 2 | Planned |
| Quality decision (pass/review/reject) | Both | Done (morphology), planned (combined) |
| Viability (live/dead) | Future | Requires stained images |

**Coverage: ~85% of CASA functionality** (up from current ~20%)
