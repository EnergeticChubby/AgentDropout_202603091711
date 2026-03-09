import json

import pytest

from AgentDropout.graph.graph import Graph


@pytest.mark.asyncio
async def test_graph_boundary_artifacts_written(tmp_path):
    graph = Graph(
        domain="gsm8k",
        llm_name="mock",
        agent_names=["MathSolver"],
        decision_method="FinalDirect",
        rounds=1,
        enable_boundary=True,
        boundary_output_dir=str(tmp_path),
    )
    answers, _ = await graph.arun({"task": "simple arithmetic"}, num_rounds=1)
    assert answers
    metrics_files = list(tmp_path.glob("*.metrics.json"))
    assert metrics_files
    metrics = json.loads(metrics_files[0].read_text(encoding="utf-8"))
    assert "handoff_count" in metrics
