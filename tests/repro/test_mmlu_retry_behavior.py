#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

tqdm_stub = types.ModuleType("tqdm")
tqdm_stub.tqdm = lambda iterable, total=None: iterable
sys.modules["tqdm"] = tqdm_stub

const_stub = types.ModuleType("AgentDropout.utils.const")
const_stub.AgentPrune_ROOT = ROOT / "tests/records/runtime_tmp"
sys.modules["AgentDropout.utils.const"] = const_stub

globals_stub = types.ModuleType("AgentDropout.utils.globals")

class _Singleton:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

class Time(_Singleton):
    def __init__(self):
        self.value = ""

class Cost(_Singleton):
    def __init__(self):
        self.value = 0.0

class PromptTokens(_Singleton):
    def __init__(self):
        self.value = 0.0

class CompletionTokens(_Singleton):
    def __init__(self):
        self.value = 0.0

globals_stub.Time = Time
globals_stub.Cost = Cost
globals_stub.PromptTokens = PromptTokens
globals_stub.CompletionTokens = CompletionTokens
sys.modules["AgentDropout.utils.globals"] = globals_stub

graph_pkg_stub = types.ModuleType("AgentDropout.graph")
graph_pkg_stub.__path__ = []
sys.modules["AgentDropout.graph"] = graph_pkg_stub

graph_mod_stub = types.ModuleType("AgentDropout.graph.graph")
class Graph:
    pass
graph_mod_stub.Graph = Graph
sys.modules["AgentDropout.graph.graph"] = graph_mod_stub

from experiments.evaluate_mmlu import evaluate


class FakeLogits:
    def __init__(self) -> None:
        self.requires_grad = True

    def requires_grad_(self, flag: bool):
        self.requires_grad = flag
        return self


class FakeDataset:
    def __init__(self, records: List[Dict[str, str]], split: str = "val") -> None:
        self._records = records
        self.split = split

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self):
        return iter(self._records)

    @staticmethod
    def record_to_input(record: Dict[str, str]) -> Dict[str, str]:
        return {"task": record["question"]}

    @staticmethod
    def postprocess_answer(answer: str) -> str:
        return answer.strip()[0]

    @staticmethod
    def record_to_target_answer(record: Dict[str, str]) -> str:
        return record["correct_answer"]


class FakeGraph:
    def __init__(self, fail_before_success: Dict[str, int]) -> None:
        self.spatial_logits = FakeLogits()
        self.temporal_logits = FakeLogits()
        self._fail_before_success = fail_before_success
        self._attempts: Dict[str, int] = {}

    def __deepcopy__(self, memo):
        return self

    async def arun(self, input_dict, num_rounds, case=True):
        task = input_dict["task"]
        self._attempts[task] = self._attempts.get(task, 0) + 1
        threshold = self._fail_before_success.get(task, 0)
        if self._attempts[task] <= threshold:
            raise RuntimeError(f"transient api overload for {task}")
        return "A", 0.0, ["A"]


async def _case_retry_then_success() -> None:
    records = [
        {"question": "Q0", "correct_answer": "A"},
        {"question": "Q1", "correct_answer": "A"},
    ]
    dataset = FakeDataset(records)
    graph = FakeGraph(fail_before_success={"Q1": 2})
    args = SimpleNamespace(domain="mmlu")
    score = await evaluate(
        graph=graph,
        dataset=dataset,
        num_rounds=1,
        limit_questions=None,
        eval_batch_size=2,
        args=args,
        max_retries_per_question=3,
        retry_backoff_sec=0.01,
        rerun_failed_rounds=1,
    )
    assert abs(score - 1.0) < 1e-9, f"Expected score 1.0, got {score}"


async def _case_retry_still_fails() -> None:
    records = [{"question": "Q_fail", "correct_answer": "A"}]
    dataset = FakeDataset(records)
    graph = FakeGraph(fail_before_success={"Q_fail": 100})
    args = SimpleNamespace(domain="mmlu")
    try:
        await evaluate(
            graph=graph,
            dataset=dataset,
            num_rounds=1,
            limit_questions=None,
            eval_batch_size=1,
            args=args,
            max_retries_per_question=2,
            retry_backoff_sec=0.01,
            rerun_failed_rounds=1,
        )
    except RuntimeError as exc:
        assert "MMLU full-val evaluation incomplete" in str(exc)
        return
    raise AssertionError("Expected RuntimeError for unresolved failed question")


async def _main() -> None:
    (ROOT / "tests/records/runtime_tmp/result/mmlu").mkdir(parents=True, exist_ok=True)
    await _case_retry_then_success()
    await _case_retry_still_fails()
    print("mmlu retry behavior tests passed")


if __name__ == "__main__":
    asyncio.run(_main())
