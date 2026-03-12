#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional

from telemetry.collector import RoundTelemetry


PHASES = [
    "exploration",
    "productive",
    "repetition_stagnation",
    "premature_consensus",
    "recovery",
]


def _softmax(scores: Dict[str, float]) -> Dict[str, float]:
    exps = {k: math.exp(v) for k, v in scores.items()}
    total = sum(exps.values())
    if total == 0:
        return {k: 1.0 / len(scores) for k in scores}
    return {k: v / total for k, v in exps.items()}


@dataclass
class ObserverOutput:
    phase_probs: Dict[str, float]
    viability_score: float
    margin_to_boundary: float
    risk_repeat: float
    risk_consensus: float
    risk_capacity: float


class StateObserver:
    def __init__(self, output_path: Optional[str] = None):
        self.output_path = Path(output_path) if output_path else None
        self.latest_output = ObserverOutput(
            phase_probs={phase: 1.0 / len(PHASES) for phase in PHASES},
            viability_score=0.5,
            margin_to_boundary=0.0,
            risk_repeat=0.0,
            risk_consensus=0.0,
            risk_capacity=0.0,
        )

    def update(self, telemetry: RoundTelemetry) -> ObserverOutput:
        risk_repeat = telemetry.repetition_ratio
        risk_consensus = telemetry.answer_consensus if telemetry.round_id <= 1 else telemetry.answer_consensus * 0.6
        risk_capacity = min(1.0, telemetry.semantic_novelty_drop + max(0.0, telemetry.token_growth) / 512.0)

        score_exploration = max(0.0, 1.0 - telemetry.answer_consensus) * (1.0 - risk_repeat)
        score_productive = max(0.0, telemetry.progress_delta + telemetry.new_information) * (1.0 - risk_capacity)
        score_repetition = risk_repeat * (1.0 + telemetry.semantic_novelty_drop)
        score_premature = risk_consensus * (1.0 if telemetry.round_id <= 1 else 0.4)
        score_recovery = max(0.0, telemetry.progress_delta) * (1.0 - risk_repeat)

        phase_probs = _softmax({
            "exploration": score_exploration,
            "productive": score_productive,
            "repetition_stagnation": score_repetition,
            "premature_consensus": score_premature,
            "recovery": score_recovery,
        })

        viability = max(
            0.0,
            min(
                1.0,
                1.0
                - 0.45 * risk_repeat
                - 0.35 * risk_consensus
                - 0.20 * risk_capacity
                + 0.15 * max(telemetry.progress_delta, 0.0),
            ),
        )
        margin = viability - 0.5

        self.latest_output = ObserverOutput(
            phase_probs=phase_probs,
            viability_score=viability,
            margin_to_boundary=margin,
            risk_repeat=risk_repeat,
            risk_consensus=risk_consensus,
            risk_capacity=risk_capacity,
        )
        self._flush()
        return self.latest_output

    def get_latest_output(self) -> ObserverOutput:
        return self.latest_output

    def _flush(self):
        if self.output_path is None:
            return
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(self.latest_output), ensure_ascii=False) + "\n")
