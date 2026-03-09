from AgentDropout.metrics.epistemic_metrics import (
    compare_phase_metrics,
    compute_quality_score,
)


def test_compute_quality_score_increases_with_verified_claims():
    base = compute_quality_score(accuracy=1.0, avg_public_disclosures=1.0, avg_verified_claims=0.0)
    improved = compute_quality_score(accuracy=1.0, avg_public_disclosures=1.0, avg_verified_claims=2.0)
    assert improved > base


def test_compare_phase_metrics_uses_quality_score():
    previous = {"accuracy": 1.0, "quality_score": 1.01}
    current = {"accuracy": 1.0, "quality_score": 1.03}
    comparison = compare_phase_metrics(previous, current)
    assert comparison["improved"] is True
    assert comparison["quality_delta"] > 0

