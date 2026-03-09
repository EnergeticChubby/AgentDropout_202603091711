# Phase 1 V0 Test Manifest

- phase: `phase1-v0`
- branch: `cursor/AdamMartinez6793-6c58`
- commit_before_phase_commit: `b5f45d77b705eb92ce4480fb61a28b0ed1cc4404`
- model: `qwen3-8b`
- base_url: `https://llm.undefined.qzz.io/` (runtime normalized to `/v1`)
- api_key: masked
- num_shards: `8`
- limit_questions_per_shard: `4`

## Commands Executed

1. Contract tests
   ```bash
   python3 -m pytest -q tests/contracts
   ```
   - raw log: `artifacts/tests/phase1/raw/pytest_contracts.log`

2. Smoke tests
   ```bash
   OPENAI_BASE_URL=... OPENAI_API_KEY=... python3 -m pytest -q tests/smoke
   ```
   - raw log: `artifacts/tests/phase1/raw/pytest_smoke.log`

3. mmlu-redux 8-shard benchmark (contracts enabled)
   ```bash
   OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=4 \
   EXTRA_ARGS="--enable_contracts --contract_output_dir artifacts/tests/phase1/contracts/raw" \
   bash scripts/repro/run_mmlu_redux_8shard.sh phase1
   ```
   - shard logs: `artifacts/tests/phase1/mmlu_redux/raw/20260309-161317/`
   - shard outputs: `artifacts/tests/phase1/mmlu_redux/raw/20260309-161317/*.json`
   - benchmark summary: `artifacts/tests/phase1/mmlu_redux/summary/20260309-161317.json`
   - contract audit files: `artifacts/tests/phase1/contracts/raw/*.json`
   - contract metrics files: `artifacts/tests/phase1/contracts/raw/*.metrics.json`

## Phase Gate Comparison (vs Phase 0)

- phase0 mean score: **0.1875**
- phase1-v0 mean score: **0.21875**
- delta: **+0.03125**
- gate result: **PASS** (Phase 1 V0 exceeds Phase 0 baseline)
