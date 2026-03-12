#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from experiments.benchmark_compare import compare_phase
from experiments.benchmark_gsm8k_phase import summarize_phase as summarize_gsm8k
from experiments.benchmark_svamp_phase import summarize_phase as summarize_svamp


def parse_args():
    parser = argparse.ArgumentParser(description="Phase execution gate controller.")
    parser.add_argument("--phases_json", type=str, required=True,
                        help="JSON file listing phases with fields: name, benchmark_type, result_glob")
    parser.add_argument("--output_json", type=str, default="result/gz10-v3/phase_history.json")
    parser.add_argument("--allow_equal", action="store_true")
    return parser.parse_args()


def load_phases(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError("phases_json must be a list.")
    return payload


def summarize_phase(phase: Dict[str, Any]) -> Dict[str, Any]:
    benchmark_type = phase.get("benchmark_type", "svamp")
    result_glob = phase["result_glob"]
    phase_name = phase["name"]
    if benchmark_type == "gsm8k":
        return summarize_gsm8k(phase_name=phase_name, result_glob=result_glob)
    return summarize_svamp(phase_name=phase_name, result_glob=result_glob)


def main():
    args = parse_args()
    phases = load_phases(args.phases_json)
    history: List[Dict[str, Any]] = []
    previous_result: Optional[str] = None

    for phase in phases:
        summary = summarize_phase(phase)
        comparison = compare_phase(
            current_result=summary["result_file"],
            previous_result=previous_result,
            strict_greater=not args.allow_equal,
        )
        entry = {"phase": phase, "summary": summary, "comparison": comparison}
        history.append(entry)
        print(json.dumps(entry, indent=2))
        if not comparison["passed"]:
            out = Path(args.output_json)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            raise SystemExit(2)
        previous_result = summary["result_file"]

    out = Path(args.output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


if __name__ == "__main__":
    main()
