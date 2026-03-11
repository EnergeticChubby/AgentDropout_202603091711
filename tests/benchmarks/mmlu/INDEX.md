# MMLU Benchmark Phase Index

This index tracks optimized MMLU benchmark results across phases.

| Phase | Direction | Benchmark Time (UTC) | Branch | Commit | Score | Delta vs Previous | Total Val Questions | Unresolved Failures | Report | Logs |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| `phase_0` | `AgentDropout baseline` | `2026-03-11T12:46:03Z` | `AdamMartinez6793_v2` | `de3e2c748d923ad8d6562808ade3608f10826d40` | `0.247551` | `N/A` | `1531` | `0` | `tests/benchmarks/mmlu/phase_0/benchmark_report.md` | `tests/benchmarks/mmlu/phase_0/logs/` |
| `phase_1` | `state estimation` | `TBD` | `AdamMartinez6793_v2` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `tests/benchmarks/mmlu/phase_1/benchmark_report.md` | `tests/benchmarks/mmlu/phase_1/logs/` |
| `phase_2` | `forecastive modeling` | `TBD` | `AdamMartinez6793_v2` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `tests/benchmarks/mmlu/phase_2/benchmark_report.md` | `tests/benchmarks/mmlu/phase_2/logs/` |
| `phase_3` | `governance + fusion` | `TBD` | `AdamMartinez6793_v2` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `tests/benchmarks/mmlu/phase_3/benchmark_report.md` | `tests/benchmarks/mmlu/phase_3/logs/` |

## Maintenance Rules

1. Append one row for every benchmark execution (including failed gate attempts).
2. Never delete intermediate or failed runs.
3. For phase `N`, ensure `Score(N) > Score(N-1)` before phase transition.
4. Keep `Report` and `Logs` paths valid and committed.
5. Benchmark rows must represent complete MMLU `val` split runs only.
6. Gate pass requires `Unresolved Failures = 0`.
