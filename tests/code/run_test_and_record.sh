#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <phase_name> <command> [args...]" >&2
  exit 2
fi

phase_name="$1"
shift

record_dir="${TEST_RECORD_DIR:-tests/records}"
mkdir -p "$record_dir"

timestamp_utc="$(date -u +%Y%m%dT%H%M%SZ)"
phase_slug="$(echo "$phase_name" | tr '[:space:]/' '__' | tr -cd '[:alnum:]_.-')"
md_file="${record_dir}/${timestamp_utc}_${phase_slug}.md"
log_file="${record_dir}/${timestamp_utc}_${phase_slug}.log"

branch_name="$(git rev-parse --abbrev-ref HEAD)"
commit_hash="$(git rev-parse HEAD)"
workdir="$(pwd)"
escaped_cmd="$(printf '%q ' "$@")"
escaped_cmd="${escaped_cmd% }"

model_name="N/A"
base_url="N/A"
env_file="template.env"
if [[ -f "$env_file" ]]; then
  model_name="$(awk -F= '/^MODEL_NAME=/{print $2; exit}' "$env_file" | tr -d '"' || true)"
  base_url="$(awk -F= '/^BASE_URL=/{print $2; exit}' "$env_file" | tr -d '"' || true)"
fi

{
  echo "# Test Record: ${phase_name}"
  echo
  echo "## Goal"
  echo "- Validate command execution and keep reproducible evidence."
  echo
  echo "## Preconditions"
  echo "- Repository is clean enough for this test scope."
  echo "- Required dependencies for target command are available."
  echo
  echo "## Command"
  echo "- \`${escaped_cmd}\`"
  echo
  echo "## Environment Snapshot"
  echo "- Timestamp (UTC): ${timestamp_utc}"
  echo "- Branch: \`${branch_name}\`"
  echo "- Commit: \`${commit_hash}\`"
  echo "- Workdir: \`${workdir}\`"
  echo "- Model: \`${model_name}\`"
  echo "- Base URL: \`${base_url}\`"
  echo
  echo "## Output Summary"
  echo "- Raw log: \`${log_file}\`"
  echo
  echo "## Exit Code"
} > "$md_file"

set +e
"$@" 2>&1 | tee "$log_file"
cmd_exit="${PIPESTATUS[0]}"
set -e

{
  echo "- \`${cmd_exit}\`"
  echo
  echo "## Reproduction Steps"
  echo "1. Checkout branch \`${branch_name}\`."
  echo "2. Ensure \`template.env\` contains expected test configuration."
  echo "3. Run command:"
  echo "   \`${escaped_cmd}\`"
  echo
  echo "## Conclusion"
  if [[ "$cmd_exit" -eq 0 ]]; then
    echo "- PASS: command finished successfully."
  else
    echo "- FAIL: command returned non-zero exit code."
  fi
} >> "$md_file"

echo "Generated:"
echo "  - ${md_file}"
echo "  - ${log_file}"

exit "$cmd_exit"

