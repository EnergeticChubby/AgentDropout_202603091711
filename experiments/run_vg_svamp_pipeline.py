#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import shlex
import subprocess
from pathlib import Path
from typing import List


def run_command(command: str, dry_run: bool = False) -> int:
    print(f"$ {command}")
    if dry_run:
        return 0
    proc = subprocess.run(shlex.split(command), check=False)
    return proc.returncode


def parse_args():
    parser = argparse.ArgumentParser(description="Run VG-AgentDropout-SVAMP end-to-end pipeline.")
    parser.add_argument("--python_bin", type=str, default="/workspace/.venv/bin/python")
    parser.add_argument("--phase_plan", type=str, default="experiments/phase_plan.example.json")
    parser.add_argument("--split_dir", type=str, default="datasets/SVAMP/split_seed42")
    parser.add_argument("--svamp_train_json", type=str, default="datasets/SVAMP/train.json")
    parser.add_argument("--svamp_test_json", type=str, default="datasets/SVAMP/test.json")
    parser.add_argument("--skip_api_check", action="store_true")
    parser.add_argument("--phase_history_out", type=str, default="result/gz10-v3/phase_history.json")
    parser.add_argument("--protocol_summary_out", type=str, default="result/gz10-v3/svamp_protocol_summary.json")
    parser.add_argument("--ablation_summary_out", type=str, default="result/gz10-v3/svamp_ablation_summary.json")
    parser.add_argument("--svamp_summary_out", type=str, default="result/gz10-v3/svamp_summary.json")
    parser.add_argument("--seed_sweep_summary_out", type=str, default="result/gz10-v3/svamp_seed_sweep_summary.json")
    parser.add_argument("--final_compare_out", type=str, default="result/gz10-v3/final_outertest_compare.json")
    parser.add_argument("--final_baseline_result_json", type=str, default="")
    parser.add_argument("--final_vg_result_json", type=str, default="")
    parser.add_argument("--llm_name", type=str, default="MiniMax-M2.5")
    parser.add_argument("--run_seed_sweep", action="store_true")
    parser.add_argument("--seed_sweep_seeds", type=str, default="42,3407,2025")
    parser.add_argument("--seed_sweep_phase_prefix", type=str, default="seed_sweep")
    parser.add_argument("--seed_sweep_base_split_dir", type=str, default="datasets/SVAMP")
    parser.add_argument("--seed_sweep_extra_args", type=str, default="")
    parser.add_argument("--validate_outputs", action="store_true")
    parser.add_argument("--report_out_md", type=str, default="result/gz10-v3/vg_svamp_report.md")
    parser.add_argument("--protocol_extra_args", type=str, default="")
    parser.add_argument("--ablation_extra_args", type=str, default="")
    parser.add_argument("--run_mode_ablation", choices=["quick", "all"], default="quick")
    parser.add_argument("--dry_run", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    readiness_cmd = (
        f"{args.python_bin} experiments/check_env_readiness.py "
        f"--svamp_train_json {args.svamp_train_json} --svamp_test_json {args.svamp_test_json} "
    )
    if args.skip_api_check:
        readiness_cmd += "--skip_api_check "

    protocol_cmd = (
        f"{args.python_bin} experiments/run_svamp_protocol.py "
        f"--python_bin {args.python_bin} --split_dir {args.split_dir} --llm_name {args.llm_name} "
        f"--summary_out {args.protocol_summary_out} "
    )
    if args.protocol_extra_args:
        protocol_cmd += f"--extra_args \"{args.protocol_extra_args}\" "

    ablation_cmd = (
        f"{args.python_bin} experiments/run_svamp_ablation.py "
        f"--python_bin {args.python_bin} --split_dir {args.split_dir} --llm_name {args.llm_name} "
        f"--summary_out {args.ablation_summary_out} --run_mode {args.run_mode_ablation} "
    )
    if args.ablation_extra_args:
        ablation_cmd += f"--extra_args \"{args.ablation_extra_args}\" "

    commands: List[str] = [
        readiness_cmd.strip(),
        f"{args.python_bin} experiments/phase_controller.py --phases_json {args.phase_plan} --output_json {args.phase_history_out}",
        protocol_cmd.strip(),
        ablation_cmd.strip(),
        f"{args.python_bin} experiments/summarize_svamp_results.py --output_json {args.svamp_summary_out}",
    ]
    if args.run_seed_sweep:
        sweep_extra = args.seed_sweep_extra_args or args.protocol_extra_args
        sweep_extra_part = f'--extra_args "{sweep_extra}"' if sweep_extra else ""
        commands.append(
            f"{args.python_bin} experiments/run_svamp_seed_sweep.py "
            f"--python_bin {args.python_bin} "
            f"--seeds \"{args.seed_sweep_seeds}\" "
            f"--base_split_dir {args.seed_sweep_base_split_dir} "
            f"--phase_prefix {args.seed_sweep_phase_prefix} "
            f"--llm_name {args.llm_name} --summary_out {args.seed_sweep_summary_out} "
            f"{sweep_extra_part}"
        )
    if args.final_baseline_result_json and args.final_vg_result_json:
        commands.append(
            f"{args.python_bin} experiments/compare_outertest_results.py "
            f"--baseline_result_json {args.final_baseline_result_json} "
            f"--vg_result_json {args.final_vg_result_json} "
            f"--output_json {args.final_compare_out}"
        )
    if args.validate_outputs:
        final_compare_arg = (
            f"--final_compare_json {args.final_compare_out} "
            if (args.final_baseline_result_json and args.final_vg_result_json)
            else ""
        )
        commands.append(
            f"{args.python_bin} experiments/validate_vg_svamp_outputs.py "
            f"--phase_history_json {args.phase_history_out} "
            f"--protocol_summary_json {args.protocol_summary_out} "
            f"--ablation_summary_json {args.ablation_summary_out} "
            f"{'' if args.run_seed_sweep else '--skip_seed_sweep'} "
            f"--seed_sweep_summary_json {args.seed_sweep_summary_out} "
            f"{final_compare_arg}"
        )
        commands.append(
            f"{args.python_bin} experiments/generate_vg_svamp_report.py "
            f"--phase_history_json {args.phase_history_out} "
            f"--protocol_summary_json {args.protocol_summary_out} "
            f"--ablation_summary_json {args.ablation_summary_out} "
            f"--seed_sweep_summary_json {args.seed_sweep_summary_out} "
            f"--overall_summary_json {args.svamp_summary_out} "
            f"{'--final_compare_json ' + args.final_compare_out if (args.final_baseline_result_json and args.final_vg_result_json) else ''} "
            f"--output_md {args.report_out_md}"
        )

    executed = []
    for command in commands:
        code = run_command(command, dry_run=args.dry_run)
        executed.append({"command": command, "return_code": code})
        if code != 0:
            print(json.dumps({"pipeline_status": "failed", "executed": executed}, indent=2))
            raise SystemExit(code)

    print(json.dumps({"pipeline_status": "success", "executed": executed}, indent=2))


if __name__ == "__main__":
    main()
