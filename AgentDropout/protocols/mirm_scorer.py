from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from AgentDropout.protocols.blackboard import PublicBlackboard
from AgentDropout.protocols.types import DisclosureObject, DisclosureType


@dataclass
class MIRMWeights:
    novelty: float = 1.0
    posterior_shift: float = 0.8
    contradiction_value: float = 0.6
    evidence_quality: float = 0.7
    token_cost: float = 0.2


class MIRMScorer:
    def __init__(self, weights: MIRMWeights | None = None):
        self.weights = weights or MIRMWeights()

    def score(self, candidates: List[DisclosureObject], blackboard: PublicBlackboard) -> List[DisclosureObject]:
        existing_texts = [item.content for item in blackboard.disclosures]
        for disclosure in candidates:
            novelty = self._novelty(disclosure.content, existing_texts)
            posterior_shift = self._posterior_shift_proxy(disclosure)
            contradiction_value = self._contradiction_value(disclosure)
            evidence_quality = self._evidence_quality(disclosure)
            token_cost_penalty = float(disclosure.token_cost or len(disclosure.content.split()))
            disclosure.score = (
                self.weights.novelty * novelty
                + self.weights.posterior_shift * posterior_shift
                + self.weights.contradiction_value * contradiction_value
                + self.weights.evidence_quality * evidence_quality
                - self.weights.token_cost * token_cost_penalty / 100.0
            )
            disclosure.metadata["mirm_features"] = {
                "novelty": novelty,
                "posterior_shift_proxy": posterior_shift,
                "contradiction_value": contradiction_value,
                "evidence_quality": evidence_quality,
                "token_cost_penalty": token_cost_penalty,
            }
        return candidates

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {token for token in text.lower().split() if token}

    def _novelty(self, text: str, existing_texts: List[str]) -> float:
        if not existing_texts:
            return 1.0
        current = self._tokenize(text)
        if not current:
            return 0.0
        max_overlap = 0.0
        for existing in existing_texts:
            other = self._tokenize(existing)
            if not other:
                continue
            overlap = len(current & other) / max(len(current | other), 1)
            max_overlap = max(max_overlap, overlap)
        return 1.0 - max_overlap

    @staticmethod
    def _posterior_shift_proxy(disclosure: DisclosureObject) -> float:
        content = disclosure.content.lower()
        strong_markers = ["therefore", "thus", "so the answer", "final answer", "must be"]
        uncertainty_markers = ["maybe", "possibly", "uncertain", "not sure"]
        strong = any(marker in content for marker in strong_markers)
        uncertain = any(marker in content for marker in uncertainty_markers)
        if strong and not uncertain:
            return 1.0
        if uncertain:
            return 0.2
        return 0.6

    @staticmethod
    def _contradiction_value(disclosure: DisclosureObject) -> float:
        if disclosure.disclosure_type == DisclosureType.COUNTEREVIDENCE:
            return 1.0
        lower = disclosure.content.lower()
        return 0.8 if any(term in lower for term in ["however", "but", "contradict"]) else 0.0

    @staticmethod
    def _evidence_quality(disclosure: DisclosureObject) -> float:
        lower = disclosure.content.lower()
        has_source_marker = any(term in lower for term in ["source", "according to", "evidence", "citation"])
        has_numeric_support = any(char.isdigit() for char in disclosure.content)
        if disclosure.disclosure_type == DisclosureType.EVIDENCE and has_source_marker:
            return 1.0
        if has_source_marker or has_numeric_support:
            return 0.7
        return 0.4

