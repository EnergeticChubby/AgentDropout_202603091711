import json
import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


@dataclass
class MMLURunConfig:
    run_tag: str
    llm_name: str = "qwen3-8b"
    split: str = "test"
    num_shards: int = 8
    max_samples: int = 1
    num_rounds: int = 1
    mode: str = "DirectAnswer"
    decision_method: str = "FinalDirect"
    agent_names: str = "AnalyzeAgent"
    agent_nums: int = 1


def run_mmlu_redux(config: MMLURunConfig, workspace: str = ".") -> Dict:
    command = [
        "python3",
        "experiments/run_mmlu_redux.py",
        "--llm_name",
        config.llm_name,
        "--split",
        config.split,
        "--num_shards",
        str(config.num_shards),
        "--max_samples",
        str(config.max_samples),
        "--num_rounds",
        str(config.num_rounds),
        "--mode",
        config.mode,
        "--decision_method",
        config.decision_method,
        "--agent_names",
        config.agent_names,
        "--agent_nums",
        str(config.agent_nums),
        "--run_tag",
        config.run_tag,
    ]
    env = os.environ.copy()
    process = subprocess.run(command, cwd=workspace, env=env, capture_output=True, text=True, check=True)
    summary_line = process.stdout.strip().splitlines()[-1]
    payload = json.loads(summary_line)
    return payload


def load_run_summary(run_tag: str, workspace: str = ".") -> Dict:
    summary_path = Path(workspace) / "artifacts" / "runs" / f"mmlu_redux-{run_tag}-all" / "summary.json"
    with summary_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)
