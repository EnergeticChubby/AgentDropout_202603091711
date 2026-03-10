import argparse
import asyncio
import copy
import json
import os
import random
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Union, Literal

import numpy as np
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding="utf-8")

import AgentDropout.agents  # noqa: F401
import AgentDropout.llm  # noqa: F401
import AgentDropout.prompt  # noqa: F401
from AgentDropout.graph.graph import Graph
from AgentDropout.llm.gpt_chat import configure_openai_endpoint
from AgentDropout.metrics.epistemic_metrics import compute_quality_score
from AgentDropout.utils.const import AgentPrune_ROOT
from datasets.mmlu_redux_dataset import DATASET_NAME, MMLUReduxRecord, load_mmlu_redux


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


def get_git_commit_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


@dataclass
class ShardResult:
    shard_id: int
    total: int
    correct: int
    accuracy: float
    avg_public_disclosures: float
    avg_total_claims: float
    avg_verified_claims: float
    quality_score: float
    output_file: str


def parse_args():
    parser = argparse.ArgumentParser(description="Run MMLU-Redux benchmark with shard parallelism.")
    parser.add_argument("--phase_name", type=str, required=True)
    parser.add_argument("--llm_name", type=str, default="qwen3-8b")
    parser.add_argument("--base_url", type=str, default=os.getenv("MINE_BASE_URL", ""))
    parser.add_argument("--api_key", type=str, default=os.getenv("MINE_API_KEYS", ""))
    parser.add_argument("--dataset_name", type=str, default=DATASET_NAME)
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--subject_limit", type=int, default=None)
    parser.add_argument("--questions_per_subject", type=int, default=None)
    parser.add_argument("--num_shards", type=int, default=8)
    parser.add_argument("--parallel_shards", type=int, default=8)
    parser.add_argument("--eval_batch_size", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", type=str, default="FullConnected",
                        choices=["DirectAnswer", "FullConnected", "Random", "Chain", "Debate", "Layered", "Star"])
    parser.add_argument("--agent_names", nargs="+", type=str, default=["AnalyzeAgent"])
    parser.add_argument("--agent_nums", nargs="+", type=int, default=[5])
    parser.add_argument("--decision_method", type=str, default="FinalRefer")
    parser.add_argument("--num_rounds", type=int, default=1)
    parser.add_argument("--output_root", type=str, default="artifacts/tests/mmlu_redux")
    parser.add_argument("--enable_mirm", action="store_true")
    parser.add_argument("--enable_edel", action="store_true")
    parser.add_argument("--enable_abpp", action="store_true")
    parser.add_argument("--token_budget", type=int, default=512)
    parser.add_argument("--topk_disclosure", type=int, default=3)
    return parser.parse_args()


def split_shards(records: List[MMLUReduxRecord], num_shards: int) -> Dict[int, List[MMLUReduxRecord]]:
    shards = {i: [] for i in range(num_shards)}
    for idx, record in enumerate(records):
        shards[idx % num_shards].append(record)
    return shards


def parse_choice_letter(answer: Union[str, List[str]]) -> str:
    text = answer[0] if isinstance(answer, list) and answer else answer
    text = "" if text is None else str(text).strip()
    if not text:
        return ""
    upper = text.upper()
    for token in ["A", "B", "C", "D"]:
        if upper.startswith(token):
            return token
    for ch in upper:
        if ch in {"A", "B", "C", "D"}:
            return ch
    return ""


