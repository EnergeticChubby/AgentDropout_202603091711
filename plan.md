# SS-IoA Master Plan（唯一总控计划）

## 0. 文档定位

本文件是项目执行的**唯一总控计划（single source of truth）**。  
所有任务、规则、门禁、测试、留档与提交要求以本文件为准。

---

## 1. 总体目标与问题定义

### 1.1 总体目标

构建并验证 SS-IoA（State-Space Internet of Agents）完整方案，使多智能体协作从“表层消息驱动”升级为“隐藏状态驱动”，并在统一评测基线下实现持续性能提升。

### 1.2 根问题定义（必须保持一致）

系统失败的根因不是单纯拓扑不优，而是：

1. 早期塌缩（证据不足时过早组织决策）
2. 重复发现（跨轮缺少状态载体）
3. 容量塌缩（集体记忆容量失配）
4. 隐状态错控（未估计隐藏状态即直接控制）

---

## 2. 全局硬规则（Non-Negotiable）

1. **每个 Phase 开始前**必须完整重读本文件。  
2. **每个 Phase 必须先做任务细分**（Task/Subtask/SubAgent）。  
3. **每个 Phase 结束必须执行 MMLU 完整 Val 测试**（不得抽样、不得截断）。  
4. 测试失败题（并发/API异常）必须进入重测队列，重测过程必须留档。  
5. 仅当 `metric_current > metric_previous` 时，允许进入下一 Phase。  
6. 若不达标，必须进入优化闭环（调参/调策略/重测），直到达标。  
7. 每个 Phase 必须独立 commit + push，不得跨 Phase 混提。  
8. 所有测试数据必须保留（md/log/json/history），保证可复现与可审计。  
9. 测试统一模型配置：
   - `MODEL_NAME=qwen3-8b`
   - `BASE_URL=https://llm.undefined.qzz.io/v1/chat/completions`
   - `API_KEY=...`（来自 `template.env`）

---

## 3. 体系化执行架构（Phase0~Phase3）

## 3.1 Phase0（基线方向）：AgentDropout Baseline

### 目标

建立可追踪、可复现、可比较的 AgentDropout 基线。

### 入口条件

- 配置冻结（模型、提示、参数、随机种子）
- 评测脚本可运行
- 记录目录已创建

### 任务拆分

- P0-T1：冻结基线参数与运行命令
- P0-T2：执行 MMLU 全量 Val（失败题重测）
- P0-T3：输出指标与失败重试详情
- P0-T4：写入 `performance_history.csv` 的 Phase0 行

### 推荐 subAgent 分工

- `phase0-config`
- `phase0-runner`
- `phase0-reporter`

### 产物

- `tests/benchmarks/mmlu/<ts>_phase0.md`
- `tests/benchmarks/mmlu/<ts>_phase0.log`
- `tests/benchmarks/mmlu/<ts>_phase0_metrics.json`
- `tests/benchmarks/mmlu/<ts>_phase0_retry_failures.json`
- `tests/benchmarks/mmlu/performance_history.csv`

### 退出门禁

- 全量 Val 完成
- 失败题重测记录完整
- 基线指标落盘完成
- commit + push 完成

---

## 3.2 Phase1（基础方向）：隐状态估计 + 衰减制度先验

### 目标

将协作控制对象从消息流升级为 `z_t`（latent collective state）与 `p_t`（decaying prior）。

### 任务拆分

- P1-T1：定义观测事件 schema（消息/工具/转移/异常）
- P1-T2：实现 `z_t = f_recon(o_{1:t})`
- P1-T3：实现 `p_t = decay(p_0, evidence_t)`
- P1-T4：实现 prior override（冲突证据快速减权）
- P1-T5：补充状态可验证性指标（future success / block risk）

### 推荐 subAgent 分工

- `phase1-state-schema`
- `phase1-state-model`
- `phase1-prior-scheduler`
- `phase1-evaluation`

### 退出门禁

- 代码与配置落盘
- MMLU 全量 Val + 重测完成
- 性能严格优于 Phase0
- commit + push 完成

---

## 3.3 Phase2（进阶方向）：跨轮记忆 + 容量感知控制

### 目标

解决 rediscovery 与 collective capacity over-squashing。

### 任务拆分

- P2-T1：实现 `m_t = f_mem(m_{t-1}, z_t, o_t)`
- P2-T2：实现 sufficient-statistics 压缩存储
- P2-T3：实现 credibility gate + quarantine memory
- P2-T4：实现 admission control + utility-priced slots
- P2-T5：实现 phase-specific memory pools
- P2-T6：实现污染检测与可追溯 forgetting

