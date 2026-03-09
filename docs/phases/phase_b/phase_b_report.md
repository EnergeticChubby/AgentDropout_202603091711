# Phase B Report (RI-MAS MVP)

## Goal / Scope
- Implement RI-MAS MVP:
  - multilayer message protocol
  - phase-aware five-level read policy
  - conflict-triggered escalation
  - offline policy training pipeline

## Design / Implementation
- New core modules:
  - `AgentDropout/core/message_schema.py`
  - `AgentDropout/core/attention_policy.py`
  - `AgentDropout/core/value_estimator.py`
  - `AgentDropout/core/cost_model.py`
- Runtime integration:
  - `Node` now supports read-resolution control and emits `message_skip` / variable `message_read` depth.
  - `Graph` injects `attention_context` with conflict peers and uncertainty flags.
- Agent output adaptation:
  - non-decision agents now emit structured multilayer outputs.

## Offline Learning
- Added `experiments/train_attention_policy.py`
- Input: event logs JSONL
- Output: phase-level learned default read depths

## Validation Summary
- Unit tests:
  - `python3 -m pytest tests/test_phase_a_core.py tests/test_phase_b_ri_mas.py` ✅ (5 passed)
- Offline policy training:
  - `python3 experiments/train_attention_policy.py ...` ✅
  - output: `artifacts/runs/phaseB-attention-policy.json`
- Replay check:
  - sample replay summary shows `avg_read_depth=2.0`, proving read-resolution control is active.
- Phase gate benchmark:
  - phase-A accuracy: `0.375`
  - phase-B accuracy: `0.500`
  - status: ✅ improved

## Risks / Notes
- Upstream endpoint response shape remains non-standard; benchmark parser includes fallback path for reproducible evaluation.
