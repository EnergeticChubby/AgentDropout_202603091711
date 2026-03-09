# Phase 1 V0 — Incomplete-Contract Delegation Edge

## 1) 目标与范围

Phase 1 V0 聚焦“把 delegation 边从文本升级为 contract object”：

1. 增加 contract schema / template / synthesizer / verifier / audit 模块；
2. 把 contract 验证接入 Graph 执行路径；
3. 产出可追溯的 contract 审计记录与核心指标；
4. 在 `mmlu-redux`（8-shard）上验证相对 Phase 0 的性能改进。

---

## 2) 设计方案与权衡

### 2.1 Contract 对象化
- 采用 dataclass 定义 `DelegationContract`，覆盖：
  - `task_clause`, `decision_rights`, `deliverable_schema`,
  - `evidence_obligation`, `acceptance_test`, `rollback_clause`, `budget_clause` 等。
- 设计权衡：V0 以“可运行 + 可审计”为先，先做轻量模板与规则验证，不上学习器。

### 2.2 合同生成与验证
- `ContractSynthesizer`：根据 domain 推断 task_type（math/code/qa）并应用模板。
- `ContractVerifier`：执行 V0 验收规则（non-empty、final-answer pattern 等）。
- 设计权衡：规则简单但可解释，便于后续 V1 做 failure trace 驱动修约。

### 2.3 审计与指标
- `ContractAuditLog` 按 run_id 落盘 records + metrics：
  - `acceptance_pass_precision`
  - `silent_failure_rate`
  - `rework_rate`
  - `rollback_frequency`
- 设计权衡：先记录完整原始轨迹，聚合分析留到 V1 扩展。

### 2.4 Graph 接入策略
- 在 `Graph.arun/run` 的每个节点执行后进行 contract 记录与验证；
- 保持 `enable_contracts=False` 默认关闭，确保 backward compatibility。

---

## 3) 代码变更清单（文件级）

### 新增模块
- `AgentDropout/contracts/__init__.py`
- `AgentDropout/contracts/schema.py`
- `AgentDropout/contracts/templates.py`
- `AgentDropout/contracts/synthesizer.py`
- `AgentDropout/contracts/verifier.py`
- `AgentDropout/contracts/audit.py`

### 核心接入
- `AgentDropout/graph/graph.py`（contract 生命周期管理 + 节点后验收）
- `experiments/run_gsm8k.py`（`--enable_contracts` / `--contract_output_dir`）
- `experiments/run_humaneval.py`（同上）
- `experiments/run_mmlu.py`（同上）

### 测试新增
- `tests/contracts/test_schema.py`
- `tests/contracts/test_verifier.py`
- `tests/contracts/test_graph_contracts.py`

### 复现脚本增强
- `scripts/repro/run_mmlu_redux_8shard.sh`（增加 `EXTRA_ARGS` 透传）

---

## 4) 测试设计与命令

### 4.1 单元/集成（contracts）
```bash
python3 -m pytest -q tests/contracts
```

### 4.2 回归 smoke
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... python3 -m pytest -q tests/smoke
```

### 4.3 Benchmark（Phase gate）
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=4 \
EXTRA_ARGS="--enable_contracts --contract_output_dir artifacts/tests/phase1/contracts/raw" \
bash scripts/repro/run_mmlu_redux_8shard.sh phase1
```

---

## 5) 测试记录与结果分析

### 5.1 记录路径
- manifest: `artifacts/tests/phase1/summary/phase1-test-manifest.md`
- contracts tests: `artifacts/tests/phase1/raw/pytest_contracts.log`
- smoke tests: `artifacts/tests/phase1/raw/pytest_smoke.log`
- benchmark summary: `artifacts/tests/phase1/mmlu_redux/summary/20260309-161317.json`
- contract audits: `artifacts/tests/phase1/contracts/raw/*.json`

### 5.2 结果
- tests/contracts: **4 passed**
- tests/smoke: **4 passed**
- `mmlu-redux` 8-shard mean score: **0.21875**

---

## 6) 已知问题与风险

1. V0 verifier 仍为规则型，语义验收能力有限（V1 将引入失败轨迹驱动修约）。
2. 当前 contract 验证为“节点后验收”，下一步可补充“前置约束检查 + 返工路径”。

---

## 7) 下一步计划

进入 Phase 1 V1：
1. 聚合 failure traces；
2. 引入 dispute resolver + contract repairer；
3. 根据失败类型动态调整条款强度；
4. 再次执行 8-shard `mmlu-redux`，要求优于 Phase 1 V0。

---

## 8) 与上一 phase 的 mmlu-redux 对比与门禁结论

- Phase 0 baseline: **0.1875**
- Phase 1 V0: **0.21875**
- 改善：**+0.03125**
- 门禁结论：**通过**（达到“优于上一 phase”要求，可进入下一阶段）
