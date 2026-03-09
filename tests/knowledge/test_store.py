from AgentDropout.knowledge.proposition import Proposition
from AgentDropout.knowledge.store import EpistemicStateStore


def test_epistemic_store_add_and_snapshot():
    store = EpistemicStateStore()
    prop = Proposition(
        proposition_id="p1",
        text="The answer is 42",
        source_node="n1",
        source_role="solver",
    )
    store.add(prop)
    snap = store.snapshot()
    assert "p1" in snap
    assert snap["p1"]["text"] == "The answer is 42"
