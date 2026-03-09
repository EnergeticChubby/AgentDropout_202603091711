import json
from pathlib import Path
from typing import Dict


def load_metrics(metrics_path: str | Path) -> Dict:
    with open(metrics_path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def compare_accuracy(current_metrics: Dict, previous_metrics: Dict) -> Dict[str, float | bool]:
    current = float(current_metrics.get("accuracy", 0.0))
    previous = float(previous_metrics.get("accuracy", 0.0))
    return {
        "current_accuracy": current,
        "previous_accuracy": previous,
        "improved": current > previous,
        "delta": current - previous,
    }

