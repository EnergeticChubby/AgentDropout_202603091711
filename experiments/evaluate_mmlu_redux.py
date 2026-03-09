import argparse
import asyncio
import copy
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding="utf-8")

from AgentDropout.graph.graph import Graph
from AgentDropout.agents.analyze_agent import AnalyzeAgent  # noqa: F401
from AgentDropout.agents.final_decision import FinalRefer, FinalDirect, FinalMajorVote  # noqa: F401
from AgentDropout.llm.price import set_token_usage_hook
from AgentDropout.utils.const import AgentPrune_ROOT
from AgentDropout.utils.globals import CompletionTokens, Cost, PromptTokens
from benchmark_datasets.mmlu_redux_dataset import MMLUReduxDataset


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate AgentDropout on MMLU-Redux shard.")
    parser.add_argument("--llm_name", type=str, default="qwen3-8b")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--num_shards", type=int, default=8)
    parser.add_argument("--shard_idx", type=int, required=True)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--num_rounds", type=int, default=1)
    parser.add_argument("--mode", type=str, default="FullConnected")
    parser.add_argument("--decision_method", type=str, default="FinalRefer")
    parser.add_argument("--agent_names", nargs="+", type=str, default=["AnalyzeAgent"])
    parser.add_argument("--agent_nums", nargs="+", type=int, default=[5])
    parser.add_argument("--disable_memory_governance", action="store_true")
    parser.add_argument("--run_tag", type=str, default=None)
    return parser.parse_args()


def get_kwargs(
    mode: Union[
        Literal["DirectAnswer"],
        Literal["FullConnected"],
        Literal["Random"],
        Literal["Chain"],
        Literal["Debate"],
        Literal["Layered"],
        Literal["Star"],
    ],
    n: int,
):
    import random

    def generate_layered_graph(size, layer_num=2):
        adj_matrix = [[0 for _ in range(size)] for _ in range(size)]
        base_size = size // layer_num
        remainder = size % layer_num
        layers = []
        for idx in range(layer_num):
            width = base_size + (1 if idx < remainder else 0)
            layers.extend([idx] * width)
        for i in range(size):
            current_layer = layers[i]
            for j in range(size):
                if layers[j] == current_layer + 1:
                    adj_matrix[i][j] = 1
        return adj_matrix

    def generate_star_graph(size):
        matrix = [[0] * size for _ in range(size)]
        for i in range(1, size):
            matrix[0][i] = 1
        return matrix

    if mode == "DirectAnswer":
        fixed_spatial_masks = [[0]]
        fixed_temporal_masks = [[0]]
        node_kwargs = [{"role": "Normal"}]
    elif mode == "FullConnected":
        fixed_spatial_masks = [[1 if i != j else 0 for i in range(n)] for j in range(n)]
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
        node_kwargs = None
    elif mode == "Random":
        fixed_spatial_masks = [[random.randint(0, 1) if i != j else 0 for i in range(n)] for j in range(n)]
        fixed_temporal_masks = [[random.randint(0, 1) for _ in range(n)] for _ in range(n)]
        node_kwargs = None
    elif mode == "Chain":
        fixed_spatial_masks = [[1 if i == j + 1 else 0 for i in range(n)] for j in range(n)]
        fixed_temporal_masks = [[1 if i == 0 and j == n - 1 else 0 for i in range(n)] for j in range(n)]
        node_kwargs = None
    elif mode == "Debate":
        fixed_spatial_masks = [[0 for _ in range(n)] for _ in range(n)]
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
        node_kwargs = None
    elif mode == "Layered":
        fixed_spatial_masks = generate_layered_graph(n)
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
        node_kwargs = None
    elif mode == "Star":
        fixed_spatial_masks = generate_star_graph(n)
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
        node_kwargs = None
    else:
        raise ValueError(f"Unsupported mode {mode}")

    return {
        "initial_spatial_probability": 0.5,
        "fixed_spatial_masks": fixed_spatial_masks,
        "initial_temporal_probability": 0.5,
        "fixed_temporal_masks": fixed_temporal_masks,
        "node_kwargs": node_kwargs,
    }


