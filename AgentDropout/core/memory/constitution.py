from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from AgentDropout.core.memory.schema import MemoryObject


@dataclass
class GovernanceConstitution:
    min_evidence_to_override: float = 0.6
    high_risk_dual_sign_threshold: float = 0.7
    challenge_limit: float = 0.5

    def validate_write(self, memory: MemoryObject) -> Tuple[bool, str]:
        if memory.type == "summary" and memory.evidence_strength < self.min_evidence_to_override:
            return False, "low_evidence_summary_cannot_override"
        if memory.error_liability >= self.high_risk_dual_sign_threshold and len(memory.signers) < 2:
            return False, "high_risk_requires_dual_sign"
        return True, "ok"

    def should_downgrade(self, memory: MemoryObject) -> bool:
        return memory.error_liability >= self.challenge_limit
