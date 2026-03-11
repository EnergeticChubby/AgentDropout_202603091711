#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RUN_ID="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
RECORD_DIR="$ROOT_DIR/tests/records/$RUN_ID"
LOG_DIR="$RECORD_DIR/logs"
REPORT_PATH="$RECORD_DIR/test_report.md"

mkdir -p "$LOG_DIR"

declare -i FAILED=0
RESULT_ROWS=()

run_and_record() {
  local name="$1"
  shift
  local log_file="$LOG_DIR/${name}.log"
  local cmd_display
  cmd_display="$(printf "%q " "$@")"
  cmd_display="${cmd_display% }"

  {
    echo "# Command"
    echo "$cmd_display"
    echo
    echo "# Output"
  } > "$log_file"

  if "$@" >> "$log_file" 2>&1; then
    RESULT_ROWS+=("| ${name} | PASS | \`${cmd_display}\` | \`${log_file#$ROOT_DIR/}\` |")
  else
    RESULT_ROWS+=("| ${name} | FAIL | \`${cmd_display}\` | \`${log_file#$ROOT_DIR/}\` |")
    FAILED+=1
  fi
}

run_and_record "python_version" python3 --version
run_and_record "git_revision" git rev-parse HEAD
run_and_record \
  "py_compile" \
  python3 -m py_compile \
  AgentDropout/llm/gpt_chat.py \
  experiments/evaluate_mmlu.py \
  experiments/run_gsm8k.py \
  experiments/run_aqua.py \
  experiments/run_svamp.py \
  experiments/run_multiarith.py \
  experiments/run_humaneval.py \
  experiments/run_mmlu.py \
  tests/repro/check_unified_config.py \
  tests/repro/test_mmlu_retry_behavior.py
run_and_record "config_assertions" python3 tests/repro/check_unified_config.py
run_and_record "mmlu_retry_behavior" python3 tests/repro/test_mmlu_retry_behavior.py

{
  echo "# Reproducible Test Report"
  echo
  echo "- Run ID: \`${RUN_ID}\`"
  echo "- UTC Time: \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`"
  echo "- Branch: \`$(git rev-parse --abbrev-ref HEAD)\`"
  echo "- Commit: \`$(git rev-parse HEAD)\`"
  echo
  echo "## Result Summary"
  echo
  echo "| Check | Status | Command | Log |"
  echo "|---|---|---|---|"
  for row in "${RESULT_ROWS[@]}"; do
    echo "$row"
  done
  echo
  echo "## Reproduction Command"
  echo
  echo "\`bash scripts/run_repro_tests.sh <run_id>\`"
  echo
  echo "## Exit Criteria"
  echo
  echo "- PASS if all checks are PASS."
  echo "- FAIL if any check is FAIL."
} > "$REPORT_PATH"

if (( FAILED > 0 )); then
  echo "Repro test failed. See: ${REPORT_PATH}"
  exit 1
fi

echo "Repro test passed. Report: ${REPORT_PATH}"
