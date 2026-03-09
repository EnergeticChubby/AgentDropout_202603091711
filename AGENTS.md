# AGENTS.md

## Cursor Cloud specific instructions

### Overview

AgentDropout is a Python research framework for multi-agent system topology optimization. It is a single-process Python project (not a web app or microservice). There is no web UI, no Docker, no database. The entry points are experiment scripts in `experiments/`.

### Environment

- **Python 3.10** is required (installed via `deadsnakes` PPA). The virtualenv lives at `/workspace/.venv`.
- Always activate with: `source /workspace/.venv/bin/activate`
- This is a **CPU-only** environment. GPU-specific packages (`nvidia-*`, `vllm`, `xformers`, `triton`) are excluded. PyTorch is installed as CPU-only (`torch==2.5.1+cpu`).

### Critical: AgentPrune symlink

The codebase internally references `AgentPrune` (the predecessor project name) in several `__init__.py` files, while the actual package directory is `AgentDropout`. A symlink `AgentPrune -> AgentDropout` at the repo root is required for imports to work. The update script creates this if missing.

### Running experiments

Experiments require an **OpenAI-compatible LLM API**. The secrets `MINE_BASE_URL` and `MINE_API_KEYS` are provided via environment variables but the code in `AgentDropout/llm/gpt_chat.py` hardcodes them as empty strings. To use the env vars at runtime, you must patch the module globals:

```python
import os, AgentDropout.llm.gpt_chat as m
m.MINE_BASE_URL = os.environ["MINE_BASE_URL"]
m.MINE_API_KEYS = os.environ["MINE_API_KEYS"]
```

**Token counting caveat:** `AgentDropout/llm/price.py` uses `tiktoken.encoding_for_model()` which only recognizes OpenAI model names (e.g. `gpt-3.5-turbo`, `gpt-4o`). If the API endpoint uses non-standard model names (e.g. OpenRouter's `openai/gpt-4o-mini`), `cost_count` will throw. Monkey-patch `cost_count` in both `price` and `gpt_chat` modules to catch the exception and estimate tokens by `len(text)//4`.

Experiments also require **dataset files** (JSONL) downloaded from HuggingFace and placed in `datasets/` (e.g., `datasets/gsm8k/gsm8k.jsonl`). See `README.md` Quick Start for CLI usage.

### Linting and testing

- No linting config is included in the repo. `ruff` can be used for basic syntax checks: `ruff check AgentDropout/ experiments/ datasets/ --select E9,F63,F7,F82`
- No automated test suite exists (no test files, no conftest.py). `pytest` is installed but collects 0 tests.
- The `requirements.txt` is encoded as **UTF-16-LE with BOM** (not standard UTF-8). Tools that read it must handle this encoding.
