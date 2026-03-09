from AgentDropout.protocols.blackboard import PublicBlackboard
from AgentDropout.protocols.mirm_extractor import MIRMExtractor
from AgentDropout.protocols.mirm_gate import MIRMGate
from AgentDropout.protocols.mirm_scorer import MIRMScorer


def test_mirm_extractor_generates_disclosures():
    extractor = MIRMExtractor()
    text = "According to source A, option B is likely right. However this contradicts option C."
    disclosures = extractor.extract(agent_id="a1", round_idx=0, raw_text=text)
    assert len(disclosures) >= 2
    assert all(item.agent_id == "a1" for item in disclosures)


def test_mirm_scoring_and_budgeted_gate():
    extractor = MIRMExtractor()
    scorer = MIRMScorer()
    gate = MIRMGate()
    blackboard = PublicBlackboard()

    candidates = extractor.extract(
        agent_id="a1",
        round_idx=1,
        raw_text=(
            "According to evidence from the chart, answer B is correct. "
            "However previous assumptions may contradict this result. "
            "I am not sure."
        ),
    )
    scored = scorer.score(candidates, blackboard)
    selected, rejected = gate.select(scored_candidates=scored, top_k=2, token_budget=20)

    assert len(selected) <= 2
    assert len(selected) + len(rejected) == len(candidates)
    assert all(item.score >= rejected[-1].score for item in selected) if rejected else True

