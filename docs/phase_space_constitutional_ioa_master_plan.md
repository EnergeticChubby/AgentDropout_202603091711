# Phase-Space Constitutional IoA：完整研究与执行主计划（Blny_v2）

> 本文档为研究主线展开；全局总纲请以 `plan.md` 为准。

## 1. 目标与核心问题重定义

本计划采用如下硬定义作为研究母题：

> Internet of Agents（IoA）的核心问题不是“通信图不够优”，而是“系统看不见自身隐协作状态，却需要在状态部分可观测、早期高脆弱、路径依赖和共享表示容量受限的条件下持续做协作控制”。

据此，本计划不再以“谁说话/谁连接/剪哪条边”为第一控制对象，而以“隐协作动力学 + 时变制度控制 + 风险一致调度”为核心控制对象。

执行级任务拆解请同时遵循：`docs/phase_implementation_breakdown.md`。

---

## 2. 总体研究假设与技术主线

### 2.1 总体假设

1. **观测序列不等于协作状态**：消息流只是隐协作状态的投影。
2. **失效具有多尺度前兆**：微观、中观、宏观尺度耦合先于最终性能退化。
3. **早期轮次最脆弱**：若无时变脚手架，系统容易进入错误吸引子。
4. **失败有双瓶颈**：信息传播不充分（sensitivity）与表示容量饱和（capacity）需分治。
5. **调度风险应结构一致**：路由/终止/切换决策输出应是合法风险分布而非单点分数。

### 2.2 三层统一主线（非并列点子）

- **Layer-1 Observer**：Phase-Space Internet of Agents（隐协作状态观测器）
- **Layer-2 Controller**：Anti-Collapse Constitutional IoA（防早期坍塌时变宪法）
- **Layer-3 Scheduler**：Dual-Bottleneck Risk-Coherent IoA（双瓶颈分布一致调度器）

---

## 3. 形式化定义（执行侧）

### 3.1 系统建模

- 将 IoA 建模为部分可观测动态系统：
  - 隐状态：`z_t`（latent collaboration state）
  - 观测：`o_t`（消息、工具结果、路由、摘要、状态标签等）
  - 动作：`a_t`（选 agent、建队、handoff、总结、终止）
  - 回报：`r_t`（任务正确率、成本、时延、风险）

### 3.2 三层对象

1. **Observer**：学习 `q(z_t | o_{1:t})`，并识别 basin（探索/拥塞/锁死/虚假共识/发散）。
2. **Controller**：基于 `z_t` 和时序阶段 `t` 调节宪法约束强度 `w_t`（早期强、后期衰减）。
3. **Scheduler**：在 capacity/sensitivity 双诊断上，输出受单调约束的风险分布用于路由决策。

---

## 4. 多尺度协作观测协议（Observer输入规范）

### 4.1 微观特征（step/token 级）

- token 压缩率
- contradiction rate
- tool failure/retry 率
- evidence novelty
- paraphrase drift

### 4.2 中观特征（round/team 级）

- team churn
- nested team 深度变化
- FSM transition 频率
- unresolved issue backlog

### 4.3 宏观特征（task/system 级）

- task rollback 率
- manager 覆盖率
- summary 替代原始证据比例
- 跨团队依赖图谱指标

---

## 5. Phase 执行路线图（按方向组织：Phase0~Phase3）

> 原则：每个 phase 必须任务细分、完整测试、独立 commit、达标后自动进入下一 phase。

### Phase 0（基线）：AgentDropout 算法测试与基线冻结

- 定位：基线方向（后续三方向的对照基准）。
- 目标：在统一协议下完成 AgentDropout 基线测试并冻结可比较基线。
- 子任务（task/subAgent）：
  1. 计划复读与 phase 任务拆解（生成 `phase_task_breakdown.md`）
  2. 基线配置冻结（模型、接口、MMLU 完整 Val、重测策略）
  3. AgentDropout 基线运行与记录归档
  4. 基线指标发布（accuracy/cost/latency）并形成 `benchmark_compare.md`
- 验收：基线测试可复跑、记录完整、成为 Phase1 的唯一比较基线。

### Phase 1（方向一，基础层）：Phase-Space Observer

- 定位：基础方向（隐协作状态“可观测化”）。
- 目标：构建多尺度观测器并完成相空间重构原型。
- 子任务（task/subAgent）：
  1. 微/中/宏尺度特征埋点与张量化
  2. delay embedding 与 latent state `z_t` 重构
  3. basin 初步识别（探索/拥塞/锁死/虚假共识/发散）
  4. 可解释性对齐（与失败事件对齐）