def get_kwargs(mode: Union[
    Literal["DirectAnswer"], Literal["FullConnected"], Literal["Random"], Literal["Chain"],
    Literal["Debate"], Literal["Layered"], Literal["Star"]
], n: int):
    initial_spatial_probability = 0.5
    initial_temporal_probability = 0.5
    node_kwargs = None

    def generate_layered_graph(size, layer_num=2):
        matrix = [[0 for _ in range(size)] for _ in range(size)]
        base_size = size // layer_num
        remainder = size % layer_num
        layers = []
        for i in range(layer_num):
            group_size = base_size + (1 if i < remainder else 0)
            layers.extend([i] * group_size)
        for i in range(size):
            for j in range(size):
                if layers[j] == layers[i] + 1:
                    matrix[i][j] = 1
        return matrix

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
    elif mode == "Random":
        fixed_spatial_masks = [[random.randint(0, 1) if i != j else 0 for i in range(n)] for j in range(n)]
        fixed_temporal_masks = [[random.randint(0, 1) for _ in range(n)] for _ in range(n)]
    elif mode == "Chain":
        fixed_spatial_masks = [[1 if i == j + 1 else 0 for i in range(n)] for j in range(n)]
        fixed_temporal_masks = [[1 if i == 0 and j == n - 1 else 0 for i in range(n)] for j in range(n)]
    elif mode == "Debate":
        fixed_spatial_masks = [[0 for _ in range(n)] for _ in range(n)]
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
    elif mode == "Layered":
        fixed_spatial_masks = generate_layered_graph(n)
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
    elif mode == "Star":
        fixed_spatial_masks = generate_star_graph(n)
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return {
        "initial_spatial_probability": initial_spatial_probability,
        "fixed_spatial_masks": fixed_spatial_masks,
        "initial_temporal_probability": initial_temporal_probability,
        "fixed_temporal_masks": fixed_temporal_masks,
        "node_kwargs": node_kwargs,
    }


async def evaluate_single_shard(
    shard_id: int,
    records: List[MMLUReduxRecord],
    args,
    run_dir: Path,
) -> ShardResult:
    if not records:
        output_path = run_dir / f"shard_{shard_id:02d}_raw_outputs.json"
        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump([], fp, ensure_ascii=False, indent=2)
        return ShardResult(
            shard_id=shard_id,
            total=0,
            correct=0,
            accuracy=0.0,
            avg_public_disclosures=0.0,
            avg_total_claims=0.0,
            avg_verified_claims=0.0,
            quality_score=0.0,
            output_file=str(output_path),
        )

    agent_names = [name for name, num in zip(args.agent_names, args.agent_nums) for _ in range(num)]
    kwargs = get_kwargs(args.mode, len(agent_names))
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
        protocol_config={
            "enable_mirm": args.enable_mirm,
            "enable_edel": args.enable_edel,
            "enable_abpp": args.enable_abpp,
            "token_budget": args.token_budget,
            "topk_disclosure": args.topk_disclosure,
        },
        **kwargs,
    )

    shard_outputs = []
    correct = 0
    public_disclosure_total = 0
    claim_total = 0
    verified_claim_total = 0
    evaluated = 0

    for start in range(0, len(records), args.eval_batch_size):
        batch = records[start:start + args.eval_batch_size]
        tasks = []
        graphs = []
        for record in batch:
            realized_graph = copy.deepcopy(graph)
            graphs.append(realized_graph)
            tasks.append(asyncio.create_task(realized_graph.arun(record.to_input(), num_rounds=args.num_rounds, case=True)))
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        for record, realized_graph, result in zip(batch, graphs, batch_results):
            error_message = None
            if isinstance(result, Exception):
                raw_answer = ""
                all_answers = []
                error_message = str(result)
            else:
                raw_answer, _, all_answers = result

            pred = parse_choice_letter(raw_answer)
            gold = record.answer_letter
            is_correct = pred == gold
            correct += int(is_correct)
            evaluated += 1

            public_disclosure_count = len(realized_graph.public_blackboard.disclosures)
            ledger_stats = realized_graph.epistemic_ledger.stats()
            public_disclosure_total += public_disclosure_count
            claim_total += ledger_stats["total_claims"]
            verified_claim_total += ledger_stats["verified_claims"]

            row_payload = {
                "subject": record.subject,
                "question": record.question,
                "choices": record.choices,
                "gold": gold,
                "pred": pred,
                "is_correct": is_correct,
                "raw_answer": raw_answer,
                "all_round_answers": all_answers,
                "protocol_stats": {
                    "public_disclosures": public_disclosure_count,
                    "ledger_total_claims": ledger_stats["total_claims"],
                    "ledger_verified_claims": ledger_stats["verified_claims"],
                },
            }
            if error_message is not None:
                row_payload["error"] = error_message
            shard_outputs.append(row_payload)

    total = len(records)
    accuracy = correct / total if total else 0.0
    avg_public_disclosures = public_disclosure_total / evaluated if evaluated else 0.0
    avg_total_claims = claim_total / evaluated if evaluated else 0.0
    avg_verified_claims = verified_claim_total / evaluated if evaluated else 0.0
    quality_score = compute_quality_score(
        accuracy=accuracy,
        avg_public_disclosures=avg_public_disclosures,
        avg_verified_claims=avg_verified_claims,
    )
    output_path = run_dir / f"shard_{shard_id:02d}_raw_outputs.json"
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(shard_outputs, fp, ensure_ascii=False, indent=2)
    return ShardResult(
        shard_id=shard_id,
        total=total,
        correct=correct,
        accuracy=accuracy,
        avg_public_disclosures=avg_public_disclosures,
        avg_total_claims=avg_total_claims,
        avg_verified_claims=avg_verified_claims,
        quality_score=quality_score,
        output_file=str(output_path),
    )


