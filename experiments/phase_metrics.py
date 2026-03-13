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
    parser.add_argument(
        "--run_config_json",
        type=str,
        default="",
        help="Optional run config json to archive (phase_gate layout).",
    )
    parser.add_argument(
        "--output_layout",
        type=str,
        default="legacy",
        choices=["legacy", "phase_gate"],
        help="legacy: write benchmark/raw/metrics files under benchmark subdir. "
             "phase_gate: write run_config/svamp_* schema under phase dir.",
    )
    parser.add_argument(
        "--telemetry_sample_limit",
        type=int,
        default=100,
        help="How many telemetry rows to keep in telemetry_samples.jsonl for phase_gate layout.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _safe_mean(values: List[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _count_surviving_nodes(round_answer: Dict[str, Any]) -> int:
    survivors = 0
    for _, outputs in (round_answer or {}).items():
        output_list = outputs if isinstance(outputs, list) else [outputs]
        if any(str(item).strip() != "None." for item in output_list):
            survivors += 1
    return survivors


def build_summary(rows: List[Dict[str, Any]], phase: str, benchmark: str) -> Dict[str, Any]:
    accuracies = [float(item.get("Accuracy", 0.0)) for item in rows if "Accuracy" in item]
    prompt_tokens = [float(item.get("PromptTokens", 0.0)) for item in rows if "PromptTokens" in item]
    completion_tokens = [
        float(item.get("CompletionTokens", 0.0)) for item in rows if "CompletionTokens" in item
    ]

    final_accuracy = accuracies[-1] if accuracies else 0.0
    solved = sum(1 for item in rows if bool(item.get("Solved", False)))
    total = len(rows)
    phase_distribution: Dict[str, int] = {}
    wrong_consensus = 0
    redundancy = 0
    unresolved = 0
    round1_node_survival: List[float] = []
    round2_node_survival: List[float] = []
    round1_edge_survival: List[float] = []
    round2_edge_survival: List[float] = []
    for row in rows:
        phase_label = row.get("PhaseLabel", "unknown")
        phase_distribution[phase_label] = phase_distribution.get(phase_label, 0) + 1
        if phase_label == "wrong_consensus_lock":
            wrong_consensus += 1
        if phase_label == "redundant_paraphrase":
            redundancy += 1
        if phase_label == "unresolved_conflict":
            unresolved += 1
        all_answers = row.get("All_answers", [])
        if len(all_answers) >= 1 and isinstance(all_answers[0], dict):
            round1_node_survival.append(float(_count_surviving_nodes(all_answers[0])))
        if len(all_answers) >= 2 and isinstance(all_answers[1], dict):
            round2_node_survival.append(float(_count_surviving_nodes(all_answers[1])))
        edge_stats = row.get("EdgeStats", [])
        if len(edge_stats) >= 1 and isinstance(edge_stats[0], dict):
            round1_edge_survival.append(
                float(sum(payload.get("progress", 0.0) for payload in edge_stats[0].values()))
            )
        if len(edge_stats) >= 2 and isinstance(edge_stats[1], dict):
            round2_edge_survival.append(
                float(sum(payload.get("progress", 0.0) for payload in edge_stats[1].values()))
            )

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
        "phase_distribution": phase_distribution,
        "wrong_consensus_rate": (wrong_consensus / total) if total else 0.0,
        "redundancy_rate": (redundancy / total) if total else 0.0,
        "conflict_unresolved_rate": (unresolved / total) if total else 0.0,
        "avg_surviving_nodes_round1": _safe_mean(round1_node_survival),
        "avg_surviving_nodes_round2": _safe_mean(round2_node_survival),
        "avg_surviving_intra_edges": _safe_mean(round1_edge_survival),
        "avg_surviving_inter_edges": _safe_mean(round2_edge_survival),
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

    current_acc = float(current["final_accuracy"])
    previous_acc = float(previous.get("final_accuracy", 0.0))
    delta = current_acc - previous_acc
    current_tokens = float(current.get("total_tokens_avg", 0.0))
    previous_tokens = float(previous.get("total_tokens_avg", 0.0))
    token_improved = previous_tokens > 0 and current_tokens > 0 and current_tokens < previous_tokens
    is_improved = delta > 0.0 or (delta == 0.0 and token_improved)

    reason = "accuracy_improved" if delta > 0.0 else (
        "accuracy_tied_token_reduced" if (delta == 0.0 and token_improved) else "not_improved"
    )
    return {
        "has_previous": True,
        "metric": "final_accuracy",
        "previous_phase": previous.get("phase", ""),
        "previous_accuracy": previous_acc,
        "current_phase": current.get("phase", ""),
        "current_accuracy": current_acc,
        "delta": delta,
        "previous_total_tokens_avg": previous_tokens,
        "current_total_tokens_avg": current_tokens,
        "token_delta": current_tokens - previous_tokens,
        "is_improved": is_improved,
        "reason": reason,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    rows = _load_json(Path(args.result_json))
    if not isinstance(rows, list):
        raise ValueError("Result JSON must be a list.")

    summary = build_summary(rows, phase=args.phase, benchmark=args.benchmark)
    prev_summary = _load_json(Path(args.prev_summary_json)) if args.prev_summary_json else None
    comparison = build_comparison(summary, prev_summary)
    output_root = Path(args.output_root)

    if args.output_layout == "legacy":
        archive_dir = output_root / args.branch_tag / args.phase / args.benchmark
        _write_json(archive_dir / "raw_results.json", rows)
        _write_json(archive_dir / "metrics_summary.json", summary)
        _write_json(archive_dir / "compare_to_prev.json", comparison)
    else:
        archive_dir = output_root / args.branch_tag / args.phase
        run_config: Dict[str, Any] = {}
        if args.run_config_json:
            run_config = _load_json(Path(args.run_config_json))
        _write_json(archive_dir / "run_config.json", run_config)
        _write_json(archive_dir / "svamp_raw_results.json", rows)
        _write_json(archive_dir / "svamp_metrics_summary.json", summary)
        _write_json(archive_dir / "compare_to_prev.json", comparison)
        telemetry_rows: List[Dict[str, Any]] = []
        for row in rows[: max(0, int(args.telemetry_sample_limit))]:
            telemetry_rows.append(
                {
                    "Question": row.get("Question"),
                    "Answer": row.get("Answer"),
                    "Attempt answer": row.get("Attempt answer"),
                    "Solved": row.get("Solved"),
                    "PhaseLabel": row.get("PhaseLabel"),
                    "PhaseMetrics": row.get("PhaseMetrics"),
                    "NodeStats": row.get("NodeStats", []),
                    "EdgeStats": row.get("EdgeStats", []),
                    "PromptTokens": row.get("PromptTokens"),
                    "CompletionTokens": row.get("CompletionTokens"),
                }
            )
        _write_jsonl(archive_dir / "telemetry_samples.jsonl", telemetry_rows)

    print(
        f"[PhaseMetrics] phase={args.phase} benchmark={args.benchmark} "
        f"final_accuracy={summary['final_accuracy']:.6f} improved={comparison['is_improved']}"
    )


if __name__ == "__main__":
    main()

