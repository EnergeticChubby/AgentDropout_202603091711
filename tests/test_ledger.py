from AgentDropout.protocols.claim_parser import ClaimParser
from AgentDropout.protocols.ledger import EpistemicLedger
from AgentDropout.protocols.types import ClaimStatus


def test_claim_parser_extracts_claims():
    parser = ClaimParser()
    claims = parser.parse(
        speaker_agent="agent-x",
        text="According to the source, answer B is correct. Maybe this is uncertain.",
    )
    assert len(claims) == 2
    assert claims[0].speaker_agent == "agent-x"
    assert claims[0].assets


def test_ledger_status_and_settlement():
    parser = ClaimParser()
    ledger = EpistemicLedger()
    claims = parser.parse(
        speaker_agent="agent-y",
        text="Maybe answer C is right.",
    )
    ledger.add_claims(claims)
    claim = list(ledger.claims.values())[0]
    assert claim.status in {ClaimStatus.CONTESTED, ClaimStatus.SUPPORTED}

    ledger.settle_claim(
        claim_id=claim.claim_id,
        asset={"type": "tool_result", "detail": "verified by checker"},
        liability_type="unresolved_ambiguity",
    )
    updated = ledger.claims[claim.claim_id]
    assert updated.status in {ClaimStatus.VERIFIED, ClaimStatus.SUPPORTED}
    stats = ledger.stats()
    assert stats["total_claims"] == 1

