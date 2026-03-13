from AgentDropout.prompt.gsm8k_prompt_set import GSM8KPromptSet
from AgentDropout.prompt.prompt_set_registry import PromptSetRegistry


@PromptSetRegistry.register('svamp')
class SVAMPPromptSet(GSM8KPromptSet):
    """SVAMP uses the same prompt schema as GSM8K in this codebase."""

