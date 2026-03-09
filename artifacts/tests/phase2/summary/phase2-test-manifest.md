# Phase 2 Test Manifest

- phase: `phase2`
- branch: `cursor/AdamMartinez6793-6c58`
- commit_before_phase_commit: `b37b1ecd9b5987a10d5e1999adb15cb1891bf04b`
- model: `qwen3-8b`
- base_url: `https://llm.undefined.qzz.io/` (runtime normalized to `/v1`)
- api_key: masked
- num_shards: `8`
- limit_questions_per_shard: `2`
- decision_method: `FinalMajorVote`
- extra_runtime: `contracts + knowledge enabled`

## Commands Executed

1. Contracts + knowledge tests
   ```bash
   python3 -m pytest -q tests/contracts tests/knowledge
   ```
   - raw log: `artifacts/tests/phase2/raw/pytest_contracts_knowledge.log`

2. Smoke tests
   ```bash
   OPENAI_BASE_URL=... OPENAI_API_KEY=... python3 -m pytest -q tests/smoke
   ```
   - raw log: `artifacts/tests/phase2/raw/pytest_smoke.log`

3. mmlu-redux 8-shard benchmark
   ```bash
   OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=2 \
   EXTRA_ARGS="--enable_contracts --contract_output_dir artifacts/tests/phase2/contracts/raw --enable_knowledge --knowledge_output_dir artifacts/tests/phase2/knowledge/raw --decision_method FinalMajorVote" \
   bash scripts/repro/run_mmlu_redux_8shard.sh phase2
   ```
   - shard logs: `artifacts/tests/phase2/mmlu_redux/raw/20260309-163017/`
   - shard outputs: `artifacts/tests/phase2/mmlu_redux/raw/20260309-163017/*.json`
   - benchmark summary: `artifacts/tests/phase2/mmlu_redux/summary/20260309-163017.json`
   - contract audit: `artifacts/tests/phase2/contracts/raw/*.json`
   - knowledge artifacts: `artifacts/tests/phase2/knowledge/raw/*.json`

## Phase Gate Comparison (vs Phase 1 V1)

- phase1-v1 mean score: **0.875**
- phase2 mean score: **1.0**
- delta: **+0.125**
- gate result: **PASS** (Phase 2 exceeds Phase 1 V1)
