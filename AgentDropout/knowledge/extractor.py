import re
import shortuuid
from typing import Any, List

from AgentDropout.knowledge.proposition import Proposition


class PropositionExtractor:
    SENTENCE_SPLIT_RE = re.compile(r"[。\n\.!?]+")

    def extract(self, output: Any, source_node: str, source_role: str) -> List[Proposition]:
        if output is None:
            return []
        if isinstance(output, list):
            text = "\n".join(str(item) for item in output if item is not None)
        else:
            text = str(output)
        candidates = [sent.strip() for sent in self.SENTENCE_SPLIT_RE.split(text) if sent.strip()]
        propositions: List[Proposition] = []
        for sent in candidates[:8]:  # keep extraction lightweight
            lowered = sent.lower()
            status = "verified" if ("the answer is" in lowered or "answer:" in lowered) else "belief"
            confidence = 0.8 if status == "verified" else 0.5
            propositions.append(
                Proposition(
                    proposition_id=shortuuid.ShortUUID().random(length=12),
                    text=sent,
                    source_node=source_node,
                    source_role=source_role,
                    status=status,
                    confidence=confidence,
                    scope="private",
                )
            )
        return propositions
