# Phase A Task Breakdown (Instrumentation / Phase / Simulator)

## Plan Re-read Record
- phase: A
- timestamp_utc: 2026-03-09T00:00:00Z
- note: Re-read completed before implementation; phase gates acknowledged.

## Task Decomposition

| Task ID | Subtask | Input | Output | Owner | Acceptance Criteria | Status |
|---|---|---|---|---|---|
| A-1 | Event schema implementation | Existing Graph/Node runtime events | `AgentDropout/core/events.py` | core-agent | EventRecord serializes to JSON-compatible dict | ✅ |
| A-2 | Instrumentation logger | Event schema | `AgentDropout/core/instrumentation.py` | core-agent | Supports emit + JSONL dump + summary | ✅ |
| A-3 | Node-level read/execute tracing | Node predecessors + outputs | `message_read` / `node_execute_*` events | runtime-agent | Events emitted during `execute/async_execute` | ✅ |
| A-4 | Graph-level round tracing | round execution loop | `round_start/round_end/token_usage` events | runtime-agent | Round metadata persisted with phase tags | ✅ |
| A-5 | Phase scheduler | round index + sequence | `AgentDropout/core/phase.py` | policy-agent | `phase_at(round_idx)` deterministic and configurable | ✅ |
| A-6 | Offline replay summary | event jsonl | `AgentDropout/core/simulator.py` | analysis-agent | Produces event/phase/read-depth summary | ✅ |
| A-7 | MMLU-Redux 8-shard eval script | model + shard config | `experiments/evaluate_mmlu_redux.py` | benchmark-agent | Single shard run writes predictions/metrics/events | ✅ |
| A-8 | 8-shard parallel launcher | shard eval script | `experiments/run_mmlu_redux.py` | benchmark-agent | Launches 8 shard workers and aggregates summary | ✅ |
| A-9 | Reproducibility configs | phase and model constraints | `configs/common.yaml`, `configs/phase_a.yaml` | ops-agent | Configs document env/model/dataset/sharding | ✅ |
| A-10 | Phase documentation set | code + benchmark artifacts | phase markdown docs | documentation-agent | Report + benchmark + changelog complete | ✅ |

## Test Plan (Phase A)
1. Unit smoke: import new core modules and run basic serialization.
2. Runtime smoke: run a tiny local graph call and verify event JSONL output.
3. Benchmark smoke: run MMLU-Redux shard evaluation with small `max_samples_per_shard`.
4. 8-shard orchestration smoke: run launcher and verify shard logs + aggregated summary.

## Artifact Contract
- output root: `artifacts/runs/`
- per shard:
  - `metrics.json`
  - `predictions.jsonl`
  - `events/*.jsonl`
- run-level:
  - `summary.json`
  - `shard_process_logs.json`
