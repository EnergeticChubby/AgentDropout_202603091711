#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import random
from pathlib import Path
from typing import List, Dict, Any
from urllib.request import urlopen


DEFAULT_URL = "https://raw.githubusercontent.com/arkilpatel/SVAMP/master/SVAMP.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Download and prepare SVAMP train/test files.")
    parser.add_argument("--source_url", type=str, default=DEFAULT_URL)
    parser.add_argument("--output_dir", type=str, default="datasets/SVAMP")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train_ratio", type=float, default=0.8)
    return parser.parse_args()


def download_dataset(source_url: str) -> List[Dict[str, Any]]:
    with urlopen(source_url, timeout=60) as resp:
        data = json.load(resp)
    if not isinstance(data, list):
        raise ValueError("SVAMP payload must be a list of records.")
    required = {"Body", "Question", "Answer"}
    for i, rec in enumerate(data):
        if not required.issubset(rec.keys()):
            raise ValueError(f"Record {i} missing required keys: {required - set(rec.keys())}")
    return data


def split_records(records: List[Dict[str, Any]], seed: int, train_ratio: float):
    if not (0.0 < train_ratio < 1.0):
        raise ValueError("train_ratio must be in (0, 1).")
    idx = list(range(len(records)))
    rng = random.Random(seed)
    rng.shuffle(idx)
    cutoff = int(len(idx) * train_ratio)
    train = [records[i] for i in idx[:cutoff]]
    test = [records[i] for i in idx[cutoff:]]
    return train, test


def main():
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records = download_dataset(args.source_url)
    train, test = split_records(records, seed=args.seed, train_ratio=args.train_ratio)

    full_path = out_dir / "SVAMP.json"
    train_path = out_dir / "train.json"
    test_path = out_dir / "test.json"
    meta_path = out_dir / "prepare_meta.json"

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train, f, ensure_ascii=False, indent=2)
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test, f, ensure_ascii=False, indent=2)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source_url": args.source_url,
                "seed": args.seed,
                "train_ratio": args.train_ratio,
                "total": len(records),
                "train": len(train),
                "test": len(test),
                "files": {
                    "full": str(full_path),
                    "train": str(train_path),
                    "test": str(test_path),
                },
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        json.dumps(
            {
                "status": "ok",
                "total": len(records),
                "train": len(train),
                "test": len(test),
                "meta": str(meta_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
