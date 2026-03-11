# Testing Guide: Code, Records, and Reproducibility

## Scope

This guide defines how to:

1. add test code,
2. execute tests reproducibly, and
3. store complete, auditable test records.

## Directory Convention

- Test code: `tests/repro/`
- Test runners: `scripts/`
- Test records: `tests/records/<run_id>/`
  - report: `test_report.md`
  - raw logs: `logs/*.log`

## Required Workflow

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

## Report Quality Requirements

Each `test_report.md` must include:

1. run metadata: run id, UTC time, branch, commit
2. summary table with exact commands
3. pass/fail status for each check
4. reproduction command
5. clear exit criteria

## Markdown Professional Standards

- Use concise, precise technical language.
- Use heading hierarchy consistently.
- Use monospace for commands, paths, and identifiers.
- Keep operational content executable without interpretation.
