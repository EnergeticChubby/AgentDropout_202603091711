from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryObject:
    content: str
    type: str
    source_agent: str
    provenance: Dict[str, Any]
    phase: str
    evidence_strength: float = 0.5
    verification_status: str = "proposed"
    ttl: int = 3
    challenge_status: str = "none"
    read_count: int = 0
    error_liability: float = 0.0
    signers: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
