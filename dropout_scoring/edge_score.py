#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch


@dataclass
class EdgeRiskWeights:
    repeatflow: float = 0.1
    echo: float = 0.1
    capacityflow: float = 0.05


def compute_state_aware_edge_scores(
    base_scores: Dict[str, float],
    repeatflow_risk: Dict[str, float],
    echo_risk: Dict[str, float],
    capacityflow_risk: Dict[str, float],
    weights: EdgeRiskWeights,
) -> Dict[str, float]:
    scores = {}
    for edge_id, base_score in base_scores.items():
        penalty = (
            weights.repeatflow * repeatflow_risk.get(edge_id, 0.0)
            + weights.echo * echo_risk.get(edge_id, 0.0)
            + weights.capacityflow * capacityflow_risk.get(edge_id, 0.0)
        )
        scores[edge_id] = float(base_score - penalty)
    return scores


def edge_base_scores_from_logits(logits: torch.Tensor, masks: torch.Tensor) -> Dict[int, float]:
    if len(logits.shape) != 1 or len(masks.shape) != 1:
        raise ValueError("logits and masks must be flat tensors")
    if logits.shape[0] != masks.shape[0]:
        raise ValueError("logits and masks must have same length")
    scores = {}
    for i in range(logits.shape[0]):
        scores[i] = float(logits[i].item()) if float(masks[i].item()) > 0 else float("-inf")
    return scores
