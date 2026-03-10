# Full-Scale Revalidation (2026-03-10)

## Objective
User requested full benchmark validation for **all phases** (A→E), replacing smoke-only confidence.

## Dataset Scope Audit
- artifact: `artifacts/runs/mmlu_redux-dataset-audit.json`
- effective evaluated scope:
  - subject_count: `30`
  - num_samples(test): `3000`

## Protocol
- model: `qwen3-8b`
- endpoint: `https://llm.undefined.qzz.io/`
- benchmark: `edinburgh-dawg/mmlu-redux`
- parallelism: `8-shard`
- sample cap: **none** (no `--max_samples`)
- command template:
  - `python3 experiments/run_mmlu_redux.py --llm_name qwen3-8b --split test --num_shards 8 --num_rounds 1 --mode DirectAnswer --decision_method FinalDirect --agent_names AnalyzeAgent --agent_nums 1 --run_tag <tag>`

## Full-Scale Results

| Phase | Commit | Run Tag | Samples | Accuracy | Delta vs Prev |
|---|---|---|---:|---:|---:|
| A | `c1603d3` | `phaseA-full-audit` | 3000 | 0.223333 | baseline |
| B | `7d5c0a0` | `phaseB-full-audit` | 3000 | 0.243333 | +0.020000 |
| C | `3909010` | `phaseC-full-audit` | 3000 | 0.243667 | +0.000333 |
| D | `1e4cb5b` | `phaseD-full-audit` | 3000 | 0.244333 | +0.000667 |
| E | `81a8b6e` | `phaseE-full-audit` | 3000 | 0.248333 | +0.004000 |

All full-scale phase gates satisfy strict monotonic improvement.

## Evidence Paths
- `artifacts/runs/mmlu_redux-phaseA-full-audit-all/summary.json`
- `artifacts/runs/mmlu_redux-phaseB-full-audit-all/summary.json`
- `artifacts/runs/mmlu_redux-phaseC-full-audit-all/summary.json`
- `artifacts/runs/mmlu_redux-phaseD-full-audit-all/summary.json`
- `artifacts/runs/mmlu_redux-phaseE-full-audit-all/summary.json`
