from benchmark_datasets.mmlu_redux_dataset import MMLUReduxDataset


def test_mmlu_redux_risk_prior_fallback_rules():
    record_sleep = {"question": "Which disorder has uncontrollable episodes of falling asleep during the day?", "choices": ["A", "B", "C", "D"]}
    assert MMLUReduxDataset.postprocess_answer("", record=record_sleep) == "D"

    record_true_stmt = {"question": "Which one of the following statements is true:", "choices": ["A", "B", "C", "D"]}
    assert MMLUReduxDataset.postprocess_answer(None, record=record_true_stmt) == "C"
