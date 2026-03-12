from dataclasses import dataclass
from typing import Dict

from AgentDropout.runtime.barrier_model import BarrierOutput
from AgentDropout.runtime.state_model import CollaborationState


ACTIONS = [
    "CONTINUE",
    "WAIT_FOR_EVIDENCE",
    "FREEZE_SUMMARY",
    "SPLIT_DISCUSSION",
    "ADD_SPECIALIST",
    "DROP_ECHO_AGENT",
    "SWAP_COORDINATOR",
]


@dataclass
class InterventionDecision:
    action: str
    triggered: bool
    reason: str
    penalty: float

    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "triggered": self.triggered,
            "reason": self.reason,
            "penalty": self.penalty,
        }


class MinimalInterventionPolicy:
    def __init__(
        self,
        tau_warn: float = 0.35,
        tau_danger: float = 0.50,
        cooldown_events: int = 2,
    ):
        self.tau_warn = tau_warn
        self.tau_danger = tau_danger
        self.cooldown_events = cooldown_events
        self.last_trigger_event_idx = -10_000
        self.penalties = {
            "CONTINUE": 0.0,
            "WAIT_FOR_EVIDENCE": 0.1,
            "FREEZE_SUMMARY": 0.2,
            "SPLIT_DISCUSSION": 0.3,
            "ADD_SPECIALIST": 0.6,
            "DROP_ECHO_AGENT": 0.25,
            "SWAP_COORDINATOR": 0.4,
        }

    def _cooldown_active(self, event_idx: int) -> bool:
        return event_idx - self.last_trigger_event_idx < self.cooldown_events

    def decide(
        self,
        state: CollaborationState,
        barrier: BarrierOutput,
        event_idx: int,
    ) -> InterventionDecision:
        if self._cooldown_active(event_idx):
            return InterventionDecision("CONTINUE", False, "cooldown_active", self.penalties["CONTINUE"])

        if barrier.hazard_head < self.tau_warn and barrier.barrier_score > 0:
            return InterventionDecision("CONTINUE", False, "safe_region", self.penalties["CONTINUE"])

        if barrier.hazard_head >= self.tau_danger:
            if state.consensus_fragility >= 0.45:
                action = "SPLIT_DISCUSSION"
                reason = "danger_high_fragility"
            elif state.redundancy_pressure >= 0.45:
                action = "DROP_ECHO_AGENT"
                reason = "danger_high_redundancy"
            else:
                action = "SWAP_COORDINATOR"
                reason = "danger_default"
        else:
            if state.evidence_closure < 0.35:
                action = "WAIT_FOR_EVIDENCE"
                reason = "warning_low_evidence"
            elif state.consensus_fragility > 0.40:
                action = "FREEZE_SUMMARY"
                reason = "warning_fragile_consensus"
            else:
                action = "ADD_SPECIALIST"
                reason = "warning_escalate"

        self.last_trigger_event_idx = event_idx
        return InterventionDecision(action, True, reason, self.penalties[action])
