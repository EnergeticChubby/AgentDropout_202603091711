#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.append(str(Path(__file__).resolve().parents[1]))
from experiments.validate_protocol_artifacts import validate_with_jsonschema


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def schema_validate(instance_path: Path, schema_path: Path) -> Tuple[bool, str]:
    if not instance_path.exists():
        return False, f"missing instance: {instance_path}"
    if not schema_path.exists():
        return False, f"missing schema: {schema_path}"
    instance = load_json(instance_path)
    schema = load_json(schema_path)
    mode = validate_with_jsonschema(instance, schema)
    return True, mode


def parse_args():
    parser = argparse.ArgumentParser(description="Validate core VG-SVAMP output artifacts.")
    parser.add_argument("--phase_history_json", type=str, default="result/gz10-v3/phase_history.json")
    parser.add_argument("--protocol_summary_json", type=str, default="result/gz10-v3/svamp_protocol_summary.json")
    parser.add_argument("--ablation_summary_json", type=str, default="result/gz10-v3/svamp_ablation_summary.json")
    parser.add_argument("--seed_sweep_summary_json", type=str, default="result/gz10-v3/svamp_seed_sweep_summary.json")
    parser.add_argument("--skip_seed_sweep", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    phase_history_path = Path(args.phase_history_json)
    protocol_path = Path(args.protocol_summary_json)
    ablation_path = Path(args.ablation_summary_json)
    seed_sweep_path = Path(args.seed_sweep_summary_json)

    checks: List[Dict[str, Any]] = []
    failed = False

    # Existence checks
    for key, path in [
        ("phase_history", phase_history_path),
        ("protocol_summary", protocol_path),
        ("ablation_summary", ablation_path),
    ]:
        ok = path.exists()
        checks.append({"check": f"{key}_exists", "ok": ok, "path": str(path)})
        failed = failed or (not ok)

    if not args.skip_seed_sweep:
        ok = seed_sweep_path.exists()
        checks.append({"check": "seed_sweep_exists", "ok": ok, "path": str(seed_sweep_path)})
        failed = failed or (not ok)

    # Phase pass checks
    if phase_history_path.exists():
        phase_history = load_json(phase_history_path)
        if isinstance(phase_history, list):
            for idx, item in enumerate(phase_history):
                passed = bool(item.get("passed", False))
                checks.append({"check": f"phase_{idx}_passed", "ok": passed})
                failed = failed or (not passed)
        else:
            checks.append({"check": "phase_history_type", "ok": False, "detail": "phase_history must be list"})
            failed = True

    # Schema checks
    root = Path("experiments/schemas")
    schema_pairs = [
        (protocol_path, root / "protocol_summary.schema.json", "protocol_schema"),
        (ablation_path, root / "ablation_summary.schema.json", "ablation_schema"),
    ]
    if not args.skip_seed_sweep:
        # no strict schema for seed sweep; check aggregate key
        if seed_sweep_path.exists():
            payload = load_json(seed_sweep_path)
            ok = isinstance(payload, dict) and "runs" in payload
            checks.append({"check": "seed_sweep_structure", "ok": ok})
            failed = failed or (not ok)

    for instance_path, schema_path, check_name in schema_pairs:
        ok, detail = schema_validate(instance_path, schema_path)
        checks.append({"check": check_name, "ok": ok, "detail": detail})
        failed = failed or (not ok)

    result = {"valid": not failed, "checks": checks}
    print(json.dumps(result, indent=2))
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
