"""BovineVision AI — Inference Pipeline.

Takes a microscopy image, runs detection + classification, returns structured results.
"""
import cv2
import numpy as np
import torch
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional
import time
import logging

from app.config import (
    YOLO_WEIGHTS, CNN_WEIGHTS, YOLO_PRETRAINED,
    DETECTION_CONF, DETECTION_IOU, IMAGE_SIZE, CROP_SIZE,
    CLASS_NAMES, DEFECT_CATEGORIES, QUALITY_THRESHOLDS
)

logger = logging.getLogger("bovinevision")

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class CellResult:
    cell_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2] in pixels
    category: str
    severity: str

@dataclass
class AnalysisResult:
    total_cells: int
    normal_count: int
    abnormal_count: int
    normal_pct: float
    abnormal_pct: float
    quality_class: str  # satisfactory / deferred / unsatisfactory
    defect_breakdown: dict  # class_name -> count
    defect_pct_breakdown: dict  # class_name -> percentage
    category_breakdown: dict  # Head/Tail/Midpiece/Droplet -> count
    cells: List[CellResult]
    annotated_image_path: Optional[str] = None
    processing_time_s: float = 0.0
    model_info: dict = field(default_factory=dict)

# ── Model Loading ─────────────────────────────────────────────────────────────

_yolo_model = None
_cnn_model = None
_cnn_device = None

def load_yolo():
    """Load YOLOv8 model (trained or pretrained fallback)."""
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model

    from ultralytics import YOLO

    if YOLO_WEIGHTS.exists():
        logger.info(f"Loading trained YOLO: {YOLO_WEIGHTS}")
        _yolo_model = YOLO(str(YOLO_WEIGHTS))
    else:
        logger.warning(f"Trained YOLO not found at {YOLO_WEIGHTS}, using pretrained")
        _yolo_model = YOLO(YOLO_PRETRAINED)

    return _yolo_model

def load_cnn():
    """Load CNN classifier (EfficientNet-B0)."""
    global _cnn_model, _cnn_device
    if _cnn_model is not None:
        return _cnn_model, _cnn_device

    from torchvision import models, transforms

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    _cnn_device = device

    if CNN_WEIGHTS.exists():
        logger.info(f"Loading trained CNN: {CNN_WEIGHTS}")
        model = models.efficientnet_b0(weights=None)
        # Determine number of classes from saved weights
        state = torch.load(CNN_WEIGHTS, map_location=device, weights_only=True)
        n_classes = state["classifier.1.weight"].shape[0]
        model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, n_classes)
        model.load_state_dict(state)
        model = model.to(device)
        model.eval()
        _cnn_model = model
        logger.info(f"CNN loaded: {n_classes} classes on {device}")
    else:
        logger.warning(f"CNN weights not found at {CNN_WEIGHTS}")
        _cnn_model = None

    return _cnn_model, _cnn_device

# ── Inference ─────────────────────────────────────────────────────────────────

