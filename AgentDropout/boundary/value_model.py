from collections import defaultdict
from typing import Dict


class BoundaryValueModel:
    """
    Lightweight contextual value tracker (bandit-style average reward).
    """

    def __init__(self) -> None:
        self.counts = defaultdict(int)
        self.values = defaultdict(float)

    def update(self, action_type: str, reward: float) -> None:
        self.counts[action_type] += 1
        n = self.counts[action_type]
        prev = self.values[action_type]
        self.values[action_type] = prev + (reward - prev) / n

    def best_action(self, candidates: list[str]) -> str:
        if not candidates:
            return "internalize"
        return max(candidates, key=lambda a: self.values.get(a, 0.0))

    def snapshot(self) -> Dict[str, float]:
        return dict(self.values)