async def evaluate_shard(args):
    if len(args.agent_names) != len(args.agent_nums):
        raise ValueError("agent_names and agent_nums length mismatch")
    agent_names = [name for name, count in zip(args.agent_names, args.agent_nums) for _ in range(count)]

    dataset = MMLUReduxDataset(
        split=args.split,
        num_shards=args.num_shards,
        shard_idx=args.shard_idx,
        max_samples=args.max_samples,
    )

    run_id = args.run_tag or time.strftime("%Y%m%d-%H%M%S")
    output_dir = Path(AgentPrune_ROOT) / "artifacts" / "runs" / f"mmlu_redux-{run_id}-shard{args.shard_idx}"
    events_dir = output_dir / "events"
    output_dir.mkdir(parents=True, exist_ok=True)
    events_dir.mkdir(parents=True, exist_ok=True)

    graph = Graph(
        domain="mmlu",
        llm_name=args.llm_name,
        agent_names=agent_names,
        decision_method=args.decision_method,
        optimized_spatial=False,
        optimized_temporal=False,
        rounds=args.num_rounds,
        diff=False,
        dec=False,
        phase_sequence=["propose", "critique", "verify", "aggregate"],
        enable_memory_governance=not args.disable_memory_governance,
        **get_kwargs(args.mode, len(agent_names)),
    )

    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()
    Cost.instance().reset()

    predictions: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    total_correct = 0
    start_ts = time.time()

    records = [dataset[idx] for idx in range(len(dataset))]
    for record_idx, record in enumerate(records):
        realized_graph = copy.deepcopy(graph)
        realized_graph.instrumentation.output_path = str(events_dir / f"sample_{record_idx:05d}.jsonl")
        set_token_usage_hook(realized_graph._on_token_usage)

        input_dict = dataset.record_to_input(record)
        raw_answer, _ = await realized_graph.arun(input_dict, num_rounds=args.num_rounds)
        prediction = dataset.postprocess_answer(raw_answer, record=record)
        target = dataset.record_to_target_answer(record)
        is_correct = prediction == target
        total_correct += int(is_correct)

        predictions.append(
            {
                "sample_idx": record_idx,
                "question": record["question"],
                "prediction": prediction,
                "target": target,
                "is_correct": is_correct,
                "raw_answer": raw_answer,
            }
        )
        if not is_correct:
            failures.append(
                {
                    "sample_idx": record_idx,
                    "question": record["question"],
                    "prediction": prediction,
                    "target": target,
                    "raw_answer": raw_answer,
                }
            )

    elapsed = time.time() - start_ts
    accuracy = total_correct / len(predictions) if predictions else 0.0
    metrics = {
        "dataset": "edinburgh-dawg/mmlu-redux",
        "split": args.split,
        "num_samples": len(predictions),
        "num_shards": args.num_shards,
        "shard_idx": args.shard_idx,
        "accuracy": accuracy,
        "total_correct": total_correct,
        "elapsed_seconds": elapsed,
        "prompt_tokens": PromptTokens.instance().value,
        "completion_tokens": CompletionTokens.instance().value,
        "cost": Cost.instance().value,
    }

    with (output_dir / "predictions.jsonl").open("w", encoding="utf-8") as fp:
        for row in predictions:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    with (output_dir / "metrics.json").open("w", encoding="utf-8") as fp:
        json.dump(metrics, fp, ensure_ascii=False, indent=2)

    with (output_dir / "failures.jsonl").open("w", encoding="utf-8") as fp:
        for row in failures:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    with (output_dir / "config.json").open("w", encoding="utf-8") as fp:
        json.dump(vars(args), fp, ensure_ascii=False, indent=2)

    print(json.dumps(metrics, ensure_ascii=False))
    return metrics


def aggregate_shards(run_root: Path) -> Dict[str, Any]:
    shard_dirs = sorted([path for path in run_root.iterdir() if path.is_dir() and "shard" in path.name])
    metrics = []
    for shard_dir in shard_dirs:
        metrics_file = shard_dir / "metrics.json"
        if metrics_file.exists():
            with metrics_file.open("r", encoding="utf-8") as fp:
                metrics.append(json.load(fp))
    if len(metrics) == 0:
        raise RuntimeError(f"No shard metrics found in {run_root}")

    total_samples = sum(item["num_samples"] for item in metrics)
    total_correct = sum(item["total_correct"] for item in metrics)
    total_prompt_tokens = sum(item["prompt_tokens"] for item in metrics)
    total_completion_tokens = sum(item["completion_tokens"] for item in metrics)
    total_cost = sum(item["cost"] for item in metrics)
    max_elapsed = max(item["elapsed_seconds"] for item in metrics)

    summary = {
        "dataset": "edinburgh-dawg/mmlu-redux",
        "num_shards": len(metrics),
        "num_samples": total_samples,
        "total_correct": total_correct,
        "accuracy": total_correct / total_samples if total_samples else 0.0,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "cost": total_cost,
        "elapsed_seconds_max_shard": max_elapsed,
    }
    with (run_root / "summary.json").open("w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)
    return summary


if __name__ == "__main__":
    arguments = parse_args()
    asyncio.run(evaluate_shard(arguments))
