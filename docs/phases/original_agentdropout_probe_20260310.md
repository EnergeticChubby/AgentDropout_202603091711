# Original AgentDropout Probe (2026-03-10)

## User Question
Why current MMLU-Redux accuracy is far lower than paper-level MMLU numbers; run original AgentDropout first.

## Probe Runs

### 1) Original-style topology / decision
- command:
  - `python3 experiments/evaluate_mmlu_redux.py --llm_name qwen3-8b --split test --num_shards 8 --shard_idx 0 --max_samples 100 --num_rounds 1 --mode FullConnected --decision_method FinalRefer --agent_names AnalyzeAgent --agent_nums 5 --run_tag original-agentdropout-probe`
- output:
  - `artifacts/runs/mmlu_redux-original-agentdropout-probe-shard0/metrics.json`
  - accuracy: `0.25` (25/100)

### 2) Direct-answer baseline (same shard/sample cap)
- command:
  - `python3 experiments/evaluate_mmlu_redux.py --llm_name qwen3-8b --split test --num_shards 8 --shard_idx 0 --max_samples 100 --num_rounds 1 --mode DirectAnswer --decision_method FinalDirect --agent_names AnalyzeAgent --agent_nums 1 --run_tag directanswer-probe`
- output:
  - `artifacts/runs/mmlu_redux-directanswer-probe-shard0/metrics.json`
  - accuracy: `0.25` (25/100)

## Response Audit
- Both runs returned HTML-like payload for all 100/100 predictions (`<!doctype html>` / `<html ...>` content in `raw_answer`).
- Since raw model answers are malformed, postprocess fallback determines labels, capping realistic accuracy.

## Why this differs from paper numbers
1. Paper table corresponds to standard MMLU + specific base models (e.g., Qwen2.5-72B/DeepSeek-V3), not this endpoint behavior.
2. Current environment uses `qwen3-8b` on the provided endpoint; runtime returns HTML-like bodies instead of valid answer content.
3. Existing legacy `run_mmlu.py` path expects local `datasets/MMLU` assets (`datasets.MMLU.download`) which are absent in this repo snapshot, so probe used the working MMLU-Redux pipeline with original-style topology configuration.
