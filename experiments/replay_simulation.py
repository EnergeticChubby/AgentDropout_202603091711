import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from AgentDropout.core.simulator import replay_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Replay and summarize AgentDropout event logs.")
    parser.add_argument("--events_jsonl", type=str, required=True, help="Path to events jsonl file.")
    parser.add_argument(
        "--output_json",
        type=str,
        default=None,
        help="Optional output file to save summary JSON.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    summary = replay_summary(args.events_jsonl)
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fp:
            json.dump(summary, fp, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
