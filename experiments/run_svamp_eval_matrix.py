import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List


DEFAULT_SEEDS = [13]


def parse_args():
    parser = argparse.ArgumentParser(description="Run SVAMP baseline/ablation evaluation matrix.")
    parser.add_argument("--split_root", type=str, default="datasets/SVAMP/splits")
    parser.add_argument("--output_dir", type=str, default="result/Blny-v3/phase5")
    parser.add_argument("--python_bin", type=str, default="/workspace/.venv/bin/python")
    parser.add_argument("--llm_name", type=str, default="MiniMax-M2.5")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--execute", action="store_true", help="Execute commands; default only writes command plan.")
    parser.add_argument("--base_url", type=str, default="https://gpt-agent.cc/v1")
    parser.add_argument("--api_key", type=str, default="")
    parser.add_argument(
        "--config_names",
        nargs="*",
        default=None,
        help="Optional config names to run (subset of matrix_configs names).",
    )
    parser.add_argument(
        "--max_configs",
        type=int,
        default=0,
        help="If >0, only first N selected configs are used.",
    )
    parser.add_argument(
        "--test_filename",
        type=str,
        default="svamp_test_200.json",
        help="Test split filename under each seed directory.",
    )
    parser.add_argument("--batch_size", type=int, default=1, help="Batch size passed to run_svamp.")
    parser.add_argument("--num_iterations", type=int, default=1, help="Training iterations passed to run_svamp.")
    parser.add_argument(
        "--graph_setting",
        type=str,
        default="strict40",
        choices=["strict40", "full720"],
        help="Graph-learning dataset setting passed to run_svamp.",
    )
    parser.add_argument(
        "--graph_train_size",
        type=int,
        default=40,
        help="Graph-learning sample size passed to run_svamp.",
    )
    parser.add_argument(
        "--run_timeout_sec",
        type=int,
        default=0,
        help="Per-run timeout in seconds (0 means no timeout).",
    )
    return parser.parse_args()


def matrix_configs() -> List[Dict]:
    return [
        {"name": "Vanilla", "kind": "baseline", "mode": "DirectAnswer", "agent_nums": [1], "num_rounds": 1},
        {"name": "MASround_T", "kind": "baseline", "mode": "FullConnected", "agent_nums": [5], "num_rounds": 2},
        {"name": "AgentPrune", "kind": "baseline", "mode": "FullConnected", "agent_nums": [5], "num_rounds": 2, "optimized": True},
        {"name": "AgentDropout", "kind": "baseline", "mode": "FullConnected", "agent_nums": [5], "num_rounds": 2, "optimized": True, "diff": True, "dec": True},
        {"name": "AgentDropout_Ours", "kind": "baseline", "mode": "FullConnected", "agent_nums": [5], "num_rounds": 2, "optimized": True, "diff": True, "dec": True, "runtime_control": True},
        {"name": "Ablation_state_only", "kind": "ablation", "mode": "FullConnected", "agent_nums": [5], "num_rounds": 2, "runtime_control": True, "ablation_note": "state_only_scaffold"},
        {"name": "Ablation_barrier_no_intervention", "kind": "ablation", "mode": "FullConnected", "agent_nums": [5], "num_rounds": 2, "runtime_control": True, "ablation_note": "barrier_no_intervention_scaffold"},
        {"name": "Ablation_intervention_no_barrier", "kind": "ablation", "mode": "FullConnected", "agent_nums": [5], "num_rounds": 2, "runtime_control": True, "ablation_note": "intervention_no_barrier_scaffold"},
        {"name": "Ablation_random_intervention", "kind": "ablation", "mode": "FullConnected", "agent_nums": [5], "num_rounds": 2, "runtime_control": True, "ablation_note": "random_intervention_scaffold"},
        {"name": "Ablation_full_method", "kind": "ablation", "mode": "FullConnected", "agent_nums": [5], "num_rounds": 2, "runtime_control": True},
    ]


