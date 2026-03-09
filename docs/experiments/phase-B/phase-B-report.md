# Phase B Report — MIRM (Marginal Information Revelation Mechanism)

## 1) Objective and Scope

Phase B introduces the first operational MIRM loop:

- Extract candidate disclosures from agent outputs.
- Score disclosure marginal utility with heuristic features.
- Apply top-k + token-budget gate to move selected disclosures into public blackboard.

This phase adds content-level reveal control while keeping existing topology optimization behavior compatible.

---

## 2) Implementation Details

### 2.1 New MIRM modules

- `AgentDropout/protocols/mirm_extractor.py`
  - Sentence-level disclosure extraction
  - Type classification: claim / evidence / counterevidence / uncertainty / question
- `AgentDropout/protocols/mirm_scorer.py`
  - Heuristic scoring features:
    - novelty
    - posterior-shift proxy
    - contradiction value
    - evidence quality
    - token cost penalty
- `AgentDropout/protocols/mirm_gate.py`
  - Budgeted top-k selection gate
  - Returns selected + rejected disclosures

### 2.2 Graph integration

- `AgentDropout/graph/graph.py`
  - Added MIRM runtime components:
    - `mirm_extractor`
    - `mirm_scorer`
    - `mirm_gate`
  - Added `_process_mirm_disclosures(node_id, round_idx)`
  - Hooked MIRM processing into both sync and async node execution loops
  - MIRM is activated via `protocol_config.enable_mirm`

### 2.3 Benchmark runner interface extension

- `experiments/run_mmlu_redux.py`
  - Added protocol toggles:
    - `--enable_mirm`
    - `--enable_edel`
    - `--enable_abpp`
    - `--token_budget`
    - `--topk_disclosure`
  - Passes protocol config to graph runtime

### 2.4 Tests

- Added `tests/test_mirm.py`
  - extractor output coverage
  - scorer + gate behavior under constrained budget

---

## 3) Validation and Benchmark Evidence

## 3.1 Unit tests

```bash
python3 -m pytest -q tests/test_phase_a_protocols.py tests/test_mirm.py
```

Result: **5 passed**.

## 3.2 MMLU-Redux benchmark (8-shard)

- dataset: `edinburgh-dawg/mmlu-redux`
- model: `qwen3-8b`
- parallelism: `8-shard`
- command summary:
  - `subject_limit=1`
  - `questions_per_subject=1`
  - `--enable_mirm`

Artifacts:

- Phase B metrics:  
  `artifacts/tests/mmlu_redux/phase-B/20260309-155929/metrics.json`
- Comparison vs Phase A:  
  `artifacts/tests/mmlu_redux/phase-B/20260309-155929/comparison_vs_phase-A.json`

Measured outcome:

- previous (Phase A) accuracy: **0.5**
- current (Phase B) accuracy: **1.0**
- delta: **+0.5**
- improved: **true**

Phase B passes the phase-gating performance rule.

---

## 4) Reproducibility Steps

```bash
export MINE_BASE_URL="https://llm.undefined.qzz.io/"
export MINE_API_KEYS="<YOUR_API_KEY>"

python3 experiments/run_mmlu_redux.py \
  --phase_name phase-B \
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
  --token_budget 256 \
  --topk_disclosure 2 \
  --eval_batch_size 1
```

---

## 5) Risk and Limitations

- Current MIRM scorer is fully heuristic; no learned policy yet.
- Benchmark sample size is intentionally small for phase gating speed.  
  Next phase should scale sample size while maintaining comparability constraints.

