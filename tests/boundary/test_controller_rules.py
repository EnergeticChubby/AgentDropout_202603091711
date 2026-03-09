from AgentDropout.boundary.controller import BoundaryController


class _DummyNode:
    def __init__(self, node_id: str):
        self.id = node_id
        self.node_name = node_id
        self.role = node_id
        self.spatial_successors = []

    def add_successor(self, other, edge_type="spatial"):
        if other not in self.spatial_successors:
            self.spatial_successors.append(other)


class _DummyGraph:
    def __init__(self):
        self.nodes = {k: _DummyNode(k) for k in ["a", "b", "c"]}

    def find_node(self, node_id):
        return self.nodes[node_id]

    def clear_spatial_connection(self):
        for node in self.nodes.values():
            node.spatial_successors = []


def test_boundary_controller_applies_actions():
    graph = _DummyGraph()
    graph.find_node("a").add_successor(graph.find_node("b"))
    graph.find_node("a").add_successor(graph.find_node("c"))
    controller = BoundaryController(output_dir="/tmp/boundary-test")
    controller.begin_run()
    applied = controller.apply(graph, round_idx=0, task="short task", failure_count=0)
    assert isinstance(applied, list)
    assert len(applied) >= 1


def test_boundary_controller_flush_metrics(tmp_path):
    graph = _DummyGraph()
    controller = BoundaryController(output_dir=str(tmp_path))
    controller.begin_run()
    controller.apply(graph, round_idx=0, task="complex " * 50, failure_count=0)
    metrics = controller.flush()
    assert "boundary_reconfiguration_count" in metrics
