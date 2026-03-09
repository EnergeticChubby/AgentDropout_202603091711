def test_graph_import():
    import AgentDropout.graph.graph  # noqa: F401


def test_registry_imports():
    from AgentDropout.agents.agent_registry import AgentRegistry
    from AgentDropout.prompt.prompt_set_registry import PromptSetRegistry
    from AgentDropout.llm.llm_registry import LLMRegistry

    assert "MathSolver" in AgentRegistry.keys()
    assert "gsm8k" in PromptSetRegistry.keys()
    assert "mock" in LLMRegistry.keys()
