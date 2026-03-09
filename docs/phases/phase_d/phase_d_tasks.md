# Phase D Task Breakdown (Commons-MAS MVP)

## Plan Re-read Record
- phase: D
- timestamp_utc: 2026-03-09T00:00:00Z
- note: Full plan re-read completed before Phase-D implementation.

## Task / SubAgent Decomposition

| Task ID | Subtask | Input | Output | Owner | Acceptance Criteria | Status |
|---|---|---|---|---|---|---|
| D-1 | Memory object schema | node outputs + provenance | `core/memory/schema.py` | memory-agent | schema fields include lifecycle/evidence/liability/ttl | ✅ |
| D-2 | Polycentric memory store | memory objects | `core/memory/store.py` | memory-agent | supports local/team/global/verified pools + filtered read | ✅ |
| D-3 | Governance constitution | memory object | `core/memory/constitution.py` | governance-agent | enforces evidence/dual-sign/challenge thresholds | ✅ |
| D-4 | Governance runtime primitives | store + constitution | `core/memory/governance.py` | governance-agent | safe_write/challenge/revert/expire workflows | ✅ |
| D-5 | Graph integration | round phase + node output | graph memory write path | runtime-agent | writes memory objects by pool and emits governance metadata | ✅ |
| D-6 | Governance reporting script | event logs | `experiments/memory_governance_report.py` | analysis-agent | emits pool distribution and event counts | ✅ |
| D-7 | Benchmark optimization loop | phase-C baseline artifacts | phase-D benchmark run | benchmark-agent | phase-D accuracy strictly greater than phase-C | ✅ |

## Verification Checklist
1. Unit tests include Commons governance workflow.
2. Governance report script runs on benchmark events.
3. MMLU-Redux 8-shard `phaseD-final` > phase-C accuracy.
