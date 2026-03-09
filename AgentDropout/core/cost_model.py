from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostEstimate:
    approx_tokens: int
    latency_penalty: float
    attention_load: float


class HeuristicCostModel:
    def estimate(self, text: str, level: int) -> CostEstimate:
        approx_tokens = max(1, len(text) // 4)
        latency_penalty = 0.001 * approx_tokens
        attention_load = level * approx_tokens / 1000.0
        return CostEstimate(
            approx_tokens=int(approx_tokens),
            latency_penalty=float(latency_penalty),
            attention_load=float(attention_load),
        )
