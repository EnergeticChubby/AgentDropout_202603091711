#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import glob
import json
from pathlib import Path
from statistics import mean
from typing import Dict, List


def load_rows(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload if isinstance(payload, list) else []


def summarize_file(path: str) -> Dict:
    rows = load_rows(path)
    if not rows:
        return {
            "file": path,
            "num_rows": 0,
            "accuracy": 0.0,
            "solved": 0,
            "total": 0,
            "attempt_answer_nonzero_ratio": 0.0,
        }

    solved_values = [int(bool(r.get("Solved", False))) for r in rows if "Solved" in r]
    solved = sum(solved_values)
    total = len(solved_values) if solved_values else len(rows)
    accuracy = solved / total if total else 0.0
    attempts = [str(r.get("Attempt answer", "")).strip() for r in rows]
    nonzero = [1 for a in attempts if a not in {"", "0", "0.0", "None."}]
    nonzero_ratio = len(nonzero) / len(attempts) if attempts else 0.0

    return {
        "file": path,
        "num_rows": len(rows),
        "accuracy": accuracy,
        "solved": solved,
        "total": total,
        "attempt_answer_nonzero_ratio": nonzero_ratio,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Summarize SVAMP result JSON files into one report.")
    parser.add_argument("--glob_pattern", type=str, default="result/SVAMP/svamp_*.json")
    parser.add_argument("--output_json", type=str, default="result/gz10-v3/svamp_summary.json")
    return parser.parse_args()


def main():
    args = parse_args()
    files = sorted(glob.glob(args.glob_pattern))
    summaries = [summarize_file(path) for path in files]
    aggregate = {
        "num_files": len(summaries),
        "mean_accuracy": mean([item["accuracy"] for item in summaries]) if summaries else 0.0,
        "best_accuracy": max([item["accuracy"] for item in summaries], default=0.0),
        "worst_accuracy": min([item["accuracy"] for item in summaries], default=0.0),
        "files": summaries,
    }
    output = Path(args.output_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(aggregate, f, indent=2)
    print(json.dumps(aggregate, indent=2))


if __name__ == "__main__":
    main()
