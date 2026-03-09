import shortuuid
from typing import Dict, Any

from AgentDropout.contracts.schema import DelegationContract
from AgentDropout.contracts.templates import CONTRACT_TEMPLATES, DEFAULT_TEMPLATE


class ContractSynthesizer:
    def infer_task_type(self, domain: str) -> str:
        if domain in {"gsm8k", "aqua", "svamp", "multiarith"}:
            return "math"
        if domain in {"humaneval"}:
            return "code"
        return "qa"

    def synthesize(
        self,
        domain: str,
        task: str,
        sender_role: str,
        receiver_role: str,
        context: Dict[str, Any] | None = None,
    ) -> DelegationContract:
        task_type = self.infer_task_type(domain)
        template = {**DEFAULT_TEMPLATE, **CONTRACT_TEMPLATES.get(task_type, {})}
        return DelegationContract(
            contract_id=shortuuid.ShortUUID().random(length=10),
            task_clause=task[:800],
            decision_rights=template["decision_rights"],
            deliverable_schema=template["deliverable_schema"],
            evidence_obligation=list(template["evidence_obligation"]),
            uncertainty_report=list(template["uncertainty_report"]),
            acceptance_test=list(template["acceptance_test"]),
            budget_clause=dict(template["budget_clause"]),
            metadata={
                "domain": domain,
                "task_type": task_type,
                "sender_role": sender_role,
                "receiver_role": receiver_role,
                **(context or {}),
            },
        )
