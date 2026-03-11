import os

import pytest

from AgentDropout.llm.llm_registry import LLMRegistry


@pytest.mark.asyncio
async def test_qwen3_connectivity():
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not base_url or not api_key:
        pytest.skip("OPENAI_BASE_URL/OPENAI_API_KEY is not configured for connectivity test.")

    llm = LLMRegistry.get("gpt-5.1-codex-mini")
    response = await llm.agen(
        [
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "Reply with the word READY only."},
        ]
    )
    assert isinstance(response, str)
    assert "<!doctype html>" not in response.lower()
    assert "ready" in response.lower()
