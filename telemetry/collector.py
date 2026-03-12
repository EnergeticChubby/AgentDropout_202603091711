#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import math
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


ANSWER_REGEX = re.compile(r"(?:[Tt]he answer is\s*)([-+]?\d*\.?\d+|[A-Z])")


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9]+", text.lower())


def _extract_answer(text: str) -> str:
    if not isinstance(text, str):
        return ""
    match = ANSWER_REGEX.search(text)
    if match:
        return match.group(1)
    numbers = re.findall(r"[-+]?\d*\.?\d+", text)
    if numbers:
        return numbers[-1]
    letters = re.findall(r"[A-Z]", text)
    return letters[-1] if letters else ""


def _safe_div(num: float, den: float) -> float:
    return 0.0 if den == 0 else num / den


def _cosine_like(tokens_a: Sequence[str], tokens_b: Sequence[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    counter_a = {}
    counter_b = {}
    for tok in tokens_a:
        counter_a[tok] = counter_a.get(tok, 0) + 1
    for tok in tokens_b:
        counter_b[tok] = counter_b.get(tok, 0) + 1
    dot = 0.0
    for key, value in counter_a.items():
        dot += value * counter_b.get(key, 0)
    norm_a = math.sqrt(sum(v * v for v in counter_a.values()))
    norm_b = math.sqrt(sum(v * v for v in counter_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class RoundTelemetry:
    case_id: str
    round_id: int
    active_nodes: List[str]
    active_edges: List[Tuple[str, str, str]]
    output_lengths: Dict[str, int]
    edge_message_lengths: Dict[str, int]
    answer_consensus: float
    answer_conflict: float
    new_information: float
    repetition_ratio: float
    semantic_novelty_drop: float
    token_growth: float
    progress_delta: float
    created_at: str


@dataclass
class ObserverFeatures:
    node_repeat_risk: Dict[str, float]
    node_consensus_risk: Dict[str, float]
    node_capacity_risk: Dict[str, float]
    edge_repeatflow_risk: Dict[str, float]
    edge_echo_risk: Dict[str, float]
    edge_capacityflow_risk: Dict[str, float]


class TelemetryCollector:
    def __init__(self, output_path: Optional[str] = None):
        self.output_path = Path(output_path) if output_path else None
        self.current_case_id: Optional[str] = None
        self.rounds: List[RoundTelemetry] = []
        self.latest_features = ObserverFeatures({}, {}, {}, {}, {}, {})

    def start_case(self, case_id: str):
        if self.current_case_id is not None and self.current_case_id != case_id:
            self.flush()
        self.current_case_id = case_id
        self.rounds = []
        self.latest_features = ObserverFeatures({}, {}, {}, {}, {}, {})

    def record_round(
        self,
        case_id: str,
        round_id: int,
        node_outputs: Dict[str, str],
        active_edges: List[Tuple[str, str, str]],
    ) -> RoundTelemetry:
        if self.current_case_id is None:
            self.start_case(case_id)
        elif self.current_case_id != case_id:
            self.start_case(case_id)

        output_lengths = {node_id: len(_tokenize(text)) for node_id, text in node_outputs.items()}
        edge_message_lengths = {}
        for src, dst, edge_type in active_edges:
            src_tokens = output_lengths.get(src, 0)
            edge_message_lengths[f"{src}->{dst}:{edge_type}"] = src_tokens

        answers = [_extract_answer(text) for text in node_outputs.values()]
        answer_hist = {}
        for answer in answers:
            if answer:
                answer_hist[answer] = answer_hist.get(answer, 0) + 1
        majority = max(answer_hist.values()) if answer_hist else 0
        answer_consensus = _safe_div(majority, max(len(node_outputs), 1))
        answer_conflict = 1.0 - answer_consensus

        token_sets = {node_id: _tokenize(text) for node_id, text in node_outputs.items()}
        unique_tokens = set(tok for toks in token_sets.values() for tok in toks)
        avg_length = _safe_div(sum(output_lengths.values()), max(len(output_lengths), 1))
        new_information = _safe_div(len(unique_tokens), max(avg_length, 1.0))

        pair_sims = []
        node_ids = list(token_sets.keys())
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                pair_sims.append(_cosine_like(token_sets[node_ids[i]], token_sets[node_ids[j]]))
        repetition_ratio = _safe_div(sum(1.0 for sim in pair_sims if sim >= 0.85), max(len(pair_sims), 1))
        semantic_novelty_drop = max(0.0, 1.0 - new_information)

        prev_tokens = 0.0 if len(self.rounds) == 0 else sum(self.rounds[-1].output_lengths.values())
        curr_tokens = sum(output_lengths.values())
        token_growth = curr_tokens - prev_tokens
        prev_consensus = 0.0 if len(self.rounds) == 0 else self.rounds[-1].answer_consensus
        progress_delta = answer_consensus - prev_consensus

        telemetry = RoundTelemetry(
            case_id=case_id,
            round_id=round_id,
            active_nodes=list(node_outputs.keys()),
            active_edges=active_edges,
            output_lengths=output_lengths,
            edge_message_lengths=edge_message_lengths,
            answer_consensus=answer_consensus,
            answer_conflict=answer_conflict,
            new_information=new_information,
            repetition_ratio=repetition_ratio,
            semantic_novelty_drop=semantic_novelty_drop,
            token_growth=token_growth,
            progress_delta=progress_delta,
            created_at=time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()),
        )
        self.rounds.append(telemetry)
        self.latest_features = self._compute_risks(node_outputs, active_edges, telemetry)
        return telemetry

    def _compute_risks(
        self,
        node_outputs: Dict[str, str],
        active_edges: List[Tuple[str, str, str]],
        telemetry: RoundTelemetry,
    ) -> ObserverFeatures:
        node_repeat = {}
        node_consensus = {}
        node_capacity = {}

        answers = {node_id: _extract_answer(text) for node_id, text in node_outputs.items()}
        output_tokens = {node_id: _tokenize(text) for node_id, text in node_outputs.items()}
        avg_len = _safe_div(sum(telemetry.output_lengths.values()), max(len(telemetry.output_lengths), 1))

        for node_id, tokens in output_tokens.items():
            sims = []
            for peer_id, peer_tokens in output_tokens.items():
                if peer_id == node_id:
                    continue
                sims.append(_cosine_like(tokens, peer_tokens))
            repeat_risk = _safe_div(sum(sims), max(len(sims), 1))
            node_repeat[node_id] = repeat_risk
            node_consensus[node_id] = telemetry.answer_consensus if answers.get(node_id) else 0.0
            cap = _safe_div(max(telemetry.output_lengths.get(node_id, 0) - avg_len, 0.0), max(avg_len, 1.0))
            cap *= (1.0 + telemetry.semantic_novelty_drop)
            node_capacity[node_id] = min(cap, 2.0)

        edge_repeat = {}
        edge_echo = {}
        edge_capacity = {}
        for src, dst, edge_type in active_edges:
            key = f"{src}->{dst}:{edge_type}"
            src_tokens = output_tokens.get(src, [])
            dst_tokens = output_tokens.get(dst, [])
            sim = _cosine_like(src_tokens, dst_tokens)
            edge_repeat[key] = sim
            same_answer = 1.0 if answers.get(src) and answers.get(src) == answers.get(dst) else 0.0
            edge_echo[key] = same_answer
            edge_capacity[key] = _safe_div(
                telemetry.output_lengths.get(src, 0),
                max(sum(telemetry.output_lengths.values()), 1),
            )

        return ObserverFeatures(
            node_repeat_risk=node_repeat,
            node_consensus_risk=node_consensus,
            node_capacity_risk=node_capacity,
            edge_repeatflow_risk=edge_repeat,
            edge_echo_risk=edge_echo,
            edge_capacityflow_risk=edge_capacity,
        )

    def get_latest_features(self) -> ObserverFeatures:
        return self.latest_features

    def flush(self):
        if self.output_path is None or not self.rounds:
            return
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "case_id": self.current_case_id,
            "rounds": [asdict(round_item) for round_item in self.rounds],
            "latest_features": asdict(self.latest_features),
        }
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.rounds = []
        self.current_case_id = None
