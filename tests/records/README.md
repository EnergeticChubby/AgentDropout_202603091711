# Test Records Index

This directory stores reproducible test evidence.

## Storage Standard

- One Markdown file (`.md`) per test run.
- One raw log (`.log`) per test run.
- Shared prefix naming: `<UTC timestamp>_<phase_name>`.

## Recommended Workflow

1. Run test via `tests/code/run_test_and_record.sh`.
2. Review generated Markdown and log.
3. Commit test records in the same phase commit.

## Example

`bash tests/code/run_test_and_record.sh phase_C_validation git status --short`

