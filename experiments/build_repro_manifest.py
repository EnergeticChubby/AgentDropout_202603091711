import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _git_head() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except Exception:
        return ""


def _phase_record(
    *,
    phase: str,
    benchmark_phase_dir: Path,
    svamp_phase_dir: Path,
) -> Dict[str, Any]:
    if phase == "phase2":
        return {
            "phase": phase,
            "status": "skipped",
            "skip_marker_json": str(benchmark_phase_dir / "skipped.json"),
            "skip_marker_txt": str(svamp_phase_dir / "SKIPPED.txt"),
            "skip_json_exists": (benchmark_phase_dir / "skipped.json").exists(),
            "skip_txt_exists": (svamp_phase_dir / "SKIPPED.txt").exists(),
        }

    summary_path = benchmark_phase_dir / "svamp_metrics_summary.json"
    run_config_path = benchmark_phase_dir / "run_config.json"
    compare_prev_path = benchmark_phase_dir / "compare_to_prev.json"
    raw_path = benchmark_phase_dir / "svamp_raw_results.json"
    telemetry_path = benchmark_phase_dir / "telemetry_samples.jsonl"
    svamp_summary_path = svamp_phase_dir / f"{phase}_svamp_summary.json"
    raw_result_files = sorted(svamp_phase_dir.glob("svamp_MiniMax-M2.5_*.json"))

    summary = _load_json(summary_path) or {}
    return {
        "phase": phase,
        "status": "executed",
        "accuracy": summary.get("final_accuracy"),
        "total_tokens_avg": summary.get("total_tokens_avg"),
        "num_samples": summary.get("num_samples"),
        "files": {
            "run_config": str(run_config_path),
            "svamp_raw_results": str(raw_path),
            "svamp_metrics_summary": str(summary_path),
            "compare_to_prev": str(compare_prev_path),
            "telemetry_samples": str(telemetry_path),
            "svamp_summary": str(svamp_summary_path),
            "svamp_raw_result_files": [str(path) for path in raw_result_files],
        },
        "all_required_exists": all(
            path.exists()
            for path in [
                run_config_path,
                raw_path,
                summary_path,
                compare_prev_path,
                telemetry_path,
                svamp_summary_path,
            ]
        )
        and len(raw_result_files) > 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build reproducibility manifest for phase1/3/4 workflow with phase2 skip."
    )
    parser.add_argument("--branch_tag", type=str, default="AdamMartinez6793-v3")
    parser.add_argument(
        "--archive_root",
        type=str,
        default="result/benchmarks",
    )
    parser.add_argument(
        "--svamp_root",
        type=str,
        default="result/SVAMP",
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default=(
            "result/benchmarks/AdamMartinez6793-v3/comparisons/"
            "phase_repro_manifest.json"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    benchmark_root = Path(args.archive_root) / args.branch_tag
    svamp_root = Path(args.svamp_root) / args.branch_tag
    phases = ["phase0", "phase1", "phase2", "phase3", "phase4"]

    manifest: Dict[str, Any] = {
        "branch_tag": args.branch_tag,
        "git_head": _git_head(),
        "workflow_note": "phase2 skipped; reproduced and compared phase1/phase3/phase4",
        "phases": [],
        "comparisons": {
            "phase1_vs_phase3": str(
                benchmark_root / "comparisons" / "phase1_vs_phase3.json"
            ),
            "phase1_vs_phase4": str(
                benchmark_root / "comparisons" / "phase1_vs_phase4.json"
            ),
            "overview": str(
                benchmark_root / "comparisons" / "phase1_phase3_phase4_overview.json"
            ),
            "archive_integrity": str(
                benchmark_root / "comparisons" / "archive_integrity_audit.json"
            ),
        },
    }

    for phase in phases:
        manifest["phases"].append(
            _phase_record(
                phase=phase,
                benchmark_phase_dir=benchmark_root / phase,
                svamp_phase_dir=svamp_root / phase,
            )
        )

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[ReproManifest] wrote {output_path}")


if __name__ == "__main__":
    main()
