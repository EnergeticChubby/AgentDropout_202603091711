# Reproducible Test Report

- Run ID: `phase_02_20260311`
- UTC Time: `2026-03-11T08:43:44Z`
- Branch: `AdamMartinez6793_v2`
- Commit: `5782c2b8379bf3243afbf4c6a33384ec006e3c44`

## Result Summary

| Check | Status | Command | Log |
|---|---|---|---|
| python_version | PASS | `python3 --version` | `tests/records/phase_02_20260311/logs/python_version.log` |
| git_revision | PASS | `git rev-parse HEAD` | `tests/records/phase_02_20260311/logs/git_revision.log` |
| py_compile | PASS | `python3 -m py_compile AgentDropout/llm/gpt_chat.py experiments/run_gsm8k.py experiments/run_aqua.py experiments/run_svamp.py experiments/run_multiarith.py experiments/run_humaneval.py experiments/run_mmlu.py tests/repro/check_unified_config.py` | `tests/records/phase_02_20260311/logs/py_compile.log` |
| config_assertions | PASS | `python3 tests/repro/check_unified_config.py` | `tests/records/phase_02_20260311/logs/config_assertions.log` |

## Reproduction Command

`bash scripts/run_repro_tests.sh <run_id>`

## Exit Criteria

- PASS if all checks are PASS.
- FAIL if any check is FAIL.
