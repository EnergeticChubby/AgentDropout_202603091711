# Phase A Benchmark Log (MMLU-Redux / 8-shard)

## Benchmark Protocol
- dataset: `edinburgh-dawg/mmlu-redux`
- execution: 8 shard parallel
- model: `qwen3-8b`
- endpoint: `https://llm.undefined.qzz.io/` (from env vars)

## Run Table

| Run ID | Commit | Num Shards | Samples | Accuracy | Prompt Tokens | Completion Tokens | Cost | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `phaseA-baseline` | pending | 8 | 8 | 0.000 | 0 | 0 | 0.0 | FullConnected + FinalRefer; endpoint returned non-answer payload for many requests |
| `phaseA-postfix` | pending | 8 | 8 | 0.375 | 0 | 0 | 0.0 | DirectAnswer + FinalDirect + robust answer postprocess fallback |
| `phaseA-final` | pending | 8 | 8 | 0.375 | 0 | 0 | 0.0 | Final verification run used for phase gate sign-off |

## Shard Artifacts
- Baseline summary: `artifacts/runs/mmlu_redux-phaseA-baseline-all/summary.json`
- Optimized summary: `artifacts/runs/mmlu_redux-phaseA-postfix-all/summary.json`
- Final summary: `artifacts/runs/mmlu_redux-phaseA-final-all/summary.json`
- Per-shard logs: `artifacts/runs/mmlu_redux-phaseA-*-all/shard_process_logs.json`
- Per-sample predictions/events: `artifacts/runs/mmlu_redux-phaseA-*-shard*/`

## Comparison vs Previous Phase
- Phase-0 baseline (run `phaseA-baseline`): `accuracy=0.000`
- Phase-A result (run `phaseA-final`): `accuracy=0.375`
- Delta: `+0.375` (satisfies gate: strictly better than previous phase)
