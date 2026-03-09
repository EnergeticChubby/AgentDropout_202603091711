import argparse
import json
from pathlib import Path
from typing import Dict, List


def parse_args():
    parser = argparse.ArgumentParser(description="Train a lightweight offline attention policy from event logs.")
    parser.add_argument("--events_glob", type=str, required=True, help="Glob for event jsonl files.")
    parser.add_argument("--output_json", type=str, required=True, help="Path to output policy JSON.")
    return parser.parse_args()


def load_events(paths: List[Path]) -> List[Dict]:
    events = []
    for path in paths:
        with path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                events.append(json.loads(line))
    return events


def train_phase_level_policy(events: List[Dict]) -> Dict[str, int]:
    counts: Dict[str, Dict[int, int]] = {}
    for event in events:
        if event.get("event_type") != "message_read":
            continue
        phase = event.get("phase", "aggregate")
        level = int(event.get("read_level", 4))
        phase_counts = counts.setdefault(phase, {})
        phase_counts[level] = phase_counts.get(level, 0) + 1

    policy = {}
    for phase, level_counts in counts.items():
        best_level = sorted(level_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        policy[phase] = best_level

    default_phase_levels = {"propose": 1, "critique": 2, "verify": 3, "aggregate": 2}
    for phase, level in default_phase_levels.items():
        policy.setdefault(phase, level)
    return policy


def main():
    args = parse_args()
    paths = sorted(Path().glob(args.events_glob))
    if not paths:
        raise FileNotFoundError(f"No files found for glob: {args.events_glob}")
    events = load_events(paths)
    policy = train_phase_level_policy(events)
    output_file = Path(args.output_json)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as fp:
        json.dump({"policy": policy, "num_events": len(events), "num_files": len(paths)}, fp, ensure_ascii=False, indent=2)
    print(json.dumps({"policy": policy, "num_events": len(events), "num_files": len(paths)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
