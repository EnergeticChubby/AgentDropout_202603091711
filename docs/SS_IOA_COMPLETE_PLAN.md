# SS-IoA 完整执行计划（State-Space Internet of Agents）

> 本文档为 SS-IoA 方法论与路线细化文档；执行总控请以仓库根目录 `plan.md` 为准。

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

## 4. Phase 路线图（按“方向”分层：基础→高级→融合）

> 每个 phase 开始前，必须完整重读 `docs/TESTING_AND_PHASE_PLAN.md` 与本计划。  
> 每个 phase 必须先完成 task/subAgent 细分，再执行开发与测试。  
> 每个 phase 结束后必须执行 MMLU 完整 Val benchmark（失败题重测）并留档。  
> 性能未优于上一 phase 时，不得进入下一 phase。  
> 每个 phase 完成后必须独立 commit 并 push。

### Phase 0（基线方向）：AgentDropout 算法基线与测试

方向目标：以 AgentDropout 作为完整基线，建立可比较的零阶段性能。

子任务拆分：

1. 冻结 AgentDropout 基线配置（模型、prompt、拓扑、种子）。
2. 执行 AgentDropout 的 MMLU 完整 Val 测试（失败题重测）。
3. 输出 `phase0` 指标并写入 `performance_history.csv`。
4. 产出 baseline 报告，作为后续方向对照组。

subAgent 细分建议：

- `subagent-phase0-config`：冻结 baseline 配置清单。
- `subagent-phase0-runner`：执行 benchmark 与失败题重测。
- `subagent-phase0-report`：生成 phase0 报告与指标文件。

门禁：

- 必须完成 Phase0 测试并留档。
- 指标文件与原始日志缺一不可。
- 达标后 commit，自动进入 Phase 1。

### Phase 1（基础方向）：隐状态估计 + 衰减制度先验

方向目标：从“消息驱动”升级为“状态驱动”的基础控制层。

子任务拆分：

1. 观测事件 schema 与特征抽取（消息、工具、转移、异常）。
2. 实现 `z_t`（latent collective state）重建器。
3. 实现 decaying institutional priors（早期强、后期弱）。
4. 实现 prior override（冲突证据触发快速衰减）。

subAgent 细分建议：

- `subagent-phase1-state`：`z_t` 重建实现与验证指标。
- `subagent-phase1-prior`：先验调度器与 override 机制。
- `subagent-phase1-eval`：phase1 基线对比脚本。

门禁：

- 全量 Val + 失败题重测 + 全量留档。
- 指标严格优于 Phase0，否则继续优化。
- 达标后 commit，自动进入 Phase 2。

### Phase 2（进阶方向）：跨轮记忆 + 容量感知控制

方向目标：解决 rediscovery 与 collective capacity over-squashing。

子任务拆分：

1. 实现跨轮记忆 `m_t` 与 sufficient-statistics 压缩器。
2. 实现记忆可信写入（credibility gate + quarantine）。
3. 实现容量控制（admission control / utility-priced slots / phase pools）。
4. 实现记忆污染缓解与可追溯忘却策略。

subAgent 细分建议：

- `subagent-phase2-memory`：`m_t` 结构与写入策略实现。
- `subagent-phase2-capacity`：容量预算与槽位分配策略实现。
- `subagent-phase2-risk`：错误持久化/污染检测实验脚本。

门禁：

- 全量 Val + 失败题重测 + 全量留档。
- 指标严格优于 Phase1，否则继续优化。
- 达标后 commit，自动进入 Phase 3。

### Phase 3（高级融合方向）：多方向融合与完整解决方案

方向目标：融合 Phase1+Phase2，形成完整 SS-IoA 生产级方案。

子任务拆分：

1. 融合控制策略 `π(z_t, m_t, p_t)` 与双时间尺度控制器。
2. 增加异常触发重建（高冲突、长 barrier、持续分歧）。
3. 完成系统联调、消融、鲁棒性与开销评估。
4. 固化复现工件（脚本、日志索引、对比表、结论报告）。

subAgent 细分建议：

- `subagent-phase3-fusion`：融合控制主逻辑与调度策略。
- `subagent-phase3-ablation`：消融实验与鲁棒性评估。
- `subagent-phase3-release`：复现工件与最终报告打包。

门禁：

- 全量 Val + 失败题重测 + 全量留档。
- 指标严格优于 Phase2，否则继续优化。
- 达标后 commit，主线完成。

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

`python experiments/run_mmlu.py --llm_name qwen3-8b --batch_size 4 --retry_batch_size 1 --max_retry_rounds 5 --retry_delay 2`

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

