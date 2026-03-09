from __future__ import annotations

import shortuuid
from typing import Any, Dict

from AgentDropout.protocols.admissibility import AdmissibilityDecision, AdmissibilityEngine
from AgentDropout.protocols.types import AdmissibilityRecord, DisputeRecord, MessageAct


class ABPPProtocol:
    def __init__(self, engine: AdmissibilityEngine | None = None):
        self.engine = engine or AdmissibilityEngine()

    def process_disclosure(
        self,
        disclosure,
        state: Dict[str, Any],
        risk_level: str = "medium",
    ) -> bool:
        decision: AdmissibilityDecision = self.engine.evaluate(disclosure, risk_level=risk_level)
        record = AdmissibilityRecord(
            record_id=shortuuid.ShortUUID().random(length=10),
            message_act=self._message_act_from_disclosure(disclosure.disclosure_type.value),
            source_agent=disclosure.agent_id,
            target_id=disclosure.disclosure_id,
            admissible=decision.admissible,
            reasons=decision.reasons,
            standard=decision.standard,
        )
        state.setdefault("admissibility_records", []).append(record.to_dict())
        if not decision.admissible:
            dispute = DisputeRecord(
                dispute_id=shortuuid.ShortUUID().random(length=10),
                target_claim_id=disclosure.disclosure_id,
                opened_by="abpp_gatekeeper",
                objection="; ".join(decision.reasons) if decision.reasons else "inadmissible",
            )
            state.setdefault("disputes", []).append(dispute.to_dict())
        return decision.admissible

    @staticmethod
    def _message_act_from_disclosure(disclosure_type: str) -> MessageAct:
        mapping = {
            "claim": MessageAct.CLAIM,
            "evidence": MessageAct.EVIDENCE,
            "counterevidence": MessageAct.OBJECTION,
            "uncertainty_report": MessageAct.QUESTION,
            "question": MessageAct.QUESTION,
        }
        return mapping.get(disclosure_type, MessageAct.CLAIM)

