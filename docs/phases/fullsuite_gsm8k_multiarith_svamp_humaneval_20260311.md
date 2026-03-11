# Full-Scope Benchmark Report: GSM8K / MultiArith / SVAMP / HumanEval (2026-03-11)

## 1) Goal

Run **full test split** benchmarks on:

- GSM8K
- MultiArith
- SVAMP
- HumanEval

for both profiles:

- `agentdropout`
- `phasee`

using the user-specified model stack:

- model: `qwen3-8b`
- endpoint: `https://llm.undefined.qzz.io/v1`

---

## 2) Reproducible setup

```bash
export OPENAI_BASE_URL="https://llm.undefined.qzz.io/v1"
export OPENAI_API_KEY="<YOUR_KEY>"
export LLM_BASE_URL="https://llm.undefined.qzz.io/v1"
export LLM_API_KEY="<YOUR_KEY>"
```

Runner:

- `experiments/run_fullsuite_benchmark.py`

This runner loads datasets directly from Hugging Face and stores per-run artifacts in:

- `artifacts/runs/fullsuite-<profile>-<dataset>-<run_tag>/`

---

## 3) Exact commands used

```bash
python3 experiments/run_fullsuite_benchmark.py --dataset gsm8k --profile agentdropout --run_tag full-20260311 --math_agent_count 1 --log_every 100
python3 experiments/run_fullsuite_benchmark.py --dataset gsm8k --profile phasee --run_tag full-20260311 --math_agent_count 1 --log_every 100

python3 experiments/run_fullsuite_benchmark.py --dataset multiarith --profile agentdropout --run_tag full-20260311 --math_agent_count 1 --log_every 25
python3 experiments/run_fullsuite_benchmark.py --dataset multiarith --profile phasee --run_tag full-20260311 --math_agent_count 1 --log_every 25

python3 experiments/run_fullsuite_benchmark.py --dataset svamp --profile agentdropout --run_tag full-20260311 --math_agent_count 1 --log_every 25
python3 experiments/run_fullsuite_benchmark.py --dataset svamp --profile phasee --run_tag full-20260311 --math_agent_count 1 --log_every 25

python3 experiments/run_fullsuite_benchmark.py --dataset humaneval --profile agentdropout --run_tag full-20260311 --code_agent_count 1 --log_every 20
python3 experiments/run_fullsuite_benchmark.py --dataset humaneval --profile phasee --run_tag full-20260311 --code_agent_count 1 --log_every 20
```

---

## 4) Full-scope results

| Dataset | Source | Split | Samples | AgentDropout | PhaseE |
|---|---|---:|---:|---:|---:|
| GSM8K | `openai/gsm8k` | test | 1319 | 0.7369 (972/1319) | 0.2191 (289/1319) |
| MultiArith | `ChilleD/MultiArith` | test | 180 | 1.0000 (180/180) | 0.8111 (146/180) |
| SVAMP | `ChilleD/SVAMP` | test | 300 | 0.7900 (237/300) | 0.3200 (96/300) |
| HumanEval | `openai_humaneval` | test | 164 | 0.5366 (88/164) | 0.0000 (0/164) |

Structured summary artifact:

- `artifacts/runs/fullsuite-20260311-summary.json`

---

## 5) Runtime observations

1. Some runs emitted intermittent retry errors (`RetryError`) from the endpoint client, but all 8 full runs completed and produced full sample counts.
2. `phasee` profile is materially weaker than `agentdropout` under the current one-agent command configuration.
3. HumanEval scoring uses `PyExecutor.evaluate(entry_point, candidate, test)` with canonical `check(entry_point)` execution path.

---

## 6) Artifact index

- GSM8K
  - `artifacts/runs/fullsuite-agentdropout-gsm8k-full-20260311/summary.json`
  - `artifacts/runs/fullsuite-phasee-gsm8k-full-20260311/summary.json`
- MultiArith
  - `artifacts/runs/fullsuite-agentdropout-multiarith-full-20260311/summary.json`
  - `artifacts/runs/fullsuite-phasee-multiarith-full-20260311/summary.json`
- SVAMP
  - `artifacts/runs/fullsuite-agentdropout-svamp-full-20260311/summary.json`
  - `artifacts/runs/fullsuite-phasee-svamp-full-20260311/summary.json`
- HumanEval
  - `artifacts/runs/fullsuite-agentdropout-humaneval-full-20260311/summary.json`
  - `artifacts/runs/fullsuite-phasee-humaneval-full-20260311/summary.json`

