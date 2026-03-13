#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


PHASES = [
    "exploration",
    "productive",
    "repetition_stagnation",
    "premature_consensus",
    "recovery",
]


def load_telemetry(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def infer_phase(round_item: Dict[str, Any]) -> str:
    round_id = int(round_item.get("round_id", 0))
    consensus = float(round_item.get("answer_consensus", 0.0))
    repetition = float(round_item.get("repetition_ratio", 0.0))
    novelty_drop = float(round_item.get("semantic_novelty_drop", 0.0))
    token_growth = float(round_item.get("token_growth", 0.0))
    progress = float(round_item.get("progress_delta", 0.0))
    new_info = float(round_item.get("new_information", 0.0))

    if repetition >= 0.7 and novelty_drop >= 0.6 and progress <= 0.0:
        return "repetition_stagnation"
    if round_id <= 1 and consensus >= 0.85 and progress <= 0.0:
        return "premature_consensus"
    if progress > 0.0 and repetition < 0.6:
        return "recovery"
    if new_info >= 0.5 and consensus < 0.85:
        return "productive"
    if token_growth > 128 and novelty_drop > 0.7:
        return "repetition_stagnation"
    return "exploration"


def infer_risk_labels(round_item: Dict[str, Any]) -> Dict[str, int]:
    consensus = float(round_item.get("answer_consensus", 0.0))
    repetition = float(round_item.get("repetition_ratio", 0.0))
    novelty_drop = float(round_item.get("semantic_novelty_drop", 0.0))
    token_growth = float(round_item.get("token_growth", 0.0))
    new_info = float(round_item.get("new_information", 0.0))

    return {
        "risk_repeat_label": int(repetition >= 0.7 and novelty_drop >= 0.5),
        "risk_consensus_label": int(consensus >= 0.85),
        "risk_capacity_label": int(token_growth > 128 and new_info < 0.35),
    }


def build_dataset(telemetry_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    dataset_rows: List[Dict[str, Any]] = []
    for case in telemetry_records:
        case_id = case.get("case_id", "unknown")
        rounds = case.get("rounds", [])
        for round_item in rounds:
            phase_label = infer_phase(round_item)
            row = {
                "case_id": case_id,
                "round_id": round_item.get("round_id", 0),
                "features": {
                    "answer_consensus": float(round_item.get("answer_consensus", 0.0)),
                    "answer_conflict": float(round_item.get("answer_conflict", 0.0)),
                    "new_information": float(round_item.get("new_information", 0.0)),
                    "repetition_ratio": float(round_item.get("repetition_ratio", 0.0)),
                    "semantic_novelty_drop": float(round_item.get("semantic_novelty_drop", 0.0)),
                    "token_growth": float(round_item.get("token_growth", 0.0)),
                    "progress_delta": float(round_item.get("progress_delta", 0.0)),
                },
                "phase_label": phase_label,
            }
            row.update(infer_risk_labels(round_item))
            dataset_rows.append(row)
    return dataset_rows


def parse_args():
    parser = argparse.ArgumentParser(description="Build observer training labels from telemetry logs.")
    parser.add_argument("--telemetry_jsonl", type=str, required=True)
    parser.add_argument("--output_jsonl", type=str, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    telemetry = load_telemetry(args.telemetry_jsonl)
    dataset_rows = build_dataset(telemetry)
    output = Path(args.output_jsonl)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        for row in dataset_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({
        "telemetry_cases": len(telemetry),
        "observer_rows": len(dataset_rows),
        "output": str(output),
    }, indent=2))


if __name__ == "__main__":
    main()
