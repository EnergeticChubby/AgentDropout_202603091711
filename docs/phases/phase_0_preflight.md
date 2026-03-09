# Phase-0 Preflight Checklist

## Branch
- Target branch: `Blny`
- Status: ready

## Model/API Runtime
- model: `qwen3-8b`
- base url env: `LLM_BASE_URL`
- api key env: `LLM_API_KEY`
- note: API key must never be committed; runtime injection only.

## Benchmark Protocol
- dataset: `edinburgh-dawg/mmlu-redux`
- execution mode: 8-shard parallel
- orchestration script: `experiments/run_mmlu_redux.py`

## Reproducibility Layout
- configs:
  - `configs/common.yaml`
  - `configs/phase_a.yaml`
- run outputs:
  - `artifacts/runs/<run_id>-shard*/`
  - `artifacts/runs/<run_id>-all/`

## Go / No-Go
- [x] Branch policy captured
- [x] Config templates added
- [x] Benchmark scripts added
- [x] Baseline benchmark run archived (`artifacts/runs/mmlu_redux-phaseA-baseline-all/summary.json`)
