from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass
class CovarianceStore:
    matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def set_covariance(self, left: str, right: str, value: float) -> None:
        self.matrix.setdefault(left, {})[right] = float(value)
        self.matrix.setdefault(right, {})[left] = float(value)

    def get_covariance(self, left: str, right: str) -> float:
        return self.matrix.get(left, {}).get(right, 0.0)

    def to_dict(self) -> Dict[str, Dict[str, float]]:
        return self.matrix

    def save(self, path: str) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as fp:
            json.dump(self.matrix, fp, ensure_ascii=False, indent=2)


def compute_pairwise_error_covariance(error_vectors: Dict[str, List[int]]) -> CovarianceStore:
    store = CovarianceStore()
    agent_ids = sorted(error_vectors.keys())
    for i, left in enumerate(agent_ids):
        left_values = error_vectors[left]
        for right in agent_ids[i:]:
            right_values = error_vectors[right]
            if len(left_values) != len(right_values):
                continue
            if len(left_values) == 0:
                value = 0.0
            else:
                left_mean = sum(left_values) / len(left_values)
                right_mean = sum(right_values) / len(right_values)
                cov = sum((lv - left_mean) * (rv - right_mean) for lv, rv in zip(left_values, right_values)) / len(left_values)
                value = cov
            store.set_covariance(left, right, value)
    return store
