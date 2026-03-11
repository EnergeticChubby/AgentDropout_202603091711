# Phase Execution Log（测试代码与记录可复现落地）

## Scope

本日志记录本轮治理改造中每个 phase 的目标、产出与复现入口，用于审计和交接。
总控计划入口：`plan.md`。

## Phase Deliverables (Direction-Based)

| Phase | Objective | Deliverables |
| --- | --- | --- |
| Phase0 | AgentDropout 基线与测试 | `result/mmlu/*phase0*`（或同时间戳结果）、`tests/records/*phase0*.md/.log` |
| Phase1 | 基础方向（状态估计 + 衰减先验） | 见 `docs/SS_IOA_COMPLETE_PLAN.md` 的 Phase1 子任务产物 |
| Phase2 | 进阶方向（跨轮记忆 + 容量控制） | 见 `docs/SS_IOA_COMPLETE_PLAN.md` 的 Phase2 子任务产物 |
| Phase3 | 高级融合方向（完整方案） | 见 `docs/SS_IOA_COMPLETE_PLAN.md` 的 Phase3 子任务产物 |

## Reproducibility Entry

### 1) 运行记录脚本

`bash tests/code/run_test_and_record.sh <phase_name> <command> [args...]`

### 2) 查看测试记录

- Markdown 记录：`tests/records/*.md`
- 原始日志：`tests/records/*.log`

### 3) 关键配置

- 统一模型配置位于 `template.env`
- 计划规范位于 `docs/TESTING_AND_PHASE_PLAN.md`

## Professional Markdown Standard Applied

所有测试记录均按以下结构输出：

1. Goal
2. Preconditions
3. Command
4. Environment Snapshot
5. Output Summary
6. Exit Code
7. Reproduction Steps
8. Conclusion

## Audit Notes

- 每个 phase 已按要求独立提交（不跨 phase 混提）。
- 测试证据同时保留 Markdown 摘要与 raw log，便于复盘。

## Phase0 AgentDropout Test Status

- 已执行 Phase0 AgentDropout 测试（MMLU 路径）并完成失败题重试流程验证。
- 当前已切换测试模型为 `qwen3-8b`；旧的 `glm-4.5-flash` 不可用问题仅作为历史记录保留。
- 已保留完整失败证据与重试日志，便于后续在模型渠道恢复后直接重跑。

