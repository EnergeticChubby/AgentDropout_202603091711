from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CollaborationState:
    progress: float
    evidence_closure: float
    consensus_fragility: float
    coordination_load: float
    redundancy_pressure: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "progress": self.progress,
            "evidence_closure": self.evidence_closure,
            "consensus_fragility": self.consensus_fragility,
            "coordination_load": self.coordination_load,
            "redundancy_pressure": self.redundancy_pressure,
        }


def _event_ratio(events: List[Dict], event_type: str, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return sum(1 for e in events if e.get("type") == event_type) / denominator


class StateReconstructor:
    def reconstruct(self, events: List[Dict], active_agents: int, total_messages: int) -> CollaborationState:
        total_events = max(len(events), 1)
        claim_create = _event_ratio(events, "CLAIM_CREATE", total_events)
        claim_resolve = _event_ratio(events, "CLAIM_RESOLVE", total_events)
        claim_challenge = _event_ratio(events, "CLAIM_CHALLENGE", total_events)
        new_info = _event_ratio(events, "MSG_NEW_INFO", total_events)
        rephrase = _event_ratio(events, "MSG_REPHRASE", total_events)
        rollback = _event_ratio(events, "SUMMARY_ROLLBACK", total_events)

        progress = min(1.0, max(0.0, 0.6 * claim_resolve + 0.4 * new_info))
        evidence_closure = min(1.0, max(0.0, claim_resolve / (claim_create + 1e-6)))
        consensus_fragility = min(1.0, max(0.0, 0.7 * claim_challenge + 0.3 * rollback))
        coordination_load = min(1.0, max(0.0, (active_agents / 8.0) + (total_messages / 24.0)))
        redundancy_pressure = min(1.0, max(0.0, 0.7 * rephrase + 0.3 * max(0.0, claim_create - new_info)))

        return CollaborationState(
            progress=progress,
            evidence_closure=evidence_closure,
            consensus_fragility=consensus_fragility,
            coordination_load=coordination_load,
            redundancy_pressure=redundancy_pressure,
        )
