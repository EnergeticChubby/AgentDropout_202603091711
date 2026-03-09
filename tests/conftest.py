import os
import random

import numpy as np
import pytest

try:
    import torch
except Exception:  # pragma: no cover - optional dependency in smoke env
    torch = None


@pytest.fixture(autouse=True)
def _set_deterministic_seed():
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)


@pytest.fixture(autouse=True)
def _default_mock_model_env(monkeypatch):
    # Default all tests to mock model unless explicitly overridden.
    monkeypatch.setenv("LLM_MODEL_NAME", os.getenv("LLM_MODEL_NAME", "mock"))
