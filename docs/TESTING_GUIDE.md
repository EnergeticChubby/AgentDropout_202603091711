# Testing Guide: Code, Records, and Reproducibility

## Scope

This guide defines how to:

1. add test code,
2. execute tests reproducibly, and
3. store complete, auditable test records.

It also defines phase-gated benchmark rules:

4. re-read `PLAN.md` before every phase,
5. run optimized MMLU benchmark after every phase,
6. require benchmark improvement before phase transition.

## Directory Convention

- Test code: `tests/repro/`
- Test runners: `scripts/`
- Test records: `tests/records/<run_id>/`
  - report: `test_report.md`
  - raw logs: `logs/*.log`

## Required Workflow

### Step 0: Re-read full plan before current phase

- Fully re-read `PLAN.md`.
- Do this before phase planning, implementation, or subagent execution.

### Step 1: Update or add test code

- Add assertions under `tests/repro/`.
- Keep tests deterministic and file-based where possible.
- Avoid tests that require hidden shell/session state.

### Step 2: Run the canonical reproducibility command

```bash
bash scripts/run_repro_tests.sh <run_id>
```

Example:

```bash
bash scripts/run_repro_tests.sh phase_02_20260311
```

### Step 3: Validate generated outputs

Confirm:

1. `tests/records/<run_id>/test_report.md` exists.
2. each command in the report has a corresponding raw log file.
3. report status table matches raw log outcomes.

### Step 4: Commit by phase

- One phase, one commit.
- Never batch multiple phases into one commit.
- Use explicit commit messages, for example:
  - `Phase 1: add reproducible test scripts`
  - `Phase 2: store reproducible test records`
  - `Phase 3: update plan and markdown governance`

### Step 5: Execute optimized MMLU benchmark (phase gate)

After each phase commit candidate:

1. run optimized MMLU benchmark,
2. store all outputs under `tests/benchmarks/mmlu/phase_<N>/`,
3. generate `benchmark_report.md` and raw logs,
4. update `tests/benchmarks/mmlu/INDEX.md`.

### Step 6: Verify benchmark promotion rule

Gate condition:

- current phase score must be strictly better than previous phase score.

If not better:

1. keep all generated benchmark data,
2. continue optimization/fine-tuning in the same phase,
3. rerun benchmark and compare again,
4. repeat until better.

### Step 7: Auto-transition

Move to next phase only after both are true:

1. phase update is committed,
2. benchmark promotion rule is satisfied.

## Report Quality Requirements

Each `test_report.md` must include:

1. run metadata: run id, UTC time, branch, commit
2. summary table with exact commands
3. pass/fail status for each check
4. reproduction command
5. clear exit criteria

For benchmark reports (`benchmark_report.md`), include:

1. phase id and benchmark timestamp,
2. benchmark command(s),
3. score and scoring definition,
4. previous-phase score and score delta,
5. promotion gate pass/fail conclusion.

## Markdown Professional Standards

- Use concise, precise technical language.
- Use heading hierarchy consistently.
- Use monospace for commands, paths, and identifiers.
- Keep operational content executable without interpretation.