- 与其他方向融合要求：
  - 向 Phase2 输出可消费的状态信号 `z_t` 与 basin 标签。
- 验收：状态重构可用、可解释、且 benchmark 优于 Phase0。

### Phase 2（方向二，中间层）：Anti-Collapse Constitutional Controller

- 定位：增强方向（早期坍塌控制）。
- 目标：实现“早期强、后期弱”的时变宪法控制，并接入 Observer 状态。
- 子任务（task/subAgent）：
  1. early-stage 宪法规则模板
  2. 衰减门控 `w_t` 与过干预检测
  3. institutional memory（未结清假设保留）
  4. 基于 `z_t` 的动态约束强度调节
- 与其他方向融合要求：
  - 消费 Phase1 的 `z_t`；向 Phase3 输出稳定化后的控制轨迹与风险先验。
- 验收：早期坍塌率下降、过干预可控、且 benchmark 优于 Phase1。

### Phase 3（方向三，高级层 + 融合层）：Dual-Bottleneck Risk-Coherent Scheduler

- 定位：高级方向（容量/传播双瓶颈 + 风险一致调度）并完成全方向融合。
- 目标：构建风险一致调度器，并融合 Phase1+Phase2 形成完整解决方案。
- 子任务（task/subAgent）：
  1. capacity vs sensitivity 双诊断器
  2. 分治策略（summary fallback / retrieval switch）
  3. 风险分布头（成功率/成本/时延/回滚风险）
  4. non-crossing 与单调合法性约束
  5. 三方向端到端融合与关键消融（无L1/无L2/无L3）
- 融合交付（必须）：
  - 交付 `Observer + Controller + Scheduler` 的完整一体化方案。
- 验收：融合方案相较 Phase2 继续提升，并形成最终完整解决方案。

---

## 6. 强制测试协议（全阶段统一）

### 6.1 数据集与范围

- benchmark 统一使用 **MMLU 完整 Val 集**。
- 覆盖率必须为 **100%**，禁止抽样结果作为 phase 验收依据。

### 6.2 并发失败重测机制（硬性）

- 若出现 API 高并发导致的失败（超时/限流/连接错误），必须：
  1. 记录失败题清单（`failed_items.json`）
  2. 执行定向重测并记录（`retry_log.md`）
  3. 直到失败题全部补齐，覆盖率恢复到 100%

### 6.3 记录与复现（硬性）

- 所有测试必须使用 `scripts/testing/run_and_record.sh` 归档。
- 每次测试记录需包含：
  - `record.md`, `command.sh`, `stdout.log`, `stderr.log`, `exit_code.txt`, `env_snapshot.txt`
  - `metrics.json|csv`, `benchmark_compare.md`
  - 并发失败场景额外包含 `failed_items.json`, `retry_log.md`

---

## 7. Phase 门禁与自动推进规则（硬性）

每个 phase 结束后，必须按下列顺序执行，缺一不可：

1. **完整重读计划**：`docs/testing_plan.md` 与本主计划。
2. **任务细分归档**：基于 `docs/templates/phase_task_breakdown_template.md` 更新 `phase_task_breakdown.md`。
3. **执行优化后 MMLU 完整 Val benchmark**。
4. **性能比较**：当前 phase 主指标必须严格优于上一达标 phase（Phase0→Phase1→Phase2→Phase3）。
5. **若未优于上一 phase**：继续优化/微调并重复测试，直至达标。
6. **达标后独立 commit 并 push**。
7. **自动进入下一 phase**。

---

## 8. 指标体系与判定规则

### 8.1 主指标

- MMLU Accuracy（主指标，必须严格上升）

### 8.2 辅指标

- token 成本
- 延迟
- rollback rate
- uncertainty calibration（若启用风险头）

### 8.3 判定优于上一 phase

- 必须满足：`Accuracy_phase_t > Accuracy_phase_(t-1)`（严格大于）
- 若 accuracy 持平或下降：判定不达标，禁止进入下一 phase。

---

## 9. 产出清单（每个 phase）

1. `phase_task_breakdown.md`（task/subAgent 细分）
2. 完整测试记录目录（含全量日志与指标）
3. `benchmark_compare.md`（与上一 phase 对比）
4. 代码/配置变更
5. 独立 commit（phase 级）

---

## 10. 分支与提交规范

- 分支统一：`Blny_v2`
- 提交要求：每个 phase 至少 1 个独立 commit
- 推荐提交前缀：
  - `phase0: ...`
  - `phase1: ...`
  - `phase2: ...`
  - `phase3: ...`

