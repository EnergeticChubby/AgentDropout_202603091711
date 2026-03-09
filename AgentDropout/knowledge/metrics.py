from typing import Dict, Any

from AgentDropout.knowledge.board import SharedKnowledgeBoard
from AgentDropout.knowledge.store import EpistemicStateStore


class KnowledgeMetrics:
    def compute(self, store: EpistemicStateStore, board: SharedKnowledgeBoard) -> Dict[str, Any]:
        propositions = list(store.propositions.values())
        total = len(propositions)
        public_count = sum(1 for p in propositions if p.scope in {"team_public", "verified_shared"})
        verified_count = sum(1 for p in propositions if p.status == "verified")
        duplicate_proxy = total - len({p.text.strip().lower() for p in propositions if p.text.strip()})
        board_pollution = sum(1 for item in board.public_items if len(str(item.get("text", "")).strip()) == 0)
        false_common_ground = max(0, public_count - verified_count)
        return {
            "total_propositions": total,
            "public_propositions": public_count,
            "verified_propositions": verified_count,
            "duplicate_discussion_rate": (duplicate_proxy / total) if total else 0.0,
            "false_common_ground_rate": (false_common_ground / total) if total else 0.0,
            "re_ask_count": 0,
            "board_pollution_rate": (board_pollution / len(board.public_items)) if board.public_items else 0.0,
        }
