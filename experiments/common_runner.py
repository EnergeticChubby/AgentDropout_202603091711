import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Union


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
    agent_names: Union[str, Sequence[str]] = "AnalyzeAgent"
    agent_nums: Union[int, Sequence[int]] = 1
    disable_memory_governance: bool = False


def run_mmlu_redux(config: MMLURunConfig, workspace: str = ".") -> Dict:
    agent_names = [config.agent_names] if isinstance(config.agent_names, str) else list(config.agent_names)
    agent_nums = [config.agent_nums] if isinstance(config.agent_nums, int) else list(config.agent_nums)
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
        *agent_names,
        "--agent_nums",
        *[str(num) for num in agent_nums],
        "--run_tag",
        config.run_tag,
    ]
    if config.disable_memory_governance:
        command.append("--disable_memory_governance")
    env = os.environ.copy()
    process = subprocess.run(command, cwd=workspace, env=env, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        raise RuntimeError(
            f"run_mmlu_redux failed for {config.run_tag} with code {process.returncode}\n"
            f"stdout:\n{process.stdout}\n"
            f"stderr:\n{process.stderr}"
        )
    summary_line = process.stdout.strip().splitlines()[-1]
    payload = json.loads(summary_line)
    return payload


def load_run_summary(run_tag: str, workspace: str = ".") -> Dict:
    summary_path = Path(workspace) / "artifacts" / "runs" / f"mmlu_redux-{run_tag}-all" / "summary.json"
    with summary_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)
