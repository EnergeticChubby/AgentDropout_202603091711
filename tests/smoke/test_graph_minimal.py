import pytest

from AgentDropout.graph.graph import Graph


@pytest.mark.asyncio
async def test_minimal_graph_arun_with_mock_llm():
    graph = Graph(
        domain="gsm8k",
        llm_name="mock",
        agent_names=["MathSolver"],
        decision_method="FinalDirect",
        rounds=1,
    )
    answers, _ = await graph.arun({"task": "If 1+1=?, answer briefly."}, num_rounds=1)
    assert isinstance(answers, list)
    assert len(answers) >= 1
