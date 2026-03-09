# Phase B Changelog

## Added
- RI message schema and renderers
- rule-based attention policy (5-level read actions)
- heuristic value/cost estimators
- offline attention policy training script

## Updated
- Node read path now supports selective-resolution consumption
- Graph now injects phase/context into attention policy
- non-decision agent outputs converted to structured multilayer format

## Benchmark
- run tag: `phaseB-final`
- result: accuracy `0.500`
- gate: ✅ greater than phase-A (`0.375`)
