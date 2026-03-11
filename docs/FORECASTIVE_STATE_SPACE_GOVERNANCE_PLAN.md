# Forecastive State-Space Governance for Internet of Agents (IoA)

## 1. 研究主线与目标

### 1.1 核心命题

IoA 的本质问题不是“当前拓扑/工作流是否最优”，而是：

1. 在部分可观测条件下估计协作隐状态；
2. 预测未来协作分布与尾部风险；
3. 在失败发生前做滚动治理控制。

因此本计划将研究对象从**结构优化系统**升级为**协作动力学预测治理系统**。

### 1.2 论文标题建议

**Forecastive State-Space Governance for Internet of Agents**  
副标题建议：  
**Preventing Initial-Round Collaboration Collapse and Societal Capacity Over-Squashing via Multi-Resolution Distributional Forecasting**

### 1.3 研究目标

1. 提出 IoA 协作状态空间建模框架；
2. 定义并量化新失败模式；
3. 实现多分辨率协作未来分布预测；
4. 实现滚动治理控制策略；
5. 在完整 MMLU `val` 集上形成阶段性、可复现、可追溯的性能提升证据链。

## 2. 问题定义与形式化

### 2.1 系统设定

系统为开放异构、递归组队、部分可观测 IoA：

- 可观测事件：registry/discovery、team launch、FSM transition、routing、tool success/failure、pause/trigger 等；
- 不可直接观测：真实协作健康状态与未来风险轨迹；
- 决策目标：在预算约束下同时优化成功率、稳定性与风险可控性。

### 2.2 形式化对象

1. 事件序列：`e_1, e_2, ..., e_t`
2. 潜在协作状态：`z_t`
3. 未来协作分布：`P(Y_{t+1:t+H} | z_t, a_t)`
4. 治理动作：`a_t`（例如 team split/merge、verifier activation、rollback、priority 调整）
5. 门禁约束：阶段 `N` 必须满足 `Score(N) > Score(N-1)` 且 unresolved failures = 0

### 2.3 优化目标

1. 预测层：最小化分布预测误差 + 校准误差 + 一致性约束违背；
2. 治理层：最大化成功概率并最小化 token/latency/deadlock 尾部风险；
3. 阶段层：满足 benchmark promotion gate 后自动推进下一 phase。

## 3. 新失败模式定义

### 3.1 Initial-Round Collaboration Collapse

协作初始轮（任务分解、组队、证据标准设定）发生错误轨道选择，后续回合持续继承并放大偏差。

### 3.2 Societal Capacity Over-Squashing

组织层记忆容量不足导致关键证据、依赖和责任链在跨组汇总时被压缩失真，表现为“仍在沟通但关键状态不可恢复”。

### 3.3 Distributional Tail Failure

均值指标正常但尾部风险恶化（死锁、回滚深度、token 爆炸、错共识高置信输出）。

## 4. 方法总架构（五层）

### Layer A: 协作状态估计器（State Estimator）

- 输入：protocol-grounded events + 消息内容摘要；
- 输出：latent collaboration state `z_t`；
- 要求：可解释、可追溯、支持跨轮状态更新。

### Layer B: 早期先验与跨轮状态（Priors + Trans-Round State）

- 初期强先验：registry/workflow/evidence/trust priors；
- 衰减策略：随证据累积自动降权；
- 纠偏机制：冲突触发先验降权，避免 prior lock-in。

### Layer C: 容量感知社会记忆（Capacity-Aware Societal Memory）

- 三级记忆：agent-local / group / societal；
- 面向预测治理分配记忆预算；
- 显式监控社会层压缩失真信号。

### Layer D: 协作未来分布预测（Distributional Forecasting）

- 多分辨率输入：micro(turn)、meso(subgroup/workflow)、macro(regime)；
- 预测对象：success、rollback depth、deadlock、token overrun、latency 等；
- 合法性约束：分位数单调、风险一致性、干预一致性。

### Layer E: 滚动治理控制（Receding-Horizon Governance）

- 动作空间：暂停/回滚/拆组/并组/verifier 激活/优先级调整/预算节流；
- 控制逻辑：基于未来分布而非单点打分；
- 策略执行：每轮治理后更新状态并滚动预测。

## 5. 与现有工作的边界声明

本计划的创新定位不是以下单点：

1. 仅做拓扑剪枝或路由优化；
2. 仅做 test-time 模式调整；
3. 仅做 latent communication/memory；
4. 仅做 budget-performance 控制器；
5. 仅做事后故障归因。

本计划的研究边界是：**将 IoA 完整建模为可预测、可治理的部分可观测协作动力系统**。

## 6. 实验与评测计划

### 6.1 数据与任务

阶段门禁 benchmark 统一使用**完整 MMLU `val` 集**，禁止子集替代。

### 6.2 指标体系

1. 主任务：accuracy / success rate
2. 成本：token、latency
3. 风险：deadlock rate、rollback depth distribution、token overrun tail risk
4. 预测质量：calibration、coverage、distribution consistency
5. 治理收益：risk reduction under equal budget

