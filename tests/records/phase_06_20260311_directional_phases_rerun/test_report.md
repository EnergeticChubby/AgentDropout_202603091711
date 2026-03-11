# Reproducible Test Report

- Run ID: `phase_06_20260311_directional_phases_rerun`
- UTC Time: `2026-03-11T10:27:00Z`
- Branch: `AdamMartinez6793_v2`
- Commit: `95bcdb54de540d0aedbd2de7e7c0c3d618a8fb57`

## Result Summary

| Check | Status | Command | Log |
|---|---|---|---|
| python_version | PASS | `python3 --version` | `tests/records/phase_06_20260311_directional_phases_rerun/logs/python_version.log` |
| git_revision | PASS | `git rev-parse HEAD` | `tests/records/phase_06_20260311_directional_phases_rerun/logs/git_revision.log` |
| py_compile | PASS | `python3 -m py_compile AgentDropout/llm/gpt_chat.py experiments/evaluate_mmlu.py experiments/run_gsm8k.py experiments/run_aqua.py experiments/run_svamp.py experiments/run_multiarith.py experiments/run_humaneval.py experiments/run_mmlu.py tests/repro/check_unified_config.py tests/repro/test_mmlu_retry_behavior.py tests/repro/test_phase0_agentdropout_local.py` | `tests/records/phase_06_20260311_directional_phases_rerun/logs/py_compile.log` |
| config_assertions | PASS | `python3 tests/repro/check_unified_config.py` | `tests/records/phase_06_20260311_directional_phases_rerun/logs/config_assertions.log` |
| mmlu_retry_behavior | PASS | `python3 tests/repro/test_mmlu_retry_behavior.py` | `tests/records/phase_06_20260311_directional_phases_rerun/logs/mmlu_retry_behavior.log` |
| phase0_agentdropout_local | PASS | `python3 tests/repro/test_phase0_agentdropout_local.py` | `tests/records/phase_06_20260311_directional_phases_rerun/logs/phase0_agentdropout_local.log` |

## Reproduction Command

`bash scripts/run_repro_tests.sh <run_id>`

## Exit Criteria

- PASS if all checks are PASS.
- FAIL if any check is FAIL.
