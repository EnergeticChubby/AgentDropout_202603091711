# ScrawlD 测试执行计划（qwen3-8b）

## 固定配置
- 模型：`qwen3-8b`
- Base URL：`https://llm.undefined.qzz.io/v1`
- 数据集：`/workspace/grpo_text_classification_labeled.json`
- 标签顺序（与数据集中 `label` 对齐）：
  - `["UE", "TX-Origin", "RENT", "ARTHM", "TimeO", "LE", "TimeM"]`

## 评测流程
1. 读取 JSON 样本，解析 `messages`（输入）与 `label`（字符串化 7 维多标签）。
2. 逐样本调用 OpenAI 兼容接口 `/chat/completions`。
3. 从模型输出中提取 `<answer>...</answer>`（若缺失则回退全文）并解析漏洞类别。
4. 生成预测向量，与真实标签逐位对齐对比。
5. 输出以下结果文件：
   - `predictions.jsonl`：逐样本预测明细
   - `summary.json`：总体与分类别指标
   - `report.md`：可读报告

## 指标
- Exact Match（整条样本标签完全一致）
- Micro Precision / Recall / F1
- Macro F1
- Per-class（support/tp/fp/fn/precision/recall/f1）

## 执行命令
使用环境变量注入密钥，避免写入仓库：

`python3 experiments/eval_scrawld_qwen.py --input /workspace/grpo_text_classification_labeled.json --output_dir /workspace/result/scrawld_qwen3_8b --model qwen3-8b --base_url "$LLM_BASE_URL" --api_key "$LLM_API_KEY" --workers 4 --timeout 180 --retries 3`
