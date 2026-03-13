#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional

import torch

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
    def __init__(self, output_path: Optional[str] = None, model_path: Optional[str] = None):
        self.output_path = Path(output_path) if output_path else None
        self.model_path = Path(model_path) if model_path else None
        self._model_bundle = self._load_model_bundle(self.model_path) if self.model_path else None
        self.latest_output = ObserverOutput(
            phase_probs={phase: 1.0 / len(PHASES) for phase in PHASES},
            viability_score=0.5,
            margin_to_boundary=0.0,
            risk_repeat=0.0,
            risk_consensus=0.0,
            risk_capacity=0.0,
        )

    def update(self, telemetry: RoundTelemetry) -> ObserverOutput:
        if self._model_bundle is not None:
            self.latest_output = self._model_infer(telemetry)
            self._flush()
            return self.latest_output

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

    @staticmethod
    def _load_model_bundle(model_path: Path):
        if model_path is None or not model_path.exists():
            return None
        try:
            bundle = torch.load(model_path, map_location="cpu", weights_only=True)
        except TypeError:
            bundle = torch.load(model_path, map_location="cpu")
        state_dict = bundle.get("state_dict")
        feature_keys = bundle.get("feature_keys", [])
        phase_names = bundle.get("phase_names", PHASES)
        hidden_dim = int(bundle.get("hidden_dim", 64))
        if not state_dict or not feature_keys:
            return None

        input_dim = len(feature_keys)
        backbone = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, hidden_dim),
            torch.nn.ReLU(),
        )
        phase_head = torch.nn.Linear(hidden_dim, len(phase_names))
        risk_head = torch.nn.Linear(hidden_dim, 3)
        model = torch.nn.ModuleDict({"backbone": backbone, "phase_head": phase_head, "risk_head": risk_head})
        model.load_state_dict(state_dict)
        model.eval()
        return {
            "model": model,
            "feature_keys": feature_keys,
            "phase_names": phase_names,
        }

    def _model_infer(self, telemetry: RoundTelemetry) -> ObserverOutput:
        model = self._model_bundle["model"]
        feature_keys = self._model_bundle["feature_keys"]
        phase_names = self._model_bundle["phase_names"]
        feature_values = {
            "answer_consensus": float(telemetry.answer_consensus),
            "answer_conflict": float(telemetry.answer_conflict),
            "new_information": float(telemetry.new_information),
            "repetition_ratio": float(telemetry.repetition_ratio),
            "semantic_novelty_drop": float(telemetry.semantic_novelty_drop),
            "token_growth": float(telemetry.token_growth),
            "progress_delta": float(telemetry.progress_delta),
        }
        vec = [feature_values.get(key, 0.0) for key in feature_keys]
        x = torch.tensor([vec], dtype=torch.float32)
        with torch.no_grad():
            h = model["backbone"](x)
            phase_logits = model["phase_head"](h)
            risk_logits = model["risk_head"](h)
            phase_probs_tensor = torch.softmax(phase_logits, dim=-1).squeeze(0)
            risk_probs_tensor = torch.sigmoid(risk_logits).squeeze(0)

        phase_probs = {name: float(phase_probs_tensor[i].item()) for i, name in enumerate(phase_names)}
        risk_repeat = float(risk_probs_tensor[0].item())
        risk_consensus = float(risk_probs_tensor[1].item())
        risk_capacity = float(risk_probs_tensor[2].item())
        productive_prob = phase_probs.get("productive", 0.0) + phase_probs.get("recovery", 0.0)
        viability = max(
            0.0,
            min(
                1.0,
                0.5 * productive_prob + 0.5 * (1.0 - (0.45 * risk_repeat + 0.35 * risk_consensus + 0.20 * risk_capacity)),
            ),
        )
        return ObserverOutput(
            phase_probs=phase_probs,
            viability_score=viability,
            margin_to_boundary=viability - 0.5,
            risk_repeat=risk_repeat,
            risk_consensus=risk_consensus,
            risk_capacity=risk_capacity,
        )
