# PLAN.md — Phase-Space Constitutional IoA 全局执行总纲（Blny_v2）

## 0. 文档定位（单一真源）

本文件是仓库唯一的**全局计划真源**（single source of truth）。

- 目标：统一研究问题、任务分解、测试协议、门禁规则、提交策略和自动推进流程。
- 适用范围：`Blny_v2` 分支上的全部 task/subAgent 实施活动。
- 从属文档：
  - `docs/testing_plan.md`（测试与复现执行细则）
  - `docs/phase_space_constitutional_ioa_master_plan.md`（研究主线描述）
  - `docs/phase_implementation_breakdown.md`（phase 里程碑拆解）

---

## 1. 核心问题与研究北极星

### 1.1 问题重定义

> IoA 的核心问题不是“通信图不够优”，而是系统无法直接观测隐协作状态，却要在部分可观测、早期高脆弱、路径依赖、表示容量受限条件下持续协作控制。

### 1.2 三层统一主线（从基础到高级）

1. **Observer（Phase1）**：重构隐协作状态 `z_t`。
2. **Controller（Phase2）**：抑制 early-stage collapse 的时变制度控制。
3. **Scheduler + Fusion（Phase3）**：双瓶颈诊断 + 风险一致调度 + 全链路融合。

### 1.3 基线层

- **Phase0** 是 AgentDropout 基线算法测试与冻结层，是后续比较唯一起点。

---

## 2. 不可违背硬规则（Rule IDs）

### R01 模型与接口统一（强制）

所有测试必须统一使用：

- `model_name = glm-4.5-flash`
- `base_url = https://llm.undefined.qzz.io/v1/chat/completions`
- `api_key = sk-pc8yOBXhAVOXEa38hpH1XBtuPwadnB1rLpNxHMS6grCuMrZh`

### R02 数据集统一（强制）

- benchmark 统一使用 **MMLU 完整 Val 集**。
- 覆盖率必须为 **100%**，禁止抽样验收。

### R03 并发失败重测（强制）

若因 API 高并发导致失败（超时/限流/连接错误）：

1. 记录失败题清单；
2. 定向重测失败题；
3. 直到补齐全部失败题，恢复 100% 覆盖率。

### R04 每 phase 前复读计划（强制）

每个 phase 开始前必须完整重读：

- `plan.md`
- `docs/testing_plan.md`

### R05 任务细分（强制）

每个 phase 执行前必须产出并更新 `phase_task_breakdown.md`，将任务拆到 task/subAgent 粒度。

### R06 phase 结果门禁（强制）

每个 phase 结束必须执行优化后 MMLU benchmark，并满足：

- `Accuracy_phase_t > Accuracy_phase_(t-1)`（严格大于）；
- 若未达标，禁止进入下一 phase，必须继续优化并重测。

### R07 自动推进（强制）

仅当“phase 任务完成 + 质量门禁通过 + commit/push 完成”同时满足后，自动进入下一 phase。

### R08 数据保留（强制）

不得删除失败记录；必须保留全量测试数据（失败与成功）。

### R09 提交策略（强制）

- 分支固定：`Blny_v2`
- 每个 phase 至少一个独立 commit
- 禁止多个 phase 混在同一 commit

---

## 3. Phase 体系（Phase0 → Phase3）

## Phase0：AgentDropout 基线算法测试与冻结

### 目标

- 验证 AgentDropout 核心算法可运行；
- 冻结后续对比基线。

### 最低任务

1. 环境与依赖检查；
2. 基线算法 smoke test；
3. MMLU Full Val 基线测试；
4. 基线指标归档（accuracy/cost/latency）。

### 输出

- baseline 记录目录
- `benchmark_compare.md`（作为 Phase1 对照）

---

## Phase1：方向一（基础）— Phase-Space Observer

### 目标

- 形成可消费的隐状态 `z_t` 与 basin 标签。

### 最低任务

1. 多尺度观测埋点（微/中/宏）；
2. 相空间重构；
3. basin 识别；
4. 与失败事件可解释对齐。

### 融合接口（输出给 Phase2）

- `state_stream.jsonl`
- `observer_metrics.json`

---

## Phase2：方向二（中级）— Anti-Collapse Controller

### 目标

- 构建早期强、后期弱的时变制度控制器，降低 early collapse。

### 最低任务

