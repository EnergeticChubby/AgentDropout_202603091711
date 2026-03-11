#!/usr/bin/env bash
set -euo pipefail

# Phase0 gate: full MMLU val + required model availability.

python3 - <<'PY'
from pathlib import Path
from datasets.MMLU.download import download

download(force=False)
root = Path("datasets/MMLU/data")
dev_count = len(list((root / "dev").glob("*.csv")))
val_count = len(list((root / "val").glob("*.csv")))
print(f"dev_csv={dev_count}, val_csv={val_count}")
if dev_count < 57 or val_count < 57:
    raise SystemExit("MMLU dataset is not complete for full-val testing.")
PY

python3 - <<'PY'
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("template.env")
model_name = os.getenv("MODEL_NAME", "").strip()
if not model_name:
    raise SystemExit("MODEL_NAME is required in template.env.")
base = os.getenv("BASE_URL", "").rstrip("/")
if base.endswith("/chat/completions"):
    base = base[: -len("/chat/completions")]
client = OpenAI(api_key=os.getenv("API_KEY"), base_url=base)
models = [m.id for m in client.models.list().data]
print("available_models=", models)
print("target_model=", model_name)
if model_name not in models:
    raise SystemExit(f"Required model {model_name} is unavailable on provider.")
PY

model_name="$(python3 - <<'PY'
import os
from dotenv import load_dotenv
load_dotenv("template.env")
print(os.getenv("MODEL_NAME", "").strip())
PY
)"

python3 experiments/run_mmlu.py \
  --llm_name "$model_name" \
  --batch_size 4 \
  --retry_batch_size 1 \
  --max_retry_rounds 5 \
  --retry_delay 35