async def run_sharded_benchmark(args, run_dir: Path) -> Dict[str, object]:
    records = load_mmlu_redux(
        split=args.split,
        subject_limit=args.subject_limit,
        questions_per_subject=args.questions_per_subject,
        dataset_name=args.dataset_name,
    )
    shards = split_shards(records, args.num_shards)
    shard_ids = list(range(args.num_shards))

    semaphore = asyncio.Semaphore(args.parallel_shards)

    async def guarded_eval(shard_id: int):
        async with semaphore:
            return await evaluate_single_shard(shard_id, shards[shard_id], args, run_dir)

    shard_results = await asyncio.gather(*[guarded_eval(sid) for sid in shard_ids])
    total = sum(item.total for item in shard_results)
    correct = sum(item.correct for item in shard_results)
    accuracy = correct / total if total else 0.0
    weighted_public = sum(item.avg_public_disclosures * item.total for item in shard_results) / total if total else 0.0
    weighted_claims = sum(item.avg_total_claims * item.total for item in shard_results) / total if total else 0.0
    weighted_verified = sum(item.avg_verified_claims * item.total for item in shard_results) / total if total else 0.0
    quality_score = compute_quality_score(
        accuracy=accuracy,
        avg_public_disclosures=weighted_public,
        avg_verified_claims=weighted_verified,
    )
    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "avg_public_disclosures": weighted_public,
        "avg_total_claims": weighted_claims,
        "avg_verified_claims": weighted_verified,
        "quality_score": quality_score,
        "shards": [asdict(item) for item in shard_results],
    }


async def main():
    args = parse_args()
    set_seed(args.seed)
    if not args.base_url or not args.api_key:
        raise RuntimeError("base_url/api_key is required. Provide --base_url and --api_key or env vars.")
    configure_openai_endpoint(base_url=args.base_url, api_key=args.api_key)

    timestamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    run_dir = Path(AgentPrune_ROOT) / args.output_root / args.phase_name / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    config_payload = vars(args).copy()
    if "api_key" in config_payload and config_payload["api_key"]:
        config_payload["api_key"] = "<redacted>"
    config_payload["git_commit"] = get_git_commit_hash()
    config_payload["run_dir"] = str(run_dir)
    with open(run_dir / "config.json", "w", encoding="utf-8") as fp:
        json.dump(config_payload, fp, ensure_ascii=False, indent=2)

    started_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    metrics = await run_sharded_benchmark(args, run_dir)
    with open(run_dir / "metrics.json", "w", encoding="utf-8") as fp:
        json.dump(metrics, fp, ensure_ascii=False, indent=2)

    finished_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    run_log = {
        "started_at": started_at,
        "finished_at": finished_at,
        "phase_name": args.phase_name,
        "run_dir": str(run_dir),
        "git_commit": config_payload["git_commit"],
        "summary": {
            "total": metrics.get("total", 0),
            "correct": metrics.get("correct", 0),
            "accuracy": metrics.get("accuracy", 0.0),
            "quality_score": metrics.get("quality_score", 0.0),
            "num_shards": args.num_shards,
            "parallel_shards": args.parallel_shards,
        },
    }
    with open(run_dir / "run.log", "w", encoding="utf-8") as fp:
        fp.write(json.dumps(run_log, ensure_ascii=False, indent=2))

    print(json.dumps({"run_dir": str(run_dir), **metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

