import math
from dataclasses import dataclass

from AgentDropout.runtime.state_model import CollaborationState


@dataclass
class BarrierOutput:
    hazard_head: float
    barrier_score: float
    hazard_window: int

    def to_dict(self):
        return {
            "hazard_head": self.hazard_head,
            "barrier_score": self.barrier_score,
            "hazard_window": self.hazard_window,
        }


class BarrierScorer:
    def __init__(self, hazard_window: int = 3, margin: float = 0.2):
        self.hazard_window = hazard_window
        self.margin = margin

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    def score(self, state: CollaborationState) -> BarrierOutput:
        barrier_score = (
            state.progress
            + state.evidence_closure
            - state.consensus_fragility
            - 0.6 * state.redundancy_pressure
            - 0.3 * state.coordination_load
        )
        hazard_logit = -3.0 * (barrier_score - self.margin) + 0.8 * state.coordination_load
        hazard_prob = self._sigmoid(hazard_logit)
        return BarrierOutput(
            hazard_head=max(0.0, min(1.0, hazard_prob)),
            barrier_score=barrier_score,
            hazard_window=self.hazard_window,
        )
