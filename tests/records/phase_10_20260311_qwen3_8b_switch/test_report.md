# Reproducible Test Report

- Run ID: `phase_10_20260311_qwen3_8b_switch`
- UTC Time: `2026-03-11T13:06:50Z`
- Branch: `AdamMartinez6793_v2`
- Commit: `79c87aa02e0b966ea4f615ce07d01b9f5d731cbb`

## Result Summary

| Check | Status | Command | Log |
|---|---|---|---|
| python_version | PASS | `python3 --version` | `tests/records/phase_10_20260311_qwen3_8b_switch/logs/python_version.log` |
| git_revision | PASS | `git rev-parse HEAD` | `tests/records/phase_10_20260311_qwen3_8b_switch/logs/git_revision.log` |
| py_compile | PASS | `python3 -m py_compile AgentDropout/llm/gpt_chat.py experiments/evaluate_mmlu.py experiments/run_gsm8k.py experiments/run_aqua.py experiments/run_svamp.py experiments/run_multiarith.py experiments/run_humaneval.py experiments/run_mmlu.py tests/repro/check_unified_config.py tests/repro/test_mmlu_retry_behavior.py tests/repro/test_phase0_agentdropout_local.py tests/repro/test_phase0_full_val_local.py` | `tests/records/phase_10_20260311_qwen3_8b_switch/logs/py_compile.log` |
| config_assertions | PASS | `python3 tests/repro/check_unified_config.py` | `tests/records/phase_10_20260311_qwen3_8b_switch/logs/config_assertions.log` |
| mmlu_retry_behavior | PASS | `python3 tests/repro/test_mmlu_retry_behavior.py` | `tests/records/phase_10_20260311_qwen3_8b_switch/logs/mmlu_retry_behavior.log` |
| phase0_agentdropout_local | PASS | `python3 tests/repro/test_phase0_agentdropout_local.py` | `tests/records/phase_10_20260311_qwen3_8b_switch/logs/phase0_agentdropout_local.log` |
| phase0_full_val_local | PASS | `python3 tests/repro/test_phase0_full_val_local.py` | `tests/records/phase_10_20260311_qwen3_8b_switch/logs/phase0_full_val_local.log` |

## Reproduction Command

`bash scripts/run_repro_tests.sh <run_id>`

## Exit Criteria

- PASS if all checks are PASS.
- FAIL if any check is FAIL.
