# Phase-Space Constitutional IoA：完整研究与执行主计划（Blny_v2）

## 1. 目标与核心问题重定义

本计划采用如下硬定义作为研究母题：

> Internet of Agents（IoA）的核心问题不是“通信图不够优”，而是“系统看不见自身隐协作状态，却需要在状态部分可观测、早期高脆弱、路径依赖和共享表示容量受限的条件下持续做协作控制”。

据此，本计划不再以“谁说话/谁连接/剪哪条边”为第一控制对象，而以“隐协作动力学 + 时变制度控制 + 风险一致调度”为核心控制对象。

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

## 5. Phase 执行路线图（完整可落地）

> 原则：每个 phase 必须任务细分、完整测试、独立 commit、达标后自动进入下一 phase。

### Phase 0：治理与基线冻结

- 目标：冻结计划、规范记录、建立基线协议。
- 子任务（task/subAgent）：
  1. 计划复读与任务拆解（生成 `phase_task_breakdown.md`）
  2. 执行脚本与记录模板检查
  3. 基线运行参数冻结
- 验收：规则文档齐全、测试管线可运行。

### Phase 1：Observer 数据化与相空间重构原型

- 目标：打通多尺度观测张量与 `z_t` 重构。
- 子任务：
  1. 埋点与多尺度特征抽取
  2. delay embedding / phase-space reconstruction
  3. basin 初步标注
- 验收：可输出 `z_t`、可视化轨迹、可回放。

### Phase 2：Basin 识别与可解释对齐

- 目标：将隐状态与外部失败事件对齐。
- 子任务：
  1. 结构化扰动实验（延迟专家/隐藏证据/矛盾摘要）
  2. basin 到失败类型映射
  3. 跨任务不变量抽取
- 验收：扰动可分、映射稳定、解释一致。

### Phase 3：Anti-Collapse 宪法控制器

- 目标：实现“早期强、后期弱”的时变制度控制。
- 子任务：
  1. early-stage 约束模板
  2. 衰减门控 `w_t`
  3. institutional memory（跨轮未结清假设）
- 验收：早期坍塌率下降，后期过干预可控。

### Phase 4：Dual-Bottleneck 诊断器

- 目标：区分 capacity vs sensitivity 失效来源。
- 子任务：
  1. capacity saturation 指标
  2. sensitivity attenuation 指标
  3. 分治策略切换（summary vs retrieval）
- 验收：诊断可解释，治疗策略可复现。

### Phase 5：Risk-Coherent 路由器

- 目标：输出合法、单调、不可交叉的风险分布。
- 子任务：
  1. 多时域风险头（成功率/成本/时延/回滚风险）
  2. 单调约束与 non-crossing 校验
  3. 后验校准（可选 conformal）
- 验收：风险分布合法，路由稳定性提升。

### Phase 6：端到端集成与消融

- 目标：验证三层协同收益与边界。
- 子任务：
  1. 逐层累加实验（L1→L2→L3）
  2. 关键消融（无observer/无宪法/无双瓶颈）
  3. 成本-性能-风险权衡分析
- 验收：主结果、消融结果、误差分析完整。

### Phase 7：论文化交付

- 目标：形成主论文 + 系统论文 + 分析论文稿件框架。
- 子任务：
  1. 主论文（Phase-Space Constitutional IoA）
  2. 系统论文（Dual-Bottleneck Risk-Coherent Router）
  3. 分析论文（early-stage collapse & basin transfer）
- 验收：开题/初稿/图表/复现实验包齐备。

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
4. **性能比较**：当前 phase 主指标必须严格优于上一达标 phase。
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
  - `phase4: ...`
  - `phase5: ...`
  - `phase6: ...`
  - `phase7: ...`

