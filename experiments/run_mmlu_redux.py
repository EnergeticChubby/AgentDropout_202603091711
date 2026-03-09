import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from AgentDropout.utils.const import AgentPrune_ROOT


def parse_args():
    parser = argparse.ArgumentParser(description="Run MMLU-Redux benchmark with shard parallelism.")
    parser.add_argument("--llm_name", type=str, default="qwen3-8b")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--num_shards", type=int, default=8)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--num_rounds", type=int, default=1)
    parser.add_argument("--mode", type=str, default="FullConnected")
    parser.add_argument("--decision_method", type=str, default="FinalRefer")
    parser.add_argument("--agent_names", nargs="+", type=str, default=["AnalyzeAgent"])
    parser.add_argument("--agent_nums", nargs="+", type=int, default=[5])
    parser.add_argument("--run_tag", type=str, default=None)
    return parser.parse_args()


async def run_single_shard(args, shard_idx: int):
    script_path = Path(AgentPrune_ROOT) / "experiments" / "evaluate_mmlu_redux.py"
    command: List[str] = [
        sys.executable,
        str(script_path),
        "--llm_name",
        args.llm_name,
        "--split",
        args.split,
        "--num_shards",
        str(args.num_shards),
        "--shard_idx",
        str(shard_idx),
        "--num_rounds",
        str(args.num_rounds),
        "--mode",
        args.mode,
        "--decision_method",
        args.decision_method,
        "--run_tag",
        args.run_tag,
    ]
    if args.max_samples is not None:
        command.extend(["--max_samples", str(args.max_samples)])
    if args.agent_names:
        command.extend(["--agent_names", *args.agent_names])
    if args.agent_nums:
        command.extend(["--agent_nums", *[str(num) for num in args.agent_nums]])

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(AgentPrune_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "shard_idx": shard_idx,
        "returncode": process.returncode,
        "stdout": stdout.decode("utf-8", errors="ignore"),
        "stderr": stderr.decode("utf-8", errors="ignore"),
    }


async def main():
    args = parse_args()
    run_tag = args.run_tag or time.strftime("%Y%m%d-%H%M%S")
    args.run_tag = run_tag

    tasks = [run_single_shard(args, shard_idx) for shard_idx in range(args.num_shards)]
    shard_results = await asyncio.gather(*tasks)

    run_root = Path(AgentPrune_ROOT) / "artifacts" / "runs"
    relevant_dirs = [path for path in run_root.glob(f"mmlu_redux-{run_tag}-shard*") if path.is_dir()]
    session_dir = run_root / f"mmlu_redux-{run_tag}-all"
    session_dir.mkdir(parents=True, exist_ok=True)

    with (session_dir / "shard_process_logs.json").open("w", encoding="utf-8") as fp:
        json.dump(shard_results, fp, ensure_ascii=False, indent=2)

    failed = [row for row in shard_results if row["returncode"] != 0]
    if failed:
        print(json.dumps({"status": "failed", "failed_shards": failed}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    per_shard_metrics = []
    for shard_dir in relevant_dirs:
        metrics_file = shard_dir / "metrics.json"
        if not metrics_file.exists():
            continue
        with metrics_file.open("r", encoding="utf-8") as fp:
            per_shard_metrics.append(json.load(fp))
    total_samples = sum(item["num_samples"] for item in per_shard_metrics)
    total_correct = sum(item["total_correct"] for item in per_shard_metrics)
    summary = {
        "dataset": "edinburgh-dawg/mmlu-redux",
        "run_tag": run_tag,
        "num_shards": len(per_shard_metrics),
        "num_samples": total_samples,
        "total_correct": total_correct,
        "accuracy": total_correct / total_samples if total_samples else 0.0,
        "prompt_tokens": sum(item["prompt_tokens"] for item in per_shard_metrics),
        "completion_tokens": sum(item["completion_tokens"] for item in per_shard_metrics),
        "cost": sum(item["cost"] for item in per_shard_metrics),
        "elapsed_seconds_max_shard": max((item["elapsed_seconds"] for item in per_shard_metrics), default=0.0),
        "shard_metrics_dirs": [str(path) for path in relevant_dirs],
    }
    with (session_dir / "summary.json").open("w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)
    with (session_dir / "summary.md").open("w", encoding="utf-8") as fp:
        fp.write("# MMLU-Redux 8-shard Summary\n\n")
        fp.write(f"- run_tag: `{run_tag}`\n")
        fp.write(f"- num_shards: {summary['num_shards']}\n")
        fp.write(f"- num_samples: {summary['num_samples']}\n")
        fp.write(f"- accuracy: {summary['accuracy']:.6f}\n")
        fp.write(f"- total_correct: {summary['total_correct']}\n")
        fp.write(f"- elapsed_seconds_max_shard: {summary['elapsed_seconds_max_shard']:.3f}\n")
        fp.write(f"- prompt_tokens: {summary['prompt_tokens']}\n")
        fp.write(f"- completion_tokens: {summary['completion_tokens']}\n")
        fp.write(f"- cost: {summary['cost']}\n")
    print(json.dumps({"status": "ok", "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
