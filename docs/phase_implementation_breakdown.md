# Phase 实施细分清单（Phase0~Phase3）

本文件是 `docs/phase_space_constitutional_ioa_master_plan.md` 的执行级拆解版本，用于任务排程与融合落地。

## Phase0（AgentDropout 基线）

### M0.1 环境与依赖
- 输入：仓库代码、统一模型配置
- 输出：可运行依赖清单、环境快照
- 验收：基线命令可启动，记录落盘

### M0.2 基线图结构/执行烟测
- 输入：Graph 初始化参数
- 输出：图构建与连边验证日志
- 验收：节点/掩码/连边行为符合预期

### M0.3 基线 benchmark（MMLU Full Val）
- 输入：基线配置
- 输出：基线 accuracy/cost/latency
- 验收：覆盖率 100%，并发失败题补齐

### M0.4 基线冻结
- 输入：M0.1~M0.3 结果
- 输出：baseline tag + compare 基准
- 验收：后续 Phase 统一对比该基线

---

## Phase1（方向一：Observer）

### M1.1 多尺度观测埋点
- 微观：contradiction/tool retry/novelty
- 中观：team churn/FSM transition
- 宏观：rollback/summary dominance

### M1.2 相空间重构
- delay embedding
- latent `z_t` 建模
- 序列可视化与可回放

### M1.3 basin 识别与标注
- basin 分类：探索/拥塞/锁死/虚假共识/发散
- 与失败事件对齐标签

### M1.4 Phase1 benchmark 与对比
- 输出：`benchmark_compare.md`（vs Phase0）
- 门禁：Accuracy 严格优于 Phase0

### Phase1 → Phase2 融合接口
- `state_stream.jsonl`（`z_t` + basin）
- `observer_metrics.json`

---

## Phase2（方向二：Controller）

### M2.1 Early-stage 宪法模板
- 高风险结论延迟入 summary
- unresolved contradiction 强制保留

### M2.2 时变衰减控制
- `w_t` 衰减门控
- over-interference 监控

### M2.3 Institutional Memory
- 未结清假设账本
- 跨轮可追溯

### M2.4 状态驱动控制
- 消费 Phase1 的 `z_t`
- 按 basin 自适应调节约束强度

### M2.5 Phase2 benchmark 与对比
- 输出：`benchmark_compare.md`（vs Phase1）
- 门禁：Accuracy 严格优于 Phase1

### Phase2 → Phase3 融合接口
- `control_trace.jsonl`（时刻、规则、权重、触发原因）
- `institutional_memory_snapshot.json`

---

## Phase3（方向三：Scheduler + 全融合）

### M3.1 双瓶颈诊断
- capacity saturation 指标
- sensitivity attenuation 指标

### M3.2 分治执行策略
- capacity 超阈值：retrieval 路由
- sensitivity 衰减：minority-preserving route

### M3.3 风险一致分布头
- 成功率/成本/延迟/回滚风险分布
- 单调性与 non-crossing 约束

### M3.4 三方向端到端融合
- 接入 Observer 状态 + Controller 轨迹
- 执行一体化调度闭环

### M3.5 消融与边界分析
- 无L1/无L2/无L3
- 成本-性能-风险三维权衡

### M3.6 Phase3 benchmark 与对比
- 输出：`benchmark_compare.md`（vs Phase2）
- 门禁：Accuracy 严格优于 Phase2

---

## 融合完成判据（最终）

以下条件同时满足，认定“完整解决方案”完成：

1. Phase0~Phase3 全部通过门禁并各自独立 commit。
2. 每个 phase 均完成 MMLU Full Val（100%覆盖）与失败题补齐。
3. `Accuracy_phase3 > Accuracy_phase2 > Accuracy_phase1 > Accuracy_phase0`。
4. 三方向接口产物齐备并可复跑。

