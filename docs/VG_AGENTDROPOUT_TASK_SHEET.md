# VG-AgentDropout-SVAMP 工程任务单

> 目标：在 **AgentDropout 主链** 上实现状态感知改造，遵循 **SVAMP-only + 8:2 + train/val/test 隔离** 协议。

## 1) 模块接口（工程落地）

### 1.1 数据切分
- 脚本：`dataset/svamp_split.py`
- 输入：
  - `--svamp_train_json`
  - `--svamp_test_json`
  - `--seed`
  - `--output_dir`
- 输出：
  - `svamp_train.jsonl`
  - `svamp_val.jsonl`
  - `svamp_test.jsonl`
  - `split_meta.json`
  - `svamp_*_ids_seed*.json`

### 1.2 Telemetry 采集
- 模块：`telemetry/collector.py`
- 接口：
  - `start_case(case_id)`
  - `record_round(case_id, round_id, node_outputs, active_edges)`
  - `get_latest_features()`
  - `flush()`
- 输出：jsonl 逐 case 落盘（含 rounds 与 latest_features）。

### 1.3 Observer
- 模块：`observer/state_observer.py`
- 接口：
  - `StateObserver(output_path=None, model_path=None)`
  - `update(round_telemetry) -> ObserverOutput`
  - `get_latest_output()`
- 支持：
  - 无模型：heuristic 推断
  - 有模型：加载 `train_state_observer.py` 产物推断

### 1.4 State-aware 打分
- 模块：
  - `dropout_scoring/node_score.py`
  - `dropout_scoring/edge_score.py`
- 接口：
  - `compute_state_aware_node_scores(...)`
  - `compute_state_aware_edge_scores(...)`

### 1.5 主实验脚本
- `experiments/run_svamp.py`
  - 核心参数：
    - `--dataset_json --train_json --split_meta_json`
    - `--state_aware_node --state_aware_edge`
    - `--observer_model_path`
    - `--telemetry_output --observer_output`
    - `--train_sample_size`（40-shot）

## 2) JSON Schema（见 `experiments/schemas/`）

- `split_meta.schema.json`
- `telemetry_record.schema.json`
- `observer_label.schema.json`
- `observer_metrics.schema.json`
- `phase_plan.schema.json`

可选校验脚本：`experiments/validate_protocol_artifacts.py`

## 3) 训练脚本顺序（标准执行）

1. 切分数据：
```bash
python dataset/svamp_split.py --seed 42 --output_dir datasets/SVAMP/split_seed42
```

2. 跑 phase0 基线（可直接用 `run_svamp.py` 或 `phase_controller.py`）  
3. phase1 先采 telemetry，再构标签，再训 observer，再接入 state-aware 推理：
```bash
python experiments/build_observer_labels.py ...
python experiments/train_state_observer.py ...
python experiments/run_svamp.py --observer_model_path ...
```

4. phase 门禁与自动重试：
```bash
python experiments/phase_controller.py --phases_json experiments/phase_plan.example.json
```

5. 协议/消融：
```bash
python experiments/run_svamp_protocol.py ...
python experiments/run_svamp_ablation.py ...
python experiments/summarize_svamp_results.py ...
```

## 4) 伪代码（主链不变）

```text
for phase in phases:
  reread_plan()
  for attempt in [1..max_attempts]:
    run phase commands
    collect benchmark summary
    if current > previous:
      pass phase
      break
  if not pass:
    stop with failure
```

```text
AgentDropout core:
  learn graph (node stage)
  node dropout (state-aware score)
  re-init + relearn graph (edge stage)
  edge dropout (state-aware score)
  DAGSample
  T=2 reasoning
```

## 5) 周排期（建议）

- **Week 1**：协议切分、phase0复现、telemetry落盘
- **Week 2**：标签构建、observer训练、Node-only改造
- **Week 3**：Edge改造、A1~A7消融、40-shot vs full-train
- **Week 4**：多seed补充、报告汇总、错误案例分析
