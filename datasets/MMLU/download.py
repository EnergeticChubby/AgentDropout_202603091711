from __future__ import annotations

import csv
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

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
    for attempt in range(8):
        try:
            response = requests.get(f"{API_BASE}{path}", params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            last_error = exc
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code not in {429, 500, 502, 503, 504}:
                raise
            if status_code == 429:
                time.sleep(min(20 * (attempt + 1), 120))
            else:
                time.sleep(min(2 ** attempt, 120))
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(min(2 ** attempt, 120))
    if last_error is not None:
        raise last_error
    raise RuntimeError("Unexpected API failure in _api_get without exception.")


def _list_configs_by_split() -> Dict[str, Set[str]]:
    payload = _api_get("/splits", {"dataset": DATASET_NAME})
    config_to_splits: Dict[str, Set[str]] = {}
    for entry in payload.get("splits", []):
        config = entry.get("config")
        split = entry.get("split")
        if not config or config == "all" or not split:
            continue
        config_to_splits.setdefault(config, set()).add(split)
    return config_to_splits


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


def _split_ready(local_split: str, expected_configs: List[str]) -> bool:
    split_dir = LOCAL_ROOT / local_split
    sentinel = split_dir / ".complete"
    if not split_dir.exists() or not sentinel.exists():
        return False
    csv_files = sorted(split_dir.glob("*.csv"))
    if len(csv_files) != len(expected_configs):
        return False
    return all(path.stat().st_size > 0 for path in csv_files)


def download() -> None:
    configs_by_split = _list_configs_by_split()
    if not configs_by_split:
        raise RuntimeError("No MMLU configs returned from dataset server.")

    for local_split, remote_split in SPLIT_MAP.items():
        configs = sorted([cfg for cfg, splits in configs_by_split.items() if remote_split in splits])
        if not configs:
            continue

        if _split_ready(local_split=local_split, expected_configs=configs):
            print(f"[MMLU] Local split '{local_split}' already complete. Skipping.")
            continue

        split_dir = LOCAL_ROOT / local_split
        if split_dir.exists():
            shutil.rmtree(split_dir)
        split_dir.mkdir(parents=True, exist_ok=True)
        for config in configs:
            csv_path = split_dir / f"{config}.csv"
            tmp_path = split_dir / f"{config}.csv.part"
            print(f"[MMLU] Downloading config={config} split={remote_split}")
            with tmp_path.open("w", encoding="utf-8", newline="") as fp:
                writer = csv.writer(fp)
                for row in _iter_rows(config=config, split=remote_split):
                    writer.writerow(row)
            if tmp_path.stat().st_size == 0:
                tmp_path.unlink(missing_ok=True)
                continue
            tmp_path.replace(csv_path)
        (split_dir / ".complete").write_text("ok\n", encoding="utf-8")
