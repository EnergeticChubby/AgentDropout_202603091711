from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EventRecord:
    event_type: str
    run_id: str
    phase: str
    timestamp: str = field(default_factory=utc_now_iso)
    round_idx: Optional[int] = None
    agent_id: Optional[str] = None
    peer_id: Optional[str] = None
    message_id: Optional[str] = None
    read_level: Optional[int] = None
    latency_ms: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "event_type": self.event_type,
            "run_id": self.run_id,
            "phase": self.phase,
            "timestamp": self.timestamp,
            "round_idx": self.round_idx,
            "agent_id": self.agent_id,
            "peer_id": self.peer_id,
            "message_id": self.message_id,
            "read_level": self.read_level,
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "metadata": self.metadata,
        }
        return {key: value for key, value in payload.items() if value is not None}
