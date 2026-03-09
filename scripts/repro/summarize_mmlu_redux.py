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
    summary = {
        "num_shards": len(shard_scores),
        "mean_score": mean_score,
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
