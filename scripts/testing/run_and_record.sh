#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage:"
  echo "  $0 --phase <phase_name> --name <test_name> [--root <record_root>] -- <command...>"
  echo
  echo "Example:"
  echo "  $0 --phase phase1_baseline --name gsm8k_smoke -- python3 experiments/run_gsm8k.py --help"
}

PHASE=""
TEST_NAME=""
ROOT="result/test_records"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --phase)
      PHASE="${2:-}"
      shift 2
      ;;
    --name)
      TEST_NAME="${2:-}"
      shift 2
      ;;
    --root)
      ROOT="${2:-}"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$PHASE" || -z "$TEST_NAME" || $# -eq 0 ]]; then
  usage
  exit 2
fi

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RECORD_DIR="${ROOT}/${PHASE}/${TIMESTAMP}_${TEST_NAME}"
mkdir -p "${RECORD_DIR}"

CMD=("$@")
CMD_STRING="$(printf '%q ' "${CMD[@]}")"

{
  echo "# Test Record"
  echo
  echo "- phase: ${PHASE}"
  echo "- test_name: ${TEST_NAME}"
  echo "- utc_timestamp: ${TIMESTAMP}"
  echo "- model_name: ${MODEL_NAME:-glm-4.5-flash}"
  echo "- base_url: ${BASE_URL:-https://llm.undefined.qzz.io/v1/chat/completions}"
  echo "- api_key: ${API_KEY:-unset}"
  echo
  echo "## Command"
  echo
  echo '```bash'
  echo "${CMD_STRING}"
  echo '```'
} > "${RECORD_DIR}/record.md"

{
  echo "#!/usr/bin/env bash"
  echo "set -euo pipefail"
  echo "${CMD_STRING}"
} > "${RECORD_DIR}/command.sh"
chmod +x "${RECORD_DIR}/command.sh"

{
  PYTHON_BIN="$(command -v python || command -v python3 || true)"
  PIP_BIN="$(command -v pip || command -v pip3 || true)"
  if [[ -n "${PYTHON_BIN}" ]]; then
    PYTHON_VERSION="$("${PYTHON_BIN}" --version 2>&1 || true)"
  else
    PYTHON_VERSION="python interpreter not found"
  fi
  if [[ -n "${PIP_BIN}" ]]; then
    PIP_VERSION="$("${PIP_BIN}" --version 2>&1 || true)"
  else
    PIP_VERSION="pip not found"
  fi

  echo "timestamp_utc=${TIMESTAMP}"
  echo "branch=$(git rev-parse --abbrev-ref HEAD)"
  echo "commit=$(git rev-parse HEAD)"
  echo "python=${PYTHON_VERSION}"
  echo "pip=${PIP_VERSION}"
} > "${RECORD_DIR}/env_snapshot.txt"

set +e
"${CMD[@]}" > >(tee "${RECORD_DIR}/stdout.log") 2> >(tee "${RECORD_DIR}/stderr.log" >&2)
EXIT_CODE=$?
set -e
echo "${EXIT_CODE}" > "${RECORD_DIR}/exit_code.txt"

{
  echo
  echo "## Result"
  echo
  echo "- exit_code: ${EXIT_CODE}"
  echo "- record_dir: ${RECORD_DIR}"
} >> "${RECORD_DIR}/record.md"

echo "Saved test record to: ${RECORD_DIR}"
exit "${EXIT_CODE}"
