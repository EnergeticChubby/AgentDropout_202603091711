import argparse
import glob
import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional


def parse_args():
    parser = argparse.ArgumentParser(description="Aggregate SVAMP matrix outputs into required metric scaffold.")
    parser.add_argument(
        "--matrix_results",
        type=str,
        default="result/Blny-v3/phase5/svamp_eval_matrix_results.json",
    )
    parser.add_argument(
        "--result_root",
        type=str,
        default="result/Blny-v3/SVAMP",
        help="Directory containing run_svamp result json files.",
    )
    parser.add_argument(
        "--telemetry_glob",
        type=str,
        default="result/Blny-v3/**/telemetry*.json",
        help="Glob for telemetry json files used for process metrics.",
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default="result/Blny-v3/phase5/svamp_metrics_summary.json",
    )
    return parser.parse_args()


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_result_file(result_root: Path, phase_tag: str) -> Optional[Path]:
    candidates = sorted(result_root.glob(f"*{phase_tag}*.json"))
    return candidates[-1] if candidates else None


def extract_execution_accuracy(result_data: List[Dict]) -> Optional[float]:
    solved_values = [bool(item.get("Solved", False)) for item in result_data if isinstance(item, dict)]
    if not solved_values:
        return None
    return sum(1 for v in solved_values if v) / len(solved_values)


def _safe_mean(values: List[float]) -> Optional[float]:
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _safe_std(values: List[float]) -> Optional[float]:
    values = [v for v in values if v is not None]
    if len(values) < 2:
        return 0.0 if values else None
    return statistics.pstdev(values)


def extract_process_metrics(telemetry_data: List[Dict]) -> Dict[str, Optional[float]]:
    total = len(telemetry_data)
    if total == 0:
        return {
            "Frontier-Crossing Rate": None,
            "Early-Collapse Rate": None,
            "Recovery Cost": None,
            "Wasted Communication Ratio": None,
            "avg_prompt_tokens": None,
            "avg_completion_tokens": None,
            "avg_intervention_count": None,
            "avg_active_agents": None,
            "avg_summary_rollback_count": None,
        }

    frontier_crossings = 0
    early_collapses = 0
    recovery_costs = []
    wasted_ratios = []
    prompt_tokens = []
    completion_tokens = []
    intervention_counts = []
    active_agent_counts = []
    rollback_counts = []

    for record in telemetry_data:
        rounds = record.get("rounds", [])
        barrier_scores = []
        event_counter = 0
        rollback = 0
        intervention = 0
        token_sum_prompt = 0.0
        token_sum_completion = 0.0
        total_messages = 0
        rephrase_like = 0
        for idx, round_item in enumerate(rounds):
            events = round_item.get("events", [])
            event_counter += len(events)
            rollback += sum(1 for e in events if e.get("type") == "SUMMARY_ROLLBACK")
            intervention += sum(1 for e in events if e.get("type") == "INTERVENTION_DECISION")
            rephrase_like += sum(
                1
                for e in events
                if e.get("type") in ("MSG_REPHRASE", "SUMMARY_ROLLBACK")
            )
            tokens = round_item.get("tokens", {})
            token_sum_prompt += float(tokens.get("prompt", 0.0))
            token_sum_completion += float(tokens.get("completion", 0.0))
            total_messages += len(round_item.get("messages", {}))
            state_barrier = round_item.get("messages", {}).get("_runtime_barrier")
            if isinstance(state_barrier, str):
                try:
                    parsed = json.loads(state_barrier)
                    barrier_scores.append(float(parsed.get("barrier_score", 0.0)))
                except Exception:
                    pass
            if isinstance(round_item.get("messages", {}).get("_runtime_state"), str):
                pass
            active_agent_counts.append(len(round_item.get("active_agents", [])))

            if idx < max(1, int(0.3 * max(1, len(rounds)))):
                if any(e.get("type") == "INTERVENTION_DECISION" for e in events):
                    early_collapses += 1

        if barrier_scores and any(score < 0 for score in barrier_scores):
            frontier_crossings += 1
        if intervention > 0:
            recovery_costs.append(float(intervention))
        if total_messages > 0:
            wasted_ratios.append(min(1.0, rephrase_like / total_messages))
        prompt_tokens.append(token_sum_prompt)
        completion_tokens.append(token_sum_completion)
        intervention_counts.append(intervention)
        rollback_counts.append(rollback)

    return {
        "Frontier-Crossing Rate": frontier_crossings / total,
        "Early-Collapse Rate": early_collapses / total,
        "Recovery Cost": _safe_mean(recovery_costs),
        "Wasted Communication Ratio": _safe_mean(wasted_ratios),
        "avg_prompt_tokens": _safe_mean(prompt_tokens),
        "avg_completion_tokens": _safe_mean(completion_tokens),
        "avg_intervention_count": _safe_mean(intervention_counts),
        "avg_active_agents": _safe_mean(active_agent_counts),
        "avg_summary_rollback_count": _safe_mean(rollback_counts),
    }


def load_telemetry_pool(telemetry_glob_pattern: str) -> List[Dict]:
    records = []
    for file_path in glob.glob(telemetry_glob_pattern, recursive=True):
        path = Path(file_path)
        if not path.is_file():
            continue
        try:
            data = load_json(path)
            if isinstance(data, list):
                records.extend(data)
        except Exception:
            continue
    return records


def main():
    args = parse_args()
    matrix_results_path = Path(args.matrix_results)
    if not matrix_results_path.exists():
        raise FileNotFoundError(f"matrix results not found: {matrix_results_path}")

    matrix_results = load_json(matrix_results_path)
    result_root = Path(args.result_root)
    telemetry_pool = load_telemetry_pool(args.telemetry_glob)
    process_metrics_global = extract_process_metrics(telemetry_pool)

    per_run = []
    grouped: Dict[str, List[Dict]] = {}

    for record in matrix_results:
        config = record.get("config", "unknown")
        phase_tag = record.get("phase_tag", "")
        run_summary = dict(record)
        result_file = find_result_file(result_root, phase_tag)
        run_summary["result_file"] = str(result_file) if result_file else None
        if result_file and result_file.exists():
            result_data = load_json(result_file)
            run_summary["Execution Accuracy"] = extract_execution_accuracy(result_data)
            run_summary["result_status"] = "available"
        else:
            run_summary["Execution Accuracy"] = None
            run_summary["result_status"] = "missing"
        per_run.append(run_summary)
        grouped.setdefault(config, []).append(run_summary)

    by_config = {}
    for config, runs in grouped.items():
        accuracies = [r.get("Execution Accuracy") for r in runs]
        by_config[config] = {
            "num_runs": len(runs),
            "Execution Accuracy mean": _safe_mean(accuracies),
            "Execution Accuracy std": _safe_std(accuracies),
            "process_metrics_scaffold": process_metrics_global,
        }

    output = {
        "matrix_results_source": str(matrix_results_path),
        "result_root": str(result_root),
        "telemetry_glob": args.telemetry_glob,
        "per_run": per_run,
        "by_config": by_config,
        "required_metrics_note": {
            "Execution Accuracy": "computed when run result json is available",
            "Frontier-Crossing Rate": "computed from telemetry scaffold data pool",
            "Early-Collapse Rate": "computed from telemetry scaffold data pool",
            "Recovery Cost": "computed from intervention event counts",
            "Wasted Communication Ratio": "computed from rephrase/rollback event proportion",
        },
    }

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[SVAMP-METRICS] output={output_path}")
    print(f"[SVAMP-METRICS] configs={len(by_config)} per_run={len(per_run)}")


if __name__ == "__main__":
    main()
