# GPT-5.1-codex-mini full-suite comparison (AgentDropout vs Phase3)

- Model: `gpt-5.1-codex-mini`
- Endpoint: `https://api.xcode.best/v1`
- Max tokens: **unlimited in runner** (no explicit cap passed)

| Benchmark | AgentDropout | Phase3 | Delta (Phase3-AgentDropout) |
|---|---:|---:|---:|
| GSM8K accuracy | 0.9575435936 | 0.9613343442 | +0.0037907506 |
| MultiArith accuracy | 1.0000000000 | 1.0000000000 | 0.0000000000 |
| SVAMP accuracy | 0.9500000000 | 0.9500000000 | 0.0000000000 |
| HumanEval pass@1 | 0.9817073171 | 0.9756097561 | -0.0060975610 |

## Aggregate summaries

- AgentDropout: `artifacts/tests/fullsuite_gpt51codexmini_v2_agentdropout/summary/20260311-135316.json`
- Phase3: `artifacts/tests/fullsuite_gpt51codexmini_v2_phase3/summary/20260311-143801.json`
