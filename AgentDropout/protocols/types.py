from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DisclosureType(str, Enum):
    CLAIM = "claim"
    EVIDENCE = "evidence"
    COUNTEREVIDENCE = "counterevidence"
    UNCERTAINTY_REPORT = "uncertainty_report"
    QUESTION = "question"


class ClaimStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    CONTESTED = "contested"
    SUPPORTED = "supported"
    VERIFIED = "verified"
    BLOCKED = "blocked"
    DEPRECATED = "deprecated"


class MessageAct(str, Enum):
    CLAIM = "claim"
    EVIDENCE = "evidence"
    INFERENCE = "inference"
    QUESTION = "question"
    OBJECTION = "objection"
    REBUTTAL = "rebuttal"
    RULING = "ruling"
    APPEAL = "appeal"
    WITHDRAWAL = "withdrawal"


@dataclass
class DisclosureObject:
    disclosure_id: str
    agent_id: str
    disclosure_type: DisclosureType
    content: str
    round_idx: int
    score: float = 0.0
    token_cost: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClaimObject:
    claim_id: str
    content: str
    speaker_agent: str
    timestamp: str
    scope: str = "global"
    confidence: float = 0.0
    assets: List[Dict[str, Any]] = field(default_factory=list)
    liabilities: List[Dict[str, Any]] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)
    status: ClaimStatus = ClaimStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdmissibilityRecord:
    record_id: str
    message_act: MessageAct
    source_agent: str
    target_id: Optional[str]
    admissible: bool
    reasons: List[str] = field(default_factory=list)
    standard: str = "preponderance"
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DisputeRecord:
    dispute_id: str
    target_claim_id: str
    opened_by: str
    objection: str
    rebuttals: List[Dict[str, Any]] = field(default_factory=list)
    ruling: Optional[Dict[str, Any]] = None
    appeals: List[Dict[str, Any]] = field(default_factory=list)
    open: bool = True
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

