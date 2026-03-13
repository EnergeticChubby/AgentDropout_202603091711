import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


PHASE_ORDER: List[str] = ["phase0", "phase1", "phase2", "phase3", "phase4"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Strict SVAMP phase runner with fixed split and gate enforcement."
    )
    parser.add_argument("--phase", type=str, required=True, choices=PHASE_ORDER)
    parser.add_argument("--branch_tag", type=str, default="AdamMartinez6793-v3")
    parser.add_argument("--split_dir", type=str, default="data/svamp/split_seed42")
    parser.add_argument("--llm_name", type=str, default="MiniMax-M2.5")
    parser.add_argument("--base_url", type=str, default="https://gpt-agent.cc/v1")
    parser.add_argument("--api_key", type=str, default="")
    parser.add_argument("--batch_size", type=int, default=40)
    parser.add_argument("--num_iterations", type=int, default=2)
    parser.add_argument("--num_rounds", type=int, default=2)
    parser.add_argument("--graph_train_size", type=int, default=40)
    parser.add_argument("--graph_val_size", type=int, default=40)
    parser.add_argument("--pruning_rate", type=float, default=0.10)
    parser.add_argument("--mode", type=str, default="FullConnected")
    parser.add_argument("--agent_nums", type=int, default=5)
    parser.add_argument("--archive_root", type=str, default="result/benchmarks")
    parser.add_argument("--expected_test_size", type=int, default=200)
    parser.add_argument("--telemetry_sample_limit", type=int, default=100)
    parser.add_argument(
        "--skip_phase2",
        action="store_true",
        help="Treat phase2 as skipped when resolving previous-phase summary.",
    )
    parser.add_argument(
        "--disable_gate_enforcement",
        action="store_true",
        help="Do not pass --enforce_phase_gate to run_svamp.",
    )
    parser.add_argument(
        "--previous_phase_override",
        type=str,
        default="",
        help="Optional explicit path to previous phase summary JSON.",
    )
    parser.add_argument("--print_only", action="store_true")
    return parser.parse_args()


def _phase_defaults(phase: str) -> Dict[str, str]:
    # Keep AgentDropout chain flags on for all phases.
    common = {
        "--optimized_spatial": "",
        "--optimized_temporal": "",
        "--diff": "",
        "--dec": "",
    }
    if phase in {"phase0", "phase1"}:
        return {
            **common,
            "--utility_mode": "original",
            "--node_degree_weight": "1.0",
            "--node_correction_weight": "0.0",
            "--node_redundancy_weight": "0.0",
            "--node_wrong_consensus_weight": "0.0",
            "--edge_risk_weight": "0.0",
            "--edge_progress_weight": "0.0",
        }
    if phase == "phase2":
        return {
            **common,
            "--utility_mode": "phase_aware",
            "--node_degree_weight": "1.0",
            "--node_correction_weight": "0.0",
            "--node_redundancy_weight": "0.0",
            "--node_wrong_consensus_weight": "0.0",
            "--edge_risk_weight": "0.0",
            "--edge_progress_weight": "0.0",
        }
    if phase == "phase3":
        return {
            **common,
            "--utility_mode": "phase_aware",
            "--node_degree_weight": "1.0",
            "--node_correction_weight": "1.0",
            "--node_redundancy_weight": "1.0",
            "--node_wrong_consensus_weight": "1.0",
            "--edge_risk_weight": "0.0",
            "--edge_progress_weight": "0.0",
        }
    # phase4
    return {
        **common,
        "--utility_mode": "phase_aware",
        "--node_degree_weight": "1.0",
        "--node_correction_weight": "1.0",
        "--node_redundancy_weight": "1.0",
        "--node_wrong_consensus_weight": "1.0",
        "--edge_risk_weight": "0.2",
        "--edge_progress_weight": "0.2",
    }


def _previous_phase_summary(args: argparse.Namespace) -> str:
    if args.previous_phase_override:
        return args.previous_phase_override
    idx = PHASE_ORDER.index(args.phase)
    if idx == 0:
        return ""
    prev_phase = PHASE_ORDER[idx - 1]
    if args.skip_phase2 and args.phase == "phase3":
        prev_phase = "phase1"
    prev_path = (
        Path(args.archive_root)
        / args.branch_tag
        / prev_phase
        / "svamp_metrics_summary.json"
    )
    return str(prev_path)


def _build_command(args: argparse.Namespace) -> List[str]:
    cmd: List[str] = [
        sys.executable,
        "experiments/run_svamp.py",
        "--agent_nums",
        str(args.agent_nums),
        "--mode",
        args.mode,
        "--batch_size",
        str(args.batch_size),
        "--num_iterations",
        str(args.num_iterations),
        "--num_rounds",
        str(args.num_rounds),
        "--pruning_rate",
        str(args.pruning_rate),
        "--llm_name",
        args.llm_name,
        "--base_url",
        args.base_url,
        "--api_key",
        args.api_key,
        "--use_split_data",
        "--split_dir",
        args.split_dir,
        "--eval_split_file",
        "test.json",
        "--phase_gate_strict",
        "--expected_test_size",
        str(args.expected_test_size),
        "--graph_train_size",
        str(args.graph_train_size),
        "--graph_val_size",
        str(args.graph_val_size),
        "--phase_label",
        args.phase,
        "--branch_tag",
        args.branch_tag,
        "--archive_root",
        args.archive_root,
        "--telemetry_sample_limit",
        str(args.telemetry_sample_limit),
    ]

    prev_summary = _previous_phase_summary(args)
    if prev_summary:
        cmd.extend(["--previous_phase_summary", prev_summary])
        if not args.disable_gate_enforcement:
            cmd.append("--enforce_phase_gate")

    defaults = _phase_defaults(args.phase)
    for flag, value in defaults.items():
        cmd.append(flag)
        if value != "":
            cmd.append(value)
    return cmd


def main() -> None:
    args = parse_args()
    cmd = _build_command(args)
    print("[run_svamp_phase] command:")
    print(" ".join(cmd))
    if args.print_only:
        return
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
