from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class DelegationContract:
    contract_id: str
    task_clause: str
    decision_rights: str
    deliverable_schema: str
    evidence_obligation: List[str] = field(default_factory=list)
    uncertainty_report: List[str] = field(default_factory=list)
    acceptance_test: List[str] = field(default_factory=list)
    rollback_clause: str = "retry_upstream"
    escalation_clause: str = "none"
    liability_tag: str = "shared"
    budget_clause: Dict[str, Any] = field(default_factory=dict)
    renegotiation_rule: str = "on_repeated_failure"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContractVerificationResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