1. early-stage 宪法模板；
2. 衰减门控 `w_t`；
3. institutional memory；
4. 基于 `z_t` 的状态驱动调控。

### 融合接口（输出给 Phase3）

- `control_trace.jsonl`
- `institutional_memory_snapshot.json`

---

## Phase3：方向三（高级+融合）— Dual-Bottleneck Risk-Coherent Scheduler

### 目标

- 双瓶颈诊断（capacity/sensitivity）+ 风险一致调度，并融合三方向形成完整方案。

### 最低任务

1. 双瓶颈诊断；
2. 分治执行策略（summary/retrieval）；
3. 风险分布头（成功率/成本/时延/回滚风险）；
4. 单调合法性与 non-crossing 约束；
5. 全链路融合与关键消融。

### 最终完成判据

- `Accuracy_phase3 > Accuracy_phase2 > Accuracy_phase1 > Accuracy_phase0`
- 产物可复跑，记录完整可审计。

---

## 4. task/subAgent 细分标准

每个 phase 的 `phase_task_breakdown.md` 必须包含：

1. 子任务 ID、类型（task/subAgent）、输入、输出、依赖、负责人、状态；
2. MMLU Full Val 测试计划；
3. 并发失败重试方案；
4. 门禁勾检项。

推荐模板：`docs/templates/phase_task_breakdown_template.md`。

---

## 5. 标准执行状态机（统一工作流）

每个 phase 按如下状态机执行，不允许跳步：

1. `READ_PLAN`：复读总纲与测试计划；
2. `BREAKDOWN`：细分子任务；
3. `IMPLEMENT`：实现当前 phase 内容；
4. `TEST_FULLVAL`：执行 MMLU 完整 Val；
5. `RETRY_FAILED`：补齐并发失败题；
6. `COMPARE`：与上一 phase 指标比较；
7. `GATE`：门禁判定；
8. `COMMIT_PUSH`：独立提交并推送；
9. `NEXT_PHASE`：自动进入下一 phase。

任何阶段失败，必须回退到最近的可恢复状态重新执行。

---

## 6. Benchmark 与重试协议

## 6.1 全量测试要求

- 测试覆盖率 = 100%
- 输出必须包含准确率与成本/时延辅助指标

## 6.2 并发重试策略

建议采用“失败题队列”机制：

1. 初次全量跑；
2. 收集失败题到 `failed_items.json`；
3. 指数退避 + 固定最大重试轮次；
4. 每轮仅重测失败题；
5. 失败题清空后结束。

## 6.3 失败题仍未补齐时

- phase 判定失败；
- 禁止进入下一 phase；
- 必须继续优化（并发参数、批量大小、退避策略）后重跑。

---

## 7. 数据与证据保留规范

测试记录目录规范：`result/test_records/<phase>/<timestamp>_<test_name>/`

每条记录最少包含：

- `record.md`
- `command.sh`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`
- `env_snapshot.txt`
- `metrics.json` 或 `metrics.csv`
- `benchmark_compare.md`

并发失败场景必须附加：

- `failed_items.json`
- `retry_log.md`

---

## 8. 质量门禁（Gate Checklist）

每个 phase 提交前，以下全部为 `PASS`：

1. 已复读计划；
2. 已细分 task/subAgent；
3. MMLU Full Val 覆盖率 100%；
4. 并发失败题已补齐；
5. 性能严格优于上一 phase；
6. 记录与证据完整；
7. 独立 commit 已 push。

---

## 9. 提交、分支与命名规范

- 分支：`Blny_v2`
- commit 前缀：
  - `phase0: ...`
  - `phase1: ...`
  - `phase2: ...`
  - `phase3: ...`

建议每个 phase 至少两类提交：

1. `implementation`（实现）
2. `benchmark+records`（测试与记录）

---

## 10. 计划变更控制（Plan Change Control）

对 `plan.md` 的任何修改必须：

1. 写明变更动机与影响范围；
2. 同步更新从属文档引用；
3. 在提交说明中标明“plan change”。

---

## 11. Definition of Done（项目完成定义）

当且仅当以下条件全部满足，项目判定完成：

1. Phase0~Phase3 全部通过门禁；
2. 每个 phase 均有完整 MMLU Full Val + 失败题补齐记录；
3. 指标严格单调提升；
4. 三方向融合方案可复跑；
5. 证据链（命令、日志、指标、提交）完整。

