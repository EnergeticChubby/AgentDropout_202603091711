#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_MODEL = "glm-4.5-flash"
EXPECTED_BASE_URL = "https://llm.undefined.qzz.io/v1/chat/completions"
EXPECTED_API_KEY = "sk-pc8yOBXhAVOXEa38hpH1XBtuPwadnB1rLpNxHMS6grCuMrZh"


def check_contains(path: Path, required_fragments: List[str]) -> Tuple[bool, List[str]]:
    if not path.exists():
        return False, [f"missing file: {path}"]

    text = path.read_text(encoding="utf-8")
    missing = [frag for frag in required_fragments if frag not in text]
    return len(missing) == 0, missing


def main() -> int:
    failures: List[str] = []

    run_files = [
        ROOT / "experiments/run_gsm8k.py",
        ROOT / "experiments/run_aqua.py",
        ROOT / "experiments/run_svamp.py",
        ROOT / "experiments/run_multiarith.py",
        ROOT / "experiments/run_humaneval.py",
        ROOT / "experiments/run_mmlu.py",
    ]

    for run_file in run_files:
        ok, missing = check_contains(
            run_file,
            [f'default="{EXPECTED_MODEL}"'],
        )
        if not ok:
            failures.append(f"{run_file}: missing fragments -> {missing}")

    run_mmlu = ROOT / "experiments/run_mmlu.py"
    ok, missing = check_contains(
        run_mmlu,
        [
            "parser.add_argument('--limit_questions', type=int, default=None,",
            "parser.add_argument('--max_retries_per_question', type=int, default=6,",
            "parser.add_argument('--rerun_failed_rounds', type=int, default=3,",
        ],
    )
    if not ok:
        failures.append(f"{run_mmlu}: missing full-val/retry config fragments -> {missing}")

    template_env = ROOT / "template.env"
    ok, missing = check_contains(
        template_env,
        [
            f'TEST_MODEL="{EXPECTED_MODEL}"',
            f'BASE_URL="{EXPECTED_BASE_URL}"',
            f'API_KEY="{EXPECTED_API_KEY}"',
        ],
    )
    if not ok:
        failures.append(f"{template_env}: missing fragments -> {missing}")

    gpt_chat = ROOT / "AgentDropout/llm/gpt_chat.py"
    ok, missing = check_contains(
        gpt_chat,
        [
            f'RAW_BASE_URL = os.getenv("BASE_URL", "{EXPECTED_BASE_URL}")',
            'MINE_BASE_URL = RAW_BASE_URL.rsplit("/chat/completions", 1)[0] if RAW_BASE_URL.endswith("/chat/completions") else RAW_BASE_URL',
            f'MINE_API_KEYS = os.getenv("API_KEY", "{EXPECTED_API_KEY}")',
        ],
    )
    if not ok:
        failures.append(f"{gpt_chat}: missing fragments -> {missing}")

    eval_mmlu = ROOT / "experiments/evaluate_mmlu.py"
    ok, missing = check_contains(
        eval_mmlu,
        [
            "max_retries_per_question: int = 6,",
            "rerun_failed_rounds: int = 3,",
            "raise RuntimeError(",
            "MMLU full-val evaluation incomplete:",
        ],
    )
    if not ok:
        failures.append(f"{eval_mmlu}: missing retry/full-val enforcement fragments -> {missing}")

    phase0_test = ROOT / "tests/repro/test_phase0_agentdropout_local.py"
    ok, missing = check_contains(
        phase0_test,
        [
            "_ensure_local_mmlu_sample()",
            "phase0 agentdropout local test passed",
        ],
    )
    if not ok:
        failures.append(f"{phase0_test}: missing Phase0 local test fragments -> {missing}")

    mmlu_download = ROOT / "datasets/MMLU/download.py"
    ok, missing = check_contains(
        mmlu_download,
        [
            "def download() -> None:",
            "datasets/MMLU/data/dev",
            "datasets/MMLU/data/val",
        ],
    )
    if not ok:
        failures.append(f"{mmlu_download}: missing MMLU download shim fragments -> {missing}")

    if failures:
        print("REPRO CHECK FAILED")
        for item in failures:
            print(f"- {item}")
        return 1

    print("REPRO CHECK PASSED")
    print(f"- model: {EXPECTED_MODEL}")
    print(f"- base_url: {EXPECTED_BASE_URL}")
    print("- api_key: [present]")
    print(f"- checked files: {len(run_files) + 2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
