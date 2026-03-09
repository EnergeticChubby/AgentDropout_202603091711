# Phase A Changelog

## Added
- core event schema
- instrumentation logger
- phase scheduler
- offline event simulator
- MMLU-Redux shard evaluator and 8-shard launcher
- reproducibility configs
- phase-0 preflight checklist and phase-A task decomposition docs

## Updated
- graph runtime now emits phase-aware execution events
- node runtime now emits message-read and execution latency events
- token usage accounting now supports event hook callbacks

## Compatibility Notes
- Existing graph APIs remain callable with default arguments.
- New kwargs (`phase_sequence`, `instrumentation_output_path`) are optional.
- Benchmark run artifacts generated:
  - `phaseA-baseline`
  - `phaseA-postfix` (performance gate pass)
