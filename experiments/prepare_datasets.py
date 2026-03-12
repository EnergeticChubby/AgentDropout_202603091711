import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _import_hf_datasets():
    # Avoid local `/workspace/datasets` package shadowing HuggingFace `datasets`.
    project_root = str(Path(__file__).resolve().parents[1])
    original_sys_path = list(sys.path)
    try:
        sys.path = [p for p in sys.path if p not in ("", project_root)]
        from datasets import load_dataset  # type: ignore
    finally:
        sys.path = original_sys_path
    return load_dataset


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def prepare_svamp(load_dataset, output_root: Path) -> Dict[str, int]:
    ds = load_dataset("ChilleD/SVAMP")
    train_rows = [dict(item) for item in ds["train"]]
    test_rows = [dict(item) for item in ds["test"]]
    all_rows = train_rows + test_rows

    _write_json(output_root / "data/svamp/svamp_all.json", all_rows)
    _write_json(output_root / "datasets/SVAMP/train.json", train_rows)
    _write_json(output_root / "datasets/SVAMP/test.json", test_rows)
    return {
        "svamp_train": len(train_rows),
        "svamp_test": len(test_rows),
        "svamp_all": len(all_rows),
    }


def prepare_gsm8k(load_dataset, output_root: Path) -> Dict[str, int]:
    ds = load_dataset("openai/gsm8k", "main")
    train_rows = [dict(item) for item in ds["train"]]
    test_rows = [dict(item) for item in ds["test"]]

    _write_jsonl(output_root / "datasets/gsm8k/train.jsonl", train_rows)
    _write_jsonl(output_root / "datasets/gsm8k/gsm8k.jsonl", test_rows)
    return {
        "gsm8k_train": len(train_rows),
        "gsm8k_test": len(test_rows),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare local dataset files (SVAMP by default, optional GSM8K)."
    )
    parser.add_argument(
        "--output_root",
        type=str,
        default=".",
        help="Workspace root for writing datasets (default current dir).",
    )
    parser.add_argument("--skip_svamp", action="store_true")
    parser.add_argument(
        "--with_gsm8k",
        action="store_true",
        help="Also download/export GSM8K files (default: disabled).",
    )
    # Backward-compatible alias; prefer --with_gsm8k for new usage.
    parser.add_argument("--skip_gsm8k", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dataset = _import_hf_datasets()
    output_root = Path(args.output_root).resolve()
    stats: Dict[str, int] = {}

    if not args.skip_svamp:
        stats.update(prepare_svamp(load_dataset, output_root))
    should_prepare_gsm8k = args.with_gsm8k and not args.skip_gsm8k
    if should_prepare_gsm8k:
        stats.update(prepare_gsm8k(load_dataset, output_root))

    summary_path = output_root / "data" / "dataset_prepare_summary.json"
    _write_json(
        summary_path,
        {
            "workspace": str(output_root),
            **stats,
        },
    )
    print(f"[prepare_datasets] {json.dumps(stats)}")
    print(f"[prepare_datasets] summary={summary_path}")


if __name__ == "__main__":
    main()

