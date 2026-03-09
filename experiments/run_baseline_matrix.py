import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from experiments.common_runner import MMLURunConfig, load_run_summary, run_mmlu_redux


def parse_args():
    parser = argparse.ArgumentParser(description="Run baseline matrix on MMLU-Redux.")
    parser.add_argument("--output_json", type=str, required=True)
    parser.add_argument("--max_samples", type=int, default=1)
    return parser.parse_args()


def main():
    args = parse_args()
    baseline_specs = [
        {
            "baseline": "topology_only",
            "proxy_of": "Topology only（AgentDropout/AgentPrune style）",
            "config": MMLURunConfig(
                run_tag="phaseE-matrix-topology-only",
                max_samples=args.max_samples,
                num_shards=1,
                mode="FullConnected",
                decision_method="FinalMajorVote",
                agent_names=["AnalyzeAgent"],
                agent_nums=[5],
            ),
        },
        {
            "baseline": "dala_like_proxy",
            "proxy_of": "DALA-like 发言侧策略（以 Star 拓扑中心发言作为近似代理）",
            "config": MMLURunConfig(
                run_tag="phaseE-matrix-dala-like-proxy",
                max_samples=args.max_samples,
                num_shards=1,
                mode="Star",
                decision_method="FinalMajorVote",
                agent_names=["AnalyzeAgent"],
                agent_nums=[5],
            ),
        },
        {
            "baseline": "summary_only",
            "proxy_of": "Summary-only 极简基线",
            "config": MMLURunConfig(
                run_tag="phaseE-matrix-summary-only",
                max_samples=args.max_samples,
                num_shards=1,
                mode="DirectAnswer",
                decision_method="FinalDirect",
                agent_names=["AnalyzeAgent"],
                agent_nums=[1],
            ),
        },
        {
            "baseline": "plain_shared_memory",
            "proxy_of": "Plain shared memory（禁用 Commons governance）",
            "config": MMLURunConfig(
                run_tag="phaseE-matrix-plain-memory",
                max_samples=args.max_samples,
                num_shards=1,
                mode="FullConnected",
                decision_method="FinalMajorVote",
                agent_names=["AnalyzeAgent"],
                agent_nums=[5],
                disable_memory_governance=True,
            ),
        },
        {
            "baseline": "rollback_only_proxy",
            "proxy_of": "rollback-only（以 two-round debate 近似）",
            "config": MMLURunConfig(
                run_tag="phaseE-matrix-rollback-proxy",
                max_samples=args.max_samples,
                num_shards=1,
                mode="Debate",
                decision_method="FinalMajorVote",
                agent_names=["AnalyzeAgent"],
                agent_nums=[5],
                num_rounds=2,
            ),
        },
        {
            "baseline": "naive_diversity_random_ensemble",
            "proxy_of": "naive diversity / random ensemble",
            "config": MMLURunConfig(
                run_tag="phaseE-matrix-random-ensemble",
                max_samples=args.max_samples,
                num_shards=1,
                mode="Random",
                decision_method="FinalMajorVote",
                agent_names=["AnalyzeAgent"],
                agent_nums=[5],
            ),
        },
        {
            "baseline": "single_strong_model",
            "proxy_of": "single strong model",
            "config": MMLURunConfig(
                run_tag="phaseE-matrix-single-strong",
                max_samples=args.max_samples,
                num_shards=1,
                mode="DirectAnswer",
                decision_method="FinalDirect",
                agent_names=["AnalyzeAgent"],
                agent_nums=[1],
            ),
        },
    ]
    matrix = []
    for spec in baseline_specs:
        config = spec["config"]
        run_mmlu_redux(config, workspace=".")
        summary = load_run_summary(config.run_tag, workspace=".")
        matrix.append(
            {
                "baseline": spec["baseline"],
                "proxy_of": spec["proxy_of"],
                "run_tag": config.run_tag,
                "config": {
                    "mode": config.mode,
                    "decision_method": config.decision_method,
                    "agent_names": config.agent_names,
                    "agent_nums": config.agent_nums,
                    "max_samples": config.max_samples,
                    "num_rounds": config.num_rounds,
                    "disable_memory_governance": config.disable_memory_governance,
                },
                "accuracy": summary.get("accuracy"),
                "num_samples": summary.get("num_samples"),
                "cost": summary.get("cost"),
                "latency": summary.get("elapsed_seconds_max_shard"),
            }
        )
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump({"matrix": matrix}, fp, ensure_ascii=False, indent=2)
    print(json.dumps({"matrix": matrix}, ensure_ascii=False))


if __name__ == "__main__":
    main()
