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
    commands: List[str] = [
        f"{args.python_bin} -m compileall experiments/check_env_readiness.py experiments/phase_controller.py experiments/run_svamp.py",
        f"{args.python_bin} experiments/check_env_readiness.py",
        f"{args.python_bin} experiments/run_vg_svamp_pipeline.py --dry_run",
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
