from pathlib import Path


def download() -> None:
    """Ensure local MMLU directory layout exists.

    The original project expects CSV files under:
      datasets/MMLU/data/dev/*.csv
      datasets/MMLU/data/val/*.csv
    """
    root = Path(__file__).resolve().parent / "data"
    (root / "dev").mkdir(parents=True, exist_ok=True)
    (root / "val").mkdir(parents=True, exist_ok=True)
