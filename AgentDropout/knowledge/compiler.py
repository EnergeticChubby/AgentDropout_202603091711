from dataclasses import dataclass
from typing import List

from AgentDropout.knowledge.proposition import Proposition


@dataclass
class KnowledgePlanItem:
    proposition_id: str
    target_scope: str
    action: str


class KnowledgeCompiler:
    """
    V0/V1 lightweight knowledge scope compiler.
    """

    def compile(self, propositions: List[Proposition], domain: str) -> List[KnowledgePlanItem]:
        plan: List[KnowledgePlanItem] = []
        for prop in propositions:
            lowered = prop.text.lower()
            if "the answer is" in lowered or "answer:" in lowered:
                plan.append(
                    KnowledgePlanItem(
                        proposition_id=prop.proposition_id,
                        target_scope="verified_shared",
                        action="public-board-write",
                    )
                )
            elif any(keyword in lowered for keyword in ["assume", "maybe", "possibly"]):
                plan.append(
                    KnowledgePlanItem(
                        proposition_id=prop.proposition_id,
                        target_scope="subgroup",
                        action="scoped-broadcast",
                    )
                )
            else:
                plan.append(
                    KnowledgePlanItem(
                        proposition_id=prop.proposition_id,
                        target_scope="pairwise",
                        action="direct-send",
                    )
                )
        return plan
