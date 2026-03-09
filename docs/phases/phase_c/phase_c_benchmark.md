# Phase C Benchmark Log (MMLU-Redux / 8-shard)

## Protocol
- dataset: `edinburgh-dawg/mmlu-redux`
- parallel: `8-shard`
- model: `qwen3-8b`
- compare baseline: `phaseB-final`

## Run Table

| Run ID | Commit | Samples | Accuracy | Delta vs Phase-B | Notes |
|---|---:|---:|---:|---:|---|
| `phaseC-final` | pending | 8 | 0.625 | +0.125 | risk-prior fallback + risk modules available |

## Evidence
- phase-B summary: `artifacts/runs/mmlu_redux-phaseB-final-all/summary.json`
- phase-C summary: `artifacts/runs/mmlu_redux-phaseC-final-all/summary.json`
- covariance artifact: `artifacts/runs/phaseC-covariance.json`
- risk cards: `artifacts/runs/phaseC-risk-cards.json`

## Gate Check
- Requirement: `phaseC_accuracy > phaseB_accuracy(0.500)`
- Status: ✅ passed (`0.625 > 0.500`)
