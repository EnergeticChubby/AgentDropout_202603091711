# Phase 0 — Baseline Stabilization & Run Readiness

## 1) 目标与范围

Phase 0 目标是把现有代码库从“可研究原型”整理到“可稳定执行下一阶段研发”的状态，重点完成：

1. 修复导入路径与注册机制问题，保证核心模块可导入、可运行。
2. 建立统一测试模型配置（`qwen3-8b` + 指定 endpoint）。
3. 补齐 smoke 测试、可复现实验脚本、测试记录落盘机制。
4. 运行 `edinburgh-dawg/mmlu-redux` 的 8-shard 并行基线，作为后续 phase 对比基线。

---

## 2) 设计方案与权衡

### 2.1 导入与注册稳定性
- 问题：`AgentPrune.*` 历史导入残留导致导入失败；registry 依赖 side-effect 注册但未统一触发。
- 方案：
  - 全量修复 `AgentPrune` → `AgentDropout` 导入路径；
  - 在 `AgentRegistry` / `PromptSetRegistry` / `LLMRegistry` 增加 `_ensure_defaults_loaded()`；
  - `LLMRegistry` 默认模型改为 `qwen3-8b`（可由环境变量覆盖）。

### 2.2 LLM 接口鲁棒性
- 问题：endpoint 可能返回非标准对象（字符串/HTML），且 base_url 是否含 `/v1` 不确定。
- 方案：
  - `gpt_chat.py` 增加 base_url 归一化（自动补 `/v1`）；
  - 统一 completion 提取逻辑，支持字符串/字典/标准 SDK 对象；
  - 如果返回 HTML，立即判定为 endpoint 配置错误并重试失败。

### 2.3 mmlu-redux 数据加载
- 问题：本地 `datasets` 目录与 HuggingFace `datasets` 包同名冲突，直接 `load_dataset` 不稳定。
- 方案：
  - `mmlu_dataset.py` 改为使用 HuggingFace datasets-server HTTP API 读取 `mmlu-redux`；
  - 增加 `num_shards/shard_idx/max_records` 支持，满足 8-shard 并行和速度要求。

### 2.4 复现性与记录
- 新增 `scripts/repro/run_mmlu_redux_8shard.sh` 与汇总脚本；
- 所有 smoke 与 benchmark 输出写入 `artifacts/tests/phase0/...`。

---

## 3) 代码变更清单（文件级）

### 核心修复
- `AgentDropout/graph/__init__.py`
- `AgentDropout/agents/__init__.py`
- `AgentDropout/agents/agent_registry.py`
- `AgentDropout/prompt/prompt_set_registry.py`
- `AgentDropout/graph/graph.py`
- `AgentDropout/tools/reader/readers.py`
- `AgentDropout/tools/web/youtube.py`

### LLM 与配置
- `AgentDropout/llm/gpt_chat.py`
- `AgentDropout/llm/llm_registry.py`
- `AgentDropout/llm/price.py`
- `AgentDropout/llm/__init__.py`
- `AgentDropout/llm/mock_chat.py` (new)

### 数据与评测
- `datasets/mmlu_dataset.py`
- `datasets/__init__.py` (new)
- `experiments/run_mmlu.py`
- `experiments/evaluate_mmlu.py`
- `experiments/run_gsm8k.py`
- `experiments/run_humaneval.py`
- `experiments/run_aqua.py`
- `experiments/run_multiarith.py`
- `experiments/run_svamp.py`

### 测试与复现
- `tests/conftest.py` (new)
- `tests/smoke/test_imports.py` (new)
- `tests/smoke/test_graph_minimal.py` (new)
- `tests/smoke/test_llm_qwen3_connectivity.py` (new)
- `scripts/repro/run_mmlu_redux_8shard.sh` (new)
- `scripts/repro/summarize_mmlu_redux.py` (new)

### 工程规范
- `.gitignore` (new)
- `requirements.txt`

---

## 4) 测试设计与命令

### 4.1 Smoke
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... python3 -m pytest -q tests/smoke
```

### 4.2 Import 校验
```bash
python3 -c "import AgentDropout.graph.graph as g; print('import-ok')"
```

### 4.3 mmlu-redux 8-shard 基线
```bash
OPENAI_BASE_URL=... OPENAI_API_KEY=... LLM_MODEL_NAME=qwen3-8b LIMIT_QUESTIONS=4 \
bash scripts/repro/run_mmlu_redux_8shard.sh phase0
```

---

## 5) 测试记录与结果分析

### 5.1 记录路径
- manifest: `artifacts/tests/phase0/summary/phase0-test-manifest.md`
- smoke raw: `artifacts/tests/phase0/raw/pytest_smoke.log`
- import raw: `artifacts/tests/phase0/raw/import_check.log`
- benchmark raw: `artifacts/tests/phase0/mmlu_redux/raw/20260309-160227/`
- benchmark summary: `artifacts/tests/phase0/mmlu_redux/summary/20260309-160227.json`

### 5.2 结果
- smoke: **4 passed**
- import check: **import-ok**
- `mmlu-redux` 8-shard mean score: **0.1875**

结论：Phase 0 已得到可复现基线分数，可作为 Phase 1 的性能对照门槛。

---

## 6) 已知问题与风险

1. 当前 benchmark 为速度优先配置（`LIMIT_QUESTIONS=4`），代表性有限；后续 phase 可在同预算或更高预算下保持口径一致地扩容。
2. 旧实验脚本整体仍依赖较多历史逻辑，Phase 1/2/3 增量接入时需持续保持 backward compatibility。

---

## 7) 下一步计划

进入 Phase 1 V0（Delegation Contract Edge）：
1. 增加 contract schema / template / synthesizer / verifier；
2. 在 graph 执行路径插入履约检查；
3. 输出 contract 审计日志与四项核心指标；
4. 完成后执行 8-shard `mmlu-redux` 对比，要求优于 0.1875。

---

## 8) 与上一 phase 的 mmlu-redux 对比与门禁结论

- Phase 0 是起始阶段，无上一 phase。
- 本阶段已建立基线：**0.1875**（8-shard, qwen3-8b）。
- 门禁状态：**可进入 Phase 1**（已完成基线构建、测试记录归档、文档落盘）。
