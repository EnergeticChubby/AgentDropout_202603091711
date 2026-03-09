from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from AgentDropout.core.covariance_store import CovarianceStore


@dataclass
class TeamOptimizationResult:
    selected_agents: List[str]
    objective: float
    weights: Dict[str, float]


class RiskParityOptimizer:
    def __init__(self, lam: float = 1.0, eta: float = 0.1):
        self.lam = lam
        self.eta = eta

    def score_team(
        self,
        selected_agents: List[str],
        utilities: Dict[str, float],
        costs: Dict[str, float],
        covariance_store: CovarianceStore,
    ) -> float:
        if not selected_agents:
            return 0.0
        weight = 1.0 / len(selected_agents)
        utility_term = sum(weight * utilities.get(agent, 0.0) for agent in selected_agents)
        cost_term = sum(weight * costs.get(agent, 0.0) for agent in selected_agents)
        covariance_term = 0.0
        for left in selected_agents:
            for right in selected_agents:
                covariance_term += (weight * weight) * covariance_store.get_covariance(left, right)
        return utility_term - self.lam * covariance_term - self.eta * cost_term

    def select_team(
        self,
        candidate_agents: List[str],
        utilities: Dict[str, float],
        costs: Dict[str, float],
        covariance_store: CovarianceStore,
        team_size: int,
    ) -> TeamOptimizationResult:
        if team_size <= 0:
            return TeamOptimizationResult(selected_agents=[], objective=0.0, weights={})

        ordered = sorted(candidate_agents, key=lambda agent: utilities.get(agent, 0.0), reverse=True)
        selected: List[str] = []
        for agent in ordered:
            if len(selected) == 0:
                selected.append(agent)
                if len(selected) >= team_size:
                    break
                continue
            test_team = selected + [agent]
            test_score = self.score_team(test_team, utilities, costs, covariance_store)
            if len(selected) < team_size:
                selected.append(agent)
            if len(selected) >= team_size:
                break

        selected = selected[:team_size]
        objective = self.score_team(selected, utilities, costs, covariance_store)
        weight = 1.0 / len(selected) if selected else 0.0
        weights = {agent: weight for agent in selected}
        return TeamOptimizationResult(selected_agents=selected, objective=objective, weights=weights)
