#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from experiments.benchmark_compare import compare_phase
from experiments.benchmark_svamp_phase import summarize_phase as summarize_svamp
from experiments.validate_protocol_artifacts import validate_with_jsonschema


def parse_args():
    parser = argparse.ArgumentParser(description="Phase execution gate controller.")
    parser.add_argument("--phases_json", type=str, required=True,
                        help="JSON file listing phases with fields: name, benchmark_type, result_glob")
    parser.add_argument("--output_json", type=str, default="result/gz10-v3/phase_history.json")
    parser.add_argument("--allow_equal", action="store_true")
    parser.add_argument("--plan_path", type=str, default="/opt/cursor/artifacts/PLAN.md")
    parser.add_argument("--default_max_attempts", type=int, default=5)
    parser.add_argument("--schema_json", type=str, default="experiments/schemas/phase_plan.schema.json")
    return parser.parse_args()


def load_phases(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError("phases_json must be a list.")
    return payload


def summarize_phase(phase: Dict[str, Any]) -> Dict[str, Any]:
    benchmark_type = phase.get("benchmark_type", "svamp")
    result_glob = phase["result_glob"]
    phase_name = phase["name"]
    if benchmark_type != "svamp":
        raise ValueError(f"SVAMP-only mode: unsupported benchmark_type={benchmark_type!r}")
    return summarize_svamp(phase_name=phase_name, result_glob=result_glob)


def maybe_read_plan(plan_path: str) -> Dict[str, Any]:
    path = Path(plan_path)
    if not path.exists():
        return {"plan_exists": False, "plan_path": plan_path}
    content = path.read_text(encoding="utf-8")
    return {
        "plan_exists": True,
        "plan_path": plan_path,
        "plan_chars": len(content),
        "plan_lines": len(content.splitlines()),
    }


def run_phase_command(command: str, attempt: int, phase_name: str) -> Dict[str, Any]:
    rendered = command.replace("{attempt}", str(attempt)).replace("{phase}", phase_name)
    proc = subprocess.run(shlex.split(rendered), check=False)
    return {
        "command": rendered,
        "return_code": proc.returncode,
    }


def main():
    args = parse_args()
    phases = load_phases(args.phases_json)
    schema_path = Path(args.schema_json)
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        mode = validate_with_jsonschema(phases, schema)
        print(json.dumps({"phase_plan_schema": str(schema_path), "validation_mode": mode, "valid": True}))
    history: List[Dict[str, Any]] = []
    previous_results_by_type: Dict[str, Optional[str]] = {}
    previous_health_results_by_type: Dict[str, Optional[str]] = {}

    for phase in phases:
        phase_name = phase["name"]
        benchmark_type = phase.get("benchmark_type", "svamp")
        max_attempts = int(phase.get("max_attempts", args.default_max_attempts))
        run_cmds = phase.get("run_cmds", [])
        tasks = phase.get("tasks", [])
        health_result_glob = phase.get("health_result_glob")
        health_benchmark_type = phase.get("health_benchmark_type", "svamp")
        health_allow_equal = bool(phase.get("health_allow_equal", args.allow_equal))

        phase_attempts: List[Dict[str, Any]] = []
        passed = False
        for attempt in range(1, max_attempts + 1):
            plan_info_before = maybe_read_plan(args.plan_path)
            cmd_results = []
            for command in run_cmds:
                cmd_result = run_phase_command(command=command, attempt=attempt, phase_name=phase_name)
                cmd_results.append(cmd_result)
                if cmd_result["return_code"] != 0:
                    break

            # If any command fails, continue to next attempt.
            if any(item["return_code"] != 0 for item in cmd_results):
                attempt_entry = {
                    "attempt": attempt,
                    "tasks": tasks,
                    "plan_info_before": plan_info_before,
                    "commands": cmd_results,
                    "status": "command_failed",
                }
                phase_attempts.append(attempt_entry)
                continue

            summary = summarize_phase(phase)
            comparison = compare_phase(
                current_result=summary["result_file"],
                previous_result=previous_results_by_type.get(benchmark_type),
                strict_greater=not args.allow_equal,
            )
            health_summary = None
            health_comparison = None
            if health_result_glob:
                health_summary = summarize_phase(
                    {
                        "name": f"{phase_name}-health",
                        "benchmark_type": health_benchmark_type,
                        "result_glob": health_result_glob,
                    }
                )
                health_comparison = compare_phase(
                    current_result=health_summary["result_file"],
                    previous_result=previous_health_results_by_type.get(health_benchmark_type),
                    strict_greater=not health_allow_equal,
                )

            phase_passed = comparison["passed"] and (
                True if health_comparison is None else health_comparison["passed"]
            )
            plan_info_after = maybe_read_plan(args.plan_path)
            attempt_entry = {
                "attempt": attempt,
                "tasks": tasks,
                "plan_info_before": plan_info_before,
                "plan_info_after": plan_info_after,
                "commands": cmd_results,
                "summary": summary,
                "comparison": comparison,
                "health_summary": health_summary,
                "health_comparison": health_comparison,
                "status": "passed" if phase_passed else "not_improved",
            }
            phase_attempts.append(attempt_entry)
            print(json.dumps({"phase": phase_name, "attempt": attempt_entry}, indent=2))

            if phase_passed:
                passed = True
                previous_results_by_type[benchmark_type] = summary["result_file"]
                if health_summary is not None:
                    previous_health_results_by_type[health_benchmark_type] = health_summary["result_file"]
                break

        phase_entry = {"phase": phase, "attempts": phase_attempts, "passed": passed}
        history.append(phase_entry)
        if not passed:
            out = Path(args.output_json)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            raise SystemExit(2)

    out = Path(args.output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


if __name__ == "__main__":
    main()
