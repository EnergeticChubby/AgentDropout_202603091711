import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set


CLASS_ORDER = ["UE", "TX-Origin", "RENT", "ARTHM", "TimeO", "LE", "TimeM"]

PATTERN_MAP = {
    "ARTHM": [
        r"\barthm\b",
        r"\barithmetic\b",
        r"\boverflow\b",
        r"\bunderflow\b",
        r"\binteger overflow\b",
        r"\binteger underflow\b",
    ],
    "LE": [
        r"\ble\b",
        r"\blocked ether\b",
        r"\blocked funds\b",
        r"\bfrozen ether\b",
        r"\bether lock(?:ed)?\b",
    ],
    "RENT": [
        r"\brent\b",
        r"\breentran(?:cy|t)\b",
        r"\bre-entran(?:cy|t)\b",
    ],
    "TimeM": [
        r"\btimem\b",
        r"\btime manipulation\b",
        r"\bblock values as a proxy for time\b",
    ],
    "TimeO": [
        r"\btimeo\b",
        r"\btimestamp ordering\b",
        r"\btransaction order dependence\b",
        r"\btransaction ordering\b",
        r"\bfront running\b",
        r"\btod\b",
    ],
    "TX-Origin": [
        r"\btx-origin\b",
        r"\btx\.origin\b",
        r"\btx origin\b",
        r"\btxorigin\b",
        r"\bauthorization through tx\.origin\b",
    ],
    "UE": [
        r"\bue\b",
        r"\bunhandled exception\b",
        r"\bunchecked call return value\b",
        r"\bunchecked return value\b",
    ],
}


@dataclass
class ReparseItem:
    idx: int
    file_path: str
    gold_vector: List[int]
    pred_vector: List[int]
    gold_labels: List[str]
    pred_labels: List[str]
    exact_match: bool
    parse_mode: str
    answer_text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reparse ScrawlD predictions and recompute metrics.")
    parser.add_argument(
        "--predictions",
        type=str,
        default="/workspace/result/scrawld_qwen3_8b/predictions.jsonl",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="/workspace/result/scrawld_qwen3_8b_reparsed",
    )
    return parser.parse_args()


def vector_to_labels(vector: List[int]) -> List[str]:
    return [CLASS_ORDER[i] for i, x in enumerate(vector) if x == 1]


def labels_to_vector(labels: List[str]) -> List[int]:
    s = set(labels)
    return [1 if c in s else 0 for c in CLASS_ORDER]


