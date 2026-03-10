# Original AgentDropout MMLU Run (2026-03-10)

## Goal

Validate the original `experiments/run_mmlu.py` pipeline and compare against the low full-run scores seen in protocolized MMLU-Redux runs.

## Command

```bash
MINE_BASE_URL="https://llm.undefined.qzz.io/v1" \
MINE_API_KEYS="$MINE_API_KEYS" \
python3 experiments/run_mmlu.py \
  --mode FullConnected \
  --agent_names AnalyzeAgent \
  --agent_nums 5 \
  --num_iterations 2 \
  --imp_per_iterations 1 \
  --pruning_rate 0.10 \
  --num_rounds 2 \
  --llm_name qwen3-8b \
  --decision_method FinalRefer \
  --optimized_spatial \
  --optimized_temporal \
  --diff \
  --batch_size 1
```

## Result

### A) Original AgentDropout with training (`--optimized_spatial --optimized_temporal`)

- Final score from script stdout:
  - `Score: 0.6993464052287581`
  - Equivalent accuracy on the evaluated set: **69.93% (107/153)**
- Output record file:
  - `result/mmlu/mmlu_llama3_2026-03-10-07-23-57.json`

### B) Original AgentDropout without training (inference-only baseline)

- Final score from script stdout:
  - `Score: 0.6535947712418301`
  - Equivalent accuracy on the evaluated set: **65.36% (100/153)**
- Output record file:
  - `result/mmlu/mmlu_llama3_2026-03-10-10-13-11.json`

### Quick comparison

| Setting | Score | Accuracy |
|---|---:|---:|
| Original + Training | 0.6993 | 69.93% |
| Original (No Training) | 0.6536 | 65.36% |

## Key Diagnostic Finding

The previous low numbers were driven by a configuration mismatch and benchmark mismatch:

1. Earlier protocol runs were on **MMLU-Redux** (harder setting) rather than the classic MMLU pipeline used by `run_mmlu.py`.
2. Endpoint base URL must be OpenAI-compatible API path (`.../v1`).  
   Using `https://llm.undefined.qzz.io/` caused HTML/dashboard responses and retry failures under high request load.
