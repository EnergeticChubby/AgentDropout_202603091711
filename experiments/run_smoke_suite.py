#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import shlex
import subprocess
from pathlib import Path
from typing import List


def run(command: str, dry_run: bool = False) -> int:
    print(f"$ {command}")
    if dry_run:
        return 0
    proc = subprocess.run(shlex.split(command), check=False)
    return proc.returncode


def parse_args():
    parser = argparse.ArgumentParser(description="Run lightweight smoke checks for VG-AgentDropout-SVAMP tooling.")
    parser.add_argument("--python_bin", type=str, default="/workspace/.venv/bin/python")
    parser.add_argument("--dry_run", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    smoke_dir = ".tmp_svamp/smoke_suite/SVAMP"
    gsm_dir = ".tmp_svamp/smoke_suite/gsm8k"
    commands: List[str] = [
        f"{args.python_bin} -m compileall dataset/prepare_svamp.py dataset/prepare_gsm8k.py experiments/check_env_readiness.py experiments/phase_controller.py experiments/run_svamp.py experiments/run_gsm8k_healthcheck.py",
        f"{args.python_bin} dataset/prepare_svamp.py --output_dir {smoke_dir} --seed 42",
        f"{args.python_bin} dataset/prepare_gsm8k.py --output_dir {gsm_dir}",
        f"{args.python_bin} experiments/check_env_readiness.py --svamp_train_json {smoke_dir}/train.json --svamp_test_json {smoke_dir}/test.json --require_gsm8k --gsm8k_train_json {gsm_dir}/train.jsonl --gsm8k_test_json {gsm_dir}/test.jsonl --skip_api_check",
        f"{args.python_bin} experiments/run_vg_svamp_pipeline.py --dry_run --validate_outputs --split_dir datasets/SVAMP/split_seed42 --svamp_train_json {smoke_dir}/train.json --svamp_test_json {smoke_dir}/test.json --require_gsm8k --gsm8k_train_json {gsm_dir}/train.jsonl --gsm8k_test_json {gsm_dir}/test.jsonl --skip_api_check",
        f"{args.python_bin} experiments/run_svamp_seed_sweep.py --dry_run --seeds \"42,3407\"",
    ]
    results = []
    for command in commands:
        code = run(command, dry_run=args.dry_run)
        results.append({"command": command, "return_code": code})
        if code != 0:
            print(json.dumps({"smoke_status": "failed", "results": results}, indent=2))
            raise SystemExit(code)

    print(json.dumps({"smoke_status": "success", "results": results}, indent=2))


if __name__ == "__main__":
    main()
