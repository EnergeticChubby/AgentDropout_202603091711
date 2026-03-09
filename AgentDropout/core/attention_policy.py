from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


READ_IGNORE = 0
READ_SUMMARY = 1
READ_CLAIMS = 2
READ_CLAIMS_EVIDENCE = 3
READ_FULL = 4


@dataclass
class AttentionDecision:
    level: int
    reason: str


class RuleBasedAttentionPolicy:
    def __init__(self) -> None:
        self.default_by_phase = {
            "propose": READ_SUMMARY,
            "critique": READ_CLAIMS,
            "verify": READ_CLAIMS_EVIDENCE,
            "aggregate": READ_CLAIMS,
        }

    def decide_level(
        self,
        phase: str,
        receiver_id: str,
        predecessor_id: str,
        predecessor_output: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> AttentionDecision:
        context = context or {}
        level = self.default_by_phase.get(phase, READ_FULL)
        reason = f"default_{phase}"

        conflict_peers = set(context.get("conflict_peers", []))
        if predecessor_id in conflict_peers:
            level = max(level, READ_FULL if phase == "aggregate" else READ_CLAIMS_EVIDENCE)
            reason = "conflict_escalation"

        if context.get("high_uncertainty", False):
            level = min(READ_FULL, level + 1)
            reason = f"{reason}_uncertainty"

        if predecessor_output in (None, "", []):
            level = READ_IGNORE
            reason = "empty_message"

        return AttentionDecision(level=level, reason=reason)
