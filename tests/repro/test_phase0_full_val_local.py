#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from AgentDropout.graph.graph import Graph
import AgentDropout.llm.gpt_chat as gpt_chat
from datasets.mmlu_dataset import MMLUDataset
from experiments.evaluate_mmlu import evaluate
from experiments.run_mmlu import get_kwargs


async def _fake_achat(model: str, msg):
    return "B\nDeterministic baseline answer."


async def _main() -> None:
    gpt_chat.achat = _fake_achat

    kwargs = get_kwargs("DirectAnswer", 1)
    graph = Graph(
        domain="mmlu",
        llm_name="qwen3-8b",
        agent_names=["AnalyzeAgent"],
        decision_method="FinalRefer",
        optimized_spatial=False,
        optimized_temporal=False,
        rounds=1,
        diff=False,
        dec=False,
        **kwargs,
    )

    dataset_val = MMLUDataset("val")
    total = len(dataset_val)
    expected_hits = 0
    for i in range(total):
        if dataset_val.record_to_target_answer(dataset_val[i]) == "B":
            expected_hits += 1
    expected_score = expected_hits / total

    args = SimpleNamespace(domain="mmlu", llm_name="qwen3-8b")
    score = await evaluate(
        graph=graph,
        dataset=dataset_val,
        num_rounds=1,
        limit_questions=None,
        eval_batch_size=32,
        args=args,
        max_retries_per_question=2,
        retry_backoff_sec=0.01,
        rerun_failed_rounds=1,
    )
    assert abs(score - expected_score) < 1e-12, (
        f"Expected deterministic score {expected_score}, got {score}"
    )
    print(f"phase0 full-val local test passed: score={score:.6f}, total={total}")


if __name__ == "__main__":
    asyncio.run(_main())
