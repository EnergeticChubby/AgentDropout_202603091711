from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict, List

from AgentDropout.protocols.types import DisclosureObject


@dataclass
class PublicBlackboard:
    disclosures: List[DisclosureObject] = field(default_factory=list)
    group_belief: Dict[str, Any] = field(default_factory=dict)
    unresolved_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    information_gaps: List[str] = field(default_factory=list)
    next_round_requests: List[Dict[str, Any]] = field(default_factory=list)

    def add_disclosure(self, disclosure: DisclosureObject) -> None:
        self.disclosures.append(disclosure)

    def reset(self) -> None:
        self.disclosures.clear()
        self.group_belief.clear()
        self.unresolved_conflicts.clear()
        self.information_gaps.clear()
        self.next_round_requests.clear()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "disclosures": [item.to_dict() for item in self.disclosures],
            "group_belief": self.group_belief,
            "unresolved_conflicts": self.unresolved_conflicts,
            "information_gaps": self.information_gaps,
            "next_round_requests": self.next_round_requests,
        }


@dataclass
class PrivateWorkspace:
    objects_by_agent: DefaultDict[str, List[DisclosureObject]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def add(self, agent_id: str, disclosure: DisclosureObject) -> None:
        self.objects_by_agent[agent_id].append(disclosure)

    def get(self, agent_id: str) -> List[DisclosureObject]:
        return self.objects_by_agent.get(agent_id, [])

    def reset(self) -> None:
        self.objects_by_agent.clear()

    def snapshot(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            agent_id: [item.to_dict() for item in disclosures]
            for agent_id, disclosures in self.objects_by_agent.items()
        }

