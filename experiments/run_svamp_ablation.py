#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parents[1]))
from experiments.benchmark_compare import extract_accuracy


def run_command(command: str) -> int:
    proc = subprocess.run(shlex.split(command), check=False)
    return proc.returncode


def latest_result(result_dir: Path, phase_name: str) -> Path:
    matches = sorted(result_dir.glob(f"svamp_{phase_name}_*.json"), key=lambda p: p.stat().st_mtime)
    if not matches:
        fallback = Path("result/SVAMP")
        matches = sorted(fallback.glob(f"svamp_{phase_name}_*.json"), key=lambda p: p.stat().st_mtime)
    if not matches:
        raise FileNotFoundError(f"No result found for phase {phase_name}")
    return matches[-1]


def parse_args():
    parser = argparse.ArgumentParser(description="Run SVAMP ablation groups (A1~A7) with unified protocol.")
    parser.add_argument("--python_bin", type=str, default="/workspace/.venv/bin/python")
    parser.add_argument("--split_dir", type=str, default="datasets/SVAMP/split_seed42")
    parser.add_argument("--llm_name", type=str, default="MiniMax-M2.5")
    parser.add_argument("--result_dir", type=str, default="result/SVAMP")
    parser.add_argument("--summary_out", type=str, default="result/gz10-v3/svamp_ablation_summary.json")
    parser.add_argument("--extra_args", type=str, default="")
    parser.add_argument("--run_mode", type=str, choices=["all", "quick"], default="quick")
    return parser.parse_args()


def main():
    args = parse_args()
    split_dir = Path(args.split_dir)
    train_json = split_dir / "svamp_train.json"
    val_json = split_dir / "svamp_val.json"
    split_meta = split_dir / "split_meta.json"
    result_dir = Path(args.result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)

    common = (
        f"{args.python_bin} experiments/run_svamp.py "
        f"--dataset_json {val_json} --train_json {train_json} --split_meta_json {split_meta} "
        f"--llm_name {args.llm_name} --domain svamp --mode FullConnected --agent_nums 5 "
        f"--batch_size 40 --num_iterations 2 --imp_per_iterations 1 --pruning_rate 0.10 --num_rounds 2 "
        f"--optimized_spatial --optimized_temporal --diff --dec "
    )
    if args.extra_args:
        common += f"{args.extra_args} "

    configs: List[Dict[str, str]] = [
        {"name": "A1_baseline", "flags": ""},
        {"name": "A2_node_only", "flags": "--state_aware_node --lambda_repeat 0.1 --lambda_consensus 0.1 --lambda_capacity 0.05"},
        {"name": "A3_edge_only", "flags": "--state_aware_edge --gamma_repeatflow 0.1 --gamma_echo 0.1 --gamma_capacityflow 0.05"},
        {"name": "A4_node_edge", "flags": "--state_aware_node --state_aware_edge --lambda_repeat 0.1 --lambda_consensus 0.1 --lambda_capacity 0.05 --gamma_repeatflow 0.1 --gamma_echo 0.1 --gamma_capacityflow 0.05"},
        {"name": "A5_random_like", "flags": "--state_aware_node --state_aware_edge --lambda_repeat 0.02 --lambda_consensus 0.18 --lambda_capacity 0.07 --gamma_repeatflow 0.19 --gamma_echo 0.03 --gamma_capacityflow 0.11"},
        {"name": "A6_rule_only", "flags": "--state_aware_node --state_aware_edge"},
        {"name": "A7_40shot", "flags": "--state_aware_node --state_aware_edge --train_sample_size 40"},
    ]
    if args.run_mode == "quick":
        configs = configs[:4]

    summary = []
    for cfg in configs:
        phase_name = f"ablation_{cfg['name']}"
        command = f"{common} --phase_name {phase_name} {cfg['flags']}"
        code = run_command(command)
        if code != 0:
            raise SystemExit(code)
        result_file = latest_result(result_dir, phase_name)
        summary.append({
            "ablation": cfg["name"],
            "phase_name": phase_name,
            "result_file": str(result_file),
            "accuracy": extract_accuracy(str(result_file)),
            "flags": cfg["flags"],
        })

    output = Path(args.summary_out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
