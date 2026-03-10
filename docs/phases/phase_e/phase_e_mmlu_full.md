# Phase E MMLU Full Test (qwen3-8b, /v1 endpoint)

## Goal
Validate Phase-E on legacy MMLU pipeline after endpoint fix (`/v1`) and confirm score recovery above 60%.

## Runtime Configuration
- model: `qwen3-8b`
- endpoint: `https://llm.undefined.qzz.io/v1`
- mode: `FullConnected`
- decision: `FinalRefer`
- agents: `AnalyzeAgent x5`
- batch_size: `1`
- rounds: `1`
- command:
  - `OPENAI_BASE_URL="https://llm.undefined.qzz.io/v1" OPENAI_API_KEY="***" python3 experiments/run_mmlu.py --llm_name qwen3-8b --mode FullConnected --decision_method FinalRefer --batch_size 1 --num_rounds 1 --agent_names AnalyzeAgent --agent_nums 5`

## Result
- dataset: `cais/mmlu`
- split: `validation`
- evaluated questions: `153`
- correct: `106`
- accuracy: `0.6928104575163399` (**69.3%**)

## Evidence
- summary: `artifacts/runs/phaseE-mmlu-full-summary.json`
- result file: `result/mmlu/mmlu_llama3_2026-03-10-11-37-13.json`
- raw terminal log: `/home/ubuntu/.cursor/projects/workspace/terminals/873051.txt`
- endpoint health probes:
  - root endpoint: `artifacts/runs/qwen3-endpoint-health-probe-root.json` (`html_like_ratio=1.0`)
  - `/v1` endpoint: `artifacts/runs/qwen3-endpoint-health-probe-v1.json` (`html_like_ratio=0.0`)

## Conclusion
Phase-E MMLU test is completed with the fixed endpoint path and restored to >60% performance.
