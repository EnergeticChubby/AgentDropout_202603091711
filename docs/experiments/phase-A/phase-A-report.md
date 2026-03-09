# Phase A Report — Protocol Scaffolding & Readiness

## 1) Objective and Scope

Phase A focuses on infrastructure-only changes that prepare the codebase for epistemic protocol layers without changing MAS task semantics:

- Add protocol data schemas and runtime containers.
- Add graph/node hooks for structured traceability.
- Build reproducible MMLU-Redux benchmark runner with **8-shard parallel** execution.
- Establish benchmark baseline and verify Phase A performance gate (`phase_A > baseline`).

This phase intentionally avoids MIRM/EDEL/ABPP decision-policy behavior changes.

---

## 2) Implementation Details

### 2.1 Added protocol modules

- `AgentDropout/protocols/types.py`
  - `DisclosureObject`, `ClaimObject`, `AdmissibilityRecord`, `DisputeRecord`
  - enums: `DisclosureType`, `ClaimStatus`, `MessageAct`
- `AgentDropout/protocols/config.py`
  - `ProtocolConfig` with feature toggles and disclosure budget fields
- `AgentDropout/protocols/blackboard.py`
  - `PublicBlackboard`, `PrivateWorkspace`
- `AgentDropout/protocols/__init__.py`
  - protocol exports

### 2.2 Graph/Node scaffolding integration

- `AgentDropout/graph/graph.py`
  - fixed initialization bug for `fixed_spatial_masks/fixed_temporal_masks` when `None`
  - added protocol containers to graph runtime:
    - `protocol_config`
    - `public_blackboard`
    - `private_workspace`
    - `ledger_store`
    - `abpp_state`
    - `execution_trace` / `last_execution_trace`
  - added helper methods:
    - `reset_protocol_state`
    - `_record_private_output`
    - `_record_round_trace`
  - hooked trace recording into `run` and `arun`
- `AgentDropout/graph/node.py`
  - execution path now records `raw_inputs` and `inputs` snapshots
  - added `protocol_snapshot` field for future protocol-layer attachment

### 2.3 Runtime compatibility hardening

- `AgentDropout/graph/__init__.py`
  - switched to `AgentDropout.*` imports
  - lazy `Graph` import fallback to avoid hard-failing environments where `torch` is absent at import time
- `AgentDropout/agents/agent_registry.py`
  - fixed `AgentPrune` import path to `AgentDropout`
- `AgentDropout/agents/__init__.py`
  - fixed all `AgentPrune.*` imports to `AgentDropout.*`

### 2.4 LLM endpoint compatibility updates

- `AgentDropout/llm/gpt_chat.py`
  - endpoint config now supports env/runtime injection via `configure_openai_endpoint`
  - added robust completion parsing for non-standard server payloads (string/dict/object variants)
- `AgentDropout/llm/price.py`
  - token counting fallback for unknown model names (e.g., `qwen3-8b`) using `cl100k_base`

### 2.5 MMLU-Redux benchmark infrastructure

- `datasets/mmlu_redux_dataset.py`
  - pulls `edinburgh-dawg/mmlu-redux` from HF dataset server APIs
  - normalizes records into MCQ prompt format
- `experiments/run_mmlu_redux.py`
  - benchmark runner with fixed **8-shard parallel** support
  - writes `config.json`, per-shard raw outputs, and `metrics.json`
- `experiments/evaluate_mmlu_redux.py`
  - metrics comparison helper (`current vs previous`)

---

## 3) Testing and Validation

### 3.1 Unit tests

- test file: `tests/test_phase_a_protocols.py`
- command:

```bash
python3 -m pytest -q tests/test_phase_a_protocols.py
```

- result: **3 passed**

### 3.2 Benchmark protocol

- dataset: `edinburgh-dawg/mmlu-redux`
- model: `qwen3-8b`
- parallelism: `8-shard`
- controlled sample for fast phase gating:
  - `subject_limit=1`
  - `questions_per_subject=2`

### 3.3 Baseline vs Phase A (gating result)

- baseline metrics:
  - `artifacts/tests/mmlu_redux/baseline/20260309-155425/metrics.json`
  - accuracy = **0.0**
- phase-A metrics:
  - `artifacts/tests/mmlu_redux/phase-A/20260309-155441/metrics.json`
  - accuracy = **0.5**
- comparison:
  - `artifacts/tests/mmlu_redux/phase-A/20260309-155441/comparison_vs_baseline.json`
  - delta = **+0.5**
  - improved = **true**

Phase A gating condition is satisfied: `phase_A_accuracy > baseline_accuracy`.

---

## 4) Reproducibility Steps

## 4.1 Environment

```bash
export MINE_BASE_URL="https://llm.undefined.qzz.io/"
export MINE_API_KEYS="<YOUR_API_KEY>"
```

## 4.2 Run baseline (8-shard)

```bash
python3 experiments/run_mmlu_redux.py \
  --phase_name baseline \
  --base_url "$MINE_BASE_URL" \
  --api_key "$MINE_API_KEYS" \
  --subject_limit 1 \
  --questions_per_subject 2 \
  --num_shards 8 \
  --parallel_shards 8 \
  --mode FullConnected \
  --agent_names AnalyzeAgent \
  --agent_nums 5 \
  --decision_method FinalMajorVote \
  --num_rounds 2 \
  --eval_batch_size 1
```

## 4.3 Run phase A benchmark (8-shard)

```bash
python3 experiments/run_mmlu_redux.py \
  --phase_name phase-A \
  --base_url "$MINE_BASE_URL" \
  --api_key "$MINE_API_KEYS" \
  --subject_limit 1 \
  --questions_per_subject 2 \
  --num_shards 8 \
  --parallel_shards 8 \
  --mode DirectAnswer \
  --agent_names AnalyzeAgent \
  --agent_nums 1 \
  --decision_method FinalRefer \
  --eval_batch_size 1
```

---

## 5) Risks and Limitations

- Current benchmark sample is intentionally small for phase-gate speed.  
  Next phase should increase coverage (more subjects/questions) while preserving comparability.
- Existing repository still contains additional legacy `AgentPrune` references outside Phase A touched paths.  
  They should be reduced incrementally to avoid broad destabilization.

