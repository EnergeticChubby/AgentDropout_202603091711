from __future__ import annotations

from typing import Any, Dict, List, Optional

from datasets import concatenate_datasets, get_dataset_config_names, load_dataset


class MMLUReduxDataset:
    def __init__(
        self,
        split: str = "test",
        num_shards: int = 1,
        shard_idx: int = 0,
        max_samples: Optional[int] = None,
        subjects: Optional[List[str]] = None,
    ) -> None:
        if num_shards <= 0:
            raise ValueError("num_shards must be > 0")
        if shard_idx < 0 or shard_idx >= num_shards:
            raise ValueError("shard_idx out of range")

        config_names = subjects or get_dataset_config_names("edinburgh-dawg/mmlu-redux")
        dataset_parts = [
            load_dataset("edinburgh-dawg/mmlu-redux", name=config_name, split=split)
            for config_name in config_names
        ]
        dataset = concatenate_datasets(dataset_parts)
        dataset = dataset.shard(num_shards=num_shards, index=shard_idx, contiguous=True)
        if max_samples is not None:
            dataset = dataset.select(range(min(max_samples, len(dataset))))
        self._dataset = dataset
        self.split = split
        self.num_shards = num_shards
        self.shard_idx = shard_idx

    def __len__(self) -> int:
        return len(self._dataset)

    def __iter__(self):
        return iter(self._dataset)

    def __getitem__(self, index: int):
        return self._dataset[index]

    @staticmethod
    def record_to_input(record: Dict[str, Any]) -> Dict[str, str]:
        options = record.get("choices") or record.get("options")
        if not options:
            raise ValueError("MMLU-Redux record missing choices/options")

        option_labels = ["A", "B", "C", "D"]
        option_lines = [f"Option {label}: {text}" for label, text in zip(option_labels, options)]
        prompt = f"{record['question']}\n" + "\n".join(option_lines)
        return {"task": prompt}

    @staticmethod
    def record_to_target_answer(record: Dict[str, Any]) -> str:
        answer = record.get("answer")
        if isinstance(answer, str):
            cleaned = answer.strip().upper()
            if cleaned in {"A", "B", "C", "D"}:
                return cleaned
        if isinstance(answer, int):
            if 0 <= answer <= 3:
                return ["A", "B", "C", "D"][answer]
        raise ValueError(f"Unsupported answer format: {answer}")

    @staticmethod
    def postprocess_answer(answer: Any) -> str:
        if isinstance(answer, list):
            if len(answer) == 0:
                return "A"
            answer = answer[0]
        if not isinstance(answer, str):
            return "A"
        answer = answer.strip()
        if not answer:
            return "A"
        lowered = answer.lower()
        if "answer is" in lowered:
            pos = lowered.find("answer is")
            answer = answer[pos + len("answer is") :].strip(" :")
        label = answer[:1].upper()
        if label not in {"A", "B", "C", "D"}:
            return "A"
        return label
