from AgentDropout.core.memory import GovernanceConstitution, MemoryGovernance, MemoryObject, MemoryStore


def test_memory_governance_safe_write_and_expire():
    store = MemoryStore()
    governance = MemoryGovernance(store, GovernanceConstitution())
    memory = MemoryObject(
        content="verified claim",
        type="evidence",
        source_agent="a1",
        provenance={"test": True},
        phase="verify",
        evidence_strength=0.9,
        signers=["a1", "a2"],
    )
    result = governance.safe_write(pool="verified", memory=memory)
    assert result["status"] == "accepted"
    expire1 = governance.expire()
    expire2 = governance.expire()
    expire3 = governance.expire()
    assert expire1["expired"] >= 0
    assert expire2["expired"] >= 0
    assert expire3["expired"] >= 0


def test_memory_governance_challenge_revert_flow():
    store = MemoryStore()
    constitution = GovernanceConstitution(challenge_limit=0.2)
    governance = MemoryGovernance(store, constitution)
    memory = MemoryObject(
        content="summary",
        type="evidence",
        source_agent="a1",
        provenance={},
        phase="critique",
        evidence_strength=0.8,
        signers=["a1"],
    )
    governance.safe_write(pool="team", memory=memory)
    challenged = governance.challenge(pool="team", index=0)
    reverted = governance.revert(pool="team", index=0)
    assert challenged["challenge_status"] in {"contested", "reverted"}
    assert reverted["status"] == "deprecated"
