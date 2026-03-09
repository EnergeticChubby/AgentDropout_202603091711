# Phase B Task Breakdown (RI-MAS MVP)

## Plan Re-read Record
- phase: B
- timestamp_utc: 2026-03-09T00:00:00Z
- note: Full plan re-read completed before Phase-B implementation.

## Task / SubAgent Decomposition

| Task ID | Subtask | Input | Output | Owner | Acceptance Criteria | Status |
|---|---|---|---|---|---|---|
| B-1 | Message schema module | agent raw text outputs | `AgentDropout/core/message_schema.py` | message-agent | headline/claims/evidence/full conversion + render by read level | ✅ |
| B-2 | Attention policy module | phase + context + peer output | `AgentDropout/core/attention_policy.py` | policy-agent | 5-level read decision with conflict escalation | ✅ |
| B-3 | Value/Cost estimator modules | read-level transitions | `value_estimator.py`, `cost_model.py` | optimization-agent | heuristic utility/cost estimates callable | ✅ |
| B-4 | Node read-resolution integration | predecessors + attention policy | `Node.get_spatial_info/get_temporal_info` | runtime-agent | supports ignore/summary/claims/evidence/full render path | ✅ |
| B-5 | Graph phase-aware context injection | round phase + peer outputs | `_build_attention_context` + execute kwargs | runtime-agent | node execution receives phase-aware attention context | ✅ |
| B-6 | Agent structured output upgrade | analyze/math/code agents | structured multilayer outputs | agent-agent | non-decision agents emit multilayer dict payload | ✅ |
| B-7 | Offline policy training script | event logs jsonl | `experiments/train_attention_policy.py` | training-agent | emits phase-level learned policy json | ✅ |
| B-8 | Benchmark parser robustness | non-standard endpoint payload | lexical fallback in postprocess | benchmark-agent | invalid response still maps to legal A/B/C/D | ✅ |

## Verification Checklist
1. Unit test suite remains green.
2. Event replay still produces summaries.
3. MMLU-Redux 8-shard benchmark (`phaseB-final`) > Phase-A final accuracy.
