from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


DEFAULT_PHASE_SEQUENCE = ["propose", "critique", "verify", "aggregate"]


@dataclass
class PhaseState:
    round_idx: int
    phase: str


class PhaseScheduler:
    def __init__(self, phase_sequence: Optional[List[str]] = None):
        self.phase_sequence = phase_sequence or DEFAULT_PHASE_SEQUENCE
        if len(self.phase_sequence) == 0:
            self.phase_sequence = DEFAULT_PHASE_SEQUENCE

    def phase_at(self, round_idx: int) -> str:
        if round_idx < len(self.phase_sequence):
            return self.phase_sequence[round_idx]
        return self.phase_sequence[-1]

    def states(self, num_rounds: int) -> List[PhaseState]:
        return [PhaseState(round_idx=idx, phase=self.phase_at(idx)) for idx in range(num_rounds)]
