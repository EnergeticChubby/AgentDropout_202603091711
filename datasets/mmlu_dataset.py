import glob
import pandas as pd
from typing import Union, List, Literal, Any, Dict
import numpy as np
from abc import ABC
from pathlib import Path
import requests
import time

class MMLUDataset(ABC):
    def __init__(self,
        split: str,
        dataset_name: str = "edinburgh-dawg/mmlu-redux",
        num_shards: int = 1,
        shard_idx: int = 0,
        max_records: int | None = None,
        ) -> None:

        self._split = split
        self._dataset_name = dataset_name
        self._num_shards = max(1, int(num_shards))
        self._shard_idx = int(shard_idx)
        if self._shard_idx < 0 or self._shard_idx >= self._num_shards:
            raise ValueError("shard_idx must be in [0, num_shards).")
        self._records: List[Dict[str, Any]] = self._load_data(dataset_name, split, max_records=max_records)
        self._records = self._records[self._shard_idx::self._num_shards]

    @staticmethod
    def get_domain() -> str:
        return 'mmlu'

    @staticmethod
    def _load_data_legacy(
        data_path: str,
    ) -> List[Dict[str, Any]]:

        rng = np.random.default_rng(888)

        csv_paths = glob.glob(data_path + "*.csv")
        csv_paths = sorted(csv_paths)
        print("Number of topics: ", len(csv_paths))

        names = ['question', 'A', 'B', 'C', 'D', 'correct_answer']

        total_df = pd.DataFrame(columns=names)
        for path in csv_paths:
            single_df = pd.read_csv(path, header=None,
                            names=names,encoding='utf-8')
            total_df = pd.concat([total_df, single_df])

        total_df = total_df.reset_index(drop=True)

        # Pseudorandom shuffle
        total_df = total_df.reindex(rng.permutation(total_df.index))

        print("Total number of questions: ", len(total_df))

        return total_df.to_dict("records")

    @classmethod
    def _record_to_standard(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        question = record.get("question", "")
        options = None
        if all(key in record for key in ["A", "B", "C", "D"]):
            options = [record["A"], record["B"], record["C"], record["D"]]
        elif "choices" in record and isinstance(record["choices"], (list, tuple)) and len(record["choices"]) >= 4:
            options = list(record["choices"][:4])
        elif "options" in record and isinstance(record["options"], (list, tuple)) and len(record["options"]) >= 4:
            options = list(record["options"][:4])
        else:
            option_keys = [k for k in sorted(record.keys()) if k.lower().startswith("option")]
            if len(option_keys) >= 4:
                options = [record[option_keys[i]] for i in range(4)]
        if options is None:
            raise ValueError(f"Cannot parse options from record keys: {list(record.keys())}")

        answer_raw = record.get("correct_answer", record.get("answer", record.get("label", "")))
        if isinstance(answer_raw, (int, np.integer)):
            correct_answer = "ABCD"[int(answer_raw)]
        else:
            correct_answer = str(answer_raw).strip()
            if len(correct_answer) > 0 and correct_answer[0] in "ABCD":
                correct_answer = correct_answer[0]
            elif correct_answer in options:
                correct_answer = "ABCD"[options.index(correct_answer)]
            else:
                try:
                    idx = int(correct_answer)
                    correct_answer = "ABCD"[idx]
                except Exception:
                    correct_answer = "A"

        return {
            "question": str(question),
            "A": str(options[0]),
            "B": str(options[1]),
            "C": str(options[2]),
            "D": str(options[3]),
            "correct_answer": correct_answer,
        }

    @classmethod
    def _load_data_hf_api(cls, dataset_name: str, split: str, max_records: int | None = None) -> List[Dict[str, Any]]:
        splits_url = "https://datasets-server.huggingface.co/splits"
        rows_url = "https://datasets-server.huggingface.co/rows"
        split_resp = requests.get(splits_url, params={"dataset": dataset_name}, timeout=30)
        split_resp.raise_for_status()
        split_payload = split_resp.json()
        configs = sorted({item["config"] for item in split_payload["splits"] if item["split"] == split})
        if not configs:
            raise ValueError(f"No configs found for dataset={dataset_name} split={split}")

        records: List[Dict[str, Any]] = []
        page_size = 100
        for config in configs:
            offset = 0
            while True:
                rows_resp = requests.get(
                    rows_url,
                    params={
                        "dataset": dataset_name,
                        "config": config,
                        "split": split,
                        "offset": offset,
                        "length": page_size,
                    },
                    timeout=30,
                )
                rows_resp.raise_for_status()
                rows_payload = rows_resp.json()
                rows = rows_payload.get("rows", [])
                if not rows:
                    break
                for item in rows:
                    records.append(cls._record_to_standard(item["row"]))
                    if max_records is not None and len(records) >= max_records:
                        return records
                offset += page_size
                total = rows_payload.get("num_rows_total", offset)
                if offset >= total:
                    break
                time.sleep(0.05)
        return records

    def _load_data(self, dataset_name: str, split: str, max_records: int | None = None) -> List[Dict[str, Any]]:
        local_path = Path(f"datasets/MMLU/data/{split}/")
        if dataset_name in {"mmlu", "legacy-mmlu", "local-mmlu"} and local_path.exists():
            return self._load_data_legacy(str(local_path))
        if dataset_name == "edinburgh-dawg/mmlu-redux":
            return self._load_data_hf_api(dataset_name, split, max_records=max_records)
        # fallback: try HF dataset first, then legacy local path.
        try:
            return self._load_data_hf_api(dataset_name, split, max_records=max_records)
        except Exception:
            if local_path.exists():
                return self._load_data_legacy(str(local_path))
            raise

    @property
    def split(self) -> str:
        return self._split

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        record = self._records[index]
        assert isinstance(record, dict)
        return record

    @staticmethod
    def record_to_input(record: Dict[str, Any]) -> Dict[str, Any]:
        demo_question = (
            f"{record['question']}\n"
            f"Option A: {record['A']}\n"
            f"Option B: {record['B']}\n"
            f"Option C: {record['C']}\n"
            f"Option D: {record['D']}\n"
            )
        input_dict = {"task": demo_question}
        return input_dict

    def postprocess_answer(self, answer: Union[str, List[str]]) -> str:
        if isinstance(answer, list):
            if len(answer) > 0:
                answer = answer[0]
            else:
                answer = ""
        if not isinstance(answer, str):
            raise Exception("Expected string")
        if len(answer) > 0:
            ans_pos = answer.find("answer is")
            if ans_pos != -1:
                answer = answer[ans_pos+len("answer is"):].strip(":").strip().strip("Option").strip()
            answer = answer[0] # Try to format the answer by taking the first letter
        return answer

    @staticmethod
    def record_to_target_answer(record: Dict[str, Any]) -> str:
        correct_answer = record['correct_answer']
        assert isinstance(correct_answer, str), (
            f"String expected but got {correct_answer} "
            f"of type {type(correct_answer)} (2)" \
            f" record={record}")
        return correct_answer
