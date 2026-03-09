from AgentDropout.contracts.schema import DelegationContract
from AgentDropout.contracts.verifier import ContractVerifier


def test_contract_verifier_non_empty_pass():
    contract = DelegationContract(
        contract_id="cid-2",
        task_clause="answer question",
        decision_rights="standard",
        deliverable_schema="text",
        acceptance_test=["non_empty"],
    )
    result = ContractVerifier().verify(contract, "The answer is A")
    assert result.passed is True


def test_contract_verifier_detects_missing_final_answer():
    contract = DelegationContract(
        contract_id="cid-3",
        task_clause="math task",
        decision_rights="standard",
        deliverable_schema="text",
        acceptance_test=["non_empty", "contains_final_answer_pattern"],
    )
    result = ContractVerifier().verify(contract, "I think this might be 42.")
    assert result.passed is False
    assert "missing_final_answer_pattern" in result.violations
