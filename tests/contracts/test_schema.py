from AgentDropout.contracts.schema import DelegationContract


def test_contract_schema_to_dict():
    contract = DelegationContract(
        contract_id="cid-1",
        task_clause="solve question",
        decision_rights="standard",
        deliverable_schema="text",
    )
    payload = contract.to_dict()
    assert payload["contract_id"] == "cid-1"
    assert payload["task_clause"] == "solve question"
