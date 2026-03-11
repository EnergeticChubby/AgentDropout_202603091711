# 测试代码与测试记录治理计划（可复现）

## 1. 目标

本计划用于保证以下要求可持续执行：

1. 所有测试代码被统一保存、可追踪。
2. 所有测试记录被结构化保存、可复盘。
3. 任意一次测试可以按文档步骤复现。
4. 每个 phase 更新必须进行一次独立 commit。

总控计划文档：`plan.md`（唯一总控计划，任务与规则体系以其为准）。
配套总计划文档：`docs/SS_IOA_COMPLETE_PLAN.md`（用于补充 SS-IoA 研究背景与路线细节）。
方向 phase 映射：`Phase0(AgentDropout 基线测试) -> Phase1(基础方向) -> Phase2(进阶方向) -> Phase3(高级融合方向)`。

## 2. 固定测试配置

所有测试默认使用以下模型配置（除非在具体实验记录中明确说明偏离原因）：

- `MODEL_NAME=qwen3-8b`
- `BASE_URL=https://llm.undefined.qzz.io/v1/chat/completions`
- `API_KEY=sk-pc8yOBXhAVOXEa38hpH1XBtuPwadnB1rLpNxHMS6grCuMrZh`

## 3. 仓库落盘规范

### 3.1 测试代码存放

- 路径：`tests/code/`
- 内容：可复用测试脚本、测试辅助工具、记录生成工具。

### 3.2 测试记录存放

- 路径：`tests/records/`
- 内容：每次测试对应的 Markdown 记录与原始日志。
- 命名建议：`<UTC时间戳>_<phase名>.md/.log`

### 3.3 计划文档

- 路径：`docs/TESTING_AND_PHASE_PLAN.md`（本文件）
- 作用：统一约束 phase、commit、记录与复现标准。

## 4. Phase 执行与提交要求（强制）

在每个 phase 开始前，必须先执行以下通用步骤（对 A/B/C/D 全部生效）：

1. 重新完整阅读 `docs/TESTING_AND_PHASE_PLAN.md` 全文。
2. 将当前 phase 任务细分为可执行子任务（Task Breakdown）。
3. 如需使用 subAgent，必须对每个 subAgent 分配明确子任务、输入、输出与验收标准。

### Phase A：计划与规范更新

- 更新/新增计划文档与目录结构。
- 输出标准：计划文档可读、路径规范明确。
- MMLU门禁：完成 phase 后必须执行“优化后的 MMLU benchmark 测试”，并保存全部测试数据。
- 提交要求：仅在 MMLU 性能优于上一 phase（或基线）后允许 commit 并进入下一 phase。

### Phase B：测试工具代码更新

- 更新/新增 `tests/code/` 下的脚本。
- 输出标准：脚本可运行，能自动产出测试记录。
- MMLU门禁：完成 phase 后必须执行“优化后的 MMLU benchmark 测试”，并保存全部测试数据。
- 提交要求：仅在 MMLU 性能优于上一 phase 后允许 commit 并进入下一 phase。

### Phase C：测试执行与记录更新

- 使用测试脚本执行命令并生成记录。
- 输出标准：`tests/records/` 中包含 Markdown 与 raw log。
- MMLU门禁：完成 phase 后必须执行“优化后的 MMLU benchmark 测试”，并保存全部测试数据。
- 提交要求：仅在 MMLU 性能优于上一 phase 后允许 commit 并进入下一 phase。

### Phase D：复现校验与发布说明

- 校验记录中的命令可重跑。
- 输出标准：记录包含命令、退出码、环境信息、复现步骤。
- MMLU门禁：完成 phase 后必须执行“优化后的 MMLU benchmark 测试”，并保存全部测试数据。
- 提交要求：仅在 MMLU 性能优于上一 phase 后允许 commit 并进入下一 phase。

## 5. Commit 规则

1. 每个 phase 至少 1 个 commit，不得跨 phase 混提。
2. Commit 信息建议格式：`phase(<phase-id>): <变更摘要>`。
3. 一个 phase 未 commit，不得进入下一 phase。

## 6. 测试记录 Markdown 专业模板要求

每条测试记录（`.md`）至少包含以下字段：

1. 测试目的（Goal）
2. 前置条件（Preconditions）
3. 执行命令（Command）
4. 环境快照（Environment Snapshot）
5. 输出摘要（Output Summary）
6. 退出码（Exit Code）
7. 复现步骤（Reproduction Steps）
8. 结论（Conclusion）

## 7. 可复现性检查清单

- [ ] 记录中包含准确命令（可直接复制运行）。
- [ ] 记录中包含分支、commit、时间戳信息。
- [ ] 记录中包含模型与接口配置来源。
- [ ] 记录中有 raw log 文件路径。
- [ ] 重跑命令后结果与结论一致。

## 8. MMLU Benchmark 强制门禁（新增）

### 8.1 强制执行规则

1. 每完成一个 phase，必须执行一次“优化后的 MMLU benchmark”，且必须使用 **MMLU 完整 Val 集**（不得抽样、不得截断）。
2. 每次 benchmark 必须完整保存测试数据（命令、配置、stdout/stderr、原始结果、汇总指标）。
3. 若出现 API 高并发导致的失败题，必须对失败题进行重测，直到题目被成功评测或达到明确定义的重试上限并记录原因。
4. benchmark 性能必须严格优于上一 phase；若不满足，必须继续优化/微调并重测，直到满足为止。
5. 未达到“优于上一 phase”前，不得进入下一 phase。
6. 达标并完成 commit 后，自动进入下一 phase 处理。

### 8.2 数据留存规范

- 建议目录：`tests/benchmarks/mmlu/`
- 每次运行建议生成：
  - `<UTC时间戳>_<phase>.md`（结构化测试报告）
  - `<UTC时间戳>_<phase>.log`（原始日志）
  - `<UTC时间戳>_<phase>_metrics.json`（关键指标）
  - `performance_history.csv`（phase 间性能追踪）

### 8.3 对比判定口径

- 比较字段：建议使用同一指标（如 Accuracy）进行 phase-to-phase 对比。
- 判定条件：`current_phase_metric > previous_phase_metric`。
- 若 `<=`，则状态为“不通过”，继续优化/微调并重复 benchmark。

### 8.4 MMLU 执行参数基线（强制）

- `limit_questions` 必须为 `None`（全量 Val）。
- 必须启用失败题重试机制并记录每轮失败题索引与错误原因。
- 建议重试策略：降低重试批大小（如 `retry_batch_size=1`）并增加重试轮次。
- 参考命令（示例）：
  - `python experiments/run_mmlu.py --llm_name qwen3-8b --batch_size 4 --retry_batch_size 1 --max_retry_rounds 5 --retry_delay 2`

## 9. Task 与 subAgent 细分执行规范（新增）

1. 每个 phase 必须先给出任务拆分清单（子任务、责任主体、输入/输出）。
2. 使用 subAgent 时，必须显式约束：
   - 子任务边界
   - 期望产物路径
   - 验收命令或验收指标
3. phase 收口时，必须汇总每个子任务产物并落盘到测试记录。

