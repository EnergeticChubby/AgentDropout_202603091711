import argparse
import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from datasets import load_dataset

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import AgentDropout.llm  # noqa: F401
import AgentDropout.prompt  # noqa: F401
from AgentDropout.agents.code_writing import CodeWriting  # noqa: F401
from AgentDropout.agents.final_decision import (  # noqa: F401
    FinalDirect,
    FinalMajorVote,
    FinalRefer,
    FinalWriteCode,
)
from AgentDropout.agents.math_solver import MathSolver  # noqa: F401
from AgentDropout.core.attention_policy import AttentionDecision
from AgentDropout.graph.graph import Graph
from AgentDropout.tools.coding.python_executor import PyExecutor
from AgentDropout.utils.globals import CompletionTokens, Cost, PromptTokens


@dataclass
class Sample:
    task: str
    answer: str
    meta: Dict[str, Any]


class FullAttentionPolicy:
    def decide_level(
        self,
        phase: str,
        receiver_id: str,
        predecessor_id: str,
        predecessor_output: Any,
        context: Dict[str, Any] | None = None,
    ) -> AttentionDecision:
        return AttentionDecision(level=4, reason="baseline_full_read")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full benchmark on one dataset/profile.")
    parser.add_argument("--dataset", required=True, choices=["gsm8k", "multiarith", "svamp", "humaneval"])
    parser.add_argument("--profile", required=True, choices=["agentdropout", "phasee"])
    parser.add_argument("--run_tag", required=True)
    parser.add_argument("--llm_name", default="qwen3-8b")
    parser.add_argument("--max_samples", type=int, default=0)
    parser.add_argument("--math_agent_count", type=int, default=4)
    parser.add_argument("--code_agent_count", type=int, default=5)
    parser.add_argument("--log_every", type=int, default=20)
    return parser.parse_args()


def _extract_last_number(text: str) -> str:
    if not isinstance(text, str):
        return "0"
    if "The answer is " in text:
        candidate = text.split("The answer is ")[-1].strip()
    elif "the answer is " in text:
        candidate = text.split("the answer is ")[-1].strip()
    else:
        matches = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
        return matches[-1] if matches else "0"
    matches = re.findall(r"-?\d+(?:\.\d+)?", candidate.replace(",", ""))
    return matches[-1] if matches else "0"


def _numeric_equal(pred: str, gold: str) -> bool:
    try:
        return abs(float(pred) - float(gold)) < 1e-9
    except Exception:
        return str(pred).strip() == str(gold).strip()


