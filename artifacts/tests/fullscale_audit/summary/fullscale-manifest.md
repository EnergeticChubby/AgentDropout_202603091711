# Full-scale mmlu-redux Audit Manifest (All Phases)

## Scope
- Dataset: `edinburgh-dawg/mmlu-redux`
- Split: `test`
- Sharding: `8` shards (parallel)
- Model: `qwen3-8b`
- Endpoint: `https://llm.undefined.qzz.io/` (via env)

## Runtime profile used for full-scale reruns
- `--num_rounds 1`
- `--batch_size 64`
- `--decision_method FinalDirect`
- `--agent_nums 1` (single AnalyzeAgent instance per shard)
- `LIMIT_QUESTIONS=10000` (effective full-run, each shard reached 375/375)

## Executed commands

### Phase0 full
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=10000 \
EXTRA_ARGS="--num_rounds 1 --batch_size 64 --decision_method FinalDirect --agent_nums 1" \
bash scripts/repro/run_mmlu_redux_8shard.sh phase0_fullaudit
```

### Phase1-V0 full
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=10000 \
EXTRA_ARGS="--num_rounds 1 --batch_size 64 --decision_method FinalDirect --agent_nums 1 \
--enable_contracts --contract_output_dir artifacts/tests/phase1_v0_fullaudit/contracts/raw" \
bash scripts/repro/run_mmlu_redux_8shard.sh phase1_v0_fullaudit
```

### Phase1-V1 full
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=10000 \
EXTRA_ARGS="--num_rounds 1 --batch_size 64 --decision_method FinalDirect --agent_nums 1 \
--enable_contracts --contract_output_dir artifacts/tests/phase1_v1_fullaudit/contracts/raw" \
bash scripts/repro/run_mmlu_redux_8shard.sh phase1_v1_fullaudit
```

### Phase2 full
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=10000 \
EXTRA_ARGS="--num_rounds 1 --batch_size 64 --decision_method FinalDirect --agent_nums 1 \
--enable_contracts --contract_output_dir artifacts/tests/phase2_fullaudit/contracts/raw \
--enable_knowledge --knowledge_output_dir artifacts/tests/phase2_fullaudit/knowledge/raw" \
bash scripts/repro/run_mmlu_redux_8shard.sh phase2_fullaudit
```

### Phase3 full
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=10000 \
BOUNDARY_METRICS_DIR="artifacts/tests/phase3_fullaudit/boundary/raw" BOUNDARY_BONUS_WEIGHT=0.05 \
EXTRA_ARGS="--num_rounds 1 --batch_size 64 --decision_method FinalDirect --agent_nums 1 \
--enable_contracts --contract_output_dir artifacts/tests/phase3_fullaudit/contracts/raw \
--enable_knowledge --knowledge_output_dir artifacts/tests/phase3_fullaudit/knowledge/raw \
--enable_boundary --boundary_output_dir artifacts/tests/phase3_fullaudit/boundary/raw" \
bash scripts/repro/run_mmlu_redux_8shard.sh phase3_fullaudit
```

## Full-scale coverage check
- Every phase run produced shard logs with final denominator `375` for each of 8 shards.
- Effective evaluated count = `3000` per phase.
- Consolidated table: `artifacts/tests/fullscale_audit/summary/fullscale_phase_scores.md`
