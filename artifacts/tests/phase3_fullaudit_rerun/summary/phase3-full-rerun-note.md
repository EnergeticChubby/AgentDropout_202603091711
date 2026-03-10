# Phase3 edinburgh-dawg/mmlu-redux 全量复测（补跑版）

- 时间戳: `20260310-161318`
- 模型: `qwen3-8b`
- 数据集: `edinburgh-dawg/mmlu-redux`（test split）
- 分片: `8`
- 运行策略:
  - 第一轮并行 `batch_size=8`
  - 命中限流后按 shard 顺序自动补跑 `batch_size=4`
  - 直到所有 shard 完成

## 完成性

- `completed_all_shards = true`
- `total_attempts = 15`
- `rate_limited_attempts = 7`
- 总题量（覆盖校验）: `3000/3000`

## 结果

- mean_score: `0.6843333333333333`
- weighted_accuracy: `0.6843333333333333`

## 关键文件

- 汇总 JSON: `20260310-161318.json`
- 汇总 Markdown: `20260310-161318.md`
- 补跑报告 JSON: `20260310-161318.rerun_report.json`
- 补跑报告 Markdown: `20260310-161318.rerun_report.md`
- 覆盖校验: `20260310-161318.coverage.json`
