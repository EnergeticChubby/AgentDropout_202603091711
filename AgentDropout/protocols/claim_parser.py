from __future__ import annotations

import re
import shortuuid
from datetime import datetime, timezone
from typing import List

from AgentDropout.protocols.types import ClaimObject, ClaimStatus


class ClaimParser:
    _splitter = re.compile(r"(?<=[.!?])\s+")

    def parse(self, speaker_agent: str, text: str) -> List[ClaimObject]:
        normalized = (text or "").strip()
        if not normalized:
            return []
        sentences = [item.strip() for item in self._splitter.split(normalized) if item.strip()]
        if not sentences:
            sentences = [normalized]

        claims: List[ClaimObject] = []
        for sentence in sentences:
            status = self._infer_initial_status(sentence)
            claim = ClaimObject(
                claim_id=shortuuid.ShortUUID().random(length=10),
                content=sentence,
                speaker_agent=speaker_agent,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=self._infer_confidence(sentence),
                assets=self._extract_assets(sentence),
                liabilities=self._extract_liabilities(sentence),
                status=status,
            )
            claims.append(claim)
        return claims

    @staticmethod
    def _infer_confidence(sentence: str) -> float:
        lower = sentence.lower()
        if any(term in lower for term in ["certain", "definitely", "must be", "therefore"]):
            return 0.9
        if any(term in lower for term in ["maybe", "possibly", "not sure", "uncertain"]):
            return 0.3
        return 0.6

    @staticmethod
    def _extract_assets(sentence: str):
        lower = sentence.lower()
        assets = []
        if any(term in lower for term in ["according to", "source", "evidence", "citation"]):
            assets.append({"type": "retrieved_evidence", "detail": sentence})
        if any(char.isdigit() for char in sentence):
            assets.append({"type": "numeric_support", "detail": sentence})
        return assets

    @staticmethod
    def _extract_liabilities(sentence: str):
        lower = sentence.lower()
        liabilities = []
        if any(term in lower for term in ["maybe", "possibly", "uncertain", "not sure"]):
            liabilities.append({"type": "unresolved_ambiguity", "detail": sentence})
        if any(term in lower for term in ["assume", "suppose"]):
            liabilities.append({"type": "unverifiable_assumption", "detail": sentence})
        if "however" in lower and "because" not in lower:
            liabilities.append({"type": "unsupported_contradiction", "detail": sentence})
        return liabilities

    @staticmethod
    def _infer_initial_status(sentence: str) -> ClaimStatus:
        lower = sentence.lower()
        if any(term in lower for term in ["uncertain", "not sure", "maybe", "possibly"]):
            return ClaimStatus.CONTESTED
        if any(term in lower for term in ["according to", "evidence", "therefore"]):
            return ClaimStatus.SUPPORTED
        return ClaimStatus.PROPOSED

