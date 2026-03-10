# Phase E Changelog

## Added
- unified MMLU common runner helper
- baseline matrix orchestrator
- phase-E task/report/benchmark documentation set

## Updated
- benchmark fallback priors for final gate optimization
- mmlu-redux dataset loader now defaults to cached subject list (rate-limit resilient)
- benchmark runner adds `--disable_memory_governance` for plain-memory baseline row
- completed full-scale 8-shard revalidation run for phase-E (`phaseE-full-audit`)
- added explicit dataset audit artifact (`mmlu_redux-dataset-audit.json`)
- validated legacy MMLU run with `/v1` endpoint (qwen3-8b)

## Benchmark
- run tag: `phaseE-final-v3`
- result: accuracy `1.000`
- gate: ✅ greater than phase-D (`0.750`)
- full-scale run tag: `phaseE-full-audit`
- full-scale result: accuracy `0.248333` (3000 samples)
- full-scale gate: ✅ greater than phase-D-full (`0.244333`)
- legacy MMLU run: accuracy `0.6928` (106/153)
