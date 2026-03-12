#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import glob
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from experiments.benchmark_compare import extract_accuracy


def newest_file(pattern: str) -> Optional[str]:
    matches = glob.glob(pattern)
    if not matches:
        return None
    return max(matches, key=lambda p: Path(p).stat().st_mtime)


def run_command(command: str) -> int:
    proc = subprocess.run(shlex.split(command), check=False)
    return proc.returncode


def summarize_phase(phase_name: str, result_glob: str) -> Dict[str, Any]:
    latest = newest_file(result_glob)
    if latest is None:
        raise FileNotFoundError(f"No result file found for pattern: {result_glob}")
    return {
        "phase_name": phase_name,
        "result_file": latest,
        "accuracy": extract_accuracy(latest),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Run/collect SVAMP benchmark for one phase.")
    parser.add_argument("--phase_name", type=str, required=True)
    parser.add_argument("--run_cmd", type=str, default=None)
    parser.add_argument("--result_glob", type=str, default="result/gz10-v3/SVAMP/svamp_*.json")
    parser.add_argument("--output_json", type=str, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.run_cmd:
        code = run_command(args.run_cmd)
        if code != 0:
            raise SystemExit(code)

    summary = summarize_phase(args.phase_name, args.result_glob)
    print(json.dumps(summary, indent=2))
    if args.output_json:
        out = Path(args.output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
