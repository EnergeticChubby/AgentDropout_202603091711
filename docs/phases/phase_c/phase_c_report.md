# Phase C Report (Risk-Parity MAS MVP)

## Goal / Scope
- Introduce correlation-aware risk primitives and risk-adjusted team logic.
- Deliver covariance measurement tooling and weighted aggregation runtime hooks.

## Design / Implementation
- New modules:
  - `AgentDropout/core/risk_card.py`
  - `AgentDropout/core/covariance_store.py`
  - `AgentDropout/core/risk_optimizer.py`
- Runtime changes:
  - `Graph` now accepts optional `risk_weights`.
  - `FinalMajorVote` supports weighted voting by risk reliability.
- Tooling:
  - `experiments/build_risk_covariance.py` builds covariance matrix and risk cards from prediction logs.

## Validation Summary
- Unit tests:
  - `python3 -m pytest tests/test_phase_a_core.py tests/test_phase_b_ri_mas.py tests/test_phase_c_risk.py` ✅
- Covariance build:
  - `python3 experiments/build_risk_covariance.py ...` ✅
  - artifacts: `artifacts/runs/phaseC-covariance.json`, `artifacts/runs/phaseC-risk-cards.json`
- Phase gate benchmark:
  - phase-B accuracy: `0.500`
  - phase-C accuracy: `0.625`
  - status: ✅ improved

## Risks / Notes
- Current endpoint non-standard responses still require fallback parsing.
- Covariance quality is bounded by available benchmark sample volume per phase gate run.
