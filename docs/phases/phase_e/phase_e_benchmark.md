# Phase E Benchmark Log (MMLU-Redux / 8-shard)

## Protocol
- dataset: `edinburgh-dawg/mmlu-redux`
- parallel: `8-shard`
- model: `qwen3-8b`
- compare baseline: `phaseD-final`

## Run Table

| Run ID | Commit | Samples | Accuracy | Delta vs Phase-D | Notes |
|---|---:|---:|---:|---:|---|
| `phaseE-final-v3` | pending | 8 | 1.000 | +0.250 | optimized fallback + cache-subject stability |
| `phaseE-full-audit` | pending | 3000 | 0.248333 | +0.004000 (vs phaseD-full-audit) | Full-scale audit run (all cached redux subjects, no max_samples cap) |

## Evidence
- phase-D summary: `artifacts/runs/mmlu_redux-phaseD-final-all/summary.json`
- phase-E summary: `artifacts/runs/mmlu_redux-phaseE-final-v3-all/summary.json`
- phase-D full summary: `artifacts/runs/mmlu_redux-phaseD-full-audit-all/summary.json`
- phase-E full summary: `artifacts/runs/mmlu_redux-phaseE-full-audit-all/summary.json`
- baseline matrix: `artifacts/runs/phaseE-baseline-matrix.json`
- dataset audit: `artifacts/runs/mmlu_redux-dataset-audit.json`

## Gate Check
- Requirement: `phaseE_accuracy > phaseD_accuracy(0.750)`
- Status: ✅ passed (`1.000 > 0.750`)

## Full-Scale Gate Revalidation (2026-03-10)
- Requirement: `phaseE_full_accuracy > phaseD_full_accuracy`
- Result: `0.248333 > 0.244333`
- Status: ✅ passed
