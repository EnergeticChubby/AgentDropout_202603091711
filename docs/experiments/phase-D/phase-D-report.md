# Phase D Report — ABPP (Admissibility & Burden-of-Proof Protocol)

## 1) Objective and Scope

Phase D adds an admissibility protocol layer (ABPP) on top of MIRM + EDEL:

- Evaluate whether candidate disclosures are admissible under risk-calibrated standards.
- Log admissibility rulings and inadmissible disputes.
- Gate blackboard writes through protocol decisions.

The phase focuses on runtime message admissibility control and auditability.

---

## 2) Implementation Details

### 2.1 New ABPP modules

- `AgentDropout/protocols/admissibility.py`
  - `AdmissibilityEngine`
  - risk-level dependent standards
  - decision reasons for non-admissible messages
- `AgentDropout/protocols/abpp.py`
  - `ABPPProtocol`
  - creates admissibility records
  - creates dispute records when items are rejected

### 2.2 Graph integration

- `AgentDropout/graph/graph.py`
  - initializes:
    - `admissibility_engine`
    - `abpp_protocol`
  - MIRM selected disclosures now pass ABPP gate before blackboard write
  - rejected disclosures are recorded as disputes (auditable)

### 2.3 Tests

- Added `tests/test_abpp.py`
  - high-risk unsupported claim rejection
  - protocol ruling/dispute recording

---

## 3) Validation and Benchmark Evidence

## 3.1 Unit tests

```bash
python3 -m pytest -q tests/test_phase_a_protocols.py tests/test_mirm.py tests/test_ledger.py tests/test_abpp.py
```

Result: **9 passed**.

## 3.2 MMLU-Redux benchmark (8-shard)

Current phase (D) run:

- `artifacts/tests/mmlu_redux/phase-D/20260309-160645/metrics.json`
- `accuracy = 1.0`
- `quality_score = 1.022`

Previous reference (Phase C):

- `artifacts/tests/mmlu_redux/phase-C/20260309-160341/metrics.json`
- `accuracy = 1.0`
- `quality_score = 1.011`

Comparison artifact:

- `artifacts/tests/mmlu_redux/phase-D/20260309-160645/comparison_vs_phase-C.json`
- `quality_delta = +0.011`
- `improved = true`

Phase D passes phase-gating performance rule.

---

## 4) Reproducibility Steps

```bash
export MINE_BASE_URL="https://llm.undefined.qzz.io/"
export MINE_API_KEYS="<YOUR_API_KEY>"

python3 experiments/run_mmlu_redux.py \
  --phase_name phase-D \
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
  --num_rounds 2 \
  --enable_mirm \
  --enable_edel \
  --enable_abpp \
  --token_budget 512 \
  --topk_disclosure 5 \
  --eval_batch_size 1
```

---

## 5) Risks and Limitations

- Admissibility rules are heuristic; domain-specific legal/medical standards are not yet modeled.
- Objection/rebuttal routing currently uses a compact implementation and should be expanded in future iterations.