def analyze_image(image_path: str, output_dir: str = None) -> AnalysisResult:
    """Run full analysis pipeline on a microscopy image.

    1. YOLOv8 detects sperm cells
    2. Each detection is classified (YOLO provides class directly)
    3. Results aggregated into sample-level metrics
    4. Annotated image saved
    """
    t0 = time.time()
    image_path = Path(image_path)
    output_dir = Path(output_dir) if output_dir else image_path.parent

    # Load image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]

    # Run YOLO detection
    yolo = load_yolo()
    results = yolo.predict(
        source=str(image_path),
        conf=DETECTION_CONF,
        iou=DETECTION_IOU,
        imgsz=IMAGE_SIZE,
        verbose=False
    )

    # Parse detections
    cells = []
    detections = results[0]
    model_class_names = detections.names  # {0: 'class0', 1: 'class1', ...}

    for i, box in enumerate(detections.boxes):
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
        conf = float(box.conf[0].cpu())
        cls_id = int(box.cls[0].cpu())
        cls_name = model_class_names.get(cls_id, f"class_{cls_id}")

        defect_info = DEFECT_CATEGORIES.get(cls_name, {"category": "Unknown", "severity": "unknown"})

        cells.append(CellResult(
            cell_id=i,
            class_name=cls_name,
            confidence=round(conf, 3),
            bbox=[round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            category=defect_info["category"],
            severity=defect_info["severity"],
        ))

    # Filter out artifacts
    cells_valid = [c for c in cells if c.severity != "exclude"]
    total = len(cells_valid)

    if total == 0:
        return AnalysisResult(
            total_cells=0, normal_count=0, abnormal_count=0,
            normal_pct=0, abnormal_pct=0, quality_class="unsatisfactory",
            defect_breakdown={}, defect_pct_breakdown={},
            category_breakdown={}, cells=cells,
            processing_time_s=round(time.time() - t0, 2),
            model_info={"yolo": str(YOLO_WEIGHTS), "note": "No valid cells detected"}
        )

    # Count by class
    defect_breakdown = {}
    category_breakdown = {}
    for c in cells_valid:
        defect_breakdown[c.class_name] = defect_breakdown.get(c.class_name, 0) + 1
        category_breakdown[c.category] = category_breakdown.get(c.category, 0) + 1

    normal_count = defect_breakdown.get("normal", 0)
    abnormal_count = total - normal_count
    normal_pct = round(100 * normal_count / total, 1) if total > 0 else 0
    abnormal_pct = round(100 - normal_pct, 1)

    defect_pct_breakdown = {k: round(100 * v / total, 1) for k, v in defect_breakdown.items()}

    # Quality classification
    if normal_pct >= QUALITY_THRESHOLDS["satisfactory"]:
        quality_class = "satisfactory"
    elif normal_pct >= QUALITY_THRESHOLDS["deferred"]:
        quality_class = "deferred"
    else:
        quality_class = "unsatisfactory"

    # Generate annotated image
    annotated_path = None
    try:
        annotated_img = img.copy()
        colors = {
            "normal": (0, 200, 0), "agglutination": (0, 0, 255),
            "loose-head": (255, 0, 0), "coiled-tail": (255, 165, 0),
            "folded-tail": (0, 255, 255), "proximal-droplet": (255, 0, 255),
            "distal-droplet": (128, 0, 128), "mitocondria": (255, 255, 0),
            "others": (128, 128, 128), "error": (100, 100, 100),
        }
        for c in cells:
            x1, y1, x2, y2 = [int(v) for v in c.bbox]
            color = colors.get(c.class_name, (200, 200, 200))
            thickness = 2 if c.class_name == "normal" else 3
            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, thickness)
            label = f"{c.class_name} {c.confidence:.0%}"
            cv2.putText(annotated_img, label, (x1, max(y1 - 5, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        annotated_path = str(output_dir / f"{image_path.stem}_annotated.jpg")
        cv2.imwrite(annotated_path, annotated_img)
    except Exception as e:
        logger.warning(f"Failed to save annotated image: {e}")

    processing_time = round(time.time() - t0, 2)

    return AnalysisResult(
        total_cells=total,
        normal_count=normal_count,
        abnormal_count=abnormal_count,
        normal_pct=normal_pct,
        abnormal_pct=abnormal_pct,
        quality_class=quality_class,
        defect_breakdown=defect_breakdown,
        defect_pct_breakdown=defect_pct_breakdown,
        category_breakdown=category_breakdown,
        cells=cells,
        annotated_image_path=annotated_path,
        processing_time_s=processing_time,
        model_info={
            "yolo_weights": str(YOLO_WEIGHTS) if YOLO_WEIGHTS.exists() else "pretrained",
            "cnn_weights": str(CNN_WEIGHTS) if CNN_WEIGHTS.exists() else "none",
            "detection_conf": DETECTION_CONF,
        }
    )
