from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class BoundaryAction:
    action_type: str
    payload: Dict
    reason: str

    def to_dict(self) -> Dict:
        return asdict(self)


class BoundaryActionExecutor:
    """
    Apply boundary actions by editing current round graph connectivity.
    """

    def apply(self, graph, actions: List[BoundaryAction]) -> List[Dict]:
        applied: List[Dict] = []
        for action in actions:
            if action.action_type == "merge":
                self._merge_all(graph)
            elif action.action_type == "dissolve":
                self._dissolve_to_star(graph)
            elif action.action_type == "single_agent":
                self._single_agent(graph, action.payload.get("node_id"))
            elif action.action_type == "subteam":
                self._subteam(graph, action.payload.get("members", []))
            elif action.action_type in {"tool", "internalize"}:
                # placeholder: no direct graph mutation in this repository runtime.
                pass
            applied.append(action.to_dict())
        return applied

    @staticmethod
    def _merge_all(graph) -> None:
        node_ids = list(graph.nodes.keys())
        for out_id in node_ids:
            for in_id in node_ids:
                if out_id == in_id:
                    continue
                out_node = graph.find_node(out_id)
                in_node = graph.find_node(in_id)
                if in_node not in out_node.spatial_successors:
                    out_node.add_successor(in_node, "spatial")

    @staticmethod
    def _dissolve_to_star(graph) -> None:
        node_ids = list(graph.nodes.keys())
        if len(node_ids) <= 1:
            return
        hub_id = node_ids[0]
        graph.clear_spatial_connection()
        for node_id in node_ids[1:]:
            graph.find_node(hub_id).add_successor(graph.find_node(node_id), "spatial")

    @staticmethod
    def _single_agent(graph, node_id: str | None) -> None:
        if node_id is None:
            node_id = next(iter(graph.nodes.keys()))
        graph.clear_spatial_connection()
        # keep node active, no outgoing edges.
        _ = graph.find_node(node_id)

    @staticmethod
    def _subteam(graph, members: List[str]) -> None:
        if not members:
            members = list(graph.nodes.keys())[: max(1, len(graph.nodes) // 2)]
        member_set = set(members)
        graph.clear_spatial_connection()
        for out_id in member_set:
            for in_id in member_set:
                if out_id == in_id:
                    continue
                if out_id in graph.nodes and in_id in graph.nodes:
                    graph.find_node(out_id).add_successor(graph.find_node(in_id), "spatial")
