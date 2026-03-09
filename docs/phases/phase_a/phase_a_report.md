# Phase A Report

## Goal / Scope
- Build shared execution foundations:
  - instrumentation events
  - phase scheduler
  - offline simulator
  - MMLU-Redux 8-shard benchmark pipeline

## Design & Implementation
- See `phase_a_tasks.md` for detailed task decomposition.
- Key modules:
  - `AgentDropout/core/events.py`
  - `AgentDropout/core/instrumentation.py`
  - `AgentDropout/core/phase.py`
  - `AgentDropout/core/simulator.py`
- Runtime integration:
  - `Graph.arun/run` now emit `round_start`, `round_end`, `memory_write`, `token_usage`, `message_send`.
  - `Node.execute/async_execute` now emit `node_execute_start/end` and `message_read`.
  - token accounting exposes hook API via `AgentDropout/llm/price.py`.
- Benchmark plumbing:
  - `benchmark_datasets/mmlu_redux_dataset.py`
  - `experiments/evaluate_mmlu_redux.py`
  - `experiments/run_mmlu_redux.py`
  - `experiments/replay_simulation.py`

## Runtime / Config
- Model: `qwen3-8b`
- Dataset: `edinburgh-dawg/mmlu-redux`
- Parallel strategy: `8-shard`

## Validation Summary
- Unit tests:
  - `python3 -m pytest tests/test_phase_a_core.py` ✅ (2 passed)
- Replay simulator smoke:
  - command: `python3 experiments/replay_simulation.py --events_jsonl ...`
  - output: `total_events=9`, `avg_read_depth=4.0` ✅
- Benchmark gate:
  - baseline run `phaseA-baseline`: accuracy `0.000`
  - optimized run `phaseA-final`: accuracy `0.375`
  - gate status: ✅ improved over previous phase

## Risks / Follow-up
- Endpoint currently sometimes returns HTML payload or non-standard completion objects.
- Token usage fields remain zero with current endpoint response shape; next phase will add provider-specific token parsing fallback.
