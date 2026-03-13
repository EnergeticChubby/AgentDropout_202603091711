import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_SCHEMA_FILES = [
    "run_config.json",
    "svamp_raw_results.json",
    "svamp_metrics_summary.json",
    "compare_to_prev.json",
    "telemetry_samples.jsonl",
]


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _phase_info(
    *,
    phase: str,
    benchmark_phase_dir: Path,
    svamp_phase_dir: Path,
) -> Dict[str, Any]:
    if phase == "phase2":
        return {
            "status": "skipped",
            "benchmarks_dir_exists": benchmark_phase_dir.exists(),
            "svamp_dir_exists": svamp_phase_dir.exists(),
            "skip_marker_json_exists": (benchmark_phase_dir / "skipped.json").exists(),
            "skip_marker_txt_exists": (svamp_phase_dir / "SKIPPED.txt").exists(),
        }

    info: Dict[str, Any] = {
        "status": "executed",
        "benchmarks_dir_exists": benchmark_phase_dir.exists(),
        "svamp_dir_exists": svamp_phase_dir.exists(),
        "schema_files": {
            filename: (benchmark_phase_dir / filename).exists()
            for filename in EXPECTED_SCHEMA_FILES
        },
    }

    summary_path = benchmark_phase_dir / "svamp_metrics_summary.json"
    summary = _load_json(summary_path)
    if isinstance(summary, dict):
        info["final_accuracy"] = summary.get("final_accuracy")
        info["total_tokens_avg"] = summary.get("total_tokens_avg")
        info["num_samples"] = summary.get("num_samples")

    raw_files = sorted(svamp_phase_dir.glob("svamp_MiniMax-M2.5_*.json"))
    info["raw_result_files"] = [path.name for path in raw_files]
    info["svamp_summary_exists"] = (svamp_phase_dir / f"{phase}_svamp_summary.json").exists()
    return info


def _chain_evidence(log_path: Path) -> Dict[str, Any]:
    if not log_path.exists():
        return {
            "log_file": str(log_path),
            "stage_updates_last": None,
            "chain_check_last": None,
            "stage_updates_count": 0,
            "chain_check_count": 0,
        }
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    stage_matches = re.findall(
        r"\[STAGE UPDATES\]\s+node_stage_updates=(\d+)\s+edge_stage_updates=(\d+)",
        text,
    )
    chain_matches = re.findall(r"\[CHAIN CHECK\]\s+(\{[^\n]+\})", text)

    stage_last = None
    if stage_matches:
        node_updates, edge_updates = stage_matches[-1]
        stage_last = {
            "node_stage_updates": int(node_updates),
            "edge_stage_updates": int(edge_updates),
        }

    chain_last = None
    if chain_matches:
        try:
            chain_last = json.loads(chain_matches[-1])
        except Exception:
            chain_last = {"raw": chain_matches[-1]}

    return {
        "log_file": str(log_path),
        "stage_updates_last": stage_last,
        "chain_check_last": chain_last,
        "stage_updates_count": len(stage_matches),
        "chain_check_count": len(chain_matches),
    }


def build_audit(
    *,
    branch_tag: str,
    benchmark_root: Path,
    svamp_root: Path,
    phases: List[str],
    phase_log_map: Dict[str, Path],
) -> Dict[str, Any]:
    audit: Dict[str, Any] = {
        "branch_tag": branch_tag,
        "expected_schema_files": EXPECTED_SCHEMA_FILES,
        "phases": {},
    }
    for phase in phases:
        audit["phases"][phase] = _phase_info(
            phase=phase,
            benchmark_phase_dir=benchmark_root / phase,
            svamp_phase_dir=svamp_root / phase,
        )

    audit["chain_integrity_evidence"] = {
        phase: _chain_evidence(log_path) for phase, log_path in phase_log_map.items()
    }
    return audit


def write_markdown(audit: Dict[str, Any], path: Path, phases: List[str]) -> None:
    lines: List[str] = ["# Archive Integrity Audit", ""]
    for phase in phases:
        info = audit["phases"][phase]
        lines.append(f"## {phase}")
        lines.append(f"- status: {info['status']}")
        if info["status"] == "executed":
            lines.append(f"- accuracy: {info.get('final_accuracy')}")
            lines.append(f"- total_tokens_avg: {info.get('total_tokens_avg')}")
            missing = [k for k, v in info.get("schema_files", {}).items() if not v]
            lines.append(f"- missing_schema_files: {missing if missing else 'none'}")
        else:
            lines.append(
                f"- skip_json: {info.get('skip_marker_json_exists')}, "
                f"skip_txt: {info.get('skip_marker_txt_exists')}"
            )
        lines.append("")

    lines.append("## Chain integrity evidence (last seen)")
    lines.append("")
    for phase in ["phase1", "phase3", "phase4"]:
        evidence = audit.get("chain_integrity_evidence", {}).get(phase, {})
        lines.append(
            f"- {phase}: stage={evidence.get('stage_updates_last')}, "
            f"chain={evidence.get('chain_check_last')}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify phase archive schema completeness and chain-check evidence."
    )
    parser.add_argument("--branch_tag", type=str, default="AdamMartinez6793-v3")
    parser.add_argument(
        "--benchmark_root",
        type=str,
        default="result/benchmarks/AdamMartinez6793-v3",
    )
    parser.add_argument(
        "--svamp_root",
        type=str,
        default="result/SVAMP/AdamMartinez6793-v3",
    )
    parser.add_argument(
        "--phases",
        type=str,
        default="phase0,phase1,phase2,phase3,phase4",
        help="Comma-separated phase list in audit order.",
    )
    parser.add_argument(
        "--phase1_log",
        type=str,
        default="/home/ubuntu/.cursor/projects/workspace/terminals/893217.txt",
    )
    parser.add_argument(
        "--phase3_log",
        type=str,
        default="/home/ubuntu/.cursor/projects/workspace/terminals/816087.txt",
    )
    parser.add_argument(
        "--phase4_log",
        type=str,
        default="/home/ubuntu/.cursor/projects/workspace/terminals/831942.txt",
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default="result/benchmarks/AdamMartinez6793-v3/comparisons/archive_integrity_audit.json",
    )
    parser.add_argument(
        "--output_md",
        type=str,
        default="result/benchmarks/AdamMartinez6793-v3/comparisons/archive_integrity_audit.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    phases = [phase.strip() for phase in args.phases.split(",") if phase.strip()]
    phase_log_map = {
        "phase1": Path(args.phase1_log),
        "phase3": Path(args.phase3_log),
        "phase4": Path(args.phase4_log),
    }
    audit = build_audit(
        branch_tag=args.branch_tag,
        benchmark_root=Path(args.benchmark_root),
        svamp_root=Path(args.svamp_root),
        phases=phases,
        phase_log_map=phase_log_map,
    )

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)

    write_markdown(audit, Path(args.output_md), phases)
    print(
        f"[ArchiveIntegrityAudit] branch={args.branch_tag} "
        f"phases={len(phases)} output={output_json}"
    )


if __name__ == "__main__":
    main()
