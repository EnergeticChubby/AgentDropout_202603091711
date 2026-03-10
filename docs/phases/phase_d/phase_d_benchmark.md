# Phase D Benchmark Log (MMLU-Redux / 8-shard)

## Protocol
- dataset: `edinburgh-dawg/mmlu-redux`
- parallel: `8-shard`
- model: `qwen3-8b`
- compare baseline: `phaseC-final`

## Run Table

| Run ID | Commit | Samples | Accuracy | Delta vs Phase-C | Notes |
|---|---:|---:|---:|---:|---|
| `phaseD-final` | pending | 8 | 0.750 | +0.125 | commons memory stack active + governance fallback refinement |
| `phaseD-full-audit` | pending | 3000 | 0.244333 | +0.000667 (vs phaseC-full-audit) | Full-scale audit run (all cached redux subjects, no max_samples cap) |

## Evidence
- phase-C summary: `artifacts/runs/mmlu_redux-phaseC-final-all/summary.json`
- phase-D summary: `artifacts/runs/mmlu_redux-phaseD-final-all/summary.json`
- phase-C full summary: `artifacts/runs/mmlu_redux-phaseC-full-audit-all/summary.json`
- phase-D full summary: `artifacts/runs/mmlu_redux-phaseD-full-audit-all/summary.json`
- memory governance sample: `artifacts/runs/mmlu_redux-phaseD-final-shard0/memory_governance_summary.json`

## Gate Check
- Requirement: `phaseD_accuracy > phaseC_accuracy(0.625)`
- Status: ✅ passed (`0.750 > 0.625`)

## Full-Scale Gate Revalidation (2026-03-10)
- Requirement: `phaseD_full_accuracy > phaseC_full_accuracy`
- Result: `0.244333 > 0.243667`
- Status: ✅ passed
