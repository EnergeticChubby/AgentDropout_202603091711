# 测试代码与测试记录治理计划（可复现）

## 1. 目标

本计划用于保证以下要求可持续执行：

1. 所有测试代码被统一保存、可追踪。
2. 所有测试记录被结构化保存、可复盘。
3. 任意一次测试可以按文档步骤复现。
4. 每个 phase 更新必须进行一次独立 commit。

## 2. 固定测试配置

所有测试默认使用以下模型配置（除非在具体实验记录中明确说明偏离原因）：

- `MODEL_NAME=glm-4.5-flash`
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

### Phase A：计划与规范更新

- 更新/新增计划文档与目录结构。
- 输出标准：计划文档可读、路径规范明确。
- 提交要求：完成后立即 commit。

### Phase B：测试工具代码更新

- 更新/新增 `tests/code/` 下的脚本。
- 输出标准：脚本可运行，能自动产出测试记录。
- 提交要求：完成后立即 commit。

### Phase C：测试执行与记录更新

- 使用测试脚本执行命令并生成记录。
- 输出标准：`tests/records/` 中包含 Markdown 与 raw log。
- 提交要求：完成后立即 commit。

### Phase D：复现校验与发布说明

- 校验记录中的命令可重跑。
- 输出标准：记录包含命令、退出码、环境信息、复现步骤。
- 提交要求：完成后立即 commit。

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

