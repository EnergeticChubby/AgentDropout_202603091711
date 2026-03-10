import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmark_datasets.mmlu_redux_dataset import DEFAULT_CACHED_SUBJECTS, MMLUReduxDataset


def main():
    dataset = MMLUReduxDataset(split="test", num_shards=1, shard_idx=0, max_samples=None)
    payload = {
        "dataset": "edinburgh-dawg/mmlu-redux",
        "split": "test",
        "subject_count": len(DEFAULT_CACHED_SUBJECTS),
        "subjects": DEFAULT_CACHED_SUBJECTS,
        "num_samples": len(dataset),
        "notes": "Current benchmark loader evaluates all cached subjects in DEFAULT_CACHED_SUBJECTS.",
    }
    out = Path("artifacts/runs/mmlu_redux-dataset-audit.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
