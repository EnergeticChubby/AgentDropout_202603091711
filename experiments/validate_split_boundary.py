import argparse
import json
from pathlib import Path
from typing import Dict, List, Set


DEFAULT_SEEDS = [13, 17, 23, 42, 3407]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate SVAMP split boundaries and detect test leakage."
    )
    parser.add_argument("--split_root", type=str, default="datasets/SVAMP/splits")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument(
        "--check_files",
        nargs="*",
        default=[],
        help="Optional JSON artifact files to verify do not include test IDs.",
    )
    return parser.parse_args()


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sample_id(sample: Dict, fallback_idx: int) -> str:
    return str(sample.get("id", fallback_idx))


def collect_ids(samples: List[Dict]) -> Set[str]:
    ids = set()
    for i, item in enumerate(samples):
        ids.add(sample_id(item, i))
    return ids


def collect_question_keys(samples: List[Dict]) -> Set[str]:
    keys = set()
    for item in samples:
        body = str(item.get("Body", "")).strip()
        question_part = str(item.get("Question") or item.get("question") or item.get("task", "")).strip()
        question = f"{body} {question_part}".strip()
        if question:
            keys.add(question)
    return keys


def validate_seed(seed_dir: Path) -> Dict:
    train = load_json(seed_dir / "svamp_train_720.json")
    val = load_json(seed_dir / "svamp_val_80.json")
    test = load_json(seed_dir / "svamp_test_200.json")

    train_ids = collect_ids(train)
    val_ids = collect_ids(val)
    test_ids = collect_ids(test)

    train_q = collect_question_keys(train)
    val_q = collect_question_keys(val)
    test_q = collect_question_keys(test)

    errors = []
    if len(train) != 720:
        errors.append(f"train size expected 720, got {len(train)}")
    if len(val) != 80:
        errors.append(f"val size expected 80, got {len(val)}")
    if len(test) != 200:
        errors.append(f"test size expected 200, got {len(test)}")

    if train_ids & val_ids:
        errors.append(f"train/val ID overlap: {len(train_ids & val_ids)}")
    if train_ids & test_ids:
        errors.append(f"train/test ID overlap: {len(train_ids & test_ids)}")
    if val_ids & test_ids:
        errors.append(f"val/test ID overlap: {len(val_ids & test_ids)}")

    # secondary content-level overlap check
    if train_q & test_q:
        errors.append(f"train/test question overlap: {len(train_q & test_q)}")
    if val_q & test_q:
        errors.append(f"val/test question overlap: {len(val_q & test_q)}")

    return {
        "seed_dir": str(seed_dir),
        "counts": {"train": len(train), "val": len(val), "test": len(test)},
        "ok": not errors,
        "errors": errors,
        "test_ids": sorted(test_ids),
    }


def extract_artifact_ids(payload) -> Set[str]:
    ids = set()
    if isinstance(payload, list):
        for idx, item in enumerate(payload):
            if isinstance(item, dict):
                ids.add(str(item.get("problem_id", item.get("id", idx))))
    elif isinstance(payload, dict):
        for key in ("problem_id", "id"):
            if key in payload:
                ids.add(str(payload[key]))
    return ids


def main():
    args = parse_args()
    split_root = Path(args.split_root)
    if not split_root.exists():
        raise FileNotFoundError(f"split_root not found: {split_root}")

    reports = []
    all_test_ids = set()
    for seed in args.seeds:
        seed_dir = split_root / f"seed_{seed}"
        if not seed_dir.exists():
            raise FileNotFoundError(f"seed split dir missing: {seed_dir}")
        report = validate_seed(seed_dir)
        reports.append(report)
        all_test_ids.update(report["test_ids"])
        print(
            f"[SPLIT-BOUNDARY] seed={seed} ok={report['ok']} "
            f"counts={report['counts']} errors={len(report['errors'])}"
        )

    artifact_reports = []
    for path_str in args.check_files:
        path = Path(path_str)
        payload = load_json(path)
        artifact_ids = extract_artifact_ids(payload)
        leaked = sorted(artifact_ids & all_test_ids)
        artifact_report = {
            "artifact": str(path),
            "checked_ids": len(artifact_ids),
            "leaked_test_ids": leaked,
            "ok": len(leaked) == 0,
        }
        artifact_reports.append(artifact_report)
        print(
            f"[LEAK-CHECK] artifact={path} checked={len(artifact_ids)} leaked={len(leaked)}"
        )

    output = {
        "split_root": str(split_root),
        "seed_reports": reports,
        "artifact_reports": artifact_reports,
        "all_ok": all(r["ok"] for r in reports) and all(r["ok"] for r in artifact_reports),
    }
    output_path = split_root / "boundary_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"[SPLIT-BOUNDARY] report={output_path} all_ok={output['all_ok']}")

    if not output["all_ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
