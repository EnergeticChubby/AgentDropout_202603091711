from typing import List, Optional, Union

from AgentDropout.llm.format import Message
from AgentDropout.llm.llm import LLM
from AgentDropout.llm.llm_registry import LLMRegistry


@LLMRegistry.register('mock')
class MockChat(LLM):
    def __init__(self, model_name: str = "mock"):
        self.model_name = model_name

    async def agen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ) -> Union[List[str], str]:
        return "The answer is 0"

    def gen(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        num_comps: Optional[int] = None,
    ) -> Union[List[str], str]:
        return "The answer is 0"
