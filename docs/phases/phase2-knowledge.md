# Phase 2 — Common-Knowledge Compilation

## 1) 目标与范围

Phase 2 在已落地的 contract edge 上增加“共同知识编译”能力：

1. 引入 proposition 抽取与 epistemic state store；
2. 引入 shared board 与 scope 升级计划（private/pairwise/subgroup/verified_shared）；
3. 在 Graph 执行中串联 extractor → compiler → actions → recovery；
4. 输出知识层指标并完成 `mmlu-redux` 门禁验证。

---

## 2) 设计方案与权衡

### 2.1 数据结构层
- `Proposition`：统一命题对象（文本、来源、置信度、状态、scope、依赖、证据）。
- `EpistemicStateStore`：命题存储与状态更新。
- `SharedKnowledgeBoard`：公共板写入与撤回。

### 2.2 编译与执行层
- `PropositionExtractor`：从节点输出抽取命题（轻量句段切分）。
- `KnowledgeCompiler`：将命题映射到 scope/action 升级计划。
- `KnowledgeActionExecutor`：执行升级计划并写入公共板。
- `KnowledgeRecovery`：清理空命题等污染项。

### 2.3 指标层
- `KnowledgeMetrics` 输出：
  - `duplicate_discussion_rate`
  - `false_common_ground_rate`
  - `re_ask_count`
  - `board_pollution_rate`

### 2.4 Graph 接入
- `Graph` 新增 `enable_knowledge` / `knowledge_output_dir`；
- 每节点执行后记录知识状态，run 结束时落盘：
  - store snapshot
  - board snapshot
  - knowledge metrics

---

## 3) 代码变更清单（文件级）

### 新增文件
- `AgentDropout/knowledge/__init__.py`
- `AgentDropout/knowledge/proposition.py`
- `AgentDropout/knowledge/store.py`
- `AgentDropout/knowledge/board.py`
- `AgentDropout/knowledge/metrics.py`
- `AgentDropout/knowledge/extractor.py`
- `AgentDropout/knowledge/cluster.py`
- `AgentDropout/knowledge/compiler.py`
- `AgentDropout/knowledge/actions.py`
- `AgentDropout/knowledge/recovery.py`
- `tests/knowledge/test_store.py`
- `tests/knowledge/test_compiler.py`
- `tests/knowledge/test_graph_knowledge.py`

### 修改文件
- `AgentDropout/graph/graph.py`（knowledge 生命周期与执行链路）
- `experiments/run_mmlu.py`
- `experiments/run_gsm8k.py`
- `experiments/run_humaneval.py`

---

## 4) 测试设计与命令

### 4.1 合同+知识测试
```bash
python3 -m pytest -q tests/contracts tests/knowledge
```

### 4.2 回归 smoke
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... python3 -m pytest -q tests/smoke
```

### 4.3 Benchmark（门禁）
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=2 \
EXTRA_ARGS="--enable_contracts --contract_output_dir artifacts/tests/phase2/contracts/raw --enable_knowledge --knowledge_output_dir artifacts/tests/phase2/knowledge/raw --decision_method FinalMajorVote" \
bash scripts/repro/run_mmlu_redux_8shard.sh phase2
```

---

## 5) 测试记录与结果分析

### 5.1 记录路径
- manifest: `artifacts/tests/phase2/summary/phase2-test-manifest.md`
- contracts+knowledge tests: `artifacts/tests/phase2/raw/pytest_contracts_knowledge.log`
- smoke tests: `artifacts/tests/phase2/raw/pytest_smoke.log`
- benchmark summary: `artifacts/tests/phase2/mmlu_redux/summary/20260309-163017.json`
- contract audit: `artifacts/tests/phase2/contracts/raw/*.json`
- knowledge artifacts: `artifacts/tests/phase2/knowledge/raw/*.json`

### 5.2 结果
- tests/contracts + tests/knowledge: **9 passed**
- tests/smoke: **4 passed**
- `mmlu-redux` 8-shard mean score: **1.0**

---

## 6) 已知问题与风险

1. 当前 knowledge compiler 仍是规则驱动，尚未学习化；
2. `re_ask_count` 目前为占位值，后续可基于对话轮次和重复询问检测增强。

---

## 7) 下一步计划

进入 Phase 3（Boundary Controller）：
1. 组织单元抽象与边界动作实现；
2. rules-based controller 接入 Graph；
3. value model + online reconfiguration；
4. 在 `mmlu-redux` 上继续保持门禁单调提升。

---

## 8) 与上一 phase 的 mmlu-redux 对比与门禁结论

- Phase 1 V1: **0.875**
- Phase 2: **1.0**
- 改善：**+0.125**
- 门禁结论：**通过**（满足“Phase 2 > Phase 1 V1”）
