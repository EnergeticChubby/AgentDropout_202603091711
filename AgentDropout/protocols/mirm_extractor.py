from __future__ import annotations

import re
import shortuuid
from typing import List

from AgentDropout.protocols.types import DisclosureObject, DisclosureType


class MIRMExtractor:
    _sentence_splitter = re.compile(r"(?<=[.!?])\s+")

    def extract(self, agent_id: str, round_idx: int, raw_text: str) -> List[DisclosureObject]:
        text = (raw_text or "").strip()
        if not text:
            return []

        sentences = [item.strip() for item in self._sentence_splitter.split(text) if item.strip()]
        if not sentences:
            sentences = [text]

        disclosures: List[DisclosureObject] = []
        for sentence in sentences:
            disclosure_type = self._classify(sentence)
            token_cost = len(sentence.split())
            disclosures.append(
                DisclosureObject(
                    disclosure_id=shortuuid.ShortUUID().random(length=8),
                    agent_id=agent_id,
                    disclosure_type=disclosure_type,
                    content=sentence,
                    round_idx=round_idx,
                    token_cost=token_cost,
                    metadata={"source": "mirm_extractor"},
                )
            )
        return disclosures

    @staticmethod
    def _classify(sentence: str) -> DisclosureType:
        lower = sentence.lower()
        if "?" in sentence or lower.startswith(("why ", "what ", "which ", "how ")):
            return DisclosureType.QUESTION
        if any(token in lower for token in ["uncertain", "not sure", "maybe", "likely", "possibly"]):
            return DisclosureType.UNCERTAINTY_REPORT
        if any(token in lower for token in ["however", "but", "contradict", "inconsistent"]):
            return DisclosureType.COUNTEREVIDENCE
        if any(token in lower for token in ["according to", "evidence", "source", "citation", "because"]):
            return DisclosureType.EVIDENCE
        return DisclosureType.CLAIM

