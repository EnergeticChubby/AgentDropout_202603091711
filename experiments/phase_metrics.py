import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build phase benchmark summaries and comparisons.")
    parser.add_argument("--result_json", type=str, required=True, help="Raw result JSON path.")
    parser.add_argument("--phase", type=str, required=True, help="Phase label, e.g., phase0.")
    parser.add_argument("--benchmark", type=str, required=True, help="Benchmark name, e.g., gsm8k/svamp.")
    parser.add_argument("--branch_tag", type=str, default="AdamMartinez6793-v3", help="Branch naming tag.")
    parser.add_argument(
        "--output_root",
        type=str,
        default="result/benchmarks",
        help="Root directory for archived benchmark artifacts.",
    )
    parser.add_argument(
        "--prev_summary_json",
        type=str,
        default="",
        help="Previous phase summary path for comparison.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _safe_mean(values: List[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def build_summary(rows: List[Dict[str, Any]], phase: str, benchmark: str) -> Dict[str, Any]:
    accuracies = [float(item.get("Accuracy", 0.0)) for item in rows if "Accuracy" in item]
    prompt_tokens = [float(item.get("PromptTokens", 0.0)) for item in rows if "PromptTokens" in item]
    completion_tokens = [
        float(item.get("CompletionTokens", 0.0)) for item in rows if "CompletionTokens" in item
    ]

    final_accuracy = accuracies[-1] if accuracies else 0.0
    solved = sum(1 for item in rows if bool(item.get("Solved", False)))
    total = len(rows)

    summary = {
        "phase": phase,
        "benchmark": benchmark,
        "num_records": total,
        "num_solved": solved,
        "final_accuracy": final_accuracy,
        "prompt_tokens_avg": _safe_mean(prompt_tokens),
        "completion_tokens_avg": _safe_mean(completion_tokens),
        "total_tokens_avg": _safe_mean(
            [p + c for p, c in zip(prompt_tokens, completion_tokens)]
        )
        if prompt_tokens and completion_tokens and len(prompt_tokens) == len(completion_tokens)
        else 0.0,
    }
    return summary


def build_comparison(current: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if previous is None:
        return {
            "has_previous": False,
            "metric": "final_accuracy",
            "delta": None,
            "is_improved": True,
            "reason": "No previous phase summary provided.",
        }

    delta = float(current["final_accuracy"]) - float(previous.get("final_accuracy", 0.0))
    return {
        "has_previous": True,
        "metric": "final_accuracy",
        "previous_phase": previous.get("phase", ""),
        "previous_accuracy": float(previous.get("final_accuracy", 0.0)),
        "current_phase": current.get("phase", ""),
        "current_accuracy": float(current.get("final_accuracy", 0.0)),
        "delta": delta,
        "is_improved": delta > 0.0,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    rows = _load_json(Path(args.result_json))
    if not isinstance(rows, list):
        raise ValueError("Result JSON must be a list.")

    summary = build_summary(rows, phase=args.phase, benchmark=args.benchmark)
    prev_summary = _load_json(Path(args.prev_summary_json)) if args.prev_summary_json else None
    comparison = build_comparison(summary, prev_summary)

    archive_dir = Path(args.output_root) / args.branch_tag / args.phase / args.benchmark
    _write_json(archive_dir / "raw_results.json", rows)
    _write_json(archive_dir / "metrics_summary.json", summary)
    _write_json(archive_dir / "compare_to_prev.json", comparison)

    print(
        f"[PhaseMetrics] phase={args.phase} benchmark={args.benchmark} "
        f"final_accuracy={summary['final_accuracy']:.6f} improved={comparison['is_improved']}"
    )


if __name__ == "__main__":
    main()