### 6.3 基线与对照组

至少包含：

- AgentDropout
- AgentPrune
- MaAS
- MetaAgent
- 静态 workflow / 无治理版本
- 预测无控制、控制无预测、无多分辨率输入等消融版本

### 6.4 失败题重测协议

对于 API 并发导致的失败：

1. 单题重试 + backoff；
2. 失败集合顺序重跑；
3. unresolved failures 必须为 0 才能判定本阶段 benchmark 完成。

## 7. Phase 路线图（按方向组织，从基础到高级）

每一 phase 都必须执行以下流程：

1. 完整重读 `PLAN.md`；
2. 细分 task/subagent 子任务；
3. 实施与验证；
4. 运行完整 MMLU `val` benchmark；
5. 若未优于上一 phase，继续优化并重测；
6. 达标后 commit 并进入下一 phase。

### Phase 0（基线方向）: AgentDropout Baseline

目标：建立可复现、可对照的 AgentDropout 基线能力。

#### 细分计划

1. `P0.1` 环境与数据就绪：
   - MMLU 目录检查与下载/准备；
   - API 重试参数校验；
   - 本地可复现 smoke 测试（不依赖外部并发稳定性）。
2. `P0.2` 基线运行与归档：
   - 运行完整 MMLU `val`；
   - 对并发失败题执行重测；
   - 保留全量日志、输出、分数。
3. `P0.3` 评测报告：
   - 生成 `benchmark_report.md`；
   - 写入 `tests/benchmarks/mmlu/INDEX.md` 的 Phase 0 行。

门禁：`Score(0)` 作为后续 phase 的比较基线，且 unresolved failures = 0。

### Phase 1（方向一，基础层）: Collaboration State Estimation

目标：构建协作隐状态估计能力。

#### 细分计划

1. `P1.1` 事件模式定义（protocol-grounded event schema）；
2. `P1.2` 状态特征工程（micro/meso/macro）；
3. `P1.3` 状态估计器 MVP；
4. `P1.4` 误差分析与可解释可视化；
5. `P1.5` 完整 MMLU `val` 门禁评测。

门禁：`Score(1) > Score(0)`。

### Phase 2（方向二，中级层）: Forecastive Modeling

目标：实现“先验 + 记忆 + 分布预测”的预测核心。

#### 细分计划

1. `P2.1` 早期强先验与衰减机制；
2. `P2.2` 跨轮状态缓存；
3. `P2.3` 容量感知社会记忆（三层）；
4. `P2.4` 多分辨率分布预测头与约束；
5. `P2.5` 完整 MMLU `val` 门禁评测。

门禁：`Score(2) > Score(1)`。

### Phase 3（方向三，高级层）: Governance Control + Full Fusion

目标：融合前两方向并形成完整预测治理闭环。

#### 细分计划

1. `P3.1` 治理动作空间设计（暂停、回滚、拆并组、优先级、预算节流）；
2. `P3.2` 滚动预测控制策略；
3. `P3.3` 三方向融合（Phase0 baseline + Phase1 state + Phase2 forecasting）；
4. `P3.4` 端到端消融与鲁棒性实验；
5. `P3.5` 完整 MMLU `val` 门禁评测与 final report。

门禁：`Score(3) > Score(2)`，并输出完整融合方案。

## 8. 工程与产物规范

### 8.1 路径规范

1. 复现测试：`tests/repro/`
2. 运行脚本：`scripts/`
3. 阶段测试记录：`tests/records/<run_id>/`
4. 阶段 benchmark：`tests/benchmarks/mmlu/phase_<N>/`

### 8.2 必存产物

每个 phase 至少保留：

1. `phase_plan.md`（任务细分、subagent 细分、执行顺序）
2. `benchmark_report.md`（完整 MMLU `val`）
3. 全部原始日志
4. 失败重测日志
5. 分数对比表（含 delta vs previous phase）

### 8.3 禁止事项

1. 删除失败 benchmark 记录；
2. 使用不完整 MMLU `val` 冒充 phase gate；
3. 跳过 `Score(N) > Score(N-1)` 约束推进 phase。

## 9. 风险与缓解

### 风险 A：状态不可辨识

- 缓解：加强 protocol 信号占比，构建事件级可解释特征。

### 风险 B：先验锁死

- 缓解：时间衰减 + 证据冲突触发降权。

### 风险 C：多分辨率复杂度过高

- 缓解：不稳定 regime 才激活全模块，短任务 early-exit。

### 风险 D：Goodhart

- 缓解：治理目标绑定机制动作与证据动作，避免仅消息级 reward。

### 风险 E：分布不合法或失配

- 缓解：单调约束、校准评估、干预一致性验证。

## 10. 当前执行结论

本计划将 IoA 的研究重心从“当前结构优化”转向“未来协作分布预测与治理控制”，并通过 phase-gated、benchmark-driven、fully reproducible 工程流程保证研究推进可审计、可复现、可迭代。
