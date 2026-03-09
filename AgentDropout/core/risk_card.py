from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class RiskCard:
    agent_id: str
    base_accuracy: float = 0.0
    uncertainty: float = 0.0
    avg_latency: float = 0.0
    avg_token_cost: float = 0.0
    failure_taxonomy: Dict[str, int] = field(default_factory=dict)
    covariance_with_others: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
