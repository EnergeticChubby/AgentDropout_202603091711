from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DisputeDecision:
    action: str
    reason: str
    metadata: Dict[str, Any]


class DisputeResolver:
    """Classify contract verification failures into operational actions."""

    def resolve(self, violations: list[str]) -> DisputeDecision:
        if not violations:
            return DisputeDecision(action="accept", reason="no_violations", metadata={})
        if "empty_deliverable" in violations:
            return DisputeDecision(
                action="rework",
                reason="empty_deliverable",
                metadata={"rollback_to": "upstream_node"},
            )
        if "missing_final_answer_pattern" in violations:
            return DisputeDecision(
                action="clarify",
                reason="missing_final_answer_pattern",
                metadata={"request": "explicit_final_answer"},
            )
        return DisputeDecision(action="escalate", reason="unknown_violation", metadata={"violations": violations})
