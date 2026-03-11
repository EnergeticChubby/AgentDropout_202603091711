# Project Plan: Reproducible Testing and Documentation Governance

## 1. Objective

This plan defines mandatory engineering rules for this repository:

1. All test code must be versioned.
2. All test records must be stored in-repo and reproducible.
3. All project markdown must follow professional technical writing standards.
4. Every phase update must be committed independently.

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

## 4. Phase-Based Delivery and Commit Policy

This repository follows strict phase commits.

### Mandatory rule

- Every phase update must end with one dedicated commit.
- Do not merge multiple phases into a single commit.
- Commit message format: `Phase <N>: <concise outcome>`.

### Required phase workflow

1. **Phase 1: Test code update**
   - add or update reproducible test scripts/assertions
   - commit
2. **Phase 2: Test execution and record storage**
   - execute tests
   - store report + raw logs
   - commit
3. **Phase 3: Documentation and plan update**
   - update markdown docs and plan
   - commit

## 5. Markdown Writing Standards (Professional Quality)

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

## 6. Operational Checklist

Before pushing updates, confirm:

- [ ] reproducible test code is committed
- [ ] reproducible test records are committed
- [ ] markdown docs are updated with current behavior
- [ ] each phase has its own commit
- [ ] branch is synchronized with remote
