import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from sklearn.model_selection import train_test_split


OP_MAP = {
    "+": "add",
    "-": "sub",
    "*": "mul",
    "/": "div",
}
DEFAULT_SEEDS = [13, 17, 23, 42, 3407]
PLACEHOLDER_QUESTION_RE = re.compile(r"^Q\d+\?$")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare SVAMP 800/200 + 720/80 stratified splits."
    )
    parser.add_argument("--input_json", type=str, default="datasets/SVAMP/SVAMP.json")
    parser.add_argument("--train_json", type=str, default="datasets/SVAMP/train.json")
    parser.add_argument("--test_json", type=str, default="datasets/SVAMP/test.json")
    parser.add_argument("--output_dir", type=str, default="datasets/SVAMP/splits")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--outer_train_size", type=int, default=800)
    parser.add_argument("--outer_test_size", type=int, default=200)
    parser.add_argument("--inner_train_size", type=int, default=720)
    parser.add_argument("--inner_val_size", type=int, default=80)
    parser.add_argument(
        "--allow_noncanonical_source",
        action="store_true",
        help="Allow non-SVAMP/placeholder-like sources (disabled by default).",
    )
    return parser.parse_args()


def load_json(path: Path) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected list data in {path}")
    return data


def load_svamp_dataset(args) -> Tuple[List[Dict], str]:
    input_path = Path(args.input_json)
    if input_path.exists():
        return load_json(input_path), str(input_path)

    train_path = Path(args.train_json)
    test_path = Path(args.test_json)
    if train_path.exists() and test_path.exists():
        merged = load_json(train_path) + load_json(test_path)
        return merged, f"{train_path}+{test_path}"

    raise FileNotFoundError(
        "SVAMP source data not found. Provide --input_json or valid --train_json/--test_json."
    )


def normalize_question(sample: Dict) -> str:
    body = str(sample.get("Body") or sample.get("body") or "").strip()
    question = str(sample.get("Question") or sample.get("question") or "").strip()
    return f"{body} {question}".strip()


def assert_real_svamp_source(samples: List[Dict], data_source: str, allow_noncanonical_source: bool):
    if allow_noncanonical_source:
        return
    if len(samples) != 1000:
        raise ValueError(
            f"Expected canonical SVAMP size 1000, got {len(samples)} from {data_source}. "
            "Pass --allow_noncanonical_source to bypass."
        )

    suspicious = []
    for idx, sample in enumerate(samples):
        body = str(sample.get("Body") or sample.get("body") or "").strip()
        question = str(sample.get("Question") or sample.get("question") or "").strip()
        if body == "Body" or PLACEHOLDER_QUESTION_RE.match(question):
            suspicious.append({"idx": idx, "Body": body, "Question": question})
            if len(suspicious) >= 5:
                break

    if suspicious:
        raise ValueError(
            "Detected placeholder-like SVAMP samples (e.g., 'Body' / 'Qxxx?'). "
            f"Source={data_source}, examples={suspicious}. "
            "Pass --allow_noncanonical_source to bypass."
        )

    usable_questions = sum(1 for sample in samples if len(normalize_question(sample)) > 20)
    if usable_questions < int(0.95 * len(samples)):
        raise ValueError(
            f"Suspicious SVAMP source quality from {data_source}: "
            f"{usable_questions}/{len(samples)} questions exceed 20 chars."
        )


def infer_operator_fields(sample: Dict) -> Tuple[int, str]:
    equation = str(
        sample.get("Equation")
        or sample.get("equation")
        or sample.get("Formula")
        or sample.get("formula")
        or ""
    )
    operators = re.findall(r"[+\-*/]", equation)
    operator_count = len(operators)
    if operator_count <= 1:
        normalized_count = 1
    else:
        normalized_count = 2

    if not operators:
        operator_type = "mixed"
    else:
        mapped = [OP_MAP.get(op, "mixed") for op in operators]
        unique_types = set(mapped)
        operator_type = mapped[0] if len(unique_types) == 1 else "mixed"

    return normalized_count, operator_type


def enrich_samples(samples: List[Dict]) -> List[Dict]:
    enriched = []
    for idx, item in enumerate(samples):
        sample = dict(item)
        operator_count, operator_type = infer_operator_fields(sample)
        sample["id"] = str(sample.get("id", idx))
        sample["operator_count"] = int(sample.get("operator_count", operator_count))
        sample["operator_type"] = str(sample.get("operator_type", operator_type))
        enriched.append(sample)
    return enriched


def make_strat_labels(samples: List[Dict]) -> List[str]:
    return [f"{s['operator_count']}|{s['operator_type']}" for s in samples]


def rebalance_rare_labels(labels: List[str]) -> List[str]:
    counts = Counter(labels)
    return [label if counts[label] >= 2 else "rare" for label in labels]


