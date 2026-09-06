import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from src.utils.paths import (
    PROCESSED_DATA_DIR, PRODUCTION_MODEL_PATH, REPORTS_DIR,
    EVALUATIONS_REPORT_DIR, ensure_dir
)
from src.utils.logging import training_logger

class ModelEvaluator:
    """
    Evaluates a trained YOLO model checkpoint against test/validation splits.
    Produces structured JSON metrics, CSV exports, and a modern HTML evaluation dashboard.
    """
    def __init__(self, data_yaml_path: Path = PROCESSED_DATA_DIR / "data.yaml"):
        self.data_yaml_path = Path(data_yaml_path)

    def evaluate(self, model_path: Optional[Path] = None, split: str = "val") -> Dict[str, Any]:
        """
        Runs model evaluation and returns metrics.
        """
        from ultralytics import YOLO

        target_model = Path(model_path) if model_path else PRODUCTION_MODEL_PATH
        if not target_model.exists():
            training_logger.error(f"Model checkpoint not found for evaluation: {target_model}")
            raise FileNotFoundError(f"Model file not found at {target_model}")

        if not self.data_yaml_path.exists():
            training_logger.error(f"data.yaml not found at {self.data_yaml_path}")
            raise FileNotFoundError(f"data.yaml not found at {self.data_yaml_path}")

        training_logger.info(f"Running evaluation for model: {target_model} on split='{split}'")
        model = YOLO(str(target_model))

        metrics = model.val(
            data=str(self.data_yaml_path.resolve()).replace("\\", "/"),
            split=split,
            imgsz=640,
            device="cpu",
            verbose=True
        )

        precision = float(metrics.box.mp)
        recall = float(metrics.box.mr)
        map50 = float(metrics.box.map50)
        map50_95 = float(metrics.box.map)
        f1_score = float(2 * (precision * recall) / (precision + recall + 1e-8))

        # Per-class metrics
        class_names = metrics.names
        per_class_metrics = []
        if hasattr(metrics.box, "maps") and metrics.box.maps is not None:
            for idx, c_map in enumerate(metrics.box.maps):
                c_name = class_names.get(idx, f"Class {idx}")
                per_class_metrics.append({
                    "class_id": idx,
                    "class_name": c_name,
                    "map50_95": float(c_map),
                    "precision": float(metrics.box.p[idx]) if hasattr(metrics.box, "p") and idx < len(metrics.box.p) else precision,
                    "recall": float(metrics.box.r[idx]) if hasattr(metrics.box, "r") and idx < len(metrics.box.r) else recall,
                })

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": timestamp,
            "model_path": str(target_model),
            "split": split,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4),
            "map50": round(map50, 4),
            "map50_95": round(map50_95, 4),
            "per_class": per_class_metrics
        }

        # Save JSON report
        ensure_dir(EVALUATIONS_REPORT_DIR)
        json_report_path = EVALUATIONS_REPORT_DIR / f"{timestamp}_evaluation.json"
        with open(json_report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        # Generate HTML report
        self._generate_html_report(results)

        training_logger.info(f"Evaluation Complete: mAP50={map50:.4f}, Precision={precision:.4f}, Recall={recall:.4f}")
        return results

    def _generate_html_report(self, results: Dict[str, Any]) -> None:
        """Generates modern HTML dashboard in reports/model_evaluation.html."""
        ensure_dir(REPORTS_DIR)
        html_path = REPORTS_DIR / "model_evaluation.html"

        rows_html = ""
        for c in results.get("per_class", []):
            rows_html += f"""
            <tr>
                <td><strong>{c['class_name']}</strong></td>
                <td>{c['precision']:.4f}</td>
                <td>{c['recall']:.4f}</td>
                <td>{c['map50_95']:.4f}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Canteen - Food Model Evaluation</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border: rgba(255, 255, 255, 0.1);
            --primary: #38bdf8;
            --accent: #22c55e;
            --text: #f8fafc;
            --muted: #94a3b8;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        h1 {{
            color: var(--primary);
            margin-bottom: 5px;
        }}
        .meta {{
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 25px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(10px);
            text-align: center;
        }}
        .card-val {{
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--accent);
            margin-top: 5px;
        }}
        .card-lbl {{
            color: var(--muted);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        th, td {{
            padding: 14px 20px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background: rgba(15, 23, 42, 0.6);
            color: var(--primary);
            font-weight: 600;
        }}
        tr:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🍱 Food Detection Model Evaluation</h1>
        <div class="meta">
            Evaluated on: <strong>{results['timestamp']}</strong> | 
            Split: <strong>{results['split'].upper()}</strong> | 
            Checkpoint: <code>{Path(results['model_path']).name}</code>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-lbl">mAP @ 0.5</div>
                <div class="card-val">{results['map50']:.3f}</div>
            </div>
            <div class="card">
                <div class="card-lbl">mAP @ 0.5:0.95</div>
                <div class="card-val">{results['map50_95']:.3f}</div>
            </div>
            <div class="card">
                <div class="card-lbl">Precision</div>
                <div class="card-val">{results['precision']:.3f}</div>
            </div>
            <div class="card">
                <div class="card-lbl">Recall</div>
                <div class="card-val">{results['recall']:.3f}</div>
            </div>
            <div class="card">
                <div class="card-lbl">F1 Score</div>
                <div class="card-val">{results['f1_score']:.3f}</div>
            </div>
        </div>

        <h2>Per-Class Performance</h2>
        <table>
            <thead>
                <tr>
                    <th>Food Category</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>mAP@0.5:0.95</th>
                </tr>
            </thead>
            <tbody>
                {rows_html if rows_html else '<tr><td colspan="4">No per-class metrics recorded yet.</td></tr>'}
            </tbody>
        </table>
    </div>
</body>
</html>
        """
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        training_logger.info(f"Generated HTML evaluation dashboard at: {html_path}")
