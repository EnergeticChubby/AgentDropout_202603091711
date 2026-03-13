#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple


def _load_json_records(path: Path) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _write_jsonl(path: Path, records: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _combine_dataset(train_path: Path, test_path: Path) -> List[Dict]:
    train_records = _load_json_records(train_path)
    test_records = _load_json_records(test_path)
    return train_records + test_records


def _split_outer(records: List[Dict], seed: int, train_ratio: float = 0.8) -> Tuple[List[int], List[int]]:
    ids = list(range(len(records)))
    rng = random.Random(seed)
    rng.shuffle(ids)
    train_size = math.floor(train_ratio * len(ids))
    return ids[:train_size], ids[train_size:]


def _split_inner(train_ids: List[int], seed: int, train_ratio: float = 0.9) -> Tuple[List[int], List[int]]:
    ids = list(train_ids)
    rng = random.Random(seed)
    rng.shuffle(ids)
    inner_train_size = math.floor(train_ratio * len(ids))
    return ids[:inner_train_size], ids[inner_train_size:]


def _gather(records: List[Dict], indices: List[int]) -> List[Dict]:
    return [records[i] for i in indices]


def parse_args():
    parser = argparse.ArgumentParser(description="Create fixed SVAMP 8:2 split with inner validation split.")
    parser.add_argument(
        "--svamp_train_json",
        type=str,
        default="datasets/SVAMP/train.json",
        help="Path to original SVAMP train.json",
    )
    parser.add_argument(
        "--svamp_test_json",
        type=str,
        default="datasets/SVAMP/test.json",
        help="Path to original SVAMP test.json",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed for deterministic splitting.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="datasets/SVAMP/split_seed42",
        help="Directory to store split artifacts.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    train_path = Path(args.svamp_train_json)
    test_path = Path(args.svamp_test_json)
    output_dir = Path(args.output_dir)

    all_records = _combine_dataset(train_path, test_path)

    outer_train_ids, outer_test_ids = _split_outer(all_records, seed=args.seed, train_ratio=0.8)
    inner_train_ids, inner_val_ids = _split_inner(outer_train_ids, seed=args.seed, train_ratio=0.9)

    outer_train_records = _gather(all_records, outer_train_ids)
    inner_train_records = _gather(all_records, inner_train_ids)
    inner_val_records = _gather(all_records, inner_val_ids)
    outer_test_records = _gather(all_records, outer_test_ids)

    _write_json(output_dir / f"svamp_train_ids_seed{args.seed}.json", outer_train_ids)
    _write_json(output_dir / f"svamp_test_ids_seed{args.seed}.json", outer_test_ids)
    _write_json(output_dir / f"svamp_inner_train_ids_seed{args.seed}.json", inner_train_ids)
    _write_json(output_dir / f"svamp_inner_val_ids_seed{args.seed}.json", inner_val_ids)

    _write_jsonl(output_dir / "svamp_train.jsonl", inner_train_records)
    _write_jsonl(output_dir / "svamp_val.jsonl", inner_val_records)
    _write_jsonl(output_dir / "svamp_test.jsonl", outer_test_records)
    _write_json(output_dir / "svamp_train.json", outer_train_records)
    _write_json(output_dir / "svamp_val.json", inner_val_records)
    _write_json(output_dir / "svamp_test.json", outer_test_records)

    split_meta = {
        "seed": args.seed,
        "created_at": time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()),
        "source": {
            "train_json": str(train_path),
            "test_json": str(test_path),
        },
        "counts": {
            "total": len(all_records),
            "outer_train": len(outer_train_records),
            "inner_train": len(inner_train_records),
            "inner_val": len(inner_val_records),
            "outer_test": len(outer_test_records),
        },
        "ratios": {
            "outer_train": 0.8,
            "outer_test": 0.2,
            "inner_train_of_outer_train": 0.9,
            "inner_val_of_outer_train": 0.1,
        },
        "stratified": False,
    }
    _write_json(output_dir / "split_meta.json", split_meta)

    print(json.dumps(split_meta, indent=2))


if __name__ == "__main__":
    main()
