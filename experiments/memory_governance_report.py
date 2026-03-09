import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Summarize memory governance events from jsonl.")
    parser.add_argument("--events_jsonl", type=str, required=True)
    parser.add_argument("--output_json", type=str, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    counts = {}
    pool_counts = {}
    with open(args.events_jsonl, "r", encoding="utf-8") as fp:
        for line in fp:
            event = json.loads(line)
            event_type = event.get("event_type", "unknown")
            counts[event_type] = counts.get(event_type, 0) + 1
            if event_type == "memory_write":
                pool = event.get("metadata", {}).get("pool", "unknown")
                pool_counts[pool] = pool_counts.get(pool, 0) + 1

    output = {"counts": counts, "pool_counts": pool_counts}
    path = Path(args.output_json)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(output, fp, ensure_ascii=False, indent=2)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
