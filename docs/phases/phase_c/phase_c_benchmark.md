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
| `phaseC-full-audit` | pending | 3000 | 0.243667 | +0.000333 (vs phaseB-full-audit) | Full-scale audit run (all cached redux subjects, no max_samples cap) |

## Evidence
- phase-B summary: `artifacts/runs/mmlu_redux-phaseB-final-all/summary.json`
- phase-C summary: `artifacts/runs/mmlu_redux-phaseC-final-all/summary.json`
- phase-B full summary: `artifacts/runs/mmlu_redux-phaseB-full-audit-all/summary.json`
- phase-C full summary: `artifacts/runs/mmlu_redux-phaseC-full-audit-all/summary.json`
- covariance artifact: `artifacts/runs/phaseC-covariance.json`
- risk cards: `artifacts/runs/phaseC-risk-cards.json`

## Gate Check
- Requirement: `phaseC_accuracy > phaseB_accuracy(0.500)`
- Status: ✅ passed (`0.625 > 0.500`)

## Full-Scale Gate Revalidation (2026-03-10)
- Requirement: `phaseC_full_accuracy > phaseB_full_accuracy`
- Result: `0.243667 > 0.243333`
- Status: ✅ passed
