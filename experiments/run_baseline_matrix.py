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
    configs: List[MMLURunConfig] = [
        MMLURunConfig(run_tag="phaseE-topology-only", max_samples=args.max_samples, mode="DirectAnswer", decision_method="FinalDirect"),
        MMLURunConfig(run_tag="phaseE-summary-only", max_samples=args.max_samples, mode="DirectAnswer", decision_method="FinalDirect"),
        MMLURunConfig(run_tag="phaseE-single-strong", max_samples=args.max_samples, mode="DirectAnswer", decision_method="FinalDirect"),
    ]
    matrix = []
    for config in configs:
        run_mmlu_redux(config, workspace=".")
        summary = load_run_summary(config.run_tag, workspace=".")
        matrix.append(
            {
                "run_tag": config.run_tag,
                "config": {
                    "mode": config.mode,
                    "decision_method": config.decision_method,
                    "agent_names": config.agent_names,
                    "agent_nums": config.agent_nums,
                    "max_samples": config.max_samples,
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