def extract_answer_text(raw_response: str, fallback: str = "") -> str:
    if raw_response:
        m = re.search(r"<answer>(.*?)</answer>", raw_response, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()
        return raw_response.strip()
    return fallback.strip()


def parse_binary_vector(answer_text: str) -> Optional[List[int]]:
    txt = answer_text.strip()

    # Case 1: [0, 0, 1, 1, 0, 1, 0]
    m = re.search(r"\[([^\]]+)\]", txt)
    if m:
        nums = re.findall(r"-?\d+", m.group(1))
        if len(nums) >= 7:
            vals = [1 if int(x) > 0 else 0 for x in nums[:7]]
            return vals

    # Case 2: 0x00, 0x01, ...
    hex_nums = re.findall(r"0x[0-9a-fA-F]+", txt)
    if len(hex_nums) >= 7:
        vals = [1 if int(x, 16) > 0 else 0 for x in hex_nums[:7]]
        return vals

    # Case 3: plain 7 binary digits separated by comma/space
    nums = re.findall(r"(?<!\d)(0|1)(?!\d)", txt)
    if len(nums) == 7:
        return [int(x) for x in nums]

    return None


def parse_text_labels(answer_text: str) -> List[str]:
    txt = answer_text.lower()
    pred: Set[str] = set()
    for label, patterns in PATTERN_MAP.items():
        for p in patterns:
            if re.search(p, txt, flags=re.IGNORECASE):
                pred.add(label)
                break
    return [c for c in CLASS_ORDER if c in pred]


def parse_prediction(answer_text: str) -> (List[int], str):
    vec = parse_binary_vector(answer_text)
    if vec is not None:
        return vec, "vector"
    labels = parse_text_labels(answer_text)
    return labels_to_vector(labels), "text"


def compute_metrics(items: List[ReparseItem]) -> Dict:
    n = len(items)
    exact = sum(1 for x in items if x.exact_match)
    tp = {c: 0 for c in CLASS_ORDER}
    fp = {c: 0 for c in CLASS_ORDER}
    fn = {c: 0 for c in CLASS_ORDER}
    support = {c: 0 for c in CLASS_ORDER}

    for item in items:
        for i, cls in enumerate(CLASS_ORDER):
            g, p = item.gold_vector[i], item.pred_vector[i]
            if g == 1:
                support[cls] += 1
            if g == 1 and p == 1:
                tp[cls] += 1
            elif g == 0 and p == 1:
                fp[cls] += 1
            elif g == 1 and p == 0:
                fn[cls] += 1

    per_class = {}
    macro_f1 = 0.0
    for cls in CLASS_ORDER:
        c_tp, c_fp, c_fn = tp[cls], fp[cls], fn[cls]
        precision = c_tp / (c_tp + c_fp) if (c_tp + c_fp) else 0.0
        recall = c_tp / (c_tp + c_fn) if (c_tp + c_fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        macro_f1 += f1
        per_class[cls] = {
            "support": support[cls],
            "tp": c_tp,
            "fp": c_fp,
            "fn": c_fn,
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
        }

    micro_tp = sum(tp.values())
    micro_fp = sum(fp.values())
    micro_fn = sum(fn.values())
    micro_precision = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) else 0.0
    micro_recall = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) else 0.0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if (micro_precision + micro_recall)
        else 0.0
    )

    return {
        "samples": n,
        "exact_match": round(exact / n if n else 0.0, 6),
        "micro_precision": round(micro_precision, 6),
        "micro_recall": round(micro_recall, 6),
        "micro_f1": round(micro_f1, 6),
        "macro_f1": round(macro_f1 / len(CLASS_ORDER), 6),
        "per_class": per_class,
    }


def main() -> None:
    args = parse_args()
    pred_path = Path(args.predictions)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    items: List[ReparseItem] = []
    parse_mode_count = {"vector": 0, "text": 0}
    with pred_path.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            answer_text = extract_answer_text(row.get("raw_response", ""), row.get("parsed_answer_text", ""))
            pred_vector, parse_mode = parse_prediction(answer_text)
            parse_mode_count[parse_mode] += 1
            gold_vector = row["gold_vector"]
            item = ReparseItem(
                idx=row["idx"],
                file_path=row["file_path"],
                gold_vector=gold_vector,
                pred_vector=pred_vector,
                gold_labels=vector_to_labels(gold_vector),
                pred_labels=vector_to_labels(pred_vector),
                exact_match=(gold_vector == pred_vector),
                parse_mode=parse_mode,
                answer_text=answer_text,
            )
            items.append(item)

    metrics = compute_metrics(items)
    summary = {
        "input_predictions": str(pred_path),
        "class_order": CLASS_ORDER,
        "parse_mode_count": parse_mode_count,
        "metrics": metrics,
    }

    with (output_dir / "summary_reparsed.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with (output_dir / "predictions_reparsed.jsonl").open("w", encoding="utf-8") as f:
        for x in items:
            f.write(
                json.dumps(
                    {
                        "idx": x.idx,
                        "file_path": x.file_path,
                        "gold_vector": x.gold_vector,
                        "pred_vector": x.pred_vector,
                        "gold_labels": x.gold_labels,
                        "pred_labels": x.pred_labels,
                        "exact_match": x.exact_match,
                        "parse_mode": x.parse_mode,
                        "answer_text": x.answer_text,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(json.dumps(summary, ensure_ascii=False))
    print(f"[INFO] saved -> {output_dir / 'summary_reparsed.json'}")
    print(f"[INFO] saved -> {output_dir / 'predictions_reparsed.jsonl'}")


if __name__ == "__main__":
    main()
