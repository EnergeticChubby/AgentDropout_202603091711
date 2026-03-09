from AgentDropout.graph.node import Node
from AgentDropout.protocols.blackboard import PrivateWorkspace, PublicBlackboard
from AgentDropout.protocols.config import ProtocolConfig
from AgentDropout.protocols.types import DisclosureObject, DisclosureType


class DummyNode(Node):
    def _execute(self, input, spatial_info, temporal_info, **kwargs):
        return f"echo::{input['task']}"

    async def _async_execute(self, input, spatial_info, temporal_info, **kwargs):
        return f"echo::{input['task']}"

    def _process_inputs(self, raw_inputs, spatial_info, temporal_info, **kwargs):
        return raw_inputs


def test_protocol_config_from_dict():
    config = ProtocolConfig.from_dict(
        {
            "enable_mirm": True,
            "enable_edel": True,
            "enable_abpp": False,
            "risk_level": "high",
            "token_budget": 2048,
            "topk_disclosure": 3,
            "unknown_field": "ignored",
        }
    )
    assert config.enable_mirm is True
    assert config.enable_edel is True
    assert config.enable_abpp is False
    assert config.risk_level == "high"
    assert config.token_budget == 2048
    assert config.topk_disclosure == 3


def test_blackboard_and_private_workspace_snapshots():
    disclosure = DisclosureObject(
        disclosure_id="disc_1",
        agent_id="agent_1",
        disclosure_type=DisclosureType.CLAIM,
        content="A test claim",
        round_idx=0,
    )

    private_workspace = PrivateWorkspace()
    private_workspace.add("agent_1", disclosure)
    private_snapshot = private_workspace.snapshot()
    assert "agent_1" in private_snapshot
    assert private_snapshot["agent_1"][0]["content"] == "A test claim"

    blackboard = PublicBlackboard()
    blackboard.add_disclosure(disclosure)
    public_snapshot = blackboard.snapshot()
    assert len(public_snapshot["disclosures"]) == 1
    assert public_snapshot["disclosures"][0]["disclosure_type"] == DisclosureType.CLAIM


def test_node_records_inputs_and_raw_inputs():
    node = DummyNode(id="n1", agent_name="dummy", domain="test", llm_name="none")
    out = node.execute({"task": "hello"})
    assert out == ["echo::hello"]
    assert node.raw_inputs == [{"task": "hello"}]
    assert node.inputs and "spatial" in node.inputs[0] and "temporal" in node.inputs[0]

