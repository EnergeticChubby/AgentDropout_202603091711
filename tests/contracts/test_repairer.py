from AgentDropout.contracts.repairer import ContractRepairer
from AgentDropout.contracts.dispute import DisputeResolver


def test_repairer_generates_recommendations():
    records = [
        {
            "contract": {"metadata": {"task_type": "math"}},
            "verification": {"violations": ["missing_final_answer_pattern"]},
        },
        {
            "contract": {"metadata": {"task_type": "math"}},
            "verification": {"violations": ["empty_deliverable"]},
        },
    ]
    result = ContractRepairer().suggest(records)
    assert result["violation_counts"]["empty_deliverable"] == 1
    assert len(result["recommendations"]) >= 1


def test_dispute_resolver_rework_for_empty_deliverable():
    decision = DisputeResolver().resolve(["empty_deliverable"])
    assert decision.action == "rework"
