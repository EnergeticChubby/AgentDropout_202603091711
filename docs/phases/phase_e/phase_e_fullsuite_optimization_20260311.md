# Phase-E Fullsuite Optimization Report (2026-03-11)

## 背景

在 `full-20260311` 全量评测中，PhaseE 在 GSM8K / SVAMP / HumanEval 上显著低于 AgentDropout。  
本轮目标是定位根因并完成优化。

---

## 根因定位

### Root cause 1: 聚合阶段默认只读到 `claims`（read level=2）

- 文件：`AgentDropout/core/attention_policy.py`
- 原默认策略：
  - `aggregate: READ_CLAIMS`
- 结果：
  - 决策节点拿到的是被截断后的摘要/要点，不是完整答案。
  - 对数值题会丢失最终 `The answer is ...`。
  - 对 HumanEval 会丢失完整代码块，只剩“设计建议”文本。

### Root cause 2: benchmark 角色不确定（role cycle）

- `PromptSet.get_role()` 使用全局 `itertools.cycle(...)`。
- 不固定角色时，单 agent 可能被分配为 `Project Manager/Test Analyst`，而非 `Programming Expert/Math Solver`。
- 对 HumanEval 直接导致输出非代码文本，pass 率崩塌。

---

## 优化改动

### 1) 聚合默认深读

- 文件：`AgentDropout/core/attention_policy.py`
- 修改：
  - `aggregate` 默认读取级别从 `READ_CLAIMS` 改为 `READ_FULL`。

### 2) fullsuite runner 固定角色

- 文件：`experiments/run_fullsuite_benchmark.py`
- 修改：
  - 数学数据集统一固定 `MathSolver(role="Math Solver")`
  - HumanEval 统一固定 `CodeWriting(role="Programming Expert")`
  - 通过 `node_kwargs` 显式注入，移除 role cycle 漂移。

---

## 测试与结果

### Smoke 验证（优化后）

- GSM8K (`max_samples=20`): `0.95`
  - `artifacts/runs/fullsuite-phasee-gsm8k-opt-smoke2/summary.json`
- HumanEval (`max_samples=20`): `0.95`
  - `artifacts/runs/fullsuite-phasee-humaneval-opt-smoke2/summary.json`

### Full 验证（优化后，PhaseE）

| Dataset | Samples | Before (`full-20260311`) | After (`opt-full-20260311`) | Delta |
|---|---:|---:|---:|---:|
| GSM8K | 1319 | 0.2191 | **0.9249** | +0.7058 |
| MultiArith | 180 | 0.8111 | **0.9944** | +0.1833 |
| SVAMP | 300 | 0.3200 | **0.9233** | +0.6033 |
| HumanEval | 164 | 0.0000 | **0.8293** | +0.8293 |

汇总文件：

- `artifacts/runs/fullsuite-20260311-phasee-optimized-summary.json`

对应 full 结果文件：

- `artifacts/runs/fullsuite-phasee-gsm8k-opt-full-20260311/summary.json`
- `artifacts/runs/fullsuite-phasee-multiarith-opt-full-20260311/summary.json`
- `artifacts/runs/fullsuite-phasee-svamp-opt-full-20260311/summary.json`
- `artifacts/runs/fullsuite-phasee-humaneval-opt-full-20260311/summary.json`

---

## 结论

本次问题不是“PhaseE 理念无效”，而是**评测配置与消息读取策略错误**导致性能被系统性压低。  
完成以上两项修复后，PhaseE 在四个全量数据集上均显著恢复。

