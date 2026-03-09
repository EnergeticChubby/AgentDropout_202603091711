#!/usr/bin/env bash
set -euo pipefail

PHASE_NAME="${1:-phase0}"
MODEL_NAME="${LLM_MODEL_NAME:-qwen3-8b}"
DATASET_NAME="${DATASET_NAME:-edinburgh-dawg/mmlu-redux}"
NUM_SHARDS=8
LIMIT_QUESTIONS="${LIMIT_QUESTIONS:-8}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARTIFACT_ROOT="artifacts/tests/${PHASE_NAME}/mmlu_redux"
RAW_DIR="${ARTIFACT_ROOT}/raw/${TIMESTAMP}"
SUMMARY_DIR="${ARTIFACT_ROOT}/summary"

mkdir -p "${RAW_DIR}" "${SUMMARY_DIR}"

echo "[INFO] Running ${DATASET_NAME} with ${NUM_SHARDS} shards"
echo "[INFO] Model: ${MODEL_NAME}"
echo "[INFO] limit_questions per shard: ${LIMIT_QUESTIONS}"
echo "[INFO] extra_args: ${EXTRA_ARGS}"
echo "[INFO] Logs: ${RAW_DIR}"

for SHARD_IDX in $(seq 0 $((NUM_SHARDS - 1))); do
  python3 experiments/run_mmlu.py \
    --dataset_name "${DATASET_NAME}" \
    --num_shards "${NUM_SHARDS}" \
    --shard_idx "${SHARD_IDX}" \
    --limit_questions "${LIMIT_QUESTIONS}" \
    --llm_name "${MODEL_NAME}" \
    --eval_split test \
    ${EXTRA_ARGS} \
    > "${RAW_DIR}/shard_${SHARD_IDX}.log" 2>&1 &
done

wait

python3 scripts/repro/summarize_mmlu_redux.py \
  --raw_dir "${RAW_DIR}" \
  --summary_json "${SUMMARY_DIR}/${TIMESTAMP}.json" \
  --summary_md "${SUMMARY_DIR}/${TIMESTAMP}.md"

echo "[INFO] Done. Summary saved to ${SUMMARY_DIR}/${TIMESTAMP}.json"
