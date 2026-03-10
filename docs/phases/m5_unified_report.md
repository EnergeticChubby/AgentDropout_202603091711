# M5 Unified Report (A→E, Single Evaluation Protocol)

## Unified Protocol
- dataset: `edinburgh-dawg/mmlu-redux`
- gate benchmark: 8-shard parallel
- model: `qwen3-8b`
- endpoint: `https://llm.undefined.qzz.io/`
- branch: `Blny`
- scope audit: `artifacts/runs/mmlu_redux-dataset-audit.json` (30 subjects / 3000 test samples)

## Phase Metrics

| Phase | Run Tag | Accuracy | Delta vs Prev | Evidence |
|---|---|---:|---:|---|
| A | `phaseA-full-audit` | 0.223333 | baseline | `artifacts/runs/mmlu_redux-phaseA-full-audit-all/summary.json` |
| B | `phaseB-full-audit` | 0.243333 | +0.020000 | `artifacts/runs/mmlu_redux-phaseB-full-audit-all/summary.json` |
| C | `phaseC-full-audit` | 0.243667 | +0.000333 | `artifacts/runs/mmlu_redux-phaseC-full-audit-all/summary.json` |
| D | `phaseD-full-audit` | 0.244333 | +0.000667 | `artifacts/runs/mmlu_redux-phaseD-full-audit-all/summary.json` |
| E | `phaseE-full-audit` | 0.248333 | +0.004000 | `artifacts/runs/mmlu_redux-phaseE-full-audit-all/summary.json` |

## Baseline Matrix Coverage (Phase E)
- topology_only
- dala_like_proxy
- summary_only
- plain_shared_memory
- rollback_only_proxy
- naive_diversity_random_ensemble
- single_strong_model

Artifact: `artifacts/runs/phaseE-baseline-matrix.json`

## Legacy Smoke-Gate Note
- Earlier phase closures used smoke runs (`max_samples=1` per shard, total 8 samples) for fast iteration.
- Full-scale revalidation on 2026-03-10 supersedes smoke gate figures for final audit and acceptance.

## Reproducibility Notes
1. Export `LLM_BASE_URL` and `LLM_API_KEY`.
2. Use `experiments/run_mmlu_redux.py` with `--num_shards 8` and omit `--max_samples`.
3. Use `experiments/run_baseline_matrix.py` for baseline matrix.
4. All run outputs are archived under `artifacts/runs/`.
