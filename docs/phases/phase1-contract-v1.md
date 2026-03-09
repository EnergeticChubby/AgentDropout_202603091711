# Phase 1 V1 — Contract Repair from Failure Traces

## 1) 目标与范围

在 Phase 1 V0 的 contract edge 基础上，Phase 1 V1 目标是引入“失败轨迹驱动修约”能力：

1. 增加 dispute resolver（失败分类）；
2. 增加 contract repairer（基于 violations 的修约建议）；
3. 把 repair 建议写入审计指标输出；
4. 通过优化验证策略和决策后处理提升 `mmlu-redux` 指标，满足门禁“优于 Phase 1 V0”。

---

## 2) 设计方案与权衡

### 2.1 失败分类（DisputeResolver）
- 输入：`violations`
- 输出：`accept/rework/clarify/escalate`
- 作用：将 verifier 的失败结果映射到可执行处置动作，为后续 rollback/escalation 扩展打基础。

### 2.2 修约建议（ContractRepairer）
- 从 audit records 聚合 violation 频率（全局 + task_type 粒度）；
- 输出结构化建议（例如加强 `acceptance_test` 或显式 final answer 条款）。

### 2.3 审计增强
- `ContractAuditLog.flush()` 现在输出：
  - dispute action 分布
  - repair suggestions
- 这使 V1 的失败分析从“日志可读”升级到“机器可消费”。

### 2.4 性能优化点
- 改进 `MMLUPromptSet.postprocess_answer()`，从“取首字符”升级为：
  - 优先解析 `answer is X` / `answer: X`
  - 其次解析独立的 A/B/C/D
  - 最后回退策略
- 配合 `FinalMajorVote`，显著降低答案解析误差。

---

## 3) 代码变更清单（文件级）

### 新增
- `AgentDropout/contracts/dispute.py`
- `AgentDropout/contracts/repairer.py`
- `tests/contracts/test_repairer.py`
- `docs/phases/phase1-contract-v1.md`

### 修改
- `AgentDropout/contracts/__init__.py`
- `AgentDropout/contracts/audit.py`
- `AgentDropout/prompt/mmlu_prompt_set.py`

---

## 4) 测试设计与命令

### 4.1 合同模块测试
```bash
python3 -m pytest -q tests/contracts
```

### 4.2 回归 smoke
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... python3 -m pytest -q tests/smoke
```

### 4.3 Benchmark（门禁）
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=4 \
EXTRA_ARGS="--enable_contracts --contract_output_dir artifacts/tests/phase1v1/contracts/raw --decision_method FinalMajorVote" \
bash scripts/repro/run_mmlu_redux_8shard.sh phase1v1
```

---

## 5) 测试记录与结果分析

### 5.1 记录路径
- manifest: `artifacts/tests/phase1v1/summary/phase1-v1-test-manifest.md`
- contracts tests: `artifacts/tests/phase1v1/raw/pytest_contracts_v1.log`
- smoke tests: `artifacts/tests/phase1v1/raw/pytest_smoke_v1.log`
- benchmark summary: `artifacts/tests/phase1v1/mmlu_redux/summary/20260309-162127.json`
- contract audits: `artifacts/tests/phase1v1/contracts/raw/*.json`

### 5.2 结果
- tests/contracts: **5 passed**
- tests/smoke: **4 passed**
- `mmlu-redux` 8-shard mean score: **0.875**

---

## 6) 已知问题与风险

1. 目前 repair suggestions 仍是 rule-based 推荐，尚未形成在线自动重协商闭环；
2. 评测仍使用小样本切片（`LIMIT_QUESTIONS=4`），后续阶段需在同口径下扩大样本以验证稳定性。

---

## 7) 下一步计划

完成 Phase 1 后进入 Phase 2（Common-Knowledge Compilation）：
1. proposition 抽取与 epistemic store；
2. shared/public/private 层级管理；
3. knowledge compiler + action 执行；
4. 在 `mmlu-redux` 上继续保持门禁单调提升。

---

## 8) 与上一 phase 的 mmlu-redux 对比与门禁结论

- Phase 1 V0: **0.21875**
- Phase 1 V1: **0.875**
- 改善：**+0.65625**
- 门禁结论：**通过**（满足“Phase 1 V1 > Phase 1 V0”）
