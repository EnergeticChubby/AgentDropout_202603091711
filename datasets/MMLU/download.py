from pathlib import Path


def download() -> None:
    """
    Compatibility shim for run_mmlu.py.

    This project now expects MMLU files to exist under:
    datasets/MMLU/data/{dev,val,test}/*.csv

    We intentionally do not auto-download here to keep runs deterministic.
    """
    base = Path("datasets/MMLU/data")
    dev_dir = base / "dev"
    val_dir = base / "val"
    if not dev_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(
            "MMLU data directory not found. Expected paths: "
            "datasets/MMLU/data/dev and datasets/MMLU/data/val."
        )
