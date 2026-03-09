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

## Evidence
- phase-A summary: `artifacts/runs/mmlu_redux-phaseA-final-all/summary.json`
- phase-B summary: `artifacts/runs/mmlu_redux-phaseB-final-all/summary.json`
- phase-B replay sample: `artifacts/runs/mmlu_redux-phaseB-final-shard0/replay_summary.json`

## Gate Check
- Requirement: `phaseB_accuracy > phaseA_accuracy(0.375)`
- Status: ✅ passed (`0.500 > 0.375`)
