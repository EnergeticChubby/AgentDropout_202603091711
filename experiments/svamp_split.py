import argparse
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create fixed SVAMP 80/20 split and graph subsets.")
    parser.add_argument(
        "--input_json",
        type=str,
        default="datasets/SVAMP/all.json",
        help="Path to SVAMP full dataset JSON list.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/svamp/split_seed42",
        help="Output directory for split artifacts.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for one-time split.")
    parser.add_argument("--train_ratio", type=float, default=0.8, help="Train split ratio.")
    parser.add_argument("--graph_train_size", type=int, default=40, help="Graph training subset size.")
    parser.add_argument("--graph_val_size", type=int, default=40, help="Graph validation subset size.")
    return parser.parse_args()


def _load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"SVAMP source not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"SVAMP source must be a JSON list, got: {type(data).__name__}")
    return data


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _split_train_test(
    records: List[Dict[str, Any]], train_ratio: float, seed: int
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rng = random.Random(seed)
    idxs = list(range(len(records)))
    rng.shuffle(idxs)
    train_size = int(len(records) * train_ratio)
    train_idxs = idxs[:train_size]
    test_idxs = idxs[train_size:]
    train = [records[i] for i in train_idxs]
    test = [records[i] for i in test_idxs]
    return train, test


def _sample_subsets(
    train: List[Dict[str, Any]], graph_train_size: int, graph_val_size: int, seed: int
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    if len(train) < graph_train_size + graph_val_size:
        raise ValueError(
            f"train size {len(train)} < graph_train+graph_val "
            f"({graph_train_size + graph_val_size})"
        )
    rng = random.Random(seed)
    idxs = list(range(len(train)))
    rng.shuffle(idxs)
    graph_train_idxs = set(idxs[:graph_train_size])
    graph_val_idxs = set(idxs[graph_train_size : graph_train_size + graph_val_size])
    unused_idxs = [i for i in idxs if i not in graph_train_idxs and i not in graph_val_idxs]

    graph_train = [train[i] for i in sorted(graph_train_idxs)]
    graph_val = [train[i] for i in sorted(graph_val_idxs)]
    unused_train = [train[i] for i in unused_idxs]
    return graph_train, graph_val, unused_train


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_json)
    output_dir = Path(args.output_dir)

    records = _load_json(input_path)
    train, test = _split_train_test(records, train_ratio=args.train_ratio, seed=args.seed)
    graph_train, graph_val, unused_train = _sample_subsets(
        train,
        graph_train_size=args.graph_train_size,
        graph_val_size=args.graph_val_size,
        seed=args.seed,
    )

    _write_json(output_dir / "train.json", train)
    _write_json(output_dir / "test.json", test)
    _write_json(output_dir / f"graph_train_{args.graph_train_size}.json", graph_train)
    _write_json(output_dir / f"graph_val_{args.graph_val_size}.json", graph_val)
    _write_json(output_dir / "unused_train.json", unused_train)

    summary = {
        "seed": args.seed,
        "train_ratio": args.train_ratio,
        "train_size": len(train),
        "test_size": len(test),
        "graph_train_size": len(graph_train),
        "graph_val_size": len(graph_val),
        "unused_train_size": len(unused_train),
        "input_json": str(input_path),
        "output_dir": str(output_dir),
    }
    _write_json(output_dir / "split_summary.json", summary)

    print(
        "[SVAMP Split] "
        f"seed={summary['seed']} train={summary['train_size']} test={summary['test_size']} "
        f"graph_train={summary['graph_train_size']} graph_val={summary['graph_val_size']}"
    )


if __name__ == "__main__":
    main()

