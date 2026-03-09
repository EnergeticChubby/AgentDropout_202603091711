from __future__ import annotations

from typing import List, Tuple

from AgentDropout.protocols.types import DisclosureObject


class MIRMGate:
    def select(
        self,
        scored_candidates: List[DisclosureObject],
        top_k: int,
        token_budget: int,
    ) -> Tuple[List[DisclosureObject], List[DisclosureObject]]:
        if not scored_candidates:
            return [], []

        sorted_candidates = sorted(scored_candidates, key=lambda item: item.score, reverse=True)
        selected: List[DisclosureObject] = []
        rejected: List[DisclosureObject] = []
        remaining_budget = max(token_budget, 0)

        for candidate in sorted_candidates:
            token_cost = candidate.token_cost or len(candidate.content.split())
            within_topk = len(selected) < top_k
            affordable = token_cost <= remaining_budget
            if within_topk and affordable:
                selected.append(candidate)
                remaining_budget -= token_cost
            else:
                rejected.append(candidate)

        return selected, rejected

