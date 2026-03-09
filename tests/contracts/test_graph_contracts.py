import json

import pytest

from AgentDropout.graph.graph import Graph


@pytest.mark.asyncio
async def test_graph_contract_audit_written(tmp_path):
    graph = Graph(
        domain="gsm8k",
        llm_name="mock",
        agent_names=["MathSolver"],
        decision_method="FinalDirect",
        rounds=1,
        enable_contracts=True,
        contract_output_dir=str(tmp_path),
    )
    answers, _ = await graph.arun({"task": "2+2?"}, num_rounds=1)
    assert answers

    metric_files = list(tmp_path.glob("*.metrics.json"))
    assert metric_files, "contract metrics file should be generated"
    metrics = json.loads(metric_files[0].read_text(encoding="utf-8"))
    assert "acceptance_pass_precision" in metrics
