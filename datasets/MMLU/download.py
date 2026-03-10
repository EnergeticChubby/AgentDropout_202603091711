import csv
from pathlib import Path
from typing import Dict

from datasets import load_dataset


SPLIT_MAP: Dict[str, str] = {
    "dev": "dev",
    "validation": "val",
    "test": "test",
}


def _label_from_index(index: int) -> str:
    if index not in (0, 1, 2, 3):
        return "A"
    return ["A", "B", "C", "D"][index]


def download() -> None:
    data_root = Path("datasets/MMLU/data")
    for output_split in SPLIT_MAP.values():
        (data_root / output_split).mkdir(parents=True, exist_ok=True)

    for source_split, output_split in SPLIT_MAP.items():
        dataset = load_dataset("cais/mmlu", "all", split=source_split)
        grouped_rows: Dict[str, list] = {}
        for record in dataset:
            subject = record["subject"]
            choices = record["choices"]
            row = [
                record["question"],
                choices[0],
                choices[1],
                choices[2],
                choices[3],
                _label_from_index(int(record["answer"])),
            ]
            grouped_rows.setdefault(subject, []).append(row)

        split_dir = data_root / output_split
        for subject, rows in grouped_rows.items():
            output_csv = split_dir / f"{subject}.csv"
            with output_csv.open("w", encoding="utf-8", newline="") as fp:
                writer = csv.writer(fp)
                writer.writerows(rows)

    print(
        {
            "dataset": "cais/mmlu",
            "output_root": str(data_root),
            "splits": SPLIT_MAP,
            "status": "ok",
        }
    )


if __name__ == "__main__":
    download()
