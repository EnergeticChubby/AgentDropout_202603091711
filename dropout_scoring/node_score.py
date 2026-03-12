#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch


@dataclass
class NodeRiskWeights:
    repeat: float = 0.1
    consensus: float = 0.1
    capacity: float = 0.05


def compute_state_aware_node_scores(
    struct_scores: Dict[str, float],
    repeat_risk: Dict[str, float],
    consensus_risk: Dict[str, float],
    capacity_risk: Dict[str, float],
    weights: NodeRiskWeights,
) -> Dict[str, float]:
    scores = {}
    for node_id, struct_score in struct_scores.items():
        penalty = (
            weights.repeat * repeat_risk.get(node_id, 0.0)
            + weights.consensus * consensus_risk.get(node_id, 0.0)
            + weights.capacity * capacity_risk.get(node_id, 0.0)
        )
        scores[node_id] = float(struct_score - penalty)
    return scores


def node_struct_scores_from_matrix(spatial_matrix: torch.Tensor) -> Dict[int, float]:
    """Calculate structural node score by weighted in+out degree."""
    if len(spatial_matrix.shape) != 2 or spatial_matrix.shape[0] != spatial_matrix.shape[1]:
        raise ValueError("spatial_matrix must be square")
    n = spatial_matrix.shape[0]
    result = {}
    for i in range(n):
        score = float(torch.sum(spatial_matrix[i, :]).item() + torch.sum(spatial_matrix[:, i]).item())
        result[i] = score
    return result
