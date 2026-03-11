# Project Plan: Reproducible Testing, Benchmark Gating, and Phase Governance

## 1. Objective

This plan defines mandatory engineering rules for this repository:

1. All test code must be versioned.
2. All test records must be stored in-repo and reproducible.
3. All benchmark records must be preserved and comparable across phases.
4. All project markdown must follow professional technical writing standards.
5. Every phase update must be committed independently.
6. A phase can proceed only after benchmark improvement is validated.

## 2. Fixed Test Configuration (Unified Baseline)

All testing and experiment defaults use the following baseline:

- `TEST_MODEL`: `glm-4.5-flash`
- `BASE_URL`: `https://llm.undefined.qzz.io/v1/chat/completions`
- `API_KEY`: managed via `.env` derived from `template.env`

Reference implementation:

- `template.env`
- `AgentDropout/llm/gpt_chat.py`
- `experiments/run_*.py` default `--llm_name`

## 3. Reproducibility Standards

### 3.1 Required assets per test run

For each test run, store the following under `tests/records/<run_id>/`:

1. `test_report.md` with:
   - run id
   - UTC time
   - branch
   - commit SHA
   - command table
   - pass/fail summary
2. raw logs for every command under `tests/records/<run_id>/logs/`
3. exact command entry point used to reproduce the run

### 3.2 Reproduction entry point

- canonical command: `bash scripts/run_repro_tests.sh <run_id>`
- no hidden manual steps
- no dependency on transient shell state

### 3.3 Minimum checks in automated reproducibility suite

1. Python runtime visibility (`python3 --version`)
2. Source revision visibility (`git rev-parse HEAD`)
3. Syntax integrity of modified Python files (`python3 -m py_compile ...`)
4. Configuration integrity assertions (`python3 tests/repro/check_unified_config.py`)

## 4. Phase Execution Governance

### 4.1 Mandatory full plan re-read before each phase

Before starting any phase, the executor must fully re-read `PLAN.md` from top to bottom. Partial reading is not allowed.

### 4.2 Task and subagent decomposition requirement

When executing tasks (including task/subagent workflows), each phase must be decomposed into explicit sub-tasks:

1. implementation sub-tasks
2. validation and reproducibility sub-tasks
3. benchmark sub-tasks
4. documentation and archival sub-tasks

The decomposition must be written in markdown and stored in the phase report.

### 4.3 Phase commit policy

- Every phase update must end with at least one dedicated commit.
- Do not merge multiple phases into one commit.
- Commit message format: `Phase <N>: <concise outcome>`.

### 4.4 Mandatory optimized MMLU benchmark gate after each phase

After completing each phase, run an optimized MMLU benchmark before moving forward.

Required benchmark artifacts for phase `N`:

- directory: `tests/benchmarks/mmlu/phase_<N>/`
- `benchmark_report.md`
- raw command logs
- model outputs/predictions used for scoring
- score summary and method note

### 4.5 Benchmark promotion rule (hard gate)

Let `Score(N)` be the benchmark score for phase `N`.

Mandatory gate:

- `Score(N) > Score(N-1)` (strictly greater)

If the condition is not met:

1. continue optimization/fine-tuning within the same phase,
2. rerun optimized MMLU benchmark,
3. keep all intermediate benchmark records,
4. repeat until the promotion rule is satisfied.

### 4.6 Automatic transition to next phase

A phase is considered complete only when both conditions are true:

1. phase work is committed,
2. optimized MMLU benchmark is executed and passes the promotion rule.

After both are satisfied, proceed automatically to the next phase.

### 4.7 Full-val benchmark requirement with failed-question retest

All benchmark testing must use the complete MMLU `val` split.

- partial evaluation is not allowed for phase gating.
- `limit_questions` must remain `None` for phase benchmark runs.

Because high API concurrency can cause transient failures, failed questions must be re-tested:

1. per-question retry with backoff,
2. additional rerun rounds for unresolved failed questions,
3. mark phase as incomplete if any question remains unresolved.

## 5. Benchmark Data Retention and Indexing

All MMLU benchmark data must be retained in-repo.

- phase benchmark root: `tests/benchmarks/mmlu/`
- global index: `tests/benchmarks/mmlu/INDEX.md`
- each phase entry must include:
  - phase id
  - benchmark timestamp
  - branch
  - commit SHA
  - score
  - delta vs previous phase
  - total question count (must match full `val` split)
  - unresolved failure count (must be `0` for gate pass)
  - report/log paths

Deleting failed or intermediate benchmark runs is not allowed.

## 6. Markdown Writing Standards (Professional Quality)

All markdown files must satisfy:

1. Clear structure:
   - title
   - objective/context
   - procedure
   - evidence
   - conclusion
2. Operational precision:
   - use exact commands
   - avoid ambiguous wording
3. Auditability:
   - include version/commit references when relevant
4. Reusability:
   - steps should be executable by another engineer without private context

## 7. Operational Checklist

Before pushing updates, confirm:

- [ ] full `PLAN.md` re-read is completed for the current phase
- [ ] phase tasks are decomposed (including task/subagent sub-tasks)
- [ ] reproducible test code is committed
- [ ] reproducible test records are committed
- [ ] optimized MMLU benchmark is executed for the phase
- [ ] benchmark uses complete MMLU `val` split (no partial subset)
- [ ] benchmark score is strictly better than previous phase
- [ ] failed questions are re-tested until unresolved count is `0`
- [ ] benchmark data and logs are fully retained
- [ ] markdown docs are updated with current behavior
- [ ] each phase has its own commit
- [ ] branch is synchronized with remote
