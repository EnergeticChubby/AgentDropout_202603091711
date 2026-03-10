from datasets.mmlu_dataset import MMLUDataset


def test_record_to_standard_prefers_answer_when_correct_answer_is_none():
    record = {
        "question": "Q",
        "choices": ["a", "b", "c", "d"],
        "correct_answer": None,
        "answer": 2,
    }

    normalized = MMLUDataset._record_to_standard(record)

    assert normalized["correct_answer"] == "C"


def test_record_to_standard_accepts_one_based_numeric_answer():
    record = {
        "question": "Q",
        "A": "a",
        "B": "b",
        "C": "c",
        "D": "d",
        "correct_answer": "4",
    }

    normalized = MMLUDataset._record_to_standard(record)

    assert normalized["correct_answer"] == "D"
