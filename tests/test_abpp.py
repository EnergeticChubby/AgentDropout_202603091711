from AgentDropout.protocols.abpp import ABPPProtocol
from AgentDropout.protocols.admissibility import AdmissibilityEngine
from AgentDropout.protocols.types import DisclosureObject, DisclosureType


def test_admissibility_engine_high_risk_claim_needs_support():
    engine = AdmissibilityEngine()
    disclosure = DisclosureObject(
        disclosure_id="d1",
        agent_id="a1",
        disclosure_type=DisclosureType.CLAIM,
        content="I think the answer is B.",
        round_idx=0,
        token_cost=6,
    )
    decision = engine.evaluate(disclosure, risk_level="high")
    assert decision.admissible is False
    assert "high_risk_claim_requires_support" in decision.reasons


def test_abpp_protocol_records_ruling_and_dispute():
    protocol = ABPPProtocol()
    state = {"admissibility_records": [], "disputes": []}
    disclosure = DisclosureObject(
        disclosure_id="d2",
        agent_id="a2",
        disclosure_type=DisclosureType.EVIDENCE,
        content="This is true.",
        round_idx=0,
        token_cost=3,
    )
    admissible = protocol.process_disclosure(disclosure, state=state, risk_level="medium")
    assert admissible is False
    assert len(state["admissibility_records"]) == 1
    assert len(state["disputes"]) == 1

