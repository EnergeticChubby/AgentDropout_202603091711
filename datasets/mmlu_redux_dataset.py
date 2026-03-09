from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


DATASET_NAME = "edinburgh-dawg/mmlu-redux"
API_BASE = "https://datasets-server.huggingface.co"


@dataclass
class MMLUReduxRecord:
    subject: str
    question: str
    choices: List[str]
    answer_idx: int

    @property
    def answer_letter(self) -> str:
        return "ABCD"[self.answer_idx]

    def to_input(self) -> Dict[str, str]:
        return {
            "task": (
                f"{self.question}\n"
                f"Option A: {self.choices[0]}\n"
                f"Option B: {self.choices[1]}\n"
                f"Option C: {self.choices[2]}\n"
                f"Option D: {self.choices[3]}\n"
            )
        }


def _get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def list_subjects(dataset_name: str = DATASET_NAME) -> List[str]:
    payload = _get_json(f"{API_BASE}/splits", params={"dataset": dataset_name})
    return sorted({entry["config"] for entry in payload["splits"]})


def load_subject_rows(
    subject: str,
    dataset_name: str = DATASET_NAME,
    split: str = "test",
    limit: Optional[int] = None,
) -> List[MMLUReduxRecord]:
    offset = 0
    page_size = 100
    collected: List[MMLUReduxRecord] = []
    while True:
        if limit is not None and len(collected) >= limit:
            return collected[:limit]
        length = page_size if limit is None else min(page_size, limit - len(collected))
        payload = _get_json(
            f"{API_BASE}/rows",
            params={
                "dataset": dataset_name,
                "config": subject,
                "split": split,
                "offset": offset,
                "length": length,
            },
        )
        rows = payload.get("rows", [])
        if not rows:
            break
        for row_wrapper in rows:
            row = row_wrapper["row"]
            choices = row["choices"]
            if len(choices) < 4:
                continue
            collected.append(
                MMLUReduxRecord(
                    subject=subject,
                    question=row["question"],
                    choices=choices[:4],
                    answer_idx=int(row["answer"]),
                )
            )
        offset += len(rows)
        if len(rows) < length:
            break
    return collected


def load_mmlu_redux(
    split: str = "test",
    subject_limit: Optional[int] = None,
    questions_per_subject: Optional[int] = None,
    dataset_name: str = DATASET_NAME,
) -> List[MMLUReduxRecord]:
    subjects = list_subjects(dataset_name=dataset_name)
    if subject_limit is not None:
        subjects = subjects[:subject_limit]

    records: List[MMLUReduxRecord] = []
    for subject in subjects:
        records.extend(
            load_subject_rows(
                subject=subject,
                dataset_name=dataset_name,
                split=split,
                limit=questions_per_subject,
            )
        )
    return records

