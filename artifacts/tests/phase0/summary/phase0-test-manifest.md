# Phase 0 Test Manifest

- phase: `phase0`
- branch: `cursor/AdamMartinez6793-6c58`
- commit_before_phase_commit: `722c7fd831c8d211ac69c857f6bc8516a10f94ad`
- model: `qwen3-8b`
- base_url: `https://llm.undefined.qzz.io/` (runtime normalized to `/v1`)
- api_key: masked
- num_shards: `8`
- limit_questions_per_shard: `4`
- random_seed: `42` (pytest smoke tests)

## Commands Executed

1. Smoke tests
   ```bash
   OPENAI_BASE_URL=... OPENAI_API_KEY=... python3 -m pytest -q tests/smoke
   ```
   - raw log: `artifacts/tests/phase0/raw/pytest_smoke.log`

2. Graph import check
   ```bash
   python3 -c "import AgentDropout.graph.graph as g; print('import-ok')"
   ```
   - raw log: `artifacts/tests/phase0/raw/import_check.log`

3. mmlu-redux 8-shard benchmark
   ```bash
   OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=4 \
   bash scripts/repro/run_mmlu_redux_8shard.sh phase0
   ```
   - shard logs: `artifacts/tests/phase0/mmlu_redux/raw/20260309-160227/`
   - shard outputs: `artifacts/tests/phase0/mmlu_redux/raw/20260309-160227/*.json`
   - summary json: `artifacts/tests/phase0/mmlu_redux/summary/20260309-160227.json`
   - summary md: `artifacts/tests/phase0/mmlu_redux/summary/20260309-160227.md`

## Key Result

- `mmlu-redux` mean score (8-shard): **0.1875**
- This is the baseline score for Phase 1 comparisons.
