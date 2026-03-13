#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def extract_accuracy(result_file: str) -> float:
    path = Path(result_file)
    if not path.exists():
        raise FileNotFoundError(f"Result file not found: {result_file}")

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, list) or len(payload) == 0:
        return 0.0

    last: Dict[str, Any] = payload[-1]
    if "Accuracy" in last:
        return float(last["Accuracy"])

    solved_count = 0
    total_count = 0
    for item in payload:
        if "Solved" in item:
            solved_count += int(bool(item["Solved"]))
            total_count += 1
    return (solved_count / total_count) if total_count > 0 else 0.0


def compare_phase(current_result: str, previous_result: Optional[str], strict_greater: bool = True):
    current_acc = extract_accuracy(current_result)
    if previous_result is None:
        return {
            "current_result": current_result,
            "previous_result": None,
            "current_accuracy": current_acc,
            "previous_accuracy": None,
            "passed": True,
            "rule": "bootstrap",
        }

    prev_acc = extract_accuracy(previous_result)
    passed = (current_acc > prev_acc) if strict_greater else (current_acc >= prev_acc)
    return {
        "current_result": current_result,
        "previous_result": previous_result,
        "current_accuracy": current_acc,
        "previous_accuracy": prev_acc,
        "passed": passed,
        "rule": "strict_greater" if strict_greater else "greater_equal",
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Compare benchmark accuracy between two phase result files.")
    parser.add_argument("--current_result", type=str, required=True)
    parser.add_argument("--previous_result", type=str, default=None)
    parser.add_argument("--allow_equal", action="store_true")
    parser.add_argument("--output_json", type=str, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    comparison = compare_phase(
        current_result=args.current_result,
        previous_result=args.previous_result,
        strict_greater=not args.allow_equal,
    )
    print(json.dumps(comparison, indent=2))
    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2)

    if not comparison["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