def robust_stratify_labels(labels: List[str]) -> List[str] | None:
    balanced = rebalance_rare_labels(labels)
    counts = Counter(balanced)
    if not counts:
        return None
    if len(counts) < 2:
        return None
    if min(counts.values()) < 2:
        return None
    return balanced


def split_once(
    samples: List[Dict],
    seed: int,
    outer_train_size: int,
    outer_test_size: int,
    inner_train_size: int,
    inner_val_size: int,
):
    if len(samples) != outer_train_size + outer_test_size:
        raise ValueError(
            f"SVAMP size mismatch: expected {outer_train_size + outer_test_size}, got {len(samples)}"
        )
    if outer_train_size != inner_train_size + inner_val_size:
        raise ValueError(
            f"Inner split mismatch: outer_train={outer_train_size}, "
            f"inner_train+inner_val={inner_train_size + inner_val_size}"
        )

    labels = robust_stratify_labels(make_strat_labels(samples))
    indices = list(range(len(samples)))
    train_pool_idx, test_idx = train_test_split(
        indices,
        train_size=outer_train_size,
        test_size=outer_test_size,
        random_state=seed,
        shuffle=True,
        stratify=labels,
    )

    train_pool = [samples[i] for i in train_pool_idx]
    train_pool_labels = robust_stratify_labels(make_strat_labels(train_pool))
    train_idx_local, val_idx_local = train_test_split(
        list(range(len(train_pool))),
        train_size=inner_train_size,
        test_size=inner_val_size,
        random_state=seed,
        shuffle=True,
        stratify=train_pool_labels,
    )

    train_idx = [train_pool_idx[i] for i in train_idx_local]
    val_idx = [train_pool_idx[i] for i in val_idx_local]

    train = [samples[i] for i in train_idx]
    val = [samples[i] for i in val_idx]
    test = [samples[i] for i in test_idx]

    return (
        train,
        val,
        test,
        train_idx,
        val_idx,
        test_idx,
        labels is not None,
        train_pool_labels is not None,
    )


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def summarize_split(split_name: str, split_data: List[Dict]) -> Dict:
    op_counts = Counter(s["operator_count"] for s in split_data)
    op_types = Counter(s["operator_type"] for s in split_data)
    return {
        "name": split_name,
        "size": len(split_data),
        "operator_count_distribution": dict(sorted(op_counts.items())),
        "operator_type_distribution": dict(sorted(op_types.items())),
    }


def main():
    args = parse_args()
    random.seed(0)

    raw_samples, data_source = load_svamp_dataset(args)
    assert_real_svamp_source(raw_samples, data_source, args.allow_noncanonical_source)
    samples = enrich_samples(raw_samples)

    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    all_seed_meta = []

    for seed in args.seeds:
        (
            train,
            val,
            test,
            train_idx,
            val_idx,
            test_idx,
            outer_stratified,
            inner_stratified,
        ) = split_once(
            samples=samples,
            seed=seed,
            outer_train_size=args.outer_train_size,
            outer_test_size=args.outer_test_size,
            inner_train_size=args.inner_train_size,
            inner_val_size=args.inner_val_size,
        )

        seed_dir = output_root / f"seed_{seed}"
        write_json(seed_dir / "svamp_train_720.json", train)
        write_json(seed_dir / "svamp_val_80.json", val)
        write_json(seed_dir / "svamp_test_200.json", test)

        split_meta = {
            "seed": seed,
            "data_source": data_source,
            "stratify_fields": ["operator_count", "operator_type"],
            "stratify_status": {
                "outer_split_stratified": outer_stratified,
                "inner_split_stratified": inner_stratified,
            },
            "counts": {
                "total": len(samples),
                "outer_train_pool": len(train) + len(val),
                "outer_test": len(test),
                "inner_train": len(train),
                "inner_val": len(val),
            },
            "index_splits": {
                "train_indices": train_idx,
                "val_indices": val_idx,
                "test_indices": test_idx,
            },
            "split_summaries": [
                summarize_split("train", train),
                summarize_split("val", val),
                summarize_split("test", test),
            ],
        }
        write_json(seed_dir / "split_meta.json", split_meta)
        all_seed_meta.append(
            {
                "seed": seed,
                "output_dir": str(seed_dir),
                "counts": split_meta["counts"],
            }
        )
        print(
            f"[SVAMP-SPLIT] seed={seed} train={len(train)} val={len(val)} test={len(test)} "
            f"-> {seed_dir}"
        )

    write_json(
        output_root / "split_manifest.json",
        {
            "protocol": "SVAMP 800/200 + 720/80",
            "seeds": args.seeds,
            "items": all_seed_meta,
        },
    )
    print(f"[SVAMP-SPLIT] manifest={output_root / 'split_manifest.json'}")


if __name__ == "__main__":
    main()
