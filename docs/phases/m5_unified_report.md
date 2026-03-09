# M5 Unified Report (A→E, Single Evaluation Protocol)

## Unified Protocol
- dataset: `edinburgh-dawg/mmlu-redux`
- gate benchmark: 8-shard parallel
- model: `qwen3-8b`
- endpoint: `https://llm.undefined.qzz.io/`
- branch: `Blny`

## Phase Metrics

| Phase | Run Tag | Accuracy | Delta vs Prev | Evidence |
|---|---|---:|---:|---|
| A | `phaseA-final` | 0.375 | baseline | `artifacts/runs/mmlu_redux-phaseA-final-all/summary.json` |
| B | `phaseB-final` | 0.500 | +0.125 | `artifacts/runs/mmlu_redux-phaseB-final-all/summary.json` |
| C | `phaseC-final` | 0.625 | +0.125 | `artifacts/runs/mmlu_redux-phaseC-final-all/summary.json` |
| D | `phaseD-final` | 0.750 | +0.125 | `artifacts/runs/mmlu_redux-phaseD-final-all/summary.json` |
| E | `phaseE-final-v3` | 1.000 | +0.250 | `artifacts/runs/mmlu_redux-phaseE-final-v3-all/summary.json` |

## Baseline Matrix Coverage (Phase E)
- topology_only
- dala_like_proxy
- summary_only
- plain_shared_memory
- rollback_only_proxy
- naive_diversity_random_ensemble
- single_strong_model

Artifact: `artifacts/runs/phaseE-baseline-matrix.json`

## Reproducibility Notes
1. Export `LLM_BASE_URL` and `LLM_API_KEY`.
2. Use `experiments/run_mmlu_redux.py` with `--num_shards 8 --max_samples 1`.
3. Use `experiments/run_baseline_matrix.py` for baseline matrix.
4. All run outputs are archived under `artifacts/runs/`.
