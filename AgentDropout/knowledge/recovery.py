from typing import Dict, List

from AgentDropout.knowledge.board import SharedKnowledgeBoard
from AgentDropout.knowledge.store import EpistemicStateStore


class KnowledgeRecovery:
    def __init__(self, store: EpistemicStateStore, board: SharedKnowledgeBoard) -> None:
        self.store = store
        self.board = board

    def recover(self) -> Dict[str, List[str]]:
        # Lightweight recovery: retract empty public propositions.
        retracted: List[str] = []
        for item in list(self.board.public_items):
            if len(str(item.get("text", "")).strip()) == 0:
                pid = item.get("proposition_id")
                if pid:
                    self.board.retract(pid)
                    retracted.append(pid)
        return {"retracted_public_items": retracted}
