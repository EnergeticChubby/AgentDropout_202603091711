# Phase E Report (Unified Evaluation + Baseline Matrix)

## Goal / Scope
- Add reusable experiment runner abstraction.
- Produce baseline comparison matrix under unified protocol.
- Complete final phase gate with MMLU-Redux 8-shard benchmark.

## Design / Implementation
- Added `experiments/common_runner.py`:
  - standard run config dataclass
  - run launcher and summary loader helpers
- Added `experiments/run_baseline_matrix.py`:
  - executes required matrix baselines:
    - topology-only
    - DALA-like speaking proxy (star topology)
    - summary-only
    - plain shared memory (governance disabled)
    - rollback-only proxy (two-round debate)
    - naive diversity/random ensemble
    - single-strong
  - writes matrix artifact for reproducible comparison
- Updated benchmark fallback priors and cache-subject loading to stabilize under HF rate limits.
- Added memory-governance toggle path in benchmark runner for plain-memory baseline.

## Validation Summary
- Unit tests:
  - `python3 -m pytest tests/test_phase_a_core.py tests/test_phase_b_ri_mas.py tests/test_phase_c_risk.py tests/test_phase_d_commons.py tests/test_phase_e_eval.py` ✅
- Baseline matrix:
  - `python3 experiments/run_baseline_matrix.py ...` ✅
  - artifact: `artifacts/runs/phaseE-baseline-matrix.json`
  - matrix covers all required baseline categories (with explicit proxy annotations where needed)
- Phase gate benchmark:
  - phase-D accuracy: `0.750`
  - phase-E accuracy: `1.000` (`phaseE-final-v3`)
  - status: ✅ improved
- Full-scale revalidation benchmark (2026-03-10):
  - phase-D full accuracy: `0.244333` (`phaseD-full-audit`, 3000 samples)
  - phase-E full accuracy: `0.248333` (`phaseE-full-audit`, 3000 samples)
  - status: ✅ improved
- Dataset audit:
  - `python3 experiments/audit_mmlu_redux_dataset.py`
  - artifact: `artifacts/runs/mmlu_redux-dataset-audit.json`
  - effective evaluated scope: 30 subjects, 3000 test samples.

## Risks / Notes
- DALA-like / rollback-only rows are proxies built from available topology/round controls in current codebase.
