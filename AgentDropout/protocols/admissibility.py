from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from AgentDropout.protocols.types import DisclosureObject, DisclosureType


@dataclass
class AdmissibilityDecision:
    admissible: bool
    standard: str
    reasons: List[str] = field(default_factory=list)


class AdmissibilityEngine:
    def evaluate(self, disclosure: DisclosureObject, risk_level: str = "medium") -> AdmissibilityDecision:
        standard = self._standard_by_risk(risk_level)
        reasons: List[str] = []

        content = disclosure.content.strip()
        token_cost = disclosure.token_cost or len(content.split())
        has_evidence_marker = any(
            marker in content.lower() for marker in ["according to", "source", "evidence", "citation", "because"]
        )
        has_numeric_support = any(char.isdigit() for char in content)

        if disclosure.disclosure_type == DisclosureType.QUESTION:
            return AdmissibilityDecision(admissible=True, standard=standard, reasons=["question_is_admissible"])

        if token_cost < 3:
            reasons.append("content_too_short")

        if disclosure.disclosure_type == DisclosureType.EVIDENCE and not (has_evidence_marker or has_numeric_support):
            reasons.append("evidence_missing_verifiable_marker")

        if disclosure.disclosure_type in {DisclosureType.CLAIM, DisclosureType.COUNTEREVIDENCE}:
            if risk_level in {"high", "critical"} and not (has_evidence_marker or has_numeric_support):
                reasons.append("high_risk_claim_requires_support")

        admissible = len(reasons) == 0
        return AdmissibilityDecision(admissible=admissible, standard=standard, reasons=reasons)

    @staticmethod
    def _standard_by_risk(risk_level: str) -> str:
        if risk_level in {"low"}:
            return "preponderance"
        if risk_level in {"medium"}:
            return "clear_and_convincing"
        return "beyond_reasonable_doubt"

