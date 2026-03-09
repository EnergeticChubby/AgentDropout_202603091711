from AgentDropout.core.attention_policy import RuleBasedAttentionPolicy
from AgentDropout.core.message_schema import (
    build_multilayer_message,
    detect_conflict_peer_ids,
    render_multilayer_message,
)


def test_render_multilayer_levels():
    payload = build_multilayer_message("Answer is C. Because of physics law. Therefore choose C.")
    assert render_multilayer_message(payload, 0) == ""
    assert len(render_multilayer_message(payload, 1)) > 0
    assert "Evidence" in render_multilayer_message(payload, 3)
    assert "Because" in render_multilayer_message(payload, 4)


def test_attention_policy_escalates_on_conflict():
    policy = RuleBasedAttentionPolicy()
    decision = policy.decide_level(
        phase="aggregate",
        receiver_id="r",
        predecessor_id="p1",
        predecessor_output="The answer is B",
        context={"conflict_peers": ["p1", "p2"]},
    )
    assert decision.level == 4


def test_detect_conflict_peers():
    peers = {"a": "The answer is A", "b": "The answer is C", "c": "The answer is A"}
    conflict_ids = detect_conflict_peer_ids(peers)
    assert set(conflict_ids) == {"a", "b", "c"}
