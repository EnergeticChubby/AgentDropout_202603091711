import argparse
import json
import sys
from pathlib import Path
from typing import Iterable


def _prepare_hf_import():
    repo_root = Path(__file__).resolve().parents[1]
    sys.path = [p for p in sys.path if p not in ("", str(repo_root))]
    from datasets import load_dataset  # type: ignore
    sys.path.append(str(repo_root))
    return load_dataset


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bootstrap SVAMP and GSM8K datasets into repository-expected paths."
    )
    parser.add_argument("--svamp_output_dir", type=str, default="datasets/SVAMP")
    parser.add_argument("--gsm8k_output_dir", type=str, default="datasets/gsm8k")
    parser.add_argument("--svamp_repo_id", type=str, default="ChilleD/SVAMP")
    parser.add_argument("--gsm8k_repo_id", type=str, default="gsm8k")
    parser.add_argument("--gsm8k_config", type=str, default="main")
    parser.add_argument("--download_svamp", action="store_true", default=True)
    parser.add_argument("--download_gsm8k", action="store_true", default=True)
    return parser.parse_args()


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_jsonl(path: Path, data: Iterable[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    args = parse_args()
    load_dataset = _prepare_hf_import()

    if args.download_svamp:
        svamp_train = load_dataset(args.svamp_repo_id, split="train")
        svamp_test = load_dataset(args.svamp_repo_id, split="test")
        svamp_dir = Path(args.svamp_output_dir)
        write_json(svamp_dir / "train.json", [dict(x) for x in svamp_train])
        write_json(svamp_dir / "test.json", [dict(x) for x in svamp_test])
        write_json(
            svamp_dir / "SVAMP.json",
            [dict(x) for x in svamp_train] + [dict(x) for x in svamp_test],
        )
        print(
            f"[DATASET-BOOTSTRAP] SVAMP train={len(svamp_train)} test={len(svamp_test)} "
            f"-> {svamp_dir}"
        )

    if args.download_gsm8k:
        gsm8k_train = load_dataset(args.gsm8k_repo_id, args.gsm8k_config, split="train")
        gsm8k_test = load_dataset(args.gsm8k_repo_id, args.gsm8k_config, split="test")
        gsm8k_dir = Path(args.gsm8k_output_dir)
        write_jsonl(gsm8k_dir / "train.jsonl", [dict(x) for x in gsm8k_train])
        write_jsonl(gsm8k_dir / "gsm8k.jsonl", [dict(x) for x in gsm8k_test])
        print(
            f"[DATASET-BOOTSTRAP] GSM8K train={len(gsm8k_train)} test={len(gsm8k_test)} "
            f"-> {gsm8k_dir}"
        )


if __name__ == "__main__":
    main()
