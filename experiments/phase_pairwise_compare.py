import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _sample_entry(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "question": row.get("Question", {}).get("task", ""),
        "pred_answer": row.get("pred_answer", row.get("Attempt answer", "")),
        "gold_answer": row.get("gold_answer", row.get("Answer", "")),
        "phase_label": row.get("PhaseLabel", ""),
        "phase_metrics": row.get("PhaseMetrics", {}),
    }


def _build_index(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        task = str(row.get("Question", {}).get("task", "")).strip()
        if task:
            result[task] = row
    return result


def _transition_key(base_correct: bool, current_correct: bool) -> str:
    if base_correct and current_correct:
        return "correct_to_correct"
    if base_correct and (not current_correct):
        return "correct_to_wrong"
    if (not base_correct) and current_correct:
        return "wrong_to_correct"
    return "wrong_to_wrong"


def build_pairwise_report(
    *,
    base_phase: str,
    current_phase: str,
    base_summary: Dict[str, Any],
    current_summary: Dict[str, Any],
    base_rows: List[Dict[str, Any]],
    current_rows: List[Dict[str, Any]],
    max_examples: int,
) -> Dict[str, Any]:
    base_idx = _build_index(base_rows)
    current_idx = _build_index(current_rows)
    common_tasks = sorted(set(base_idx.keys()) & set(current_idx.keys()))

    transitions = {
        "correct_to_correct": 0,
        "correct_to_wrong": 0,
        "wrong_to_correct": 0,
        "wrong_to_wrong": 0,
    }
    regressions: List[Dict[str, Any]] = []
    improvements: List[Dict[str, Any]] = []

    for task in common_tasks:
        base_row = base_idx[task]
        current_row = current_idx[task]
        base_correct = bool(base_row.get("final_correct", base_row.get("Solved", False)))
        current_correct = bool(
            current_row.get("final_correct", current_row.get("Solved", False))
        )
        key = _transition_key(base_correct, current_correct)
        transitions[key] += 1

        if base_correct and (not current_correct) and len(regressions) < max_examples:
            regressions.append(
                {
                    "question": task,
                    "base": _sample_entry(base_row),
                    "current": _sample_entry(current_row),
                }
            )
        if (not base_correct) and current_correct and len(improvements) < max_examples:
            improvements.append(
                {
                    "question": task,
                    "base": _sample_entry(base_row),
                    "current": _sample_entry(current_row),
                }
            )

    base_acc = float(base_summary.get("final_accuracy", 0.0))
    current_acc = float(current_summary.get("final_accuracy", 0.0))
    base_tok = float(base_summary.get("total_tokens_avg", 0.0))
    current_tok = float(current_summary.get("total_tokens_avg", 0.0))

    return {
        "base_phase": base_phase,
        "current_phase": current_phase,
        "num_aligned_samples": len(common_tasks),
        "summary_delta": {
            "accuracy_base": base_acc,
            "accuracy_current": current_acc,
            "accuracy_delta": current_acc - base_acc,
            "total_tokens_avg_base": base_tok,
            "total_tokens_avg_current": current_tok,
            "total_tokens_avg_delta": current_tok - base_tok,
        },
        "transitions": transitions,
        "regressions_sample": regressions,
        "improvements_sample": improvements,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build pairwise phase comparison report from raw benchmark outputs."
    )
    parser.add_argument("--base_phase", type=str, required=True)
    parser.add_argument("--current_phase", type=str, required=True)
    parser.add_argument("--base_summary_json", type=str, required=True)
    parser.add_argument("--current_summary_json", type=str, required=True)
    parser.add_argument("--base_raw_json", type=str, required=True)
    parser.add_argument("--current_raw_json", type=str, required=True)
    parser.add_argument("--output_json", type=str, required=True)
    parser.add_argument("--max_examples", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_summary = _load_json(Path(args.base_summary_json))
    current_summary = _load_json(Path(args.current_summary_json))
    base_rows = _load_json(Path(args.base_raw_json))
    current_rows = _load_json(Path(args.current_raw_json))
    if not isinstance(base_rows, list) or not isinstance(current_rows, list):
        raise ValueError("Raw benchmark JSON must be a list.")

    report = build_pairwise_report(
        base_phase=args.base_phase,
        current_phase=args.current_phase,
        base_summary=base_summary,
        current_summary=current_summary,
        base_rows=base_rows,
        current_rows=current_rows,
        max_examples=max(1, int(args.max_examples)),
    )

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(
        f"[PairwiseCompare] {args.base_phase}->{args.current_phase} "
        f"aligned={report['num_aligned_samples']} "
        f"accuracy_delta={report['summary_delta']['accuracy_delta']:.6f}"
    )


if __name__ == "__main__":
    main()
