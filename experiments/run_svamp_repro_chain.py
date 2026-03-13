import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run reproducible SVAMP phase chain (phase1 -> phase3 -> phase4) "
            "with optional phase2 skip semantics, then refresh comparisons and audit."
        )
    )
    parser.add_argument("--branch_tag", type=str, default="AdamMartinez6793-v3")
    parser.add_argument("--llm_name", type=str, default="MiniMax-M2.5")
    parser.add_argument("--base_url", type=str, default="https://gpt-agent.cc/v1")
    parser.add_argument("--api_key", type=str, default="")
    parser.add_argument("--split_dir", type=str, default="data/svamp/split_seed42")
    parser.add_argument("--archive_root", type=str, default="result/benchmarks")
    parser.add_argument("--batch_size", type=int, default=10)
    parser.add_argument("--num_iterations", type=int, default=1)
    parser.add_argument("--num_rounds", type=int, default=2)
    parser.add_argument("--agent_nums", type=int, default=2)
    parser.add_argument("--max_async_time", type=int, default=300)
    parser.add_argument("--pruning_rate", type=float, default=0.1)
    parser.add_argument("--telemetry_sample_limit", type=int, default=100)
    parser.add_argument(
        "--enforce_gate",
        action="store_true",
        help="If set, pass --enforce_phase_gate for phase runs with previous summaries.",
    )
    parser.add_argument(
        "--skip_phase2",
        action="store_true",
        default=True,
        help="If set, route phase3 previous summary to phase1 and keep phase2 skipped.",
    )
    parser.add_argument(
        "--print_only",
        action="store_true",
        help="Print all commands without executing.",
    )
    return parser.parse_args()


def _run(command: List[str], print_only: bool) -> None:
    print("[run_svamp_repro_chain] command:")
    print(" ".join(command))
    if print_only:
        return
    subprocess.run(command, check=True)


def _phase_command(args: argparse.Namespace, phase: str) -> List[str]:
    command: List[str] = [
        sys.executable,
        "experiments/run_svamp_phase.py",
        "--phase",
        phase,
        "--branch_tag",
        args.branch_tag,
        "--llm_name",
        args.llm_name,
        "--base_url",
        args.base_url,
        "--api_key",
        args.api_key,
        "--split_dir",
        args.split_dir,
        "--archive_root",
        args.archive_root,
        "--batch_size",
        str(args.batch_size),
        "--num_iterations",
        str(args.num_iterations),
        "--num_rounds",
        str(args.num_rounds),
        "--agent_nums",
        str(args.agent_nums),
        "--pruning_rate",
        str(args.pruning_rate),
        "--telemetry_sample_limit",
        str(args.telemetry_sample_limit),
    ]

    if args.skip_phase2 and phase == "phase3":
        command.append("--skip_phase2")
    if not args.enforce_gate:
        command.append("--disable_gate_enforcement")

    return command


def _pairwise_command(
    *,
    branch_tag: str,
    archive_root: str,
    current_phase: str,
) -> List[str]:
    base = Path(archive_root) / branch_tag
    return [
        sys.executable,
        "experiments/phase_pairwise_compare.py",
        "--base_phase",
        "phase1",
        "--current_phase",
        current_phase,
        "--base_summary_json",
        str(base / "phase1" / "svamp_metrics_summary.json"),
        "--current_summary_json",
        str(base / current_phase / "svamp_metrics_summary.json"),
        "--base_raw_json",
        str(base / "phase1" / "svamp_raw_results.json"),
        "--current_raw_json",
        str(base / current_phase / "svamp_raw_results.json"),
        "--output_json",
        str(base / "comparisons" / f"phase1_vs_{current_phase}.json"),
        "--max_examples",
        "20",
    ]


def _audit_command(*, branch_tag: str, archive_root: str) -> List[str]:
    benchmark_root = str(Path(archive_root) / branch_tag)
    svamp_root = str(Path("result/SVAMP") / branch_tag)
    comparisons_root = Path(benchmark_root) / "comparisons"
    return [
        sys.executable,
        "experiments/archive_integrity_audit.py",
        "--branch_tag",
        branch_tag,
        "--benchmark_root",
        benchmark_root,
        "--svamp_root",
        svamp_root,
        "--output_json",
        str(comparisons_root / "archive_integrity_audit.json"),
        "--output_md",
        str(comparisons_root / "archive_integrity_audit.md"),
    ]


def main() -> None:
    args = parse_args()

    for phase in ["phase1", "phase3", "phase4"]:
        _run(_phase_command(args, phase), args.print_only)

    _run(
        _pairwise_command(
            branch_tag=args.branch_tag,
            archive_root=args.archive_root,
            current_phase="phase3",
        ),
        args.print_only,
    )
    _run(
        _pairwise_command(
            branch_tag=args.branch_tag,
            archive_root=args.archive_root,
            current_phase="phase4",
        ),
        args.print_only,
    )
    _run(
        _audit_command(branch_tag=args.branch_tag, archive_root=args.archive_root),
        args.print_only,
    )


if __name__ == "__main__":
    main()
