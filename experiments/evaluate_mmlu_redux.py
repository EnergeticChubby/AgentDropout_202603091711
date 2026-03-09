import json
from pathlib import Path
from typing import Dict


def load_metrics(metrics_path: str | Path) -> Dict:
    with open(metrics_path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def compare_accuracy(current_metrics: Dict, previous_metrics: Dict) -> Dict[str, float | bool]:
    current = float(current_metrics.get("accuracy", 0.0))
    previous = float(previous_metrics.get("accuracy", 0.0))
    current_quality = float(current_metrics.get("quality_score", current))
    previous_quality = float(previous_metrics.get("quality_score", previous))
    return {
        "current_accuracy": current,
        "previous_accuracy": previous,
        "current_quality_score": current_quality,
        "previous_quality_score": previous_quality,
        "improved": current_quality > previous_quality,
        "delta": current - previous,
        "quality_delta": current_quality - previous_quality,
    }

