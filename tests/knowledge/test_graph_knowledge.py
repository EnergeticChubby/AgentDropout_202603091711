import json

import pytest

from AgentDropout.graph.graph import Graph


@pytest.mark.asyncio
async def test_graph_knowledge_artifacts_written(tmp_path):
    graph = Graph(
        domain="gsm8k",
        llm_name="mock",
        agent_names=["MathSolver"],
        decision_method="FinalDirect",
        rounds=1,
        enable_knowledge=True,
        knowledge_output_dir=str(tmp_path),
    )
    answers, _ = await graph.arun({"task": "2+2?"}, num_rounds=1)
    assert answers

    metrics_files = list(tmp_path.glob("*.metrics.json"))
    assert metrics_files
    metrics = json.loads(metrics_files[0].read_text(encoding="utf-8"))
    assert "false_common_ground_rate" in metrics
