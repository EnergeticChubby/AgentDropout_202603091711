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
- command:
  - `python3 experiments/probe_qwen3_endpoint_health.py`
- artifact:
  - `artifacts/runs/qwen3-endpoint-health-probe.json`
- summary:
  - `num_requests=20`
  - `num_success=20`
  - `num_html_like=20`
  - `html_like_ratio=1.0`

## Conclusion
- MMLU data download is complete and legacy pipeline can run.
- Current low performance is dominated by endpoint behavior: responses are consistently HTML-like payload instead of valid model answers.