### 推荐 subAgent 分工

- `phase2-memory-core`
- `phase2-capacity-control`
- `phase2-poisoning-guard`
- `phase2-evaluation`

### 退出门禁

- 全量 Val + 重测完成
- 性能严格优于 Phase1
- 完整实验留档
- commit + push 完成

---

## 3.4 Phase3（高级融合方向）：完整融合与收敛发布

### 目标

融合 Phase1 + Phase2，形成可复现的完整方案与交付工件。

### 任务拆分

- P3-T1：实现融合控制策略 `π(z_t, m_t, p_t)`
- P3-T2：实现双时间尺度控制（快执行/慢重建）
- P3-T3：联调异常触发（冲突、长 barrier、持续分歧）
- P3-T4：完成消融实验与鲁棒性实验
- P3-T5：固化一键复现实验与结果汇总

### 推荐 subAgent 分工

- `phase3-fusion-controller`
- `phase3-ablation`
- `phase3-robustness`
- `phase3-release`

### 退出门禁

- 全量 Val + 重测完成
- 性能严格优于 Phase2
- 复现包可运行
- commit + push 完成

---

## 4. Benchmark 与测试治理（统一标准）

## 4.1 强制评测范围

- 数据集：**MMLU 完整 Val**
- 禁止：抽样、截断、替换子集

## 4.2 失败题重测机制（并发/API）

失败类型示例：429、timeout、连接中断、服务暂时不可用、model route unavailable。

流程：

1. 初测失败题写入 retry 队列
2. 降并发重试（建议 `retry_batch_size=1`）
3. 逐轮重试并记录轮次、错误类型、题号
4. 达上限仍失败则标注“环境/服务阻塞”，保留证据

## 4.3 强制留档文件

每次 benchmark 必须保留：

- 结构化报告：`*.md`
- 原始日志：`*.log`
- 指标：`*_metrics.json`
- 重试详情：`*_retry_failures.json`
- 历史追踪：`performance_history.csv`

## 4.4 统一命令基线（示例）

`python experiments/run_mmlu.py --llm_name qwen3-8b --batch_size 4 --retry_batch_size 1 --max_retry_rounds 5 --retry_delay 2`

---

## 5. 性能门禁与优化闭环

判定规则：`metric_current > metric_previous`

若不满足，执行优化闭环：

1. 根因定位（状态估计偏差/记忆污染/容量配置/先验衰减）
2. 参数调整（阈值、预算、衰减率、窗口）
3. 策略调整（写入规则、异常触发、重建频率）
4. 重跑全量 Val + 失败题重测
5. 更新记录并再次判定

直到达标前，不允许进入下一 Phase。

---

## 6. Task / SubAgent 运行规范

每个 Phase 的执行单必须包含：

1. 子任务 ID、目标、输入、输出
2. 责任主体（主代理 / subAgent）
3. 期望产物路径
4. 验收命令 / 指标阈值
5. 风险与回退方案

subAgent 输出要求：

- 可直接落盘
- 可直接验证
- 可直接合并

---

## 7. Git 与提交流程规范

1. 每个 Phase 独立 commit，不跨 Phase 混提。  
2. 提交消息建议：`phaseX: <summary>`。  
3. 测试记录应与对应 Phase 代码/计划同批提交。  
4. 不得遗漏 benchmark 证据文件。  
5. 提交后必须 push，并在日志中记录 commit hash。  

---

## 8. 风险治理与回退规则

## 8.1 常见风险

- 模型不可用/路由不可达
- 并发导致批量失败
- 指标波动导致阶段回退
- 记忆污染导致持续错误

## 8.2 回退策略

1. 保留当前 Phase 工件，不删除失败证据
2. 回滚到上一个“达标 commit”
3. 仅修改最小必要参数/策略
4. 重跑全量 Val + 重测队列

---

## 9. 完成定义（Definition of Done）

某个 Phase 完成必须同时满足：

1. 任务拆分已执行并落盘
2. 产物齐全且路径可追踪
3. 全量 Val + 失败题重测完成
4. 指标优于上一 Phase
5. commit + push 完成
6. 执行日志更新完成

---

## 10. 执行顺序总览

`Phase0 -> Phase1 -> Phase2 -> Phase3`

每个箭头都受制于同一门禁：

`全量Val完成 AND 失败题重测完成 AND 指标提升 AND 提交完成`

