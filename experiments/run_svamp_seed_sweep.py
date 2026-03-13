#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import math
import shlex
import subprocess
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parents[1]))


def run_cmd(command: str) -> int:
    proc = subprocess.run(shlex.split(command), check=False)
    return proc.returncode


def parse_args():
    parser = argparse.ArgumentParser(description="Run SVAMP protocol on multiple seeds and aggregate stats.")
    parser.add_argument("--python_bin", type=str, default="/workspace/.venv/bin/python")
    parser.add_argument("--seeds", type=str, default="42,3407,2025")
    parser.add_argument("--base_split_dir", type=str, default="datasets/SVAMP")
    parser.add_argument("--llm_name", type=str, default="MiniMax-M2.5")
    parser.add_argument("--phase_prefix", type=str, default="seed_sweep")
    parser.add_argument("--summary_out", type=str, default="result/gz10-v3/svamp_seed_sweep_summary.json")
    parser.add_argument("--extra_args", type=str, default="")
    parser.add_argument("--dry_run", action="store_true")
    return parser.parse_args()


def ensure_split(python_bin: str, base_split_dir: str, seed: int) -> str:
    split_dir = Path(base_split_dir) / f"split_seed{seed}"
    split_meta = split_dir / "split_meta.json"
    if split_meta.exists():
        return str(split_dir)
    cmd = (
        f"{python_bin} dataset/svamp_split.py "
        f"--seed {seed} --output_dir {split_dir} "
        f"--svamp_train_json datasets/SVAMP/train.json --svamp_test_json datasets/SVAMP/test.json"
    )
    code = run_cmd(cmd)
    if code != 0:
        raise SystemExit(code)
    return str(split_dir)


def main():
    args = parse_args()
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    results: List[Dict] = []

    for seed in seeds:
        split_dir = str(Path(args.base_split_dir) / f"split_seed{seed}")
        if not args.dry_run:
            split_dir = ensure_split(args.python_bin, args.base_split_dir, seed)

        out_path = Path("result/gz10-v3") / f"svamp_protocol_seed{seed}.json"
        cmd = (
            f"{args.python_bin} experiments/run_svamp_protocol.py "
            f"--python_bin {args.python_bin} "
            f"--split_dir {split_dir} "
            f"--phase_prefix {args.phase_prefix}_seed{seed} "
            f"--llm_name {args.llm_name} "
            f"--summary_out {out_path} "
        )
        if args.extra_args:
            cmd += f"--extra_args \"{args.extra_args}\" "

        if args.dry_run:
            results.append({"seed": seed, "command": cmd, "dry_run": True})
            continue

        code = run_cmd(cmd)
        if code != 0:
            raise SystemExit(code)
        with open(out_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        results.append({
            "seed": seed,
            "summary_file": str(out_path),
            "phase_40shot_accuracy": float(summary["phase_40shot"]["accuracy"]),
            "phase_full_train_accuracy": float(summary["phase_full_train"]["accuracy"]),
        })

    aggregate = {"runs": results}
    if not args.dry_run:
        acc_40 = [r["phase_40shot_accuracy"] for r in results]
        acc_full = [r["phase_full_train_accuracy"] for r in results]
        aggregate["aggregate"] = {
            "seeds": seeds,
            "phase_40shot_mean": mean(acc_40) if acc_40 else 0.0,
            "phase_40shot_std": pstdev(acc_40) if len(acc_40) > 1 else 0.0,
            "phase_full_train_mean": mean(acc_full) if acc_full else 0.0,
            "phase_full_train_std": pstdev(acc_full) if len(acc_full) > 1 else 0.0,
            "phase_full_minus_40_mean": mean([f - s for f, s in zip(acc_full, acc_40)]) if acc_full else 0.0,
        }

    out = Path(args.summary_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(aggregate, f, indent=2)
    print(json.dumps(aggregate, indent=2))


if __name__ == "__main__":
    main()
