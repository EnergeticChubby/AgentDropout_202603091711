from AgentDropout.core.covariance_store import compute_pairwise_error_covariance
from AgentDropout.core.risk_optimizer import RiskParityOptimizer


def test_covariance_store_symmetric():
    vectors = {"a": [0, 1, 0, 1], "b": [0, 0, 1, 1]}
    store = compute_pairwise_error_covariance(vectors)
    assert abs(store.get_covariance("a", "b") - store.get_covariance("b", "a")) < 1e-9


def test_risk_optimizer_select_team():
    optimizer = RiskParityOptimizer(lam=0.5, eta=0.1)
    vectors = {"a": [0, 1, 0], "b": [1, 1, 0], "c": [0, 0, 0]}
    cov = compute_pairwise_error_covariance(vectors)
    result = optimizer.select_team(
        candidate_agents=["a", "b", "c"],
        utilities={"a": 0.6, "b": 0.5, "c": 0.9},
        costs={"a": 0.2, "b": 0.2, "c": 0.3},
        covariance_store=cov,
        team_size=2,
    )
    assert len(result.selected_agents) == 2
    assert "c" in result.selected_agents
