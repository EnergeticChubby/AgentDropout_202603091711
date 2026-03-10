# MMLU Download + Qwen3-8B Run Audit (2026-03-10)

## 1) MMLU data download
- command:
  - `python3 datasets/MMLU/download.py`
- source:
  - `cais/mmlu` (`all` config)
- output:
  - `datasets/MMLU/data/dev/*.csv`
  - `datasets/MMLU/data/val/*.csv`
  - `datasets/MMLU/data/test/*.csv`

## 2) Legacy MMLU pipeline run with qwen3-8b

### 2.1 Original-style high-connectivity attempt
- command:
  - `python3 experiments/run_mmlu.py --llm_name qwen3-8b --mode FullConnected --decision_method FinalRefer --batch_size 4 --num_rounds 1 --agent_names AnalyzeAgent --agent_nums 5`
- status:
  - failed due endpoint 429 rate-limit after retries.
- log:
  - `/home/ubuntu/.cursor/projects/workspace/agent-tools/ddb5a71b-31fa-41fa-a7fa-335d08d61a5d.txt`

### 2.2 Low-concurrency completion run
- command:
  - `python3 experiments/run_mmlu.py --llm_name qwen3-8b --mode DirectAnswer --decision_method FinalDirect --batch_size 1 --num_rounds 1 --agent_names AnalyzeAgent --agent_nums 1`
- status:
  - completed
- score:
  - `0.0` on 153 validation questions (legacy script fixed limit)
- artifacts:
  - `result/mmlu/mmlu_llama3_2026-03-10-09-06-46.json`
  - shell output file contains `Score: 0.0`

## 3) Endpoint health probe
- root endpoint (`https://llm.undefined.qzz.io/`):
  - artifact: `artifacts/runs/qwen3-endpoint-health-probe-root.json`
  - summary: `num_success=20`, `num_html_like=20`, `html_like_ratio=1.0`
- `/v1` endpoint (`https://llm.undefined.qzz.io/v1`):
  - artifact: `artifacts/runs/qwen3-endpoint-health-probe-v1.json`
  - summary: `num_success=20`, `num_html_like=0`, `html_like_ratio=0.0`

## 4) MMLU rerun after endpoint switch to /v1

### Critical runtime fix
- `AgentDropout/llm/gpt_chat.py` 优先读取 `OPENAI_BASE_URL/OPENAI_API_KEY`。
- 仅设置 `LLM_*` 不足以覆盖现有 shell 中的旧 `OPENAI_API_KEY`。
- 实际跑分时需显式设置：
  - `OPENAI_BASE_URL="https://llm.undefined.qzz.io/v1"`
  - `OPENAI_API_KEY="sk-***"`

### Successful original-style run (qwen3-8b)
- command:
  - `OPENAI_BASE_URL="https://llm.undefined.qzz.io/v1" OPENAI_API_KEY="sk-***" python3 experiments/run_mmlu.py --llm_name qwen3-8b --mode FullConnected --decision_method FinalRefer --batch_size 1 --num_rounds 1 --agent_names AnalyzeAgent --agent_nums 5`
- status:
  - completed
- score:
  - `0.6928104575163399` (106/153, **69.3%**)
- evidence:
  - terminal log: `/home/ubuntu/.cursor/projects/workspace/terminals/873051.txt` (`Score: 0.6928`)
  - result file: `result/mmlu/mmlu_llama3_2026-03-10-11-37-13.json`

## Conclusion
- MMLU data download is complete and legacy pipeline can run with qwen3-8b.
- Root endpoint returns HTML-like payload and causes invalid evaluation.
- Switching to `/v1` and setting `OPENAI_*` variables explicitly restores normal responses; original-style MMLU run reaches **69.3%** (>60%).
