from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from AgentDropout.core.events import EventRecord


class Instrumentation:
    def __init__(self, run_id: str, output_path: Optional[str] = None) -> None:
        self.run_id = run_id
        self.output_path = output_path
        self._events: List[EventRecord] = []

    def emit(
        self,
        event_type: str,
        phase: str,
        round_idx: Optional[int] = None,
        agent_id: Optional[str] = None,
        peer_id: Optional[str] = None,
        message_id: Optional[str] = None,
        read_level: Optional[int] = None,
        latency_ms: Optional[float] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        event = EventRecord(
            event_type=event_type,
            run_id=self.run_id,
            phase=phase,
            round_idx=round_idx,
            agent_id=agent_id,
            peer_id=peer_id,
            message_id=message_id,
            read_level=read_level,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            metadata=metadata or {},
        )
        self._events.append(event)

    @property
    def events(self) -> List[EventRecord]:
        return self._events

    def to_jsonl(self, output_path: Optional[str] = None) -> Optional[Path]:
        destination = output_path or self.output_path
        if not destination:
            return None
        output_file = Path(destination)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as fp:
            for event in self._events:
                fp.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        return output_file

    def summarize(self) -> Dict[str, Any]:
        by_event: Dict[str, int] = {}
        by_phase: Dict[str, int] = {}
        for event in self._events:
            by_event[event.event_type] = by_event.get(event.event_type, 0) + 1
            by_phase[event.phase] = by_phase.get(event.phase, 0) + 1
        return {"total_events": len(self._events), "by_event": by_event, "by_phase": by_phase}
