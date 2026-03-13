#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: str):
    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt_percent(x: Any) -> str:
    try:
        return f"{float(x) * 100:.2f}%"
    except Exception:
        return "N/A"


def section_phase_history(history: Any) -> str:
    if not isinstance(history, list):
        return "## Phase History\n\nNo phase history found.\n"
    lines = ["## Phase History", ""]
    for item in history:
        phase = item.get("phase", {})
        name = phase.get("name", "unknown")
        passed = item.get("passed", False)
        attempts = item.get("attempts", [])
        lines.append(f"- **{name}**: {'PASSED' if passed else 'FAILED'} (attempts={len(attempts)})")
        if attempts:
            last = attempts[-1]
            comp = last.get("comparison", {})
            if comp:
                lines.append(
                    f"  - current={fmt_percent(comp.get('current_accuracy'))}, "
                    f"previous={fmt_percent(comp.get('previous_accuracy'))}, "
                    f"rule={comp.get('rule')}"
                )
    lines.append("")
    return "\n".join(lines)


def section_protocol(protocol: Any) -> str:
    if not isinstance(protocol, dict):
        return "## Protocol (40-shot vs full-train)\n\nNo protocol summary found.\n"
    p40 = protocol.get("phase_40shot", {})
    pfull = protocol.get("phase_full_train", {})
    lines = [
        "## Protocol (40-shot vs full-train)",
        "",
        f"- 40-shot accuracy: {fmt_percent(p40.get('accuracy'))}",
        f"- full-train accuracy: {fmt_percent(pfull.get('accuracy'))}",
        "",
    ]
    return "\n".join(lines)


def section_ablation(ablation: Any) -> str:
    if not isinstance(ablation, list) or not ablation:
        return "## Ablation\n\nNo ablation summary found.\n"
    lines = ["## Ablation", "", "| Ablation | Accuracy |", "|---|---|"]
    for row in ablation:
        lines.append(f"| {row.get('ablation','-')} | {fmt_percent(row.get('accuracy'))} |")
    lines.append("")
    return "\n".join(lines)


def section_seed_sweep(seed_sweep: Any) -> str:
    if not isinstance(seed_sweep, dict):
        return "## Seed Sweep\n\nNo seed sweep summary found.\n"
    agg = seed_sweep.get("aggregate")
    if not isinstance(agg, dict):
        return "## Seed Sweep\n\nNo aggregate metrics found.\n"
    lines = [
        "## Seed Sweep",
        "",
        f"- seeds: {agg.get('seeds', [])}",
        f"- 40-shot mean/std: {fmt_percent(agg.get('phase_40shot_mean'))} / {fmt_percent(agg.get('phase_40shot_std'))}",
        f"- full-train mean/std: {fmt_percent(agg.get('phase_full_train_mean'))} / {fmt_percent(agg.get('phase_full_train_std'))}",
        "",
    ]
    return "\n".join(lines)


def section_overall_summary(overall: Any) -> str:
    if not isinstance(overall, dict):
        return "## Overall SVAMP Summary\n\nNo overall summary found.\n"
    lines = [
        "## Overall SVAMP Summary",
        "",
        f"- files: {overall.get('num_files', 0)}",
        f"- mean accuracy: {fmt_percent(overall.get('mean_accuracy'))}",
        f"- best accuracy: {fmt_percent(overall.get('best_accuracy'))}",
        f"- worst accuracy: {fmt_percent(overall.get('worst_accuracy'))}",
        "",
    ]
    return "\n".join(lines)


def section_final_compare(final_compare: Any) -> str:
    if not isinstance(final_compare, dict):
        return "## Final Outer-Test Comparison\n\nNo final comparison found.\n"
    lines = [
        "## Final Outer-Test Comparison",
        "",
        f"- baseline accuracy: {fmt_percent(final_compare.get('baseline_accuracy'))}",
        f"- VG accuracy: {fmt_percent(final_compare.get('vg_accuracy'))}",
        f"- absolute gain: {fmt_percent(final_compare.get('absolute_gain'))}",
        f"- relative gain: {final_compare.get('relative_gain_pct', 'N/A')}%",
        "",
    ]
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate markdown report from VG-SVAMP artifacts.")
    parser.add_argument("--phase_history_json", type=str, default="result/gz10-v3/phase_history.json")
    parser.add_argument("--protocol_summary_json", type=str, default="result/gz10-v3/svamp_protocol_summary.json")
    parser.add_argument("--ablation_summary_json", type=str, default="result/gz10-v3/svamp_ablation_summary.json")
    parser.add_argument("--seed_sweep_summary_json", type=str, default="result/gz10-v3/svamp_seed_sweep_summary.json")
    parser.add_argument("--overall_summary_json", type=str, default="result/gz10-v3/svamp_summary.json")
    parser.add_argument("--final_compare_json", type=str, default="")
    parser.add_argument("--output_md", type=str, default="result/gz10-v3/vg_svamp_report.md")
    return parser.parse_args()


def main():
    args = parse_args()
    phase_history = load_json(args.phase_history_json)
    protocol = load_json(args.protocol_summary_json)
    ablation = load_json(args.ablation_summary_json)
    seed_sweep = load_json(args.seed_sweep_summary_json)
    overall_summary = load_json(args.overall_summary_json)
    final_compare = load_json(args.final_compare_json) if args.final_compare_json else None

    parts: List[str] = [
        "# VG-AgentDropout-SVAMP Report",
        "",
        section_phase_history(phase_history),
        section_protocol(protocol),
        section_ablation(ablation),
        section_seed_sweep(seed_sweep),
        section_overall_summary(overall_summary),
        section_final_compare(final_compare),
    ]
    text = "\n".join(parts).strip() + "\n"
    output = Path(args.output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(str(output))


if __name__ == "__main__":
    main()
