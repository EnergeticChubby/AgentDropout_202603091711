# Reproducible Test Report

- Run ID: `phase_05_20260311_full_val_retry_rerun2`
- UTC Time: `2026-03-11T09:34:53Z`
- Branch: `AdamMartinez6793_v2`
- Commit: `8d7e322841b2c3d32d5ea11baaa163fa1eea3bbe`

## Result Summary

| Check | Status | Command | Log |
|---|---|---|---|
| python_version | PASS | `python3 --version` | `tests/records/phase_05_20260311_full_val_retry_rerun2/logs/python_version.log` |
| git_revision | PASS | `git rev-parse HEAD` | `tests/records/phase_05_20260311_full_val_retry_rerun2/logs/git_revision.log` |
| py_compile | PASS | `python3 -m py_compile AgentDropout/llm/gpt_chat.py experiments/evaluate_mmlu.py experiments/run_gsm8k.py experiments/run_aqua.py experiments/run_svamp.py experiments/run_multiarith.py experiments/run_humaneval.py experiments/run_mmlu.py tests/repro/check_unified_config.py tests/repro/test_mmlu_retry_behavior.py` | `tests/records/phase_05_20260311_full_val_retry_rerun2/logs/py_compile.log` |
| config_assertions | PASS | `python3 tests/repro/check_unified_config.py` | `tests/records/phase_05_20260311_full_val_retry_rerun2/logs/config_assertions.log` |
| mmlu_retry_behavior | FAIL | `python3 tests/repro/test_mmlu_retry_behavior.py` | `tests/records/phase_05_20260311_full_val_retry_rerun2/logs/mmlu_retry_behavior.log` |

## Reproduction Command

`bash scripts/run_repro_tests.sh <run_id>`

## Exit Criteria

- PASS if all checks are PASS.
- FAIL if any check is FAIL.
