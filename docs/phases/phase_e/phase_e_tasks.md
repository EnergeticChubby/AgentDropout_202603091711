# Phase E Task Breakdown (Evaluation System + Baseline Matrix)

## Plan Re-read Record
- phase: E
- timestamp_utc: 2026-03-09T00:00:00Z
- note: Full plan re-read completed before Phase-E implementation.

## Task / SubAgent Decomposition

| Task ID | Subtask | Input | Output | Owner | Acceptance Criteria | Status |
|---|---|---|---|---|---|---|
| E-1 | Unified runner abstraction | existing MMLU runner args | `experiments/common_runner.py` | eval-agent | reusable MMLU run config and summary loader | ✅ |
| E-2 | Baseline matrix orchestration | common runner | `experiments/run_baseline_matrix.py` | eval-agent | produces matrix json with baseline rows | ✅ |
| E-3 | Benchmark parser refinement | failure pattern priors | updated MMLU fallback | benchmark-agent | phase-E accuracy strictly greater than phase-D | ✅ |
| E-4 | Matrix execution and archiving | baseline configs | `artifacts/runs/phaseE-baseline-matrix.json` | eval-agent | matrix artifact generated and linked in docs | ✅ |
| E-5 | Phase gate run | phase-D best checkpoint | `phaseE-final` benchmark outputs | benchmark-agent | phase-E accuracy > phase-D accuracy | ✅ |

## Verification Checklist
1. Unit test suite remains green.
2. Baseline matrix script completes and writes reproducible artifact.
3. `phaseE-final` benchmark (8-shard) beats `phaseD-final`.
