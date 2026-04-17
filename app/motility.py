"""BovineVision AI — Module 2: Video Motility Analysis.

Processes microscopy video to compute sperm motility metrics:
- Per-frame detection (YOLOv8)
- Multi-object tracking (DeepSORT)
- Kinematic parameter computation (VCL, VSL, VAP, ALH, BCF, LIN, STR, WOB)
- Motility classification (rapid/medium/slow/static/progressive)
- Concentration estimation
- Track overlay visualization
"""
import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import time
import logging

logger = logging.getLogger("bovinevision.motility")

# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class TrackResult:
    track_id: int
    positions: List[Tuple[float, float]]  # (x, y) centroids per frame
    frames: List[int]                      # frame indices
    class_name: str
    avg_confidence: float
    # Kinematics (computed after tracking)
    vcl: float = 0.0   # curvilinear velocity (px/s or um/s)
    vsl: float = 0.0   # straight-line velocity
    vap: float = 0.0   # average path velocity
    alh: float = 0.0   # lateral head amplitude
    bcf: float = 0.0   # beat cross frequency
    lin: float = 0.0   # linearity (VSL/VCL)
    str_: float = 0.0  # straightness (VSL/VAP)
    wob: float = 0.0   # wobble (VAP/VCL)
    motility_class: str = "static"  # rapid/medium/slow/static
    is_progressive: bool = False

@dataclass
class MotilityResult:
    total_tracks: int
    total_motile: int
    total_progressive: int
    total_motility_pct: float
    progressive_motility_pct: float
    rapid_pct: float
    medium_pct: float
    slow_pct: float
    static_pct: float
    # Kinematic means
    mean_vcl: float
    mean_vsl: float
    mean_vap: float
    mean_lin: float
    mean_str: float
    mean_wob: float
    mean_alh: float
    mean_bcf: float
    # Concentration
    estimated_concentration: Optional[float]  # M/mL if calibration available
    concentration_note: str = ""
    # Metadata
    fps: float = 0.0
    frames_analyzed: int = 0
    processing_time_s: float = 0.0
    tracks: List[TrackResult] = field(default_factory=list)
    track_overlay_path: Optional[str] = None
    # Quality
    mass_motility_score: int = 0  # 0-5 Evans & Maxwell scale
    quality_class: str = "unsatisfactory"  # satisfactory/deferred/unsatisfactory

# ── Kinematic Calculations ────────────────────────────────────────────────────

