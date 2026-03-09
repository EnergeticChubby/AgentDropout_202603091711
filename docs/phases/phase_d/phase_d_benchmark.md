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

## Evidence
- phase-C summary: `artifacts/runs/mmlu_redux-phaseC-final-all/summary.json`
- phase-D summary: `artifacts/runs/mmlu_redux-phaseD-final-all/summary.json`
- memory governance sample: `artifacts/runs/mmlu_redux-phaseD-final-shard0/memory_governance_summary.json`

## Gate Check
- Requirement: `phaseD_accuracy > phaseC_accuracy(0.625)`
- Status: ✅ passed (`0.750 > 0.625`)
