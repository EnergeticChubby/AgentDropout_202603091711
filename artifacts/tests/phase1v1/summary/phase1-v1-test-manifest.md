# Phase 1 V1 Test Manifest

- phase: `phase1-v1`
- branch: `cursor/AdamMartinez6793-6c58`
- commit_before_phase_commit: `719a403dce73f4eeda0ef4dd5ff0d2e1ee3cae19`
- model: `qwen3-8b`
- base_url: `https://llm.undefined.qzz.io/` (runtime normalized to `/v1`)
- api_key: masked
- num_shards: `8`
- limit_questions_per_shard: `4`
- decision_method: `FinalMajorVote`

## Commands Executed

1. Contract tests (V1)
   ```bash
   python3 -m pytest -q tests/contracts
   ```
   - raw log: `artifacts/tests/phase1v1/raw/pytest_contracts_v1.log`

2. Smoke tests (V1)
   ```bash
   OPENAI_BASE_URL=... OPENAI_API_KEY=... python3 -m pytest -q tests/smoke
   ```
   - raw log: `artifacts/tests/phase1v1/raw/pytest_smoke_v1.log`

3. mmlu-redux 8-shard benchmark (contracts + repair path + major vote)
   ```bash
   OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=4 \
   EXTRA_ARGS="--enable_contracts --contract_output_dir artifacts/tests/phase1v1/contracts/raw --decision_method FinalMajorVote" \
   bash scripts/repro/run_mmlu_redux_8shard.sh phase1v1
   ```
   - shard logs: `artifacts/tests/phase1v1/mmlu_redux/raw/20260309-162127/`
   - shard outputs: `artifacts/tests/phase1v1/mmlu_redux/raw/20260309-162127/*.json`
   - benchmark summary: `artifacts/tests/phase1v1/mmlu_redux/summary/20260309-162127.json`
   - contract audit: `artifacts/tests/phase1v1/contracts/raw/*.json`
   - contract metrics: `artifacts/tests/phase1v1/contracts/raw/*.metrics.json`

## Phase Gate Comparison (vs Phase 1 V0)

- phase1-v0 mean score: **0.21875**
- phase1-v1 mean score: **0.875**
- delta: **+0.65625**
- gate result: **PASS** (Phase 1 V1 exceeds Phase 1 V0)