def build_command(
    python_bin: str,
    cfg: Dict,
    test_split_path: Path,
    llm_name: str,
    phase_tag: str,
    batch_size: int,
    num_iterations: int,
    graph_setting: str,
    graph_train_size: int,
) -> List[str]:
    cmd = [
        python_bin,
        "experiments/run_svamp.py",
        "--dataset_json",
        str(test_split_path),
        "--llm_name",
        llm_name,
        "--mode",
        cfg["mode"],
        "--num_rounds",
        str(cfg["num_rounds"]),
        "--agent_nums",
        *[str(x) for x in cfg["agent_nums"]],
        "--phase_tag",
        phase_tag,
        "--batch_size",
        str(batch_size),
        "--num_iterations",
        str(num_iterations),
        "--node_num_iterations",
        str(num_iterations),
        "--edge_num_iterations",
        str(num_iterations),
        "--graph_setting",
        graph_setting,
        "--graph_train_size",
        str(graph_train_size),
    ]
    if cfg.get("optimized"):
        cmd.extend(["--optimized_spatial", "--optimized_temporal"])
    if cfg.get("diff"):
        cmd.append("--diff")
    if cfg.get("dec"):
        cmd.append("--dec")
    if cfg.get("runtime_control"):
        cmd.append("--enable_runtime_control")
    return cmd


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    split_root = Path(args.split_root)
    configs = matrix_configs()
    if args.config_names:
        selected = set(args.config_names)
        configs = [cfg for cfg in configs if cfg["name"] in selected]
    if args.max_configs > 0:
        configs = configs[: args.max_configs]
    if not configs:
        raise ValueError("No configs selected for evaluation matrix.")

    matrix_plan = []
    run_records = []
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())

    for seed in args.seeds:
        test_split = split_root / f"seed_{seed}" / args.test_filename
        for cfg in configs:
            phase_tag = f"phase5_{cfg['name']}_seed{seed}_{timestamp}"
            command = build_command(
                args.python_bin,
                cfg,
                test_split,
                args.llm_name,
                phase_tag,
                args.batch_size,
                args.num_iterations,
                args.graph_setting,
                args.graph_train_size,
            )
            record = {
                "seed": seed,
                "config": cfg["name"],
                "kind": cfg["kind"],
                "test_split": str(test_split),
                "phase_tag": phase_tag,
                "command": command,
            }
            if "ablation_note" in cfg:
                record["ablation_note"] = cfg["ablation_note"]
            matrix_plan.append(record)

            if not args.execute:
                record["status"] = "planned_only"
                run_records.append(record)
                continue

            log_path = output_dir / f"{phase_tag}.log"
            start = time.time()
            with open(log_path, "w", encoding="utf-8") as log_file:
                run_env = os.environ.copy()
                run_env["MINE_BASE_URL"] = args.base_url
                if args.api_key:
                    run_env["MINE_API_KEYS"] = args.api_key
                try:
                    proc = subprocess.run(
                        command,
                        cwd=Path(__file__).resolve().parents[1],
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        env=run_env,
                        timeout=args.run_timeout_sec if args.run_timeout_sec > 0 else None,
                    )
                    record["status"] = "success" if proc.returncode == 0 else "failed"
                    record["returncode"] = proc.returncode
                except subprocess.TimeoutExpired:
                    record["status"] = "failed_timeout"
                    record["returncode"] = None
                    record["timeout_sec"] = args.run_timeout_sec
            record["duration_sec"] = round(time.time() - start, 3)
            record["log_file"] = str(log_path)
            run_records.append(record)
            print(
                f"[PHASE5-MATRIX] seed={seed} config={cfg['name']} status={record['status']} "
                f"returncode={record.get('returncode')}"
            )

    plan_path = output_dir / "svamp_eval_matrix_plan.json"
    results_path = output_dir / "svamp_eval_matrix_results.json"
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(matrix_plan, f, indent=2, ensure_ascii=False)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(run_records, f, indent=2, ensure_ascii=False)
    print(f"[PHASE5-MATRIX] plan={plan_path}")
    print(f"[PHASE5-MATRIX] results={results_path}")


if __name__ == "__main__":
    main()
