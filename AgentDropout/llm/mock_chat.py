from typing import List, Union, Optional

from AgentDropout.llm.llm import LLM
from AgentDropout.llm.llm_registry import LLMRegistry
from AgentDropout.llm.format import Message


@LLMRegistry.register("mock")
class MockChat(LLM):
    """Deterministic mock LLM used for tests and smoke runs."""

    async def agen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ) -> Union[List[str], str]:
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            content = last_msg.get("content", "") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
            content = str(content).strip()
            if content:
                return f"[mock] {content[:128]}"
        return "[mock] ok"

    def gen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ) -> Union[List[str], str]:
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            content = last_msg.get("content", "") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
            content = str(content).strip()
            if content:
                return f"[mock] {content[:128]}"
        return "[mock] ok"
