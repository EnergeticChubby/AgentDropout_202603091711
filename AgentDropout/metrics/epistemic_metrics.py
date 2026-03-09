from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class EpistemicMetrics:
    accuracy: float
    avg_public_disclosures: float
    avg_total_claims: float
    avg_verified_claims: float
    quality_score: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "accuracy": self.accuracy,
            "avg_public_disclosures": self.avg_public_disclosures,
            "avg_total_claims": self.avg_total_claims,
            "avg_verified_claims": self.avg_verified_claims,
            "quality_score": self.quality_score,
        }


def compute_quality_score(
    accuracy: float,
    avg_public_disclosures: float,
    avg_verified_claims: float,
) -> float:
    return accuracy + 0.01 * avg_verified_claims + 0.001 * avg_public_disclosures


def compare_phase_metrics(previous: Dict[str, float], current: Dict[str, float]) -> Dict[str, float | bool]:
    prev_quality = float(previous.get("quality_score", previous.get("accuracy", 0.0)))
    curr_quality = float(current.get("quality_score", current.get("accuracy", 0.0)))
    return {
        "previous_accuracy": float(previous.get("accuracy", 0.0)),
        "current_accuracy": float(current.get("accuracy", 0.0)),
        "previous_quality_score": prev_quality,
        "current_quality_score": curr_quality,
        "quality_delta": curr_quality - prev_quality,
        "improved": curr_quality > prev_quality,
    }

