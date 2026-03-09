import json
import shortuuid
import time
from pathlib import Path
from typing import Dict, List, Any

from AgentDropout.boundary.actions import BoundaryAction, BoundaryActionExecutor
from AgentDropout.boundary.costs import estimate_boundary_cost
from AgentDropout.boundary.reconfigure import OnlineReconfigure
from AgentDropout.boundary.unit import OrganizationUnit
from AgentDropout.boundary.value_model import BoundaryValueModel


class BoundaryController:
    def __init__(self, output_dir: str = "artifacts/tests/phase3/boundary/raw") -> None:
        self.output_dir = Path(output_dir)
        self.action_executor = BoundaryActionExecutor()
        self.reconfigure = OnlineReconfigure()
        self.value_model = BoundaryValueModel()
        self.records: List[Dict[str, Any]] = []
        self.units: List[OrganizationUnit] = []
        self.run_id = None

    def begin_run(self) -> None:
        self.run_id = shortuuid.ShortUUID().random(length=12)
        self.records = []
        self.units = []

    def _build_units(self, graph) -> None:
        self.units = [
            OrganizationUnit(
                unit_id=f"unit-{idx}",
                unit_type="single_agent",
                members=[node_id],
                metadata={"role": getattr(node, "role", node.node_name)},
            )
            for idx, (node_id, node) in enumerate(graph.nodes.items())
        ]

    def decide_actions(self, graph, round_idx: int, task: str, failure_count: int = 0) -> List[BoundaryAction]:
        if not self.units:
            self._build_units(graph)
        task_len = len(task or "")
        cost = estimate_boundary_cost(graph)
        suggestions = self.reconfigure.suggest(int(cost["handoff_count"]), failure_count, round_idx)
        actions: List[BoundaryAction] = []

        if task_len < 80 and cost["handoff_count"] > 6:
            actions.append(BoundaryAction("dissolve", {}, "short_task_reduce_coordination"))
        if task_len > 180 and cost["handoff_count"] < 10:
            actions.append(BoundaryAction("merge", {}, "complex_task_increase_parallelism"))

        for action_name in suggestions:
            if action_name not in {a.action_type for a in actions}:
                payload = {}
                if action_name == "subteam":
                    payload = {"members": list(graph.nodes.keys())[: max(1, len(graph.nodes) // 2)]}
                actions.append(BoundaryAction(action_name, payload, "online_trigger"))

        if not actions:
            best = self.value_model.best_action(["internalize", "tool", "single_agent"])
            if best == "single_agent":
                actions.append(
                    BoundaryAction("single_agent", {"node_id": next(iter(graph.nodes.keys()))}, "value_model_choice")
                )
            else:
                actions.append(BoundaryAction(best, {}, "value_model_choice"))
        return actions

    def apply(self, graph, round_idx: int, task: str, failure_count: int = 0) -> List[Dict[str, Any]]:
        pre_cost = estimate_boundary_cost(graph)
        actions = self.decide_actions(graph, round_idx, task, failure_count)
        applied = self.action_executor.apply(graph, actions)
        post_cost = estimate_boundary_cost(graph)
        reward = pre_cost["total_organization_cost"] - post_cost["total_organization_cost"]
        for act in actions:
            self.value_model.update(act.action_type, reward)
        self.records.append(
            {
                "timestamp": time.time(),
                "round_idx": round_idx,
                "task_len": len(task or ""),
                "pre_cost": pre_cost,
                "post_cost": post_cost,
                "applied_actions": applied,
                "reward": reward,
            }
        )
        return applied

    def flush(self) -> Dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        records_path = self.output_dir / f"{self.run_id}.json"
        records_path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

        reconfiguration_count = sum(len(r["applied_actions"]) for r in self.records)
        final_cost = self.records[-1]["post_cost"] if self.records else {"handoff_count": 0, "context_fragmentation_score": 0}
        metrics = {
            "boundary_reconfiguration_count": reconfiguration_count,
            "handoff_count": final_cost.get("handoff_count", 0),
            "context_fragmentation_score": final_cost.get("context_fragmentation_score", 0),
            "value_model": self.value_model.snapshot(),
        }
        metrics_path = self.output_dir / f"{self.run_id}.metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return {"records_path": str(records_path), "metrics_path": str(metrics_path), **metrics}
