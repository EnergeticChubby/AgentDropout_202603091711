import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build coordination/competence collapse labels from rollout telemetry."
    )
    parser.add_argument("--telemetry_json", type=str, required=True)
    parser.add_argument("--output_json", type=str, required=True)
    return parser.parse_args()


def flatten_events(rounds: List[Dict]) -> List[Dict]:
    events = []
    for r in rounds:
        events.extend(r.get("events", []))
    return events


def sum_tokens(rounds: List[Dict]) -> float:
    total = 0.0
    for r in rounds:
        tokens = r.get("tokens", {})
        total += float(tokens.get("prompt", 0.0)) + float(tokens.get("completion", 0.0))
    return total


def detect_coordination_failure(record: Dict, events: List[Dict]) -> Dict:
    event_counter = Counter(e.get("type", "") for e in events)
    claim_create = event_counter.get("CLAIM_CREATE", 0)
    claim_resolve = event_counter.get("CLAIM_RESOLVE", 0)
    claim_challenge = event_counter.get("CLAIM_CHALLENGE", 0)
    rollback = event_counter.get("SUMMARY_ROLLBACK", 0)
    new_info = event_counter.get("MSG_NEW_INFO", 0)
    rephrase = event_counter.get("MSG_REPHRASE", 0)

    rounds = record.get("rounds", [])
    total_tokens = sum_tokens(rounds)
    no_progress = claim_create > 0 and claim_resolve == 0
    high_consensus_no_evidence = claim_create >= 3 and new_info == 0 and claim_challenge == 0
    repeated_rephrase = rephrase >= 3 and new_info <= 1
    high_token_stall = total_tokens > 0 and claim_resolve == 0 and rollback > 0

    coordination_failure = any(
        [rollback > 0, no_progress, high_consensus_no_evidence, repeated_rephrase, high_token_stall]
    )
    reasons = {
        "rollback_present": rollback > 0,
        "no_progress": no_progress,
        "high_consensus_no_evidence": high_consensus_no_evidence,
        "repeated_rephrase": repeated_rephrase,
        "high_token_stall": high_token_stall,
    }
    return {"coordination_failure": coordination_failure, "reasons": reasons, "event_counter": dict(event_counter)}


def main():
    args = parse_args()
    telemetry_path = Path(args.telemetry_json)
    output_path = Path(args.output_json)

    if not telemetry_path.exists():
        raise FileNotFoundError(f"Telemetry file not found: {telemetry_path}")

    with open(telemetry_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    labeled_records = []
    summary = {"total": 0, "coordination_failure": 0, "competence_failure": 0, "correct": 0}

    for record in records:
        events = flatten_events(record.get("rounds", []))
        coordination = detect_coordination_failure(record, events)
        is_correct = bool(record.get("is_correct", False))
        competence_failure = (not is_correct) and (not coordination["coordination_failure"])

        labeled = {
            "problem_id": record.get("problem_id"),
            "split": record.get("split"),
            "is_correct": is_correct,
            "coordination_failure": coordination["coordination_failure"],
            "competence_failure": competence_failure,
            "coordination_reasons": coordination["reasons"],
            "event_counter": coordination["event_counter"],
        }
        labeled_records.append(labeled)

        summary["total"] += 1
        summary["correct"] += int(is_correct)
        summary["coordination_failure"] += int(coordination["coordination_failure"])
        summary["competence_failure"] += int(competence_failure)

    output = {"summary": summary, "labels": labeled_records}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"[COLLAPSE-LABEL] output={output_path} summary={summary}")


if __name__ == "__main__":
    main()
