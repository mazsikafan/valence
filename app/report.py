"""BovineVision AI — PDF Report Generation.

Generates professional CASA-style semen analysis reports.
"""
import io
import base64
import csv
import json
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from app.config import TEMPLATES_DIR, DEFECT_CATEGORIES

def _chart_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 PNG for embedding in HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

def _image_to_base64(image_path: str) -> str:
    """Convert image file to base64 for embedding."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_defect_pie_chart(defect_breakdown: dict) -> str:
    """Generate pie chart of defect distribution."""
    if not defect_breakdown:
        return ""

    labels = list(defect_breakdown.keys())
    sizes = list(defect_breakdown.values())
    colors_map = {
        "normal": "#2ecc71", "agglutination": "#e74c3c", "loose-head": "#c0392b",
        "coiled-tail": "#e67e22", "folded-tail": "#f39c12", "proximal-droplet": "#9b59b6",
        "distal-droplet": "#8e44ad", "mitocondria": "#f1c40f", "others": "#95a5a6",
        "error": "#bdc3c7",
    }
    colors = [colors_map.get(l, "#7f8c8d") for l in labels]

    fig, ax = plt.subplots(figsize=(6, 4))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.1f%%",
        startangle=90, pctdistance=0.85, textprops={"fontsize": 9}
    )
    for t in autotexts:
        t.set_fontsize(8)
    ax.set_title("Morphology Distribution", fontsize=12, fontweight="bold")

    return _chart_to_base64(fig)

def generate_confidence_bar_chart(cells) -> str:
    """Generate bar chart of per-class average confidence."""
    if not cells:
        return ""

    class_confs = {}
    for c in cells:
        if c.class_name not in class_confs:
            class_confs[c.class_name] = []
        class_confs[c.class_name].append(c.confidence)

    labels = sorted(class_confs.keys())
    means = [np.mean(class_confs[l]) for l in labels]

    fig, ax = plt.subplots(figsize=(7, 3))
    bars = ax.barh(labels, means, color="#3498db", edgecolor="white")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Average Confidence")
    ax.set_title("Detection Confidence by Class", fontsize=11, fontweight="bold")
    for bar, val in zip(bars, means):
        ax.text(val + 0.02, bar.get_y() + bar.get_height()/2, f"{val:.0%}",
                va="center", fontsize=9)

    return _chart_to_base64(fig)

def generate_html_report(analysis_result, sample_info: dict = None) -> str:
    """Generate full HTML report from analysis results."""
    r = analysis_result
    info = sample_info or {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate charts
    pie_b64 = generate_defect_pie_chart(r.defect_breakdown)
    conf_b64 = generate_confidence_bar_chart(r.cells)

    # Annotated image
    annot_b64 = ""
    if r.annotated_image_path and Path(r.annotated_image_path).exists():
        annot_b64 = _image_to_base64(r.annotated_image_path)

    # Quality styling
    quality_colors = {
        "satisfactory": "#27ae60", "deferred": "#f39c12", "unsatisfactory": "#e74c3c"
    }
    q_color = quality_colors.get(r.quality_class, "#7f8c8d")

    # Defect table rows
    defect_rows = ""
    for cls_name in sorted(r.defect_breakdown.keys()):
        count = r.defect_breakdown[cls_name]
        pct = r.defect_pct_breakdown.get(cls_name, 0)
        cat_info = DEFECT_CATEGORIES.get(cls_name, {})
        category = cat_info.get("category", "Unknown")
        severity = cat_info.get("severity", "unknown")
        sev_color = {"major": "#e74c3c", "minor": "#f39c12", "none": "#27ae60"}.get(severity, "#95a5a6")
        defect_rows += f"""
        <tr>
            <td>{cls_name}</td>
            <td>{category}</td>
            <td style="color:{sev_color};font-weight:bold">{severity}</td>
            <td style="text-align:right">{count}</td>
            <td style="text-align:right">{pct}%</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>BovineVision AI — Semen Analysis Report</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #2c3e50; background: #fff; padding: 40px; max-width: 900px; margin: 0 auto; }}
    .header {{ border-bottom: 3px solid #2c3e50; padding-bottom: 15px; margin-bottom: 25px; }}
    .header h1 {{ font-size: 24px; color: #2c3e50; }}
    .header .subtitle {{ color: #7f8c8d; font-size: 13px; margin-top: 5px; }}
    .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px; }}
    .meta-box {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 12px 15px; }}
    .meta-box h3 {{ font-size: 11px; text-transform: uppercase; color: #7f8c8d; margin-bottom: 8px; letter-spacing: 0.5px; }}
    .meta-box p {{ font-size: 13px; margin: 3px 0; }}
    .quality-badge {{ display: inline-block; padding: 8px 20px; border-radius: 6px; color: white; font-size: 18px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }}
    .section {{ margin: 30px 0; }}
    .section h2 {{ font-size: 16px; color: #2c3e50; border-bottom: 1px solid #dee2e6; padding-bottom: 8px; margin-bottom: 15px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 13px; }}
    th {{ background: #2c3e50; color: white; padding: 8px 12px; text-align: left; font-size: 11px; text-transform: uppercase; }}
    td {{ padding: 7px 12px; border-bottom: 1px solid #eee; }}
    tr:nth-child(even) {{ background: #f8f9fa; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 15px 0; }}
    .summary-card {{ text-align: center; background: #f8f9fa; border-radius: 6px; padding: 15px; border: 1px solid #dee2e6; }}
    .summary-card .value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
    .summary-card .label {{ font-size: 11px; color: #7f8c8d; text-transform: uppercase; margin-top: 4px; }}
    .chart-container {{ text-align: center; margin: 15px 0; }}
    .chart-container img {{ max-width: 100%; border: 1px solid #eee; border-radius: 4px; }}
    .annotated-img {{ text-align: center; margin: 15px 0; }}
    .annotated-img img {{ max-width: 100%; border: 2px solid #dee2e6; border-radius: 6px; }}
    .footer {{ margin-top: 40px; padding-top: 15px; border-top: 1px solid #dee2e6; font-size: 11px; color: #95a5a6; text-align: center; }}
    .disclaimer {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; padding: 10px 15px; font-size: 11px; color: #856404; margin: 20px 0; }}
    @media print {{ body {{ padding: 20px; }} }}
</style>
</head>
<body>

<div class="header">
    <h1>BovineVision AI</h1>
    <div class="subtitle">Automated Bovine Semen Morphology Analysis Report</div>
</div>

<div class="meta-grid">
    <div class="meta-box">
        <h3>Sample Information</h3>
        <p><strong>Sample ID:</strong> {info.get('sample_id', 'N/A')}</p>
        <p><strong>Bull ID:</strong> {info.get('bull_id', 'N/A')}</p>
        <p><strong>Breed:</strong> {info.get('breed', 'N/A')}</p>
        <p><strong>Collection Date:</strong> {info.get('collection_date', 'N/A')}</p>
        <p><strong>Fresh / Thawed:</strong> {info.get('fresh_thawed', 'N/A')}</p>
    </div>
    <div class="meta-box">
        <h3>Analysis Details</h3>
        <p><strong>Report Date:</strong> {now}</p>
        <p><strong>Lab:</strong> {info.get('lab_name', 'N/A')}</p>
        <p><strong>Operator:</strong> {info.get('operator', 'N/A')}</p>
        <p><strong>Magnification:</strong> {info.get('magnification', 'N/A')}</p>
        <p><strong>Processing Time:</strong> {r.processing_time_s}s</p>
    </div>
</div>

<div class="section" style="text-align:center">
    <h2>Quality Assessment</h2>
    <div class="quality-badge" style="background:{q_color}">{r.quality_class}</div>
    <p style="margin-top:10px;color:#7f8c8d;font-size:12px">
        Based on Society for Theriogenology BSE criteria (>=70% normal = Satisfactory)
    </p>
</div>

<div class="section">
    <h2>Summary</h2>
    <div class="summary-grid">
        <div class="summary-card">
            <div class="value">{r.total_cells}</div>
            <div class="label">Total Cells</div>
        </div>
        <div class="summary-card">
            <div class="value" style="color:#27ae60">{r.normal_pct}%</div>
            <div class="label">Normal</div>
        </div>
        <div class="summary-card">
            <div class="value" style="color:#e74c3c">{r.abnormal_pct}%</div>
            <div class="label">Abnormal</div>
        </div>
        <div class="summary-card">
            <div class="value">{r.normal_count}/{r.total_cells}</div>
            <div class="label">Normal / Total</div>
        </div>
    </div>
</div>

<div class="section">
    <h2>Morphology Defect Breakdown</h2>
    <table>
        <thead>
            <tr><th>Defect Type</th><th>Category</th><th>Severity</th><th style="text-align:right">Count</th><th style="text-align:right">Percentage</th></tr>
        </thead>
        <tbody>
            {defect_rows}
        </tbody>
    </table>
</div>

{"<div class='section'><h2>Morphology Distribution</h2><div class='chart-container'><img src='data:image/png;base64," + pie_b64 + "'></div></div>" if pie_b64 else ""}

{"<div class='section'><h2>Detection Confidence</h2><div class='chart-container'><img src='data:image/png;base64," + conf_b64 + "'></div></div>" if conf_b64 else ""}

{("<div class='section'><h2>Annotated Microscopy Image</h2><div class='annotated-img'><img src='data:image/jpeg;base64," + annot_b64 + "'></div><p style='font-size:11px;color:#7f8c8d;text-align:center;margin-top:8px'>Bounding boxes: Normal (green) | Head defects (red) | Tail defects (orange) | Droplets (purple)</p></div>") if annot_b64 else ""}

<div class="disclaimer">
    <strong>Disclaimer:</strong> This report is generated by BovineVision AI, an automated analysis system.
    Results are intended as decision support and should be interpreted by a qualified professional.
    This system is not a replacement for expert morphological assessment or certified CASA analysis.
    For breeding decisions, consult with a veterinary andrologist.
</div>

<div class="footer">
    <p>BovineVision AI v1.0 | Powered by YOLOv8 + EfficientNet | Report generated {now}</p>
</div>

</body>
</html>"""
    return html

def generate_pdf_report(analysis_result, sample_info: dict = None, output_path: str = None) -> str:
    """Generate PDF report. Falls back to HTML if WeasyPrint not available."""
    html = generate_html_report(analysis_result, sample_info)

    if output_path is None:
        output_path = str(Path(analysis_result.annotated_image_path).parent / "report.pdf") if analysis_result.annotated_image_path else "report.pdf"

    # Try WeasyPrint, fall back to saving HTML
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(output_path)
        return output_path
    except ImportError:
        # Save as HTML instead
        html_path = output_path.replace(".pdf", ".html")
        with open(html_path, "w") as f:
            f.write(html)
        return html_path

def generate_csv_export(analysis_result) -> str:
    """Generate per-cell CSV data for researchers."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["cell_id", "class_name", "confidence", "category", "severity",
                     "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2"])
    for c in analysis_result.cells:
        writer.writerow([c.cell_id, c.class_name, c.confidence, c.category, c.severity,
                         *c.bbox])
    return output.getvalue()

def generate_json_export(analysis_result, sample_info: dict = None) -> dict:
    """Generate JSON export for API integration."""
    r = analysis_result
    return {
        "report_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "sample_info": sample_info or {},
        "summary": {
            "total_cells": r.total_cells,
            "normal_count": r.normal_count,
            "abnormal_count": r.abnormal_count,
            "normal_pct": r.normal_pct,
            "abnormal_pct": r.abnormal_pct,
            "quality_class": r.quality_class,
        },
        "defect_breakdown": r.defect_breakdown,
        "defect_pct_breakdown": r.defect_pct_breakdown,
        "category_breakdown": r.category_breakdown,
        "cells": [asdict(c) for c in r.cells],
        "model_info": r.model_info,
        "processing_time_s": r.processing_time_s,
    }
