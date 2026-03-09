from typing import Dict, List

from AgentDropout.knowledge.proposition import Proposition


class EntailmentCluster:
    """
    Lightweight duplicate clustering via normalized text key.
    """

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().split())

    def cluster(self, propositions: List[Proposition]) -> Dict[str, List[Proposition]]:
        groups: Dict[str, List[Proposition]] = {}
        for prop in propositions:
            key = self._normalize(prop.text)
            groups.setdefault(key, []).append(prop)
        return groups
