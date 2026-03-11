# PLAN.md - Unified Governance System

## 0. Document Control

- Plan scope: repository-wide execution and quality governance.
- Plan type: mandatory rules + operational workflow.
- Primary audience: anyone implementing, testing, or reviewing phase work.
- Source of truth: this file has highest priority among project docs for execution policy.

## 1. Mission and Non-Negotiable Principles

This repository executes a forecastive IoA research program through strict phase governance.

Non-negotiable principles:

1. Reproducibility first: no phase output is valid without reproducible records.
2. Benchmark-gated progress: no phase transition without benchmark proof.
3. Full-data evaluation: phase gates must use complete MMLU `val`.
4. Strict improvement: every next phase must outperform previous phase.
5. Full trace retention: failed and intermediate runs are never deleted.
6. One phase, one commit boundary: each phase update must end in dedicated commit(s).

## 2. Fixed Runtime Baseline

All test/evaluation defaults must use:

- `TEST_MODEL="gpt-5.1-codex-mini"`
- `BASE_URL="https://llm.undefined.qzz.io/v1/chat/completions"`
- `API_KEY` from `.env` (derived from `template.env`)

Reference locations:

- `template.env`
- `AgentDropout/llm/gpt_chat.py`
- `experiments/run_*.py` defaults

## 3. Phase Architecture (Direction-Based)

Phases are directions from base capability to complete solution fusion:

- `Phase 0`: AgentDropout baseline establishment and validation.
- `Phase 1`: collaboration state estimation direction.
- `Phase 2`: forecastive modeling direction.
- `Phase 3`: governance control and full fusion direction.

Master research roadmap:

- `docs/FORECASTIVE_STATE_SPACE_GOVERNANCE_PLAN.md`

## 4. Lifecycle Workflow for Every Phase

Each phase must follow this exact lifecycle:

1. **Plan re-read**
   - Fully re-read this `PLAN.md` before any implementation.
2. **Task decomposition**
   - Split into implementation, validation, benchmark, and documentation tasks.
   - Include subagent/task decomposition when used.
3. **Implementation**
   - Make scoped changes for current phase objective only.
4. **Reproducibility test execution**
   - Run canonical suite: `bash scripts/run_repro_tests.sh <run_id>`.
5. **Full MMLU gate benchmark**
   - Run complete MMLU `val` benchmark for the phase.
   - Retry failed questions until unresolved count becomes `0`.
6. **Promotion check**
   - Enforce `Score(N) > Score(N-1)`.
   - If not satisfied, continue optimize/fine-tune inside same phase, then rerun.
7. **Archival**
   - Save all logs, reports, predictions, and benchmark outputs.
8. **Commit and push**
   - Commit phase update(s), then push.
9. **Auto-transition**
   - Only after commit + gate pass, proceed to next phase.

## 5. Task/Subagent Decomposition Standard

Every phase report must include a decomposition table with at least:

1. task id
2. task type (`implementation` | `validation` | `benchmark` | `documentation`)
3. owner (`main` or subagent name)
4. input artifact(s)
5. output artifact(s)
6. status

Minimum decomposition granularity:

- no phase may have fewer than 4 top-level tasks.
- benchmark task must be explicit and standalone.

## 6. Benchmark Governance (Hard Gate)

### 6.1 Mandatory dataset policy

- Gate benchmark must use complete MMLU `val`.
- Partial evaluation is forbidden for phase promotion.
- `limit_questions` for gate run must be `None` or equivalent full-set behavior.

### 6.2 Failed-question retest policy

Due to API concurrency instability:

1. use per-question retry with backoff,
2. use additional rerun rounds for unresolved failures,
3. gate status is **FAIL** if unresolved failures `> 0`.

### 6.3 Promotion rule

For phase `N`:

- `Score(N) > Score(N-1)` is mandatory.
- `UnresolvedFailures(N) == 0` is mandatory.

If either condition fails:

1. remain in current phase,
2. continue optimization/fine-tuning,
3. rerun benchmark,
4. retain all failed/intermediate artifacts,
5. repeat until both conditions pass.

## 7. Phase Entry/Exit Criteria

### 7.1 Common entry criteria

- previous phase committed and pushed,
- previous phase benchmark gate passed,
- current phase decomposition written.

### 7.2 Common exit criteria

- scoped implementation completed,
- reproducibility suite passed,
- full MMLU gate passed (`Score` improved + unresolved `0`),
- artifacts archived,
- phase commit(s) pushed.

### 7.3 Phase-specific objectives

- `Phase 0`: establish reproducible AgentDropout baseline and baseline score.
- `Phase 1`: deliver state estimation components with measurable gain over phase 0.
- `Phase 2`: deliver forecastive modeling components with measurable gain over phase 1.
- `Phase 3`: deliver governance + fusion system with measurable gain over phase 2.

## 8. Reproducibility and Artifact System

### 8.1 Required run records

For each run id under `tests/records/<run_id>/`:

- `test_report.md`
- `logs/*.log`
- exact command evidence
- pass/fail status

### 8.2 Required benchmark records

For each phase benchmark under `tests/benchmarks/mmlu/phase_<N>/`:

- `benchmark_report.md`
- raw logs
- predictions/outputs used for scoring
- score summary, delta to previous phase
- unresolved failure count

### 8.3 Mandatory indexes

- reproducibility index: `tests/records/INDEX.md`
- benchmark index: `tests/benchmarks/mmlu/INDEX.md`

Indexes must be updated whenever a new run/benchmark is added.

## 9. Commit, Branch, and Naming Policy

1. Each phase update must end with dedicated commit(s).
2. Do not combine multiple phases into one commit.
3. Commit message pattern: `Phase <N>: <outcome>`.
4. Branch naming must follow current active branch policy.
5. Push after each completed phase update.

## 10. Quality Standards for Markdown and Reports

All markdown artifacts must satisfy:

1. clear structure (`title`, `objective`, `procedure`, `evidence`, `conclusion`),
2. exact commands and file paths in monospace,
3. benchmark claims backed by logs and report files,
4. no ambiguous phrasing for pass/fail conditions.

## 11. Exception and Incident Procedure

When blocked by environment/API issues:

1. record incident in phase report (`issue`, `impact`, `attempted fixes`),
2. perform at least 3 remediation attempts,
3. keep failed logs,
4. do not fake gate completion,
5. only mark phase blocked, never mark phase passed.

## 12. Audit Checklist (Pre-Push)

Before push, all items must be true:

- [ ] `PLAN.md` fully re-read at phase start
- [ ] phase and subagent tasks are decomposed and documented
- [ ] reproducibility suite executed and recorded
- [ ] full MMLU `val` benchmark executed
- [ ] failed questions re-tested; unresolved count is `0`
- [ ] `Score(N) > Score(N-1)` verified
- [ ] all run/benchmark artifacts retained
- [ ] `tests/records/INDEX.md` updated
- [ ] `tests/benchmarks/mmlu/INDEX.md` updated
- [ ] phase commit(s) created and pushed

## 13. Plan Change Management

Rules for updating this plan:

1. changes must preserve existing hard gates unless explicitly superseded,
2. updates require rationale and scope note in commit message,
3. after plan change, re-run relevant reproducibility checks,
4. subsequent phase execution must follow updated plan immediately.