def compute_kinematics(positions: List[Tuple[float, float]], fps: float,
                       px_to_um: float = 1.0) -> dict:
    """Compute CASA kinematic parameters from a sequence of (x,y) positions.

    Args:
        positions: List of (x, y) centroids, one per frame
        fps: Frames per second
        px_to_um: Pixel-to-micron conversion factor (1.0 if uncalibrated)

    Returns:
        Dictionary of kinematic parameters
    """
    if len(positions) < 5:
        return {"vcl": 0, "vsl": 0, "vap": 0, "alh": 0, "bcf": 0,
                "lin": 0, "str": 0, "wob": 0}

    pts = np.array(positions) * px_to_um
    n = len(pts)
    dt = 1.0 / fps
    total_time = (n - 1) * dt

    if total_time <= 0:
        return {"vcl": 0, "vsl": 0, "vap": 0, "alh": 0, "bcf": 0,
                "lin": 0, "str": 0, "wob": 0}

    # VCL — Curvilinear velocity: total path length / time
    frame_dists = np.sqrt(np.sum(np.diff(pts, axis=0)**2, axis=1))
    total_path = np.sum(frame_dists)
    vcl = total_path / total_time

    # VSL — Straight-line velocity: start-to-end distance / time
    straight_dist = np.sqrt(np.sum((pts[-1] - pts[0])**2))
    vsl = straight_dist / total_time

    # VAP — Average path velocity: smoothed path length / time
    # Use 5-point moving average for smoothing
    window = min(5, n)
    if window >= 3:
        kernel = np.ones(window) / window
        smoothed_x = np.convolve(pts[:, 0], kernel, mode='valid')
        smoothed_y = np.convolve(pts[:, 1], kernel, mode='valid')
        smoothed_pts = np.column_stack([smoothed_x, smoothed_y])
        smoothed_dists = np.sqrt(np.sum(np.diff(smoothed_pts, axis=0)**2, axis=1))
        smoothed_path = np.sum(smoothed_dists)
        smoothed_time = (len(smoothed_pts) - 1) * dt
        vap = smoothed_path / smoothed_time if smoothed_time > 0 else 0
    else:
        vap = (vcl + vsl) / 2

    # ALH — Amplitude of lateral head displacement
    # Max perpendicular distance from the average path line
    if len(pts) >= 3:
        # Compute perpendicular distances from each point to the start-end line
        start, end = pts[0], pts[-1]
        line_vec = end - start
        line_len = np.sqrt(np.sum(line_vec**2))
        if line_len > 0:
            line_unit = line_vec / line_len
            perp_dists = []
            for p in pts:
                v = p - start
                proj = np.dot(v, line_unit)
                closest = start + proj * line_unit
                perp_dists.append(np.sqrt(np.sum((p - closest)**2)))
            alh = np.max(perp_dists)
        else:
            alh = 0
    else:
        alh = 0

    # BCF — Beat cross frequency
    # Count how many times the actual path crosses the average (smoothed) path
    if len(pts) >= 5 and window >= 3:
        # Use the smoothed path as reference
        # Compute signed distance from actual to smoothed at each valid point
        offset = (window - 1) // 2
        valid_actual = pts[offset:offset + len(smoothed_pts)]
        diffs = valid_actual - smoothed_pts
        # Project onto perpendicular direction
        if line_len > 0:
            perp_unit = np.array([-line_unit[1], line_unit[0]])
            signed_dists = np.dot(diffs, perp_unit)
            # Count zero crossings
            crossings = np.sum(np.diff(np.sign(signed_dists)) != 0)
            valid_time = (len(signed_dists) - 1) * dt
            bcf = crossings / valid_time if valid_time > 0 else 0
        else:
            bcf = 0
    else:
        bcf = 0

    # Derived ratios
    lin = (vsl / vcl * 100) if vcl > 0 else 0
    str_ = (vsl / vap * 100) if vap > 0 else 0
    wob = (vap / vcl * 100) if vcl > 0 else 0

    return {
        "vcl": round(vcl, 2),
        "vsl": round(vsl, 2),
        "vap": round(vap, 2),
        "alh": round(alh, 2),
        "bcf": round(bcf, 2),
        "lin": round(min(lin, 100), 1),
        "str": round(min(str_, 100), 1),
        "wob": round(min(wob, 100), 1),
    }

def classify_motility(vcl: float, str_: float, progressive_threshold_vcl: float = 50,
                      progressive_threshold_str: float = 70) -> Tuple[str, bool]:
    """Classify a sperm's motility based on WHO/CASA thresholds.

    Default thresholds are in pixels/sec when uncalibrated.
    With px_to_um calibration, standard bovine thresholds:
      rapid: VCL > 100 um/s
      medium: VCL 50-100 um/s
      slow: VCL 20-50 um/s
      static: VCL < 20 um/s
      progressive: STR > 70% AND VCL > 50 um/s
    """
    if vcl < 10:
        return "static", False
    elif vcl < 25:
        return "slow", False
    elif vcl < 50:
        return "medium", str_ > progressive_threshold_str
    else:
        is_prog = str_ > progressive_threshold_str
        return "rapid", is_prog

# ── Video Analysis Pipeline ───────────────────────────────────────────────────

