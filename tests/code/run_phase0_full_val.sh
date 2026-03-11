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
base = os.getenv("BASE_URL", "").rstrip("/")
if base.endswith("/chat/completions"):
    base = base[: -len("/chat/completions")]
client = OpenAI(api_key=os.getenv("API_KEY"), base_url=base)
models = [m.id for m in client.models.list().data]
print("available_models=", models)
if "glm-4.5-flash" not in models:
    raise SystemExit("Required model glm-4.5-flash is unavailable on provider.")
PY

python3 experiments/run_mmlu.py \
  --llm_name glm-4.5-flash \
  --batch_size 4 \
  --retry_batch_size 1 \
  --max_retry_rounds 5 \
  --retry_delay 2
