# SS-IoA 完整执行计划（State-Space Internet of Agents）

## 0. 计划目的与结论先行

本计划基于最新分析报告，明确将研究问题从“图结构优化”升级为“部分可观测的集体动力系统控制”：

- 目标不再是单纯优化“谁和谁说话”。
- 目标是优化“团队—任务—环境”联合隐藏状态如何被估计、记忆、控制与演化。

核心结论：

1. 现有 IoA/MAS 方法主要优化可见协作层（拓扑、路由、FSM、资源调度）。
2. 本工作改为优化隐藏集体状态层（latent collective state）。
3. 执行上采用单一主线框架：**SS-IoA**。

---

## 1. 问题重定义（Root-Cause First）

### 1.1 旧问题定义（不足）

“通信冗余/拓扑不优/角色冗余导致性能下降，因此应做剪枝或路由优化。”

### 1.2 新问题定义（本计划采用）

IoA/LLM-MAS 的协作过程本质上是一个**部分可观测、非平稳、容量受限**的集体动力系统。  
如果系统直接基于表层消息流控制协作，而非先恢复联合隐藏状态再控制，会产生系统性失败：

1. 早期塌缩（early-stage collapse）
2. 重复发现（rediscovery）
3. 容量塌缩（collective capacity over-squashing）
4. 隐状态错控（miscontrol under hidden-state uncertainty）

---

## 2. SS-IoA 总体框架（四模块 + 双时间尺度）

## 2.1 模块 M1：集体隐状态重建（Latent Collective State Reconstruction）

输入观测流（消息、工具调用、结果、speaker 转移、sub-team 事件、traceback 事件等），重建 `z_t`：

- 任务阶段
- 证据充分度
- 依赖阻塞状态
- 知识覆盖缺口
- 决策风险水平
- 协作停滞/重复程度

> 控制不直接看原始消息，而看 `z_t`。

## 2.2 模块 M2：衰减制度先验（Decaying Institutional Priors）

早期强先验，后期弱先验，避免“初期高噪声下重组织决策”：

- 初期任务树 scaffold
- 初期角色边界
- 初期风险约束
- 初期同步/异步切换规则
- 初期 traceback 触发阈值

先验随证据增长衰减，允许 posterior override。

## 2.3 模块 M3：跨轮次连续协作记忆（Refinement-Oriented Memory）

建立 `m_t` 作为跨轮状态载体，保存 sufficient statistics（而非全文）：

- 已确认事实
- 未决冲突点
- 待验证高价值假设
- 高价值工具输出摘要
- 不确定性画像
- 子任务完成度
- agent 历史可靠性

目标：从“重复发现”转向“增量 refinement”。

## 2.4 模块 M4：容量感知记忆控制（Capacity-Aware Memory Control）

将通信问题下沉为容量问题，定义并控制 collective capacity over-squashing：

- admission control（是否允许写共享记忆）
- utility-priced slots（按边际价值分配槽位）
- compressed statistics（优先写统计量）
- phase-specific pools（按阶段隔离记忆）

## 2.5 模块 M5：双时间尺度控制（Dual-Timescale Control）

- 快时间尺度：常规 reactive 执行。
- 慢时间尺度：phase 切换、异常、长 barrier、持续分歧时触发状态重建与重规划。

---

## 3. 形式化接口（工程导向）

将系统建模为 POMDP-like 集体控制问题：

- 隐状态：`s_t`（不可直接观测）
- 观测：`o_t`（消息、工具、事件流）
- 重建状态：`z_t = f_recon(o_{1:t})`
- 记忆状态：`m_t = f_mem(m_{t-1}, z_t, o_t)`
- 控制动作：`a_t = π(z_t, m_t, p_t)`（组队、路由、说话顺序、pause/traceback）
- 衰减先验：`p_t = decay(p_0, evidence_t)`

---

## 4. Phase 路线图（强制细分 + 强制门禁）

> 每个 phase 开始前，必须完整重读 `docs/TESTING_AND_PHASE_PLAN.md` 与本计划。  
> 每个 phase 必须先完成 task/subAgent 细分，再执行开发与测试。  
> 每个 phase 结束后必须执行 MMLU 完整 Val benchmark（失败题重测）并留档。  
> 性能未优于上一 phase 时，不得进入下一 phase。

### Phase 0：基线冻结与评测基线建立

子任务拆分：

1. 冻结基线配置（模型、prompt、agent 拓扑、随机种子）。
2. 运行 MMLU 完整 Val 基线评测。
3. 建立 `performance_history.csv` 初始行（Phase0）。

产物：

- `tests/benchmarks/mmlu/<ts>_phase0.md`
- `tests/benchmarks/mmlu/<ts>_phase0.log`
- `tests/benchmarks/mmlu/<ts>_phase0_metrics.json`
- `tests/benchmarks/mmlu/performance_history.csv`

门禁：

- 必须完成全量 Val。
- 必须完成失败题重测。
- 完成后 commit 并进入 Phase 1。

### Phase 1：M1 隐状态重建层

子任务拆分：

1. 定义观测事件 schema（消息/工具/转移/异常）。
2. 实现 `z_t` 重建器与状态可视化日志。
3. 增加状态可验证性指标（future success/block risk）。

subAgent 细分建议：

