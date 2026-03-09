from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def load_events(path: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def summarize_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_event: Dict[str, int] = {}
    by_phase: Dict[str, int] = {}
    read_depth_count: Dict[int, int] = {}
    for event in events:
        event_type = event.get("event_type", "unknown")
        phase = event.get("phase", "unknown")
        by_event[event_type] = by_event.get(event_type, 0) + 1
        by_phase[phase] = by_phase.get(phase, 0) + 1
        if event_type == "message_read":
            depth = int(event.get("read_level", 4))
            read_depth_count[depth] = read_depth_count.get(depth, 0) + 1

    avg_read_depth = 0.0
    total_reads = sum(read_depth_count.values())
    if total_reads:
        avg_read_depth = sum(depth * count for depth, count in read_depth_count.items()) / total_reads

    return {
        "total_events": len(events),
        "by_event": by_event,
        "by_phase": by_phase,
        "read_depth_histogram": read_depth_count,
        "avg_read_depth": avg_read_depth,
    }


def replay_summary(path: str) -> Dict[str, Any]:
    events = load_events(path)
    return summarize_events(events)
