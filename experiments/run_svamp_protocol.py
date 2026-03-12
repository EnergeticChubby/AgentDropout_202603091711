#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict

sys.path.append(str(Path(__file__).resolve().parents[1]))
from experiments.benchmark_compare import extract_accuracy


def run(command: str):
    proc = subprocess.run(shlex.split(command), check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def latest_result(result_dir: Path, phase_name: str) -> Path:
    matches = sorted(result_dir.glob(f"svamp_{phase_name}_*.json"), key=lambda p: p.stat().st_mtime)
    if not matches:
        raise FileNotFoundError(f"No result generated for phase_name={phase_name} in {result_dir}")
    return matches[-1]


def parse_args():
    parser = argparse.ArgumentParser(description="Run SVAMP 40-shot and full-train protocol.")
    parser.add_argument("--python_bin", type=str, default="/workspace/.venv/bin/python")
    parser.add_argument("--split_dir", type=str, default="datasets/SVAMP/split_seed42")
    parser.add_argument("--phase_prefix", type=str, default="protocol")
    parser.add_argument("--llm_name", type=str, default="MiniMax-M2.5")
    parser.add_argument("--result_dir", type=str, default="result/gz10-v3/SVAMP")
    parser.add_argument("--summary_out", type=str, default="result/gz10-v3/svamp_protocol_summary.json")
    parser.add_argument("--extra_args", type=str, default="")
    return parser.parse_args()


def main():
    args = parse_args()
    split_dir = Path(args.split_dir)
    split_meta = split_dir / "split_meta.json"
    train_json = split_dir / "svamp_train.json"
    val_json = split_dir / "svamp_val.json"

    phase_40 = f"{args.phase_prefix}_40shot"
    phase_full = f"{args.phase_prefix}_full"

    base_cmd = (
        f"{args.python_bin} experiments/run_svamp.py "
        f"--dataset_json {val_json} --train_json {train_json} --split_meta_json {split_meta} "
        f"--result_dir {result_dir} "
        f"--llm_name {args.llm_name} --domain svamp --mode FullConnected "
        f"--agent_nums 5 --batch_size 40 --num_iterations 2 --imp_per_iterations 1 "
        f"--pruning_rate 0.10 --num_rounds 2 --optimized_spatial --optimized_temporal --diff --dec "
    )
    if args.extra_args:
        base_cmd += f"{args.extra_args} "

    run(base_cmd + f"--phase_name {phase_40} --train_sample_size 40")
    run(base_cmd + f"--phase_name {phase_full}")

    result_dir = Path(args.result_dir)
    result_40 = latest_result(result_dir, phase_40)
    result_full = latest_result(result_dir, phase_full)
    summary: Dict[str, object] = {
        "phase_40shot": {
            "result_file": str(result_40),
            "accuracy": extract_accuracy(str(result_40)),
        },
        "phase_full_train": {
            "result_file": str(result_full),
            "accuracy": extract_accuracy(str(result_full)),
        },
    }
    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
