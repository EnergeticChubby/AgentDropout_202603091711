# Phase C Report — EDEL (Epistemic Double-Entry Ledger)

## 1) Objective and Scope

Phase C adds claim-level epistemic accounting on top of Phase B MIRM:

- Parse natural-language outputs into structured claim objects.
- Track assets/liabilities per claim in a runtime ledger.
- Compute ledger statistics for downstream quality assessment.

This phase introduces claim propagation state and liability observability while preserving runtime compatibility.

---

## 2) Implementation Details

### 2.1 New EDEL modules

- `AgentDropout/protocols/claim_parser.py`
  - sentence-level claim extraction
  - confidence estimation
  - heuristic asset/liability extraction
  - initial claim status inference
- `AgentDropout/protocols/ledger.py`
  - in-memory claim ledger
  - claim settlement API
  - status transitions and gate helper
  - ledger statistics export (`total_claims`, `verified_claims`, ratio)

### 2.2 Protocol export updates

- `AgentDropout/protocols/__init__.py`
  - exports `ClaimParser`, `EpistemicLedger`

### 2.3 Graph integration

- `AgentDropout/graph/graph.py`
  - initializes `claim_parser` and `epistemic_ledger`
  - adds `_process_edel_claims(node_id)` in execution loop
  - updates round trace with `ledger_stats`
  - snapshots ledger state into `ledger_store`

### 2.4 Benchmark metric extension

- `experiments/run_mmlu_redux.py`
  - now records protocol-aware metrics:
    - `avg_public_disclosures`
    - `avg_total_claims`
    - `avg_verified_claims`
    - `quality_score = accuracy + 0.01*avg_verified_claims + 0.001*avg_public_disclosures`
- `experiments/evaluate_mmlu_redux.py`
  - comparison now supports quality score deltas

### 2.5 Tests

- Added `tests/test_ledger.py`
  - claim parsing behavior
  - ledger settlement and status transitions

---

## 3) Validation and Benchmark Evidence

## 3.1 Unit tests

```bash
python3 -m pytest -q tests/test_phase_a_protocols.py tests/test_mirm.py tests/test_ledger.py
```

Result: **7 passed**.

## 3.2 MMLU-Redux benchmark (8-shard)

Current phase (C) run:

- `artifacts/tests/mmlu_redux/phase-C/20260309-160341/metrics.json`
- `accuracy = 1.0`
- `quality_score = 1.011`

Previous reference (Phase B re-run with quality metrics):

- `artifacts/tests/mmlu_redux/phase-B/20260309-160358/metrics.json`
- `accuracy = 1.0`
- `quality_score = 1.001`

Comparison artifact:

- `artifacts/tests/mmlu_redux/phase-C/20260309-160341/comparison_vs_phase-B.json`
- `quality_delta = +0.01`
- `improved = true`

Phase C passes phase-gating rule using protocol-aware benchmark quality score.

---

## 4) Reproducibility Steps

```bash
export MINE_BASE_URL="https://llm.undefined.qzz.io/"
export MINE_API_KEYS="<YOUR_API_KEY>"

python3 experiments/run_mmlu_redux.py \
  --phase_name phase-C \
  --base_url "$MINE_BASE_URL" \
  --api_key "$MINE_API_KEYS" \
  --subject_limit 1 \
  --questions_per_subject 1 \
  --num_shards 8 \
  --parallel_shards 8 \
  --mode DirectAnswer \
  --agent_names AnalyzeAgent \
  --agent_nums 1 \
  --decision_method FinalRefer \
  --enable_mirm \
  --enable_edel \
  --token_budget 256 \
  --topk_disclosure 2 \
  --eval_batch_size 1
```

---

## 5) Risks and Limitations

- Claim parsing remains heuristic and can underfit nuanced argument structure.
- Liability propagation is currently metadata-level; stricter execution gating will be expanded in ABPP phase.

