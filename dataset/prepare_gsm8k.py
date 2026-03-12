#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path
from urllib.request import urlopen


TRAIN_URL = "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/train.jsonl"
TEST_URL = "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl"


def parse_args():
    parser = argparse.ArgumentParser(description="Download GSM8K train/test jsonl files.")
    parser.add_argument("--train_url", type=str, default=TRAIN_URL)
    parser.add_argument("--test_url", type=str, default=TEST_URL)
    parser.add_argument("--output_dir", type=str, default="datasets/gsm8k")
    return parser.parse_args()


def download_text(url: str) -> str:
    with urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8")


def count_jsonl_rows(payload: str) -> int:
    return len([line for line in payload.splitlines() if line.strip()])


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_raw = download_text(args.train_url)
    test_raw = download_text(args.test_url)

    train_path = output_dir / "train.jsonl"
    test_path = output_dir / "test.jsonl"
    meta_path = output_dir / "prepare_meta.json"

    train_path.write_text(train_raw, encoding="utf-8")
    test_path.write_text(test_raw, encoding="utf-8")

    payload = {
        "status": "ok",
        "train_rows": count_jsonl_rows(train_raw),
        "test_rows": count_jsonl_rows(test_raw),
        "train_url": args.train_url,
        "test_url": args.test_url,
        "output": {
            "train_jsonl": str(train_path),
            "test_jsonl": str(test_path),
            "meta_json": str(meta_path),
        },
    }
    meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
