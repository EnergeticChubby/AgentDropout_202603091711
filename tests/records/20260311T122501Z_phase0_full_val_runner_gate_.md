# Test Record: phase0_full_val_runner_gate

## Goal
- Validate command execution and keep reproducible evidence.

## Preconditions
- Repository is clean enough for this test scope.
- Required dependencies for target command are available.

## Command
- `bash tests/code/run_phase0_full_val.sh`

## Environment Snapshot
- Timestamp (UTC): 20260311T122501Z
- Branch: `gz10_v2`
- Commit: `51c05d6adf32f030c54f20a9f65d814a4a405aef`
- Workdir: `/workspace`
- Model: `glm-4.5-flash`
- Base URL: `https://llm.undefined.qzz.io/v1/chat/completions`

## Output Summary
- Raw log: `tests/records/20260311T122501Z_phase0_full_val_runner_gate_.log`

## Exit Code
- `1`

## Reproduction Steps
1. Checkout branch `gz10_v2`.
2. Ensure `template.env` contains expected test configuration.
3. Run command:
   `bash tests/code/run_phase0_full_val.sh`

## Conclusion
- FAIL: command returned non-zero exit code.
