# MMLU Benchmark Phase Index

This index tracks optimized MMLU benchmark results across phases.

| Phase | Benchmark Time (UTC) | Branch | Commit | Score | Delta vs Previous | Total Val Questions | Unresolved Failures | Report | Logs |
|---|---|---|---|---:|---:|---:|---:|---|---|
| `phase_01` | `TBD` | `AdamMartinez6793_v2` | `TBD` | `TBD` | `N/A` | `TBD` | `TBD` | `tests/benchmarks/mmlu/phase_01/benchmark_report.md` | `tests/benchmarks/mmlu/phase_01/logs/` |

## Maintenance Rules

1. Append one row for every benchmark execution (including failed gate attempts).
2. Never delete intermediate or failed runs.
3. For phase `N`, ensure `Score(N) > Score(N-1)` before phase transition.
4. Keep `Report` and `Logs` paths valid and committed.
5. Benchmark rows must represent complete MMLU `val` split runs only.
6. Gate pass requires `Unresolved Failures = 0`.
