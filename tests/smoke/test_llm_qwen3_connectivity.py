import os

import pytest

from AgentDropout.llm.llm_registry import LLMRegistry


@pytest.mark.asyncio
async def test_default_model_connectivity():
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not base_url or not api_key:
        pytest.skip("OPENAI_BASE_URL/OPENAI_API_KEY is not configured for connectivity test.")

    model_name = os.getenv("LLM_MODEL_NAME", "glm-4.5-flash")
    llm = LLMRegistry.get(model_name)
    try:
        response = await llm.agen(
            [
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": "Reply with the word READY only."},
            ]
        )
    except Exception as exc:  # noqa: BLE001
        chain = [str(exc)]
        cause = getattr(exc, "__cause__", None)
        while cause is not None:
            chain.append(str(cause))
            cause = getattr(cause, "__cause__", None)
        err = " ".join(chain).lower()
        if "model_not_found" in err:
            pytest.skip(f"Model {model_name} is not available on this endpoint.")
        if "429" in err or "rate limit" in err or "rate_limited" in err:
            pytest.skip("Connectivity check skipped due transient rate limit.")
        raise
    assert isinstance(response, str)
    assert "<!doctype html>" not in response.lower()
    assert "ready" in response.lower()
