# Phase C Changelog

## Added
- risk card dataclass
- covariance store and pairwise covariance builder
- risk parity optimizer
- covariance build experiment script

## Updated
- graph supports passing risk weights into decision node
- final major vote supports risk-weighted aggregation

## Benchmark
- run tag: `phaseC-final`
- result: accuracy `0.625`
- gate: ✅ greater than phase-B (`0.500`)
