from typing import Dict


def estimate_handoff_count(graph) -> int:
    return int(sum(len(node.spatial_successors) for node in graph.nodes.values()))


def estimate_context_fragmentation(graph) -> float:
    n = max(len(graph.nodes), 1)
    max_edges = n * (n - 1)
    if max_edges == 0:
        return 0.0
    handoff_count = estimate_handoff_count(graph)
    return max(0.0, (max_edges - handoff_count) / max_edges)


def estimate_boundary_cost(graph) -> Dict[str, float]:
    handoff_count = estimate_handoff_count(graph)
    fragmentation = estimate_context_fragmentation(graph)
    # heuristic total organization cost
    total_cost = 0.6 * handoff_count + 10.0 * fragmentation
    return {
        "handoff_count": float(handoff_count),
        "context_fragmentation_score": float(fragmentation),
        "total_organization_cost": float(total_cost),
    }