def analyze_video(video_path: str, output_dir: str = None,
                  max_frames: int = 300, fps_override: float = None,
                  px_to_um: float = 1.0, chamber_depth_um: float = 20.0,
                  field_area_um2: float = None, dilution_factor: float = 1.0,
                  detection_conf: float = 0.25) -> MotilityResult:
    """Run full motility analysis on a microscopy video.

    Args:
        video_path: Path to video file (MP4, AVI)
        output_dir: Where to save results (annotated frame, etc.)
        max_frames: Maximum frames to analyze (limits processing time)
        fps_override: Override detected FPS
        px_to_um: Pixel-to-micron conversion (1.0 = report in pixels)
        chamber_depth_um: Chamber depth in microns (for concentration)
        field_area_um2: Field of view area in um^2 (for concentration)
        dilution_factor: Sample dilution factor
        detection_conf: YOLO detection confidence threshold
    """
    t0 = time.time()
    video_path = Path(video_path)
    output_dir = Path(output_dir) if output_dir else video_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = fps_override or cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frames_to_analyze = min(max_frames, total_frames)
    logger.info(f"Video: {width}x{height} @ {fps}fps, {total_frames} frames, analyzing {frames_to_analyze}")

    # Load YOLO detector
    from ultralytics import YOLO
    from app.config import YOLO_WEIGHTS, YOLO_PRETRAINED

    yolo_path = YOLO_WEIGHTS if YOLO_WEIGHTS.exists() else YOLO_PRETRAINED
    yolo = YOLO(str(yolo_path))

    # Initialize tracker
    from deep_sort_realtime.deepsort_tracker import DeepSort
    tracker = DeepSort(
        max_age=30,           # frames to keep lost tracks
        n_init=3,             # detections before confirmed
        max_iou_distance=0.7,
        embedder="clip_ViT-B/16",  # use CLIP embeddings
        embedder_gpu=False,
    )

    # Process frames
    all_track_data: Dict[int, dict] = {}  # track_id -> {positions, frames, confs, classes}
    reference_frame = None

    for frame_idx in range(frames_to_analyze):
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx == frames_to_analyze // 2:
            reference_frame = frame.copy()

        # Detect
        results = yolo.predict(source=frame, conf=detection_conf, verbose=False)
        detections = results[0]

        # Prepare detections for DeepSORT: [[x1, y1, w, h], confidence, class]
        det_list = []
        for box in detections.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu())
            cls = int(box.cls[0].cpu())
            cls_name = detections.names.get(cls, f"cls_{cls}")
            det_list.append(([x1, y1, x2 - x1, y2 - y1], conf, cls_name))

        # Update tracker
        if det_list:
            bbs = [d[0] for d in det_list]
            confs = [d[1] for d in det_list]
            clses = [d[2] for d in det_list]
            tracks = tracker.update_tracks(
                raw_detections=list(zip(bbs, confs, clses)),
                frame=frame
            )
        else:
            tracks = tracker.update_tracks([], frame=frame)

        # Record track positions
        for track in tracks:
            if not track.is_confirmed():
                continue
            tid = track.track_id
            ltrb = track.to_ltrb()
            cx = (ltrb[0] + ltrb[2]) / 2
            cy = (ltrb[1] + ltrb[3]) / 2

            if tid not in all_track_data:
                all_track_data[tid] = {
                    "positions": [], "frames": [], "confs": [],
                    "class": track.det_class or "sperm"
                }
            all_track_data[tid]["positions"].append((cx, cy))
            all_track_data[tid]["frames"].append(frame_idx)
            all_track_data[tid]["confs"].append(track.det_conf or 0.5)

    cap.release()

    if reference_frame is None:
        # Use first frame as fallback
        cap2 = cv2.VideoCapture(str(video_path))
        ret, reference_frame = cap2.read()
        cap2.release()

    # ── Compute kinematics for each track ─────────────────────────────────
    track_results = []
    min_track_length = 10  # minimum frames for valid track

    for tid, data in all_track_data.items():
        if len(data["positions"]) < min_track_length:
            continue

        kin = compute_kinematics(data["positions"], fps, px_to_um)
        mot_class, is_prog = classify_motility(kin["vcl"], kin["str"])

        tr = TrackResult(
            track_id=tid,
            positions=data["positions"],
            frames=data["frames"],
            class_name=data["class"],
            avg_confidence=round(np.mean(data["confs"]), 3),
            vcl=kin["vcl"], vsl=kin["vsl"], vap=kin["vap"],
            alh=kin["alh"], bcf=kin["bcf"],
            lin=kin["lin"], str_=kin["str"], wob=kin["wob"],
            motility_class=mot_class,
            is_progressive=is_prog,
        )
        track_results.append(tr)

    # ── Aggregate ─────────────────────────────────────────────────────────
    total = len(track_results)
    if total == 0:
        return MotilityResult(
            total_tracks=0, total_motile=0, total_progressive=0,
            total_motility_pct=0, progressive_motility_pct=0,
            rapid_pct=0, medium_pct=0, slow_pct=0, static_pct=100,
            mean_vcl=0, mean_vsl=0, mean_vap=0, mean_lin=0,
            mean_str=0, mean_wob=0, mean_alh=0, mean_bcf=0,
            estimated_concentration=None,
            fps=fps, frames_analyzed=frames_to_analyze,
            processing_time_s=round(time.time() - t0, 2),
            quality_class="unsatisfactory",
        )

    motile = [t for t in track_results if t.motility_class != "static"]
    progressive = [t for t in track_results if t.is_progressive]
    rapid = [t for t in track_results if t.motility_class == "rapid"]
    medium = [t for t in track_results if t.motility_class == "medium"]
    slow = [t for t in track_results if t.motility_class == "slow"]
    static = [t for t in track_results if t.motility_class == "static"]

    total_motility_pct = round(100 * len(motile) / total, 1)
    progressive_pct = round(100 * len(progressive) / total, 1)

    # Kinematic means (motile cells only)
    motile_tracks = motile if motile else track_results
    mean_vcl = round(np.mean([t.vcl for t in motile_tracks]), 1)
    mean_vsl = round(np.mean([t.vsl for t in motile_tracks]), 1)
    mean_vap = round(np.mean([t.vap for t in motile_tracks]), 1)
    mean_lin = round(np.mean([t.lin for t in motile_tracks]), 1)
    mean_str = round(np.mean([t.str_ for t in motile_tracks]), 1)
    mean_wob = round(np.mean([t.wob for t in motile_tracks]), 1)
    mean_alh = round(np.mean([t.alh for t in motile_tracks]), 1)
    mean_bcf = round(np.mean([t.bcf for t in motile_tracks]), 1)

    # Concentration estimation (if calibration available)
    concentration = None
    conc_note = "Uncalibrated (px_to_um=1.0). Provide magnification for μm/s values."
    if px_to_um != 1.0 and field_area_um2 and chamber_depth_um:
        # cells per field / (field_volume in mL) / dilution
        field_vol_ml = (field_area_um2 * chamber_depth_um) * 1e-12  # um^3 to mL
        concentration = round(total / field_vol_ml / dilution_factor / 1e6, 1)  # in M/mL
        conc_note = f"Estimated: {concentration} M/mL (chamber {chamber_depth_um}μm, dilution {dilution_factor}x)"

    # Mass motility score (Evans & Maxwell 0-5)
    if total_motility_pct >= 90:
        mass_score = 5
    elif total_motility_pct >= 75:
        mass_score = 4
    elif total_motility_pct >= 40:
        mass_score = 3
    elif total_motility_pct >= 20:
        mass_score = 2
    elif total_motility_pct >= 10:
        mass_score = 1
    else:
        mass_score = 0

    # Quality classification (BSE: motility >= 30% = satisfactory for motility component)
    if total_motility_pct >= 60:
        quality = "satisfactory"
    elif total_motility_pct >= 30:
        quality = "deferred"
    else:
        quality = "unsatisfactory"

    # ── Track overlay visualization ───────────────────────────────────────
    overlay_path = None
    if reference_frame is not None:
        overlay = reference_frame.copy()
        colors = {
            "rapid": (0, 255, 0),     # green
            "medium": (0, 255, 255),   # yellow
            "slow": (0, 0, 255),       # red
            "static": (255, 0, 0),     # blue
        }
        for tr in track_results:
            color = colors.get(tr.motility_class, (200, 200, 200))
            pts = [(int(x), int(y)) for x, y in tr.positions]
            if len(pts) >= 2:
                for i in range(1, len(pts)):
                    cv2.line(overlay, pts[i-1], pts[i], color, 1)
            # Draw current position
            if pts:
                cv2.circle(overlay, pts[-1], 3, color, -1)

        # Legend
        y_off = 20
        for cls, color in colors.items():
            cv2.putText(overlay, f"{cls}", (10, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            y_off += 20

        overlay_path = str(output_dir / f"{video_path.stem}_tracks.jpg")
        cv2.imwrite(overlay_path, overlay)

    processing_time = round(time.time() - t0, 2)

    return MotilityResult(
        total_tracks=total,
        total_motile=len(motile),
        total_progressive=len(progressive),
        total_motility_pct=total_motility_pct,
        progressive_motility_pct=progressive_pct,
        rapid_pct=round(100 * len(rapid) / total, 1),
        medium_pct=round(100 * len(medium) / total, 1),
        slow_pct=round(100 * len(slow) / total, 1),
        static_pct=round(100 * len(static) / total, 1),
        mean_vcl=mean_vcl, mean_vsl=mean_vsl, mean_vap=mean_vap,
        mean_lin=mean_lin, mean_str=mean_str, mean_wob=mean_wob,
        mean_alh=mean_alh, mean_bcf=mean_bcf,
        estimated_concentration=concentration,
        concentration_note=conc_note,
        fps=fps,
        frames_analyzed=frames_to_analyze,
        processing_time_s=processing_time,
        tracks=track_results,
        track_overlay_path=overlay_path,
        mass_motility_score=mass_score,
        quality_class=quality,
    )
