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

## Evidence
- phase-D summary: `artifacts/runs/mmlu_redux-phaseD-final-all/summary.json`
- phase-E summary: `artifacts/runs/mmlu_redux-phaseE-final-v3-all/summary.json`
- baseline matrix: `artifacts/runs/phaseE-baseline-matrix.json`

## Gate Check
- Requirement: `phaseE_accuracy > phaseD_accuracy(0.750)`
- Status: ✅ passed (`1.000 > 0.750`)
