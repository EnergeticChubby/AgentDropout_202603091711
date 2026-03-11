# phase_task_breakdown.md 模板

## Phase 信息

- phase_id:
- phase_name:
- direction_name:  # Phase0=AgentDropout baseline, Phase1=Observer, Phase2=Controller, Phase3=Scheduler+Fusion
- owner:
- date_utc:
- previous_phase_commit:

## 计划复读确认（必填）

- [ ] 已完整阅读 `plan.md`
- [ ] 已完整阅读 `docs/testing_plan.md`
- [ ] 已完整阅读 `docs/phase_space_constitutional_ioa_master_plan.md`

## 任务细分（task/subAgent）

| 子任务ID | 子任务名称 | 类型(task/subAgent) | 输入 | 输出 | 负责人 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 |  |  |  |  |  | pending |
| T2 |  |  |  |  |  | pending |
| T3 |  |  |  |  |  | pending |

## MMLU 完整 Val 测试计划（必填）

- 数据范围：MMLU Full Val（100%覆盖）
- 运行命令：
- 并发重试策略：
- 失败题补齐策略：

## 验收门禁（必填）

- [ ] 已完成优化后 MMLU benchmark
- [ ] 覆盖率 100%
- [ ] 性能严格优于上一 phase
- [ ] 测试记录与数据已完整存档
- [ ] 已完成 phase 独立 commit 与 push

## 结果摘要

- accuracy_current:
- accuracy_previous:
- delta:
- conclusion:

