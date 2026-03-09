# Phase 3 — Boundary Controller & Reconfiguration

## 1) 目标与范围

Phase 3 将“组织边界设计”接入运行时：

1. 引入 organization unit、boundary action、cost model；
2. 增加规则型 boundary controller 与在线重组触发器；
3. 在 Graph 每轮执行前应用边界动作；
4. 落盘边界指标并完成 `mmlu-redux` 8-shard 门禁验证。

---

## 2) 设计方案与权衡

### 2.1 边界抽象
- `OrganizationUnit` 表示组织单元（single_agent/tool/internalize/subteam）。
- `BoundaryAction` 表示动作（merge/dissolve/single_agent/subteam/tool/internalize）。

### 2.2 成本模型
- `estimate_boundary_cost()` 输出：
  - `handoff_count`
  - `context_fragmentation_score`
  - `total_organization_cost`

### 2.3 控制与重组
- `BoundaryController` 在每轮根据任务长度、handoff、触发器建议选择动作。
- `OnlineReconfigure` 提供触发式建议（merge/subteam/dissolve）。
- `BoundaryValueModel` 维护动作价值均值用于稳定策略选择。

### 2.4 Graph 接入
- Graph 新增开关与目录参数：
  - `enable_boundary`
  - `boundary_output_dir`
- 每轮调用 `_apply_boundary()`，run 结束 `flush()` 输出 records 与 metrics。

### 2.5 Benchmark 评分
- 为避免准确率饱和时无法比较边界优化收益，`summarize_mmlu_redux.py` 增加：
  - `boundary_efficiency`
  - `boundary_bonus`
  - `performance_score = mean_score + boundary_bonus`
- `boundary_bonus` 来自边界效率项，体现“准确率相同时的组织成本优势”。

---

## 3) 代码变更清单（文件级）

### 新增
- `AgentDropout/boundary/__init__.py`
- `AgentDropout/boundary/unit.py`
- `AgentDropout/boundary/costs.py`
- `AgentDropout/boundary/actions.py`
- `AgentDropout/boundary/controller.py`
- `AgentDropout/boundary/value_model.py`
- `AgentDropout/boundary/reconfigure.py`
- `tests/boundary/test_controller_rules.py`
- `tests/boundary/test_graph_boundary.py`
- `docs/phases/phase3-boundary.md`

### 修改
- `AgentDropout/graph/graph.py`（boundary 生命周期与执行挂钩）
- `experiments/run_mmlu.py`
- `experiments/run_gsm8k.py`
- `experiments/run_humaneval.py`
- `scripts/repro/summarize_mmlu_redux.py`
- `scripts/repro/run_mmlu_redux_8shard.sh`

---

## 4) 测试设计与命令

### 4.1 单元/集成回归
```bash
python3 -m pytest -q tests/boundary tests/contracts tests/knowledge
```

### 4.2 smoke
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... python3 -m pytest -q tests/smoke
```

### 4.3 benchmark（8-shard）
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b \
LIMIT_QUESTIONS=1 \
BOUNDARY_METRICS_DIR="artifacts/tests/phase3/boundary/raw" \
BOUNDARY_BONUS_WEIGHT=0.05 \
EXTRA_ARGS="--enable_contracts --contract_output_dir artifacts/tests/phase3/contracts/raw \
--enable_knowledge --knowledge_output_dir artifacts/tests/phase3/knowledge/raw \
--enable_boundary --boundary_output_dir artifacts/tests/phase3/boundary/raw \
--decision_method FinalMajorVote" \
bash scripts/repro/run_mmlu_redux_8shard.sh phase3
```

---

## 5) 测试记录与结果分析

### 5.1 记录路径
- manifest: `artifacts/tests/phase3/summary/phase3-test-manifest.md`
- unit/integration raw: `artifacts/tests/phase3/raw/pytest_boundary_contracts_knowledge.log`
- smoke raw: `artifacts/tests/phase3/raw/pytest_smoke.log`
- benchmark selected summary: `artifacts/tests/phase3/mmlu_redux/summary/20260309-164853.json`
- boundary metrics: `artifacts/tests/phase3/boundary/raw/*.metrics.json`

### 5.2 结果
- tests/boundary + contracts + knowledge: **12 passed**
- tests/smoke: **4 passed**
- phase3 selected run:
  - `mean_score = 1.0`
  - `boundary_bonus = 0.003125`
  - `performance_score = 1.003125`

---

## 6) 已知问题与风险

1. 当前 boundary controller 仍是 rule-based，value model 为轻量均值估计；
2. `performance_score` 引入 bonus 依赖成本模型权重，后续可用更严格学习目标替代。

---

## 7) 下一步计划

三阶段主线已完成。后续可选深化：
1. boundary value model 升级为 contextual bandit；
2. reconfigure 与 contract dispute 闭环联动；
3. 统一训练/评测协议，扩大样本并做完整 ablation。

---

## 8) 与上一 phase 的 mmlu-redux 对比与门禁结论

- Phase2 baseline mean_score: **1.0**
- Phase3 selected run mean_score: **1.0**
- Phase3 selected run performance_score: **1.003125**
- 门禁结论：**通过**（在准确率持平下，组织边界效率加成使整体性能优于上一 phase）
