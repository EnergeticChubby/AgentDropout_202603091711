import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RoundTrace:
    round_id: int
    active_agents: List[str]
    messages: Dict[str, str]
    summary: str
    tool_calls: List[Dict]
    tokens: Dict[str, float]
    events: List[Dict] = field(default_factory=list)


@dataclass
class ProblemTrace:
    problem_id: str
    split: str
    graph_id: str
    rounds: List[RoundTrace] = field(default_factory=list)
    final_answer: str = ""
    gold_answer: str = ""
    is_correct: bool = False
    extra: Dict = field(default_factory=dict)


class TelemetryRecorder:
    def __init__(self, output_path: Optional[str] = None):
        self.output_path = Path(output_path) if output_path else None
        self.records: List[ProblemTrace] = []

    def start_problem(
        self,
        problem_id: str,
        split: str,
        graph_id: str,
        extra: Optional[Dict] = None,
    ) -> ProblemTrace:
        trace = ProblemTrace(problem_id=problem_id, split=split, graph_id=graph_id, extra=extra or {})
        self.records.append(trace)
        return trace

    def add_round(
        self,
        trace: ProblemTrace,
        round_id: int,
        active_agents: List[str],
        messages: Dict[str, str],
        summary: str,
        tool_calls: Optional[List[Dict]] = None,
        tokens: Optional[Dict[str, float]] = None,
        events: Optional[List[Dict]] = None,
    ) -> None:
        trace.rounds.append(
            RoundTrace(
                round_id=round_id,
                active_agents=active_agents,
                messages=messages,
                summary=summary,
                tool_calls=tool_calls or [],
                tokens=tokens or {},
                events=events or [],
            )
        )

    def finalize_problem(
        self,
        trace: ProblemTrace,
        final_answer: str,
        gold_answer: str,
        is_correct: bool,
    ) -> None:
        trace.final_answer = final_answer
        trace.gold_answer = gold_answer
        trace.is_correct = is_correct

    def to_serializable(self) -> List[Dict]:
        payload = []
        for record in self.records:
            payload.append(
                {
                    "problem_id": record.problem_id,
                    "split": record.split,
                    "graph_id": record.graph_id,
                    "rounds": [
                        {
                            "round_id": r.round_id,
                            "active_agents": r.active_agents,
                            "messages": r.messages,
                            "summary": r.summary,
                            "tool_calls": r.tool_calls,
                            "tokens": r.tokens,
                            "events": r.events,
                        }
                        for r in record.rounds
                    ],
                    "final_answer": record.final_answer,
                    "gold_answer": record.gold_answer,
                    "is_correct": record.is_correct,
                    "extra": record.extra,
                }
            )
        return payload

    def dump(self, output_path: Optional[str] = None) -> Path:
        path = Path(output_path) if output_path else self.output_path
        if path is None:
            raise ValueError("No output path provided for telemetry dump.")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_serializable(), f, ensure_ascii=False, indent=2)
        return path
