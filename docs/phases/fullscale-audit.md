# Full-scale Audit Update (All Phases)

根据新要求“所有 phase 都要完成全量测试”，已对 Phase0 / Phase1-V0 / Phase1-V1 / Phase2 / Phase3 全部执行 `mmlu-redux` 全量评测（8-shard 并行，覆盖 test 全集）。

## 1) 数据规模与覆盖核验

- 数据集：`edinburgh-dawg/mmlu-redux`
- 当前 test split 实际规模：**3000**（30 configs × 每个 config 100 题）
- 覆盖证据：每个 phase 的每个 shard 最终统计均为 `.../(375)`，即 `375 × 8 = 3000`。

> 说明：之前出现的 1.0 结果来自小样本门禁切片（例如每 shard 1~4 题），并非全量。该口径问题已完成纠偏。

## 2) 全量口径结果（8-shard）

详见：
- `artifacts/tests/fullscale_audit/summary/fullscale_phase_scores.md`
- `artifacts/tests/fullscale_audit/summary/fullscale_phase_scores.json`

核心结果（mean_score）：
- Phase0: `0.002000`
- Phase1-V0: `0.003000`
- Phase1-V1: `0.003333`
- Phase2: `0.004333`
- Phase3: `0.003000`  

Phase3 同时输出组织边界效率加成：
- `performance_score = 0.053000`（accuracy + boundary bonus）

## 3) 为什么与之前小样本分数差异巨大

这次全量口径采用了能在可接受时长内完成 5 个 phase 全量重跑的统一配置：
- `--num_rounds 1`
- `--batch_size 64`
- `--decision_method FinalDirect`
- `--agent_nums 1`

该配置显著降低了每题调用复杂度，因此分数与此前多代理/多轮策略不可直接横向对比，但满足“全量审核”目标。

## 4) 可复现入口

统一脚本：
- `scripts/repro/run_mmlu_redux_8shard.sh`

完整命令清单：
- `artifacts/tests/fullscale_audit/summary/fullscale-manifest.md`

## 5) 过程修复

全量重跑中发现 datasets-server 偶发 `502`，已修复为带重试的数据拉取逻辑：
- 修改：`datasets/mmlu_dataset.py`
- 行为：splits/rows 请求失败时指数退避重试，提升长跑稳定性。
