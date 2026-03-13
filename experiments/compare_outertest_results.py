#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_json_list(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list payload: {path}")
    return payload


def extract_final_accuracy(rows: List[Dict[str, Any]], path: Path) -> float:
    if not rows:
        raise ValueError(f"Result file has no rows: {path}")
    if "Accuracy" not in rows[-1]:
        raise ValueError(f"Last row missing Accuracy field: {path}")
    return float(rows[-1]["Accuracy"])


def parse_args():
    parser = argparse.ArgumentParser(description="Compare baseline vs VG outer-test SVAMP results.")
    parser.add_argument("--baseline_result_json", type=str, required=True)
    parser.add_argument("--vg_result_json", type=str, required=True)
    parser.add_argument("--output_json", type=str, default="result/gz10-v3/final_outertest_compare.json")
    return parser.parse_args()


def main():
    args = parse_args()
    baseline_path = Path(args.baseline_result_json)
    vg_path = Path(args.vg_result_json)

    baseline_rows = load_json_list(baseline_path)
    vg_rows = load_json_list(vg_path)

    baseline_acc = extract_final_accuracy(baseline_rows, baseline_path)
    vg_acc = extract_final_accuracy(vg_rows, vg_path)

    absolute_gain = vg_acc - baseline_acc
    relative_gain_pct = (absolute_gain / baseline_acc * 100.0) if baseline_acc != 0 else 0.0

    summary = {
        "baseline_result_file": str(baseline_path),
        "vg_result_file": str(vg_path),
        "baseline_accuracy": baseline_acc,
        "vg_accuracy": vg_acc,
        "absolute_gain": absolute_gain,
        "relative_gain_pct": relative_gain_pct,
        "baseline_rows": len(baseline_rows),
        "vg_rows": len(vg_rows),
    }

    output = Path(args.output_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
