from typing import Optional
from class_registry import ClassRegistry
import os

from AgentDropout.llm.llm import LLM


class LLMRegistry:
    registry = ClassRegistry()

    @classmethod
    def _ensure_defaults_loaded(cls):
        # Import side effects register built-in LLM adapters.
        import AgentDropout.llm.gpt_chat  # noqa: F401
        import AgentDropout.llm.mock_chat  # noqa: F401

    @classmethod
    def register(cls, *args, **kwargs):
        return cls.registry.register(*args, **kwargs)
    
    @classmethod
    def keys(cls):
        cls._ensure_defaults_loaded()
        return cls.registry.keys()

    @classmethod
    def get(cls, model_name: Optional[str] = None) -> LLM:
        cls._ensure_defaults_loaded()
        if model_name is None or model_name=="":
            model_name = os.getenv("LLM_MODEL_NAME", "glm-4.5-flash")

        if 'Llama' in model_name or 'Qwen' in model_name:
            # print(11111111111)
            model = cls.registry.get('llama', model_name)
        elif 'deepseek' in model_name:
            # print(11111111111)
            model = cls.registry.get('deepseek', model_name)
        elif model_name == 'mock':
            model = cls.registry.get(model_name)
        else: # any version of GPTChat like "gpt-4o"
            model = cls.registry.get('GPTChat', model_name)

        return model
