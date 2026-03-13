import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict JSON at {path}")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build consolidated phase1/phase3/phase4 overview report "
            "from existing phase summaries and pairwise comparisons."
        )
    )
    parser.add_argument("--branch_tag", type=str, default="AdamMartinez6793-v3")
    parser.add_argument("--archive_root", type=str, default="result/benchmarks")
    parser.add_argument(
        "--output_json",
        type=str,
        default=(
            "result/benchmarks/AdamMartinez6793-v3/comparisons/"
            "phase1_phase3_phase4_overview.json"
        ),
    )
    parser.add_argument(
        "--output_md",
        type=str,
        default=(
            "result/benchmarks/AdamMartinez6793-v3/comparisons/"
            "phase1_phase3_phase4_overview.md"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = Path(args.archive_root) / args.branch_tag
    comp = base / "comparisons"

    phase1 = _load_json(base / "phase1" / "svamp_metrics_summary.json")
    phase3 = _load_json(base / "phase3" / "svamp_metrics_summary.json")
    phase4 = _load_json(base / "phase4" / "svamp_metrics_summary.json")
    phase2 = _load_json(base / "phase2" / "skipped.json")
    p13 = _load_json(comp / "phase1_vs_phase3.json")
    p14 = _load_json(comp / "phase1_vs_phase4.json")

    overview: Dict[str, Any] = {
        "branch_tag": args.branch_tag,
        "protocol": "fixed test.json (n=200), strict split seed42, num_rounds=2",
        "phase2": phase2,
        "reproduced_phases": {
            "phase1": {
                "final_accuracy": phase1.get("final_accuracy"),
                "total_tokens_avg": phase1.get("total_tokens_avg"),
                "prompt_tokens_avg": phase1.get("prompt_tokens_avg"),
                "completion_tokens_avg": phase1.get("completion_tokens_avg"),
            },
            "phase3": {
                "final_accuracy": phase3.get("final_accuracy"),
                "total_tokens_avg": phase3.get("total_tokens_avg"),
                "prompt_tokens_avg": phase3.get("prompt_tokens_avg"),
                "completion_tokens_avg": phase3.get("completion_tokens_avg"),
            },
            "phase4": {
                "final_accuracy": phase4.get("final_accuracy"),
                "total_tokens_avg": phase4.get("total_tokens_avg"),
                "prompt_tokens_avg": phase4.get("prompt_tokens_avg"),
                "completion_tokens_avg": phase4.get("completion_tokens_avg"),
            },
        },
        "comparisons_against_phase1": {
            "phase1_vs_phase3": {
                "summary_delta": p13.get("summary_delta", {}),
                "transitions": p13.get("transitions", {}),
                "regression_count": p13.get("transitions", {}).get("correct_to_wrong", 0),
                "improvement_count": p13.get("transitions", {}).get("wrong_to_correct", 0),
            },
            "phase1_vs_phase4": {
                "summary_delta": p14.get("summary_delta", {}),
                "transitions": p14.get("transitions", {}),
                "regression_count": p14.get("transitions", {}).get("correct_to_wrong", 0),
                "improvement_count": p14.get("transitions", {}).get("wrong_to_correct", 0),
            },
        },
    }

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(overview, f, ensure_ascii=False, indent=2)

    lines = [
        "# Phase Reproduction Overview",
        "",
        f"- Branch tag: {args.branch_tag}",
        "- Protocol: fixed `test.json` (n=200), seed42, strict mode, num_rounds=2",
        "- Phase2: skipped by user decision",
        "",
        "## Accuracy / Tokens",
        "",
        f"- Phase1: acc={phase1.get('final_accuracy')}, tokens_avg={phase1.get('total_tokens_avg')}",
        f"- Phase3: acc={phase3.get('final_accuracy')}, tokens_avg={phase3.get('total_tokens_avg')}",
        f"- Phase4: acc={phase4.get('final_accuracy')}, tokens_avg={phase4.get('total_tokens_avg')}",
        "",
        "## Pairwise vs Phase1",
        "",
        f"- Phase1→Phase3 transitions: {p13.get('transitions', {})}",
        f"- Phase1→Phase4 transitions: {p14.get('transitions', {})}",
    ]
    output_md = Path(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[PhaseOverview] wrote {output_json} and {output_md}")


if __name__ == "__main__":
    main()
