# Phase B Benchmark Log (MMLU-Redux / 8-shard)

## Protocol
- dataset: `edinburgh-dawg/mmlu-redux`
- parallel: `8-shard`
- model: `qwen3-8b`
- compare baseline: `phaseA-final`

## Run Table

| Run ID | Commit | Samples | Accuracy | Delta vs Phase-A | Notes |
|---|---:|---:|---:|---:|---|
| `phaseB-final` | pending | 8 | 0.500 | +0.125 | 8-shard run with RI read-resolution stack enabled |
| `phaseB-full-audit` | pending | 3000 | 0.243333 | +0.020000 (vs phaseA-full-audit) | Full-scale audit run (all cached redux subjects, no max_samples cap) |

## Evidence
- phase-A summary: `artifacts/runs/mmlu_redux-phaseA-final-all/summary.json`
- phase-B summary: `artifacts/runs/mmlu_redux-phaseB-final-all/summary.json`
- phase-A full summary: `artifacts/runs/mmlu_redux-phaseA-full-audit-all/summary.json`
- phase-B full summary: `artifacts/runs/mmlu_redux-phaseB-full-audit-all/summary.json`
- phase-B replay sample: `artifacts/runs/mmlu_redux-phaseB-final-shard0/replay_summary.json`

## Gate Check
- Requirement: `phaseB_accuracy > phaseA_accuracy(0.375)`
- Status: ✅ passed (`0.500 > 0.375`)

## Full-Scale Gate Revalidation (2026-03-10)
- Requirement: `phaseB_full_accuracy > phaseA_full_accuracy`
- Result: `0.243333 > 0.223333`
- Status: ✅ passed
