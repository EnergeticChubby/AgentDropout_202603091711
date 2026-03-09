from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValueEstimate:
    marginal_value: float
    uncertainty: float
    conflict_score: float


class HeuristicValueEstimator:
    def estimate(self, current_level: int, target_level: int, uncertainty: float, conflict_score: float) -> ValueEstimate:
        depth_gain = max(0, target_level - current_level)
        marginal_value = 0.5 * depth_gain + 0.3 * uncertainty + 0.2 * conflict_score
        return ValueEstimate(marginal_value=float(marginal_value), uncertainty=float(uncertainty), conflict_score=float(conflict_score))
