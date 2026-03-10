# Full-Phase Benchmark Retry Log (2026-03-10)

## Goal

Continue benchmark testing and retry on runtime errors for MMLU-Redux (`edinburgh-dawg/mmlu-redux`) with 8-shard parallel execution.

## Environment

- Branch: `cursor/gz10`
- Model config used for retries:
  - `llm_name=qwen/qwen3-8b` (valid endpoint ID for `qwen3-8b`)
  - `base_url=$MINE_BASE_URL`
  - `api_key=$MINE_API_KEYS`
- Runner: `python3 experiments/run_mmlu_redux.py`

## Retry Procedure

Smoke benchmark command (1 subject, 1 question, 8 shards) was retried **3 times** with exponential backoff:

```bash
python3 experiments/run_mmlu_redux.py \
  --phase_name phase-A-credit-smoke-retry \
  --llm_name qwen/qwen3-8b \
  --mode DirectAnswer \
  --agent_names AnalyzeAgent --agent_nums 1 \
  --decision_method FinalRefer \
  --num_rounds 1 \
  --eval_batch_size 1 \
  --subject_limit 1 \
  --questions_per_subject 1 \
  --num_shards 8 --parallel_shards 8
```

Backoff schedule: 2s, 4s, 8s.

## Result

All 3 retries failed with the same API-side error:

- `Error code: 402`
- `Insufficient credits. This account never purchased credits.`

This confirms failure is external account-credit blocking, not transient transport error.

## Artifacts Produced

Retry artifacts were persisted for auditability:

- `artifacts/tests/mmlu_redux/phase-A-credit-smoke-retry/20260310-013000/`
- `artifacts/tests/mmlu_redux/phase-A-credit-smoke-retry/20260310-013014/`
- `artifacts/tests/mmlu_redux/phase-A-credit-smoke-retry/20260310-013027/`

Each directory includes `config.json` and generated shard raw-output files for completed empty shards prior to failure.

## Blocking Condition

Full-phase runs (phase A-E full dataset) cannot proceed until the configured API key has available credits.
