# Reproducible Test Report

- Run ID: `phase_08_20260311_phase0_full_val`
- UTC Time: `2026-03-11T12:43:01Z`
- Branch: `AdamMartinez6793_v2`
- Commit: `de3e2c748d923ad8d6562808ade3608f10826d40`

## Result Summary

| Check | Status | Command | Log |
|---|---|---|---|
| python_version | PASS | `python3 --version` | `tests/records/phase_08_20260311_phase0_full_val/logs/python_version.log` |
| git_revision | PASS | `git rev-parse HEAD` | `tests/records/phase_08_20260311_phase0_full_val/logs/git_revision.log` |
| py_compile | PASS | `python3 -m py_compile AgentDropout/llm/gpt_chat.py experiments/evaluate_mmlu.py experiments/run_gsm8k.py experiments/run_aqua.py experiments/run_svamp.py experiments/run_multiarith.py experiments/run_humaneval.py experiments/run_mmlu.py tests/repro/check_unified_config.py tests/repro/test_mmlu_retry_behavior.py tests/repro/test_phase0_agentdropout_local.py tests/repro/test_phase0_full_val_local.py` | `tests/records/phase_08_20260311_phase0_full_val/logs/py_compile.log` |
| config_assertions | PASS | `python3 tests/repro/check_unified_config.py` | `tests/records/phase_08_20260311_phase0_full_val/logs/config_assertions.log` |
| mmlu_retry_behavior | PASS | `python3 tests/repro/test_mmlu_retry_behavior.py` | `tests/records/phase_08_20260311_phase0_full_val/logs/mmlu_retry_behavior.log` |
| phase0_agentdropout_local | FAIL | `python3 tests/repro/test_phase0_agentdropout_local.py` | `tests/records/phase_08_20260311_phase0_full_val/logs/phase0_agentdropout_local.log` |
| phase0_full_val_local | PASS | `python3 tests/repro/test_phase0_full_val_local.py` | `tests/records/phase_08_20260311_phase0_full_val/logs/phase0_full_val_local.log` |

## Reproduction Command

`bash scripts/run_repro_tests.sh <run_id>`

## Exit Criteria

- PASS if all checks are PASS.
- FAIL if any check is FAIL.
