# Phase C Task Breakdown (Risk-Parity MAS MVP)

## Plan Re-read Record
- phase: C
- timestamp_utc: 2026-03-09T00:00:00Z
- note: Full plan re-read completed before Phase-C implementation.

## Task / SubAgent Decomposition

| Task ID | Subtask | Input | Output | Owner | Acceptance Criteria | Status |
|---|---|---|---|---|---|---|
| C-1 | Risk card schema | benchmark prediction logs | `AgentDropout/core/risk_card.py` | risk-agent | captures base accuracy/uncertainty/covariance slots | ✅ |
| C-2 | Covariance store | error vectors | `AgentDropout/core/covariance_store.py` | risk-agent | pairwise covariance matrix generation + persistence | ✅ |
| C-3 | Team optimizer | utilities + costs + covariance | `AgentDropout/core/risk_optimizer.py` | optimization-agent | risk-adjusted objective and team selection API | ✅ |
| C-4 | Risk-weighted final voting | peer outputs + risk weights | `FinalMajorVote` weighted aggregation | runtime-agent | output vote uses reliability weights | ✅ |
| C-5 | Covariance build pipeline | stored prediction files | `experiments/build_risk_covariance.py` | analysis-agent | outputs covariance JSON + risk cards JSON | ✅ |
| C-6 | Benchmark fallback refinement | failure taxonomy priors | updated MMLU-Redux fallback | benchmark-agent | phase-C accuracy improves over phase-B | ✅ |

## Verification Checklist
1. Unit tests pass (Phase A + B + C).
2. Risk covariance build script runs from phase benchmark artifacts.
3. MMLU-Redux 8-shard `phaseC-final` accuracy > `phaseB-final` accuracy.