def _extract_code(candidate: str) -> str:
    if not isinstance(candidate, str):
        return ""
    code_blocks = re.findall(r"```python\s*(.*?)```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if code_blocks:
        return code_blocks[-1].strip()
    any_blocks = re.findall(r"```\s*(.*?)```", candidate, flags=re.DOTALL)
    if any_blocks:
        return any_blocks[-1].strip()
    return candidate.strip()


def _sanitize_response(raw: Any) -> str:
    if isinstance(raw, list):
        if len(raw) == 0:
            return ""
        return _sanitize_response(raw[-1])
    if isinstance(raw, dict):
        if "full_rationale" in raw and raw.get("full_rationale"):
            return str(raw["full_rationale"])
        if "raw_text" in raw and raw.get("raw_text"):
            return str(raw["raw_text"])
        if "headline" in raw and raw.get("headline"):
            return str(raw["headline"])
        return json.dumps(raw, ensure_ascii=False)
    return str(raw)


def load_samples(dataset_name: str, max_samples: int) -> List[Sample]:
    if dataset_name == "gsm8k":
        ds = load_dataset("openai/gsm8k", "main", split="test")
        rows = [
            Sample(
                task=row["question"],
                answer=str(row["answer"]).split("\n####")[-1].replace(",", "").strip(),
                meta={"question": row["question"]},
            )
            for row in ds
        ]
    elif dataset_name == "multiarith":
        ds = load_dataset("ChilleD/MultiArith", split="test")
        rows = [
            Sample(
                task=row["question"],
                answer=str(row["final_ans"]).replace(",", "").strip(),
                meta={"question": row["question"]},
            )
            for row in ds
        ]
    elif dataset_name == "svamp":
        ds = load_dataset("ChilleD/SVAMP", split="test")
        rows = [
            Sample(
                task=f"{row['Body']} {row['Question']}",
                answer=str(row["Answer"]).replace(",", "").strip(),
                meta={
                    "id": row.get("ID"),
                    "body": row["Body"],
                    "question": row["Question"],
                    "equation": row.get("Equation"),
                },
            )
            for row in ds
        ]
    else:
        ds = load_dataset("openai_humaneval", split="test")
        rows = [
            Sample(
                task=row["prompt"],
                answer=row["entry_point"],
                meta={"task_id": row["task_id"], "test": row["test"], "entry_point": row["entry_point"]},
            )
            for row in ds
        ]
    if max_samples > 0:
        return rows[:max_samples]
    return rows


def build_graph(args: argparse.Namespace) -> Tuple[Graph, int]:
    if args.dataset == "humaneval":
        domain = "humaneval"
        agent_name = "CodeWriting"
        agent_count = args.code_agent_count
        node_kwargs = [{"role": "Programming Expert"} for _ in range(agent_count)]
        decision_method = "FinalDirect" if agent_count == 1 else "FinalWriteCode"
        num_rounds = 1 if agent_count == 1 else 2
    else:
        domain = "gsm8k"
        agent_name = "MathSolver"
        agent_count = args.math_agent_count
        node_kwargs = [{"role": "Math Solver"} for _ in range(agent_count)]
        decision_method = "FinalDirect" if agent_count == 1 else "FinalRefer"
        num_rounds = 1

    graph_kwargs: Dict[str, Any] = {
        "domain": domain,
        "llm_name": args.llm_name,
        "agent_names": [agent_name] * agent_count,
        "decision_method": decision_method,
        "optimized_spatial": False,
        "optimized_temporal": False,
        "rounds": num_rounds,
        "diff": False,
        "dec": False,
        "initial_spatial_probability": 0.5,
        "fixed_spatial_masks": [[1 if i != j else 0 for i in range(agent_count)] for j in range(agent_count)],
        "initial_temporal_probability": 0.5,
        "fixed_temporal_masks": [[1 for _ in range(agent_count)] for _ in range(agent_count)],
        "node_kwargs": node_kwargs,
    }

    if args.profile == "agentdropout":
        graph_kwargs["attention_policy"] = FullAttentionPolicy()
        graph_kwargs["phase_sequence"] = ["aggregate"]
        graph_kwargs["enable_memory_governance"] = False

    graph = Graph(**graph_kwargs)
    return graph, num_rounds


async def run_eval(args: argparse.Namespace) -> Dict[str, Any]:
    samples = load_samples(args.dataset, args.max_samples)
    run_dir = Path("artifacts") / "runs" / f"fullsuite-{args.profile}-{args.dataset}-{args.run_tag}"
    run_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = run_dir / "predictions.jsonl"
    config_path = run_dir / "config.json"
    summary_path = run_dir / "summary.json"

    with config_path.open("w", encoding="utf-8") as fp:
        json.dump(
            {
                "dataset": args.dataset,
                "profile": args.profile,
                "run_tag": args.run_tag,
                "llm_name": args.llm_name,
                "max_samples": args.max_samples,
                "math_agent_count": args.math_agent_count,
                "code_agent_count": args.code_agent_count,
                "num_samples": len(samples),
            },
            fp,
            ensure_ascii=False,
            indent=2,
        )

    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    graph, num_rounds = build_graph(args)
    executor = PyExecutor()
    solved = 0
    started_at = time.time()

    with prediction_path.open("w", encoding="utf-8") as fp:
        for idx, sample in enumerate(samples):
            raw_answers, _ = await graph.arun({"task": sample.task}, num_rounds=num_rounds)
            raw_answer = _sanitize_response(raw_answers)

            if args.dataset == "humaneval":
                code = _extract_code(raw_answer)
                is_solved = executor.evaluate(
                    sample.meta["entry_point"],
                    code,
                    sample.meta["test"],
                    timeout=10,
                )
                pred_answer = code
                gold_answer = sample.meta["entry_point"]
            else:
                pred_answer = _extract_last_number(raw_answer)
                gold_answer = _extract_last_number(str(sample.answer))
                is_solved = _numeric_equal(pred_answer, gold_answer)

            solved += int(is_solved)
            row = {
                "index": idx,
                "dataset": args.dataset,
                "profile": args.profile,
                "question": sample.task,
                "gold_answer": gold_answer,
                "pred_answer": pred_answer,
                "raw_answer": raw_answer,
                "is_solved": bool(is_solved),
                "running_accuracy": solved / (idx + 1),
                "meta": sample.meta,
            }
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

            if args.log_every > 0 and (idx + 1) % args.log_every == 0:
                print(
                    json.dumps(
                        {
                            "dataset": args.dataset,
                            "profile": args.profile,
                            "completed": idx + 1,
                            "total": len(samples),
                            "running_accuracy": solved / (idx + 1),
                        },
                        ensure_ascii=False,
                    )
                )

    elapsed = time.time() - started_at
    summary = {
        "dataset": args.dataset,
        "profile": args.profile,
        "run_tag": args.run_tag,
        "llm_name": args.llm_name,
        "num_samples": len(samples),
        "num_correct": solved,
        "accuracy": (solved / len(samples)) if samples else 0.0,
        "elapsed_seconds": elapsed,
        "cost": Cost.instance().value,
        "prompt_tokens": PromptTokens.instance().value,
        "completion_tokens": CompletionTokens.instance().value,
        "prediction_path": str(prediction_path),
        "config_path": str(config_path),
    }

    with summary_path.open("w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> None:
    args = parse_args()
    asyncio.run(run_eval(args))


if __name__ == "__main__":
    main()
