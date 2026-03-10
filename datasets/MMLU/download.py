from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests


DATASET_NAME = "cais/mmlu"
API_BASE = "https://datasets-server.huggingface.co"
LOCAL_ROOT = Path(__file__).resolve().parent / "data"
SPLIT_MAP = {
    "dev": "dev",
    "val": "validation",
    "test": "test",
}


def _api_get(path: str, params: Dict[str, object], timeout: int = 60) -> Dict[str, object]:
    last_error: Optional[Exception] = None
    for attempt in range(5):
        try:
            response = requests.get(f"{API_BASE}{path}", params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            last_error = exc
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code not in {429, 500, 502, 503, 504}:
                raise
            time.sleep(2 ** attempt)
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2 ** attempt)
    if last_error is not None:
        raise last_error
    raise RuntimeError("Unexpected API failure in _api_get without exception.")


def _list_configs() -> List[str]:
    payload = _api_get("/splits", {"dataset": DATASET_NAME})
    configs = sorted({entry["config"] for entry in payload.get("splits", [])})
    return [cfg for cfg in configs if cfg and cfg != "all"]


def _iter_rows(config: str, split: str):
    offset = 0
    page_size = 100
    while True:
        payload = _api_get(
            "/rows",
            {
                "dataset": DATASET_NAME,
                "config": config,
                "split": split,
                "offset": offset,
                "length": page_size,
            },
        )
        rows = payload.get("rows", [])
        if not rows:
            break
        for wrapper in rows:
            row = wrapper.get("row", {})
            choices = row.get("choices", [])
            if len(choices) < 4:
                continue
            answer = row.get("answer")
            try:
                answer_idx = int(answer)
            except Exception:
                continue
            if answer_idx < 0 or answer_idx > 3:
                continue
            yield [
                str(row.get("question", "")),
                str(choices[0]),
                str(choices[1]),
                str(choices[2]),
                str(choices[3]),
                "ABCD"[answer_idx],
            ]
        offset += len(rows)
        if len(rows) < page_size:
            break


def _split_ready(local_split: str) -> bool:
    split_dir = LOCAL_ROOT / local_split
    if not split_dir.exists():
        return False
    csv_files = list(split_dir.glob("*.csv"))
    return len(csv_files) > 0


def download() -> None:
    if all(_split_ready(split_name) for split_name in SPLIT_MAP):
        print("[MMLU] Local CSV files already prepared. Skipping download.")
        return

    configs = _list_configs()
    if not configs:
        raise RuntimeError("No MMLU configs returned from dataset server.")

    for local_split, remote_split in SPLIT_MAP.items():
        split_dir = LOCAL_ROOT / local_split
        split_dir.mkdir(parents=True, exist_ok=True)
        for config in configs:
            csv_path = split_dir / f"{config}.csv"
            if csv_path.exists() and csv_path.stat().st_size > 0:
                continue
            print(f"[MMLU] Downloading config={config} split={remote_split}")
            with csv_path.open("w", encoding="utf-8", newline="") as fp:
                writer = csv.writer(fp)
                for row in _iter_rows(config=config, split=remote_split):
                    writer.writerow(row)
