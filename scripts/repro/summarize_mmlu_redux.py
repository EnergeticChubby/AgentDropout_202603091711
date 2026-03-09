import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any


def parse_score(log_text: str) -> float:
    matches = re.findall(r"Score:\s*([0-9]*\.?[0-9]+)", log_text)
    if not matches:
        raise ValueError("No Score found in shard log.")
    return float(matches[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_dir", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--summary_md", required=True)
    parser.add_argument("--boundary_dir", default="")
    parser.add_argument("--boundary_bonus_weight", type=float, default=0.05)
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    shard_logs = sorted(raw_dir.glob("shard_*.log"))
    if not shard_logs:
        raise FileNotFoundError(f"No shard logs found in {raw_dir}")

    shard_scores: List[Dict[str, Any]] = []
    for path in shard_logs:
        text = path.read_text(encoding="utf-8", errors="ignore")
        score = parse_score(text)
        shard_scores.append({"shard": path.stem, "score": score, "log_path": str(path)})

    mean_score = sum(item["score"] for item in shard_scores) / len(shard_scores)
    boundary_efficiency = 0.0
    boundary_bonus = 0.0
    boundary_metrics_files: List[str] = []
    if args.boundary_dir:
        boundary_dir = Path(args.boundary_dir)
        metric_paths = sorted(boundary_dir.glob("*.metrics.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if metric_paths:
            # Use most recent shard-count-aligned metrics to avoid stale accumulation.
            selected = metric_paths[: len(shard_scores)]
            efficiencies = []
            for path in selected:
                payload = json.loads(path.read_text(encoding="utf-8"))
                handoff = float(payload.get("handoff_count", 0.0))
                frag = float(payload.get("context_fragmentation_score", 0.0))
                efficiencies.append(1.0 / (1.0 + handoff + 10.0 * frag))
            if efficiencies:
                boundary_efficiency = sum(efficiencies) / len(efficiencies)
                boundary_bonus = args.boundary_bonus_weight * boundary_efficiency
                boundary_metrics_files = [str(p) for p in selected]
    performance_score = mean_score + boundary_bonus

    summary = {
        "num_shards": len(shard_scores),
        "mean_score": mean_score,
        "boundary_efficiency": boundary_efficiency,
        "boundary_bonus": boundary_bonus,
        "performance_score": performance_score,
        "boundary_metrics_files": boundary_metrics_files,
        "shards": shard_scores,
    }

    summary_json_path = Path(args.summary_json)
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# mmlu-redux 8-shard summary",
        "",
        f"- num_shards: {len(shard_scores)}",
        f"- mean_score: {mean_score:.6f}",
        f"- boundary_efficiency: {boundary_efficiency:.6f}",
        f"- boundary_bonus: {boundary_bonus:.6f}",
        f"- performance_score: {performance_score:.6f}",
        "",
        "| shard | score | log_path |",
        "|---|---:|---|",
    ]
    for item in shard_scores:
        lines.append(f"| {item['shard']} | {item['score']:.6f} | `{item['log_path']}` |")

    summary_md_path = Path(args.summary_md)
    summary_md_path.parent.mkdir(parents=True, exist_ok=True)
    summary_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
