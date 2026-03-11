# 测试与复现执行计划（Blny_v2）

## 1. 目标与范围

本计划用于规范 `Blny_v2` 分支上的所有测试活动，确保以下目标同时成立：

1. **测试代码可追溯**：每次测试使用的脚本、命令、参数可定位。
2. **测试记录可复核**：每次测试有标准化记录文件（命令、日志、退出码、环境快照）。
3. **结果可复现**：任意成员可依据记录在相同代码版本上复跑测试。
4. **流程可审计**：每个 phase 更新均有独立 commit。

主研究路线与完整 phase 设计请同步遵循：`docs/phase_space_constitutional_ioa_master_plan.md` 与 `docs/phase_implementation_breakdown.md`。

---

## 2. 强制模型与接口配置（所有测试统一）

所有测试必须使用以下配置，不允许混用其他模型或接口：

- `model_name`: `glm-4.5-flash`
- `base_url`: `https://llm.undefined.qzz.io/v1/chat/completions`
- `api_key`: `sk-pc8yOBXhAVOXEa38hpH1XBtuPwadnB1rLpNxHMS6grCuMrZh`

建议将上述配置写入环境文件，并在测试记录中完整回填。

### 2.1 MMLU 测试范围硬性要求

- 所有 benchmark 测试统一使用 **MMLU 完整 Val 集**。
- 不允许仅抽样测试或只测子集作为 phase 验收依据。
- phase 验收时必须提供“完整 Val 集覆盖率=100%”的证明。

---

## 3. 测试资产存储规范

### 3.1 测试代码（必须入库）

- 目录：`experiments/tests/`
- 内容：测试脚本、测试驱动程序、参数模板、数据切分脚本。
- 命名建议：`test_<dataset>_<target>.py` 或 `run_<dataset>_<target>.sh`

### 3.2 测试记录（必须入库）

- 目录：`result/test_records/`
- 分层规则：`result/test_records/<phase>/<UTC_TIMESTAMP>_<test_name>/`
- 每条记录至少包含：
  - `record.md`（执行摘要）
  - `command.sh`（可直接复跑）
  - `stdout.log`、`stderr.log`
  - `exit_code.txt`
  - `env_snapshot.txt`（分支、commit、Python版本等）

---

## 4. Phase 管理与提交策略（强制）

每个 phase 更新完成后，必须立即 commit，不得把多个 phase 混在同一个 commit 中。

### 4.1 推荐 phase 划分

- **Phase 0：AgentDropout 基线算法测试与基线冻结**
- **Phase 1：方向一（基础）- Phase-Space Observer**
- **Phase 2：方向二（中级）- Anti-Collapse Controller**
- **Phase 3：方向三（高级+融合）- Dual-Bottleneck Risk-Coherent Scheduler**

### 4.2 Commit 规则

- 分支命名：统一使用 `Blny_v2`
- 每个 phase 至少 1 个 commit
- 提交信息格式建议：
  - `phase0: agentdropout baseline`
  - `phase1: observer implementation and tests`
  - `phase2: controller implementation and tests`
  - `phase3: scheduler fusion implementation and tests`

---

## 5. Phase 强制执行闭环（新增硬性规则）

以下规则对每个 phase 均为**硬性要求**：

1. **每完成一个 phase，进入下一 phase 前必须重新完整阅读计划文档**（`docs/testing_plan.md` 与 `docs/phase_space_constitutional_ioa_master_plan.md`），不得跳读。
2. **在进行 task 与 subAgent 处理时，必须对该 phase 任务进行细分**，并形成可追踪子任务清单（建议保存为 `phase_task_breakdown.md`）。
3. **每个 phase 完成后，必须执行“优化后的 MMLU benchmark”测试**，且测试必须写入标准记录目录。
4. **必须保留所有测试数据**（原始日志、命令、退出码、环境快照、指标汇总、对比结论），不得仅保留摘要。
5. **每个 phase 的 benchmark 性能必须优于上一个 phase**（以主指标为准，默认 `accuracy` 严格大于上一 phase）。
6. **若性能未优于上一 phase，则必须继续优化/微调并重复 benchmark**，直到满足“优于上一 phase”为止。
7. **当且仅当“phase 完成 + benchmark 优于上一 phase”同时满足后，才自动进入下一 phase**。
8. **MMLU benchmark 必须基于完整 Val 集的完整测试结果**，不得以部分结果提前推进 phase。
9. **若因 API 高并发导致题目失败（超时/限流/连接错误等），必须对失败题目定向重测，直到失败题全部补齐**。

> 说明：第一个产生 MMLU benchmark 的 phase 作为基线 phase；之后所有 phase 必须与最近一个已达标 phase 对比并实现提升。

---

## 6. 可复现执行流程（标准）

1. 切到 `Blny_v2` 并确认工作区干净（允许未跟踪文件但不得污染测试结果）。
2. 固化配置（模型、接口、密钥）到环境变量或配置文件。
3. 使用 `scripts/testing/run_and_record.sh` 执行测试并自动归档记录。
4. 检查 `result/test_records/` 中记录完整性。
5. 将测试代码和记录一起提交，按 phase 进行 commit。
6. 推送远端并在变更说明中引用对应记录路径。

---

## 7. 质量门禁（通过标准）

以下条件全部满足才可判定该 phase 完成：

- 测试命令可复跑，且退出码与记录一致。
- 关键指标（accuracy/正确率/耗时/成本）有明确对比或解释。
- `record.md` 提供输入、输出、配置、结论四要素。
- commit 与 phase 一一对应，便于审计和回滚。
- 已执行优化后的 MMLU benchmark，并有与上一 phase 的对比结论。
- MMLU 主指标严格优于上一 phase；若未达到则不得进入下一 phase。
- MMLU 完整 Val 集覆盖率必须为 100%。
- 因 API 并发导致失败的题目已完成重测并补齐最终结果。

---

## 8. 交付物清单（每个 phase）

- 测试代码变更（如有）
- 测试记录目录（必须）
- 结论性 Markdown（必须，专业、可读、可复核）
- 独立 commit（必须）
- `phase_task_breakdown.md`（task/subAgent 细分清单，必须）
- MMLU benchmark 全量数据与对比报告（必须）
- 失败题重测清单与重测结果（必须，若发生 API 并发失败）