- `subagent-state-schema`：事件 schema 与日志路径定义。
- `subagent-state-model`：`z_t` 重建器实现。
- `subagent-state-metrics`：状态可验证性评测脚本。

门禁：

- MMLU 全量 Val 测试 + 失败题重测。
- 指标必须优于 Phase 0，否则进入优化循环（见第 6 节）。
- 达标后 commit，自动进入 Phase 2。

### Phase 2：M2 衰减制度先验

子任务拆分：

1. 定义初期制度先验模板与参数化强度。
2. 实现基于证据的 prior decay 调度。
3. 实现 posterior override（冲突证据触发快速衰减）。

门禁：

- 全量 Val + 失败题重测 + 全量留档。
- 指标优于 Phase 1；否则继续微调。
- 达标后 commit，自动进入 Phase 3。

### Phase 3：M3 跨轮连续记忆

子任务拆分：

1. 实现记忆结构 `m_t` 与写入 API。
2. 定义 sufficient statistics 压缩器。
3. 引入记忆可信度门（credibility gate）与隔离区（quarantine）。

门禁：

- 全量 Val + 失败题重测 + 全量留档。
- 指标优于 Phase 2；否则继续微调。
- 达标后 commit，自动进入 Phase 4。

### Phase 4：M4 容量感知控制

子任务拆分：

1. 实现 admission control 与 memory budget。
2. 实现 utility-priced memory slots。
3. 实现 phase-specific memory pools。

门禁：

- 全量 Val + 失败题重测 + 全量留档。
- 指标优于 Phase 3；否则继续微调。
- 达标后 commit，自动进入 Phase 5。

### Phase 5：M5 双时间尺度控制与系统联调

子任务拆分：

1. 快/慢控制器切换策略实现。
2. 异常触发重建策略（高冲突、长 barrier、持续分歧）。
3. 联调与性能剖析（token、延迟、失败恢复）。

门禁：

- 全量 Val + 失败题重测 + 全量留档。
- 指标优于 Phase 4；否则继续微调。
- 达标后 commit，自动进入 Phase 6。

### Phase 6：完整消融与鲁棒性评估

子任务拆分：

1. 单模块消融（-M1/-M2/-M3/-M4/-M5）。
2. 噪声与并发压力场景评测。
3. 错误持久化与记忆污染对抗实验。

门禁：

- 主模型全量 Val + 失败题重测 + 全量留档。
- 主模型指标仍需优于 Phase 5。
- 达标后 commit，自动进入 Phase 7。

### Phase 7：论文/报告打包与复现工件发布

子任务拆分：

1. 方法描述、伪代码、接口说明。
2. 实验表格与 ablation 汇总。
3. 一键复现实验脚本与工件索引文档。

门禁：

- 全量 Val 终版复测 + 失败题重测 + 全量留档。
- 指标优于 Phase 6（至少不退化，建议保持提升）。
- 达标后 commit，完成主线。

---

## 5. Benchmark 标准作业程序（SOP，强制）

## 5.1 数据与范围

- 必须使用 **MMLU 完整 Val 集**。
- 严禁抽样、严禁截断、严禁替换子集。

## 5.2 并发失败重测机制

若出现高并发 API 异常（如 429、timeout、连接错误）：

1. 记录失败题索引、错误类型、发生轮次。
2. 将失败题进入 retry 队列。
3. 采用更保守重试（如 `retry_batch_size=1`）逐题重跑。
4. 达到重试上限仍失败时必须留档并标注原因。

## 5.3 基线命令模板

`python experiments/run_mmlu.py --llm_name glm-4.5-flash --batch_size 4 --retry_batch_size 1 --max_retry_rounds 5 --retry_delay 2`

## 5.4 强制留档

每次 phase benchmark 至少保留：

- 结构化报告（`.md`）
- 原始日志（`.log`）
- 指标文件（`_metrics.json`）
- 历史追踪（`performance_history.csv`）
- 失败重试详情（`_retry_failures.json`）

---

## 6. 指标不达标时的优化闭环（必须执行）

若 `metric_current <= metric_previous`：

1. 禁止进入下一 phase。
2. 进入优化循环：
   - 参数微调（记忆预算、衰减速率、重建窗口等）
   - 结构微调（门控阈值、写入策略、异常触发条件）
   - 重跑全量 Val + 重测失败题
3. 仅当 `metric_current > metric_previous` 后允许 commit 并进入下一 phase。

---

## 7. Task 与 subAgent 执行模板（每个 phase 强制）

每个 phase 必须提供如下清单：

1. 子任务列表（ID、目标、输入、输出、负责方）。
2. subAgent 分配（名称、边界、预期产物路径、验收命令）。
3. phase 收口报告（完成项、未完成项、风险项、下一步）。

---

## 8. 质量门禁与完成定义（Definition of Done）

某 phase 完成的必要且充分条件：

1. 实现产物已落盘并可复查。
2. 全量 Val benchmark 已执行。
3. 并发失败题重测已完成并留档。
4. 性能严格优于上一 phase。
5. phase 独立 commit 已完成并推送。

---

## 9. 与现有计划文件的关系

- 本文件定义 SS-IoA 的“研究与执行总计划”。
- `docs/TESTING_AND_PHASE_PLAN.md` 定义“测试治理与 phase 门禁规则”。
- 两者共同生效；若冲突，以“更严格约束”为准。

