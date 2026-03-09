from typing import Type
from class_registry import ClassRegistry

from AgentDropout.prompt.prompt_set import PromptSet

class PromptSetRegistry:
    registry = ClassRegistry()

    @classmethod
    def _ensure_defaults_loaded(cls):
        import AgentDropout.prompt  # noqa: F401

    @classmethod
    def register(cls, *args, **kwargs):
        return cls.registry.register(*args, **kwargs)
    
    @classmethod
    def keys(cls):
        cls._ensure_defaults_loaded()
        return cls.registry.keys()

    @classmethod
    def get(cls, name: str, *args, **kwargs) -> PromptSet:
        cls._ensure_defaults_loaded()
        return cls.registry.get(name, *args, **kwargs)

    @classmethod
    def get_class(cls, name: str) -> Type:
        cls._ensure_defaults_loaded()
        return cls.registry.get_class(name)
