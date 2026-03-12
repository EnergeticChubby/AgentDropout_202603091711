# AgentDropout

This repository releases the codes and data for the paper -- AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-Performance LLM-Based Multi-Agent Collaboration.

<div align="center">
    <img src="image/README/logo.png" width=200></img>
    <p class="image-caption">AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-Performance LLM-Based Multi-Agent Collaboration</p>
</div>

## **📣 News**
- **[16/05/2025]**  🎉🎉Our paper is accepted by [ACL 2025]!🎉🎉
- **[25/03/2025]** Our paper has been submitted to arXiv: [https://arxiv.org/abs/2503.18891](https://arxiv.org/abs/2503.18891)!

## **🔗 Quick Links**

- **[About AgentDropout](#about)**
- **[File Structure](#structure)**
- **[Requirements](#requirements)**
- **[Quick Start](#start)**
- **[Citation](#citation)**

## **🧠 About AgentDropout**<a name="about"></a>

<!-- **AgentDropout** is a novel topology optimization method for Multi-agent system with domain transferability and structure robustness. AgentDropout dynamically adjusts the participating agents and communication links among agents in each round, allowing for more flexible and adaptive team configurations.  -->
**AgentDropout** is a novel topology optimization method for Multi-agent systems (MAS), inspired by the management theory that more flexible and adaptive team configurations can make teamwork more efficient and effective. AgentDropout dynamically identify and drop out the redundant agents and communication links in each interaction round of the MAS, allowing for higher token efficiency and task performance.
It conducts two types of dropout:
<!-- It abstracts the structures of MAS into communication graphs, with agents as nodes and the interactions between them as edges, and conduct two types of dropout: -->
- **Node Dropout**: Remove agent nodes with the smallest trainable weighted degree to involve different responsible roles in different disscussion steps.
- **Edge Dropout**: Remove interaction edges with the smallest task contribution to improve communication efficiency.

<!-- <img src="image/README/main.png" alt="main" style="zoom: 33%;" /> -->
<div align="center">
    <img src="image/README/main.png"></img>
    <p class="image-caption">The Framework of AgentDropout</p>
</div>



## **📂 File Structure**<a name="structure"></a>

| Directory       | Contents              |
| --------------- | --------------------- |
| [`datasets/`](https://github.com/wangzx1219/AgentDropout/tree/main/datasets)     | Experimental data     |
| [`AgentDropout/`](https://github.com/wangzx1219/AgentDropout/tree/main/AgentDropout) | Main codes            |
| [`experiments/`](https://github.com/wangzx1219/AgentDropout/tree/main/experiments)  | Test scripts          |
| [`result/`](https://github.com/wangzx1219/AgentDropout/tree/main/result)       | Few samples of output |

## **⚙️ Requirements**<a name="requirements"></a>

1. **Environment Setup**:

```shell
conda create -n myenv python=3.10
conda activate myenv
pip install -r requirements.txt
```

2. **API Configuration**:

Set environment variables (recommended) before running experiments:

```bash
export AGENTDROPOUT_BASE_URL="https://gpt-agent.cc/v1"
export AGENTDROPOUT_API_KEY="<YOUR_API_KEY>"
export DEFAULT_LLM_NAME="MiniMax-M2.5"
```

Supported fallback names:
- `MINIMAX_BASE_URL` / `MINIMAX_API_KEY`
- `BASE_URL` / `API_KEY`

3. **Local Model Deployment** (Optional):

```bash
# Using vLLM for local inference
CUDA_VISIBLE_DEVICES=0 vllm serve /path/to/model --dtype auto --api-key API_KEYS --port 6789
```

```python
api_key = API_KEYS
base_url = "http://localhost:6789/v1"
```

Prepare data from [Huggingface](https://huggingface.co/). And put them in `datasets/`.

## **🚀 Quick Start**<a name="start"></a>

Run AgentDropout on SVAMP (VG-AgentDropout-SVAMP phase0 baseline):

```shell
python experiments/run_svamp.py \
  --agent_nums 5 \
  --mode FullConnected \
  --batch_size 40 \
  --num_iterations 2 \
  --imp_per_iterations 1 \
  --pruning_rate 0.10 \
  --num_rounds 2 \
  --llm_name MiniMax-M2.5 \
  --optimized_spatial \
  --optimized_temporal \
  --diff \
  --dec

# quick-cost debug run
python experiments/run_svamp.py \
  --agent_nums 5 \
  --mode FullConnected \
  --batch_size 20 \
  --num_iterations 1 \
  --imp_per_iterations 1 \
  --pruning_rate 0.10 \
  --num_rounds 2 \
  --llm_name MiniMax-M2.5 \
  --train_sample_size 40 \
  --eval_sample_size 20 \
  --optimized_spatial \
  --optimized_temporal \
  --diff \
  --dec
```

Create a fixed SVAMP 8:2 split (with inner train/val) before phased experiments:

```bash
python dataset/prepare_svamp.py \
  --output_dir datasets/SVAMP \
  --seed 42

# optional: prepare GSM8K files for phase health checks
python dataset/prepare_gsm8k.py \
  --output_dir datasets/gsm8k
```

Then generate the protocol split artifacts:

```bash
python dataset/svamp_split.py \
  --svamp_train_json datasets/SVAMP/train.json \
  --svamp_test_json datasets/SVAMP/test.json \
  --seed 42 \
  --output_dir datasets/SVAMP/split_seed42
```

Run multi-phase execution with automatic retry-until-improved gate:

```bash
python experiments/phase_controller.py \
  --phases_json experiments/phase_plan.example.json \
  --output_json result/gz10-v3/phase_history.json

# lighter real-run preset (smaller samples, still gated)
python experiments/phase_controller.py \
  --phases_json experiments/phase_plan.quick.json \
  --output_json result/gz10-v3/phase_history.quick.json
# note: quick plan uses a lightweight baseline to exercise improvement gating rapidly

# quick plan with GSM8K health benchmarks enabled
python experiments/phase_controller.py \
  --phases_json experiments/phase_plan.quick_health.json \
  --output_json result/gz10-v3/phase_history.quick_health.json
# optional per-phase health gate fields in phase json:
# - "health_benchmark_type": "gsm8k" | "svamp"
# - "health_result_glob": "<glob>"
# - "health_allow_equal": false
# comparisons are tracked per benchmark type (svamp/gsm8k)

# optional GSM8K health benchmark command (for phase run_cmds)
python experiments/run_gsm8k_healthcheck.py \
  --dataset_json datasets/gsm8k/test.jsonl \
  --train_json datasets/gsm8k/train.jsonl \
  --result_dir result/gz10-v3/GSM8K \
  --phase_name phase0-health \
  --llm_name MiniMax-M2.5 \
  --mode FullConnected \
  --agent_nums 5 \
  --num_rounds 2 \
  --eval_sample_size 20 \
  --train_sample_size 40 \
  --optimized_spatial \
  --optimized_temporal \
  --diff \
  --dec
```

Run the SVAMP protocol bundle for **40-shot vs full-train**:

```bash
python experiments/run_svamp_protocol.py \
  --split_dir datasets/SVAMP/split_seed42 \
  --phase_prefix protocol \
  --llm_name MiniMax-M2.5 \
  --summary_out result/gz10-v3/svamp_protocol_summary.json
```

Run SVAMP ablations (A1~A7; `--run_mode quick` only runs A1~A4):

```bash
python experiments/run_svamp_ablation.py \
  --split_dir datasets/SVAMP/split_seed42 \
  --llm_name MiniMax-M2.5 \
  --summary_out result/gz10-v3/svamp_ablation_summary.json \
  --run_mode quick
```

Run multi-seed protocol sweep (42, 3407, 2025) and aggregate mean/std:

```bash
python experiments/run_svamp_seed_sweep.py \
  --seeds "42,3407,2025" \
  --llm_name MiniMax-M2.5 \
  --summary_out result/gz10-v3/svamp_seed_sweep_summary.json
```

Summarize all generated SVAMP result files:

```bash
python experiments/summarize_svamp_results.py \
  --glob_pattern "result/gz10-v3/SVAMP/svamp_*.json" \
  --output_json result/gz10-v3/svamp_summary.json
```

Schema files and task sheet:
- `docs/VG_AGENTDROPOUT_TASK_SHEET.md`
- `experiments/schemas/*.schema.json`

Validate an artifact against schema:

```bash
python experiments/validate_protocol_artifacts.py \
  --instance_json datasets/SVAMP/split_seed42/split_meta.json \
  --schema_json experiments/schemas/split_meta.schema.json
```

Additional schemas:
- `experiments/schemas/run_manifest.schema.json`
- `experiments/schemas/protocol_summary.schema.json`
- `experiments/schemas/ablation_summary.schema.json`

Check local experiment readiness (SVAMP files + API envs):

```bash
python experiments/check_env_readiness.py

# data-only smoke check with custom paths
python experiments/check_env_readiness.py \
  --svamp_train_json .tmp_svamp/SVAMP/train.json \
  --svamp_test_json .tmp_svamp/SVAMP/test.json \
  --skip_api_check

# include GSM8K readiness for phase health benchmarks
python experiments/check_env_readiness.py \
  --require_gsm8k \
  --gsm8k_train_json datasets/gsm8k/train.jsonl \
  --gsm8k_test_json datasets/gsm8k/test.jsonl
```

Run full VG-AgentDropout-SVAMP pipeline (readiness → phase gate → protocol → ablation → summary):

```bash
python experiments/run_vg_svamp_pipeline.py \
  --llm_name MiniMax-M2.5 \
  --run_mode_ablation quick \
  --validate_outputs

# custom readiness paths + lightweight protocol/ablation pass-through
python experiments/run_vg_svamp_pipeline.py \
  --llm_name MiniMax-M2.5 \
  --split_dir datasets/SVAMP/split_seed42 \
  --svamp_train_json datasets/SVAMP/train.json \
  --svamp_test_json datasets/SVAMP/test.json \
  --require_gsm8k \
  --gsm8k_train_json datasets/gsm8k/train.jsonl \
  --gsm8k_test_json datasets/gsm8k/test.jsonl \
  --protocol_extra_args "--eval_sample_size 20" \
  --ablation_extra_args "--eval_sample_size 20 --train_sample_size 40" \
  --run_seed_sweep \
  --seed_sweep_seeds "42,3407,2025" \
  --seed_sweep_extra_args "--eval_sample_size 20" \
  --run_mode_ablation quick \
  --validate_outputs
```

Use `--dry_run` to print all commands without executing.

Run tooling smoke suite:

```bash
python experiments/run_smoke_suite.py --dry_run
```

Generate markdown report from produced artifacts:

```bash
python experiments/generate_vg_svamp_report.py \
  --output_md result/gz10-v3/vg_svamp_report.md
```

Build observer labels from telemetry and train an observer model:

```bash
python experiments/build_observer_labels.py \
  --telemetry_jsonl result/gz10-v3/phase1/telemetry_1.jsonl \
  --output_jsonl result/gz10-v3/phase1/observer_labels_1.jsonl

python experiments/train_state_observer.py \
  --dataset_jsonl result/gz10-v3/phase1/observer_labels_1.jsonl \
  --model_out result/gz10-v3/phase1/observer_model_1.pt \
  --metrics_out result/gz10-v3/phase1/observer_metrics_1.json \
  --epochs 20 \
  --val_ratio 0.1 \
  --seed 42
```

Use trained observer in SVAMP run:

```bash
python experiments/run_svamp.py \
  --dataset_json datasets/SVAMP/split_seed42/svamp_val.json \
  --train_json datasets/SVAMP/split_seed42/svamp_train.json \
  --split_meta_json datasets/SVAMP/split_seed42/split_meta.json \
  --phase_name phase1 \
  --llm_name MiniMax-M2.5 \
  --state_aware_node \
  --state_aware_edge \
  --observer_model_path result/gz10-v3/phase1/observer_model_1.pt
```

Each run writes:
- result json: `result/gz10-v3/SVAMP/svamp_<phase>_<timestamp>.json`
- run manifest: `result/gz10-v3/SVAMP/svamp_<phase>_<timestamp>.meta.json`

## **📜 Citation**<a name="citation"></a>

If you find this work useful, please cite:

```tex
@misc{wang2025agentdropoutdynamicagentelimination,
      title={AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-Performance LLM-Based Multi-Agent Collaboration}, 
      author={Zhexuan Wang and Yutong Wang and Xuebo Liu and Liang Ding and Miao Zhang and Jie Liu and Min Zhang},
      year={2025},
      eprint={2503.18891},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2503.18891}, 
}
```

```tex
@inproceedings{wang-etal-2025-agentdropout,
    title = {AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-Performance LLM-Based Multi-Agent Collaboration},
    author = {Wang, Zhexuan  and
      Wang, Yutong  and
      Liu, Xuebo  and
      Ding, Liang  and
      Zhang, Miao  and
      Liu, Jie  and
      Zhang, Min},
    editor = {Che, Wanxiang  and
      Nabende, Joyce  and
      Shutova, Ekaterina  and
      Pilehvar, Mohammad Taher},
    booktitle = {Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
    month = jul,
    year = {2025},
    address = {Vienna, Austria},
    publisher = {Association for Computational Linguistics},
    url = {https://aclanthology.org/2025.acl-long.1170/},
    doi = {10.18653/v1/2025.acl-long.1170},
    pages = {24013--24035},
    ISBN = {979-8-89176-251-0}
}
```

## **💡 Acknowledgments**<a name="acknowledgments"></a>

Code framework based on [GPTSwarm](https://github.com/metauto-ai/GPTSwarm) and [AgentPrune](https://github.com/yanweiyue/AgentPrune).
