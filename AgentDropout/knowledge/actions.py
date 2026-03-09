from typing import Dict, List

from AgentDropout.knowledge.board import SharedKnowledgeBoard
from AgentDropout.knowledge.compiler import KnowledgePlanItem
from AgentDropout.knowledge.store import EpistemicStateStore


class KnowledgeActionExecutor:
    def __init__(self, store: EpistemicStateStore, board: SharedKnowledgeBoard) -> None:
        self.store = store
        self.board = board

    def execute(self, plan_items: List[KnowledgePlanItem]) -> List[Dict]:
        executed: List[Dict] = []
        snapshot = self.store.snapshot()
        for item in plan_items:
            self.store.update_scope(item.proposition_id, item.target_scope)
            if item.target_scope in {"team_public", "verified_shared"}:
                prop = snapshot.get(item.proposition_id) or self.store.snapshot().get(item.proposition_id)
                if prop is not None:
                    self.board.write(prop)
            executed.append(
                {
                    "proposition_id": item.proposition_id,
                    "action": item.action,
                    "target_scope": item.target_scope,
                }
            )
        return executed
