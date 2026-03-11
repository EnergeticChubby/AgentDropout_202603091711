#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from AgentDropout.graph.graph import Graph
import AgentDropout.llm.gpt_chat as gpt_chat
from datasets.mmlu_dataset import MMLUDataset
from experiments.evaluate_mmlu import evaluate
from experiments.run_mmlu import get_kwargs


def _ensure_local_mmlu_sample() -> None:
    dev_dir = Path("datasets/MMLU/data/dev")
    val_dir = Path("datasets/MMLU/data/val")
    dev_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    dev_file = dev_dir / "toy_math_dev.csv"
    val_file = val_dir / "toy_math_val.csv"
    if not dev_file.exists():
        dev_file.write_text("What is 2 + 2?,1,4,6,8,B\n", encoding="utf-8")
    if not val_file.exists():
        val_file.write_text("What is 3 + 2?,4,5,6,7,B\n", encoding="utf-8")


async def _fake_achat(model: str, msg):
    return "B\nBecause 3 + 2 = 5."


async def _main() -> None:
    _ensure_local_mmlu_sample()
    gpt_chat.achat = _fake_achat

    kwargs = get_kwargs("DirectAnswer", 1)
    graph = Graph(
        domain="mmlu",
        llm_name="glm-4.5-flash",
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
    args = SimpleNamespace(domain="mmlu", llm_name="glm-4.5-flash")
    score = await evaluate(
        graph=graph,
        dataset=dataset_val,
        num_rounds=1,
        limit_questions=1,
        eval_batch_size=1,
        args=args,
        max_retries_per_question=2,
        retry_backoff_sec=0.01,
        rerun_failed_rounds=1,
    )
    assert abs(score - 1.0) < 1e-9, f"Expected score 1.0, got {score}"
    print("phase0 agentdropout local test passed")


if __name__ == "__main__":
    asyncio.run(_main())
