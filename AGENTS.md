# AGENTS.md

## Cursor Cloud specific instructions

### Project overview
AgentDropout is a Python research codebase for topology optimization in LLM-based Multi-Agent Systems. See `README.md` for details. There is no web UI, database, or persistent service — it runs experiment scripts that call LLM APIs.

### Python environment
- Python 3.10 is required (installed via deadsnakes PPA). The virtualenv is at `/workspace/.venv`.
- Activate with: `source /workspace/.venv/bin/activate`
- GPU-specific packages (nvidia-*, vllm, xformers, triton, xgrammar, gmpy2) are excluded since the VM is CPU-only. CPU-only PyTorch is installed instead.

### AgentPrune symlink
The codebase was renamed from `AgentPrune` to `AgentDropout`, but several `__init__.py` files and `agent_registry.py` still import from `AgentPrune`. A symlink `AgentPrune -> AgentDropout` in the repo root resolves this. If the symlink is missing, recreate it: `ln -sf AgentDropout AgentPrune`

### Running experiments
Experiments are in `experiments/` (e.g., `run_gsm8k.py`). They require:
1. An OpenAI-compatible LLM API endpoint configured in `AgentDropout/llm/gpt_chat.py` (set `MINE_BASE_URL` and `MINE_API_KEYS`), or via `.env` (copy `template.env` to `.env`).
2. Dataset files downloaded from HuggingFace and placed in `datasets/` (e.g., `datasets/gsm8k/gsm8k.jsonl`).

See `README.md` Quick Start section for example commands.

### Linting and testing
- No linter configuration exists. Use `python -m py_compile <file>` for syntax checks.
- No automated test files exist in the repo. `pytest` is installed and runs but collects 0 tests.
- `pytest` can be run from the repo root: `/workspace/.venv/bin/python -m pytest`

### Verifying the environment without API keys
The core framework (Graph, Node, agents, mask optimization, norms) can be exercised without LLM API keys. Only actual experiment runs (which call LLM inference) require `MINE_BASE_URL`/`MINE_API_KEYS`. Import checks and Graph construction/pruning logic work fully offline.

### Key gotchas
- The `requirements.txt` file is UTF-16LE encoded with CRLF line endings. Convert before processing: `iconv -f UTF-16LE -t UTF-8 requirements.txt | tr -d '\r'`
- All experiment scripts use `sys.path.append(...)` to add the repo root; run them from the repo root.
