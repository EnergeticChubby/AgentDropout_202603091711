import argparse
import ast
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

import requests


# Label index order inferred from dataset labels and file names.
CLASS_ORDER = ["UE", "TX-Origin", "RENT", "ARTHM", "TimeO", "LE", "TimeM"]
CLASS_SET = set(CLASS_ORDER)

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
        r"\block(?:ed)? e(?:a)?ther\b",
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
        r"\btod\b",
    ],
    "TX-Origin": [
        r"\btx-origin\b",
        r"\btx\.origin\b",
        r"\btx origin\b",
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
class EvalItem:
    idx: int
    file_path: str
    gold_vector: List[int]
    pred_vector: List[int]
    gold_labels: List[str]
    pred_labels: List[str]
    exact_match: bool
    raw_response: str
    parsed_answer_text: str
    error: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate qwen3-8b on ScrawlD-style JSON labels.")
    parser.add_argument(
        "--input",
        type=str,
        default="/workspace/grpo_text_classification_labeled.json",
        help="Path to ScrawlD-style labeled JSON file.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="/workspace/result/scrawld_qwen3_8b",
        help="Directory to save detailed predictions and summary.",
    )
    parser.add_argument("--model", type=str, default="qwen3-8b")
    parser.add_argument("--base_url", type=str, required=True, help="OpenAI-compatible base URL.")
    parser.add_argument("--api_key", type=str, required=True, help="API key for model service.")
    parser.add_argument("--workers", type=int, default=4, help="Parallel request workers.")
    parser.add_argument("--timeout", type=int, default=180, help="Single request timeout seconds.")
    parser.add_argument("--retries", type=int, default=3, help="Retry count per sample.")
    parser.add_argument("--max_samples", type=int, default=None, help="Optional cap for quick run.")
    return parser.parse_args()


def load_dataset(path: Path, max_samples: int = None) -> List[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if max_samples is not None:
        rows = rows[:max_samples]
    return rows


def parse_label(raw_label) -> List[int]:
    if isinstance(raw_label, str):
        values = ast.literal_eval(raw_label)
    else:
        values = raw_label
    if not isinstance(values, list) or len(values) != len(CLASS_ORDER):
        raise ValueError(f"Invalid label format: {raw_label}")
    return [int(x) for x in values]


def vector_to_labels(vector: List[int]) -> List[str]:
    return [CLASS_ORDER[i] for i, x in enumerate(vector) if x == 1]


def normalize_answer_text(raw_text: str) -> str:
    m = re.search(r"<answer>(.*?)</answer>", raw_text, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return raw_text.strip()


def parse_predicted_labels(answer_text: str) -> List[str]:
    txt = answer_text.lower()
    pred: Set[str] = set()
    for label, patterns in PATTERN_MAP.items():
        for p in patterns:
            if re.search(p, txt, flags=re.IGNORECASE):
                pred.add(label)
                break
    return [x for x in CLASS_ORDER if x in pred]


def labels_to_vector(labels: List[str]) -> List[int]:
    label_set = set(labels)
    return [1 if cls in label_set else 0 for cls in CLASS_ORDER]


def request_chat(
    session: requests.Session,
    base_url: str,
    api_key: str,
    model: str,
    messages: List[dict],
    timeout: int,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
    }
    resp = session.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    body = resp.json()
    return body["choices"][0]["message"]["content"]


def eval_one(
    idx: int,
    row: dict,
    base_url: str,
    api_key: str,
    model: str,
    timeout: int,
    retries: int,
) -> EvalItem:
    gold_vector = parse_label(row["label"])
    gold_labels = vector_to_labels(gold_vector)
    file_path = str(row.get("file_path", ""))
    messages = row.get("messages", [])

    if not messages:
        return EvalItem(
            idx=idx,
            file_path=file_path,
            gold_vector=gold_vector,
            pred_vector=[0] * len(CLASS_ORDER),
            gold_labels=gold_labels,
            pred_labels=[],
            exact_match=False,
            raw_response="",
            parsed_answer_text="",
            error="empty_messages",
        )

    session = requests.Session()
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            raw_response = request_chat(session, base_url, api_key, model, messages, timeout)
            answer_text = normalize_answer_text(raw_response)
            pred_labels = parse_predicted_labels(answer_text)
            pred_vector = labels_to_vector(pred_labels)
            return EvalItem(
                idx=idx,
                file_path=file_path,
                gold_vector=gold_vector,
                pred_vector=pred_vector,
                gold_labels=gold_labels,
                pred_labels=pred_labels,
                exact_match=(gold_vector == pred_vector),
                raw_response=raw_response,
                parsed_answer_text=answer_text,
                error="",
            )
        except Exception as exc:
            last_error = f"attempt_{attempt}: {exc}"
            time.sleep(min(2 * attempt, 8))

    return EvalItem(
        idx=idx,
        file_path=file_path,
        gold_vector=gold_vector,
        pred_vector=[0] * len(CLASS_ORDER),
        gold_labels=gold_labels,
        pred_labels=[],
        exact_match=False,
        raw_response="",
        parsed_answer_text="",
        error=last_error or "unknown_error",
    )


def compute_metrics(items: List[EvalItem]) -> Dict:
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
    f1_sum = 0.0
    for cls in CLASS_ORDER:
        c_tp, c_fp, c_fn = tp[cls], fp[cls], fn[cls]
        prec = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
        rec = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        f1_sum += f1
        per_class[cls] = {
            "support": support[cls],
            "tp": c_tp,
            "fp": c_fp,
            "fn": c_fn,
            "precision": round(prec, 6),
            "recall": round(rec, 6),
            "f1": round(f1, 6),
        }

    micro_tp = sum(tp.values())
    micro_fp = sum(fp.values())
    micro_fn = sum(fn.values())
    micro_precision = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) > 0 else 0.0
    micro_recall = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) > 0 else 0.0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if (micro_precision + micro_recall) > 0
        else 0.0
    )

    return {
        "samples": n,
        "exact_match": round(exact / n if n else 0.0, 6),
        "micro_precision": round(micro_precision, 6),
        "micro_recall": round(micro_recall, 6),
        "micro_f1": round(micro_f1, 6),
        "macro_f1": round(f1_sum / len(CLASS_ORDER), 6),
        "per_class": per_class,
        "error_count": sum(1 for x in items if x.error),
    }


def save_outputs(output_dir: Path, items: List[EvalItem], metrics: Dict, config: Dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    detail_path = output_dir / "predictions.jsonl"
    summary_path = output_dir / "summary.json"
    markdown_path = output_dir / "report.md"

    with detail_path.open("w", encoding="utf-8") as f:
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
                        "error": x.error,
                        "parsed_answer_text": x.parsed_answer_text,
                        "raw_response": x.raw_response,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump({"config": config, "metrics": metrics}, f, ensure_ascii=False, indent=2)

    lines = [
        "# ScrawlD subset evaluation report",
        "",
        "## Config",
        f"- model: {config['model']}",
        f"- input: {config['input']}",
        f"- workers: {config['workers']}",
        f"- timeout: {config['timeout']}",
        f"- retries: {config['retries']}",
        f"- max_samples: {config['max_samples']}",
        "",
        "## Metrics",
        f"- samples: {metrics['samples']}",
        f"- exact_match: {metrics['exact_match']}",
        f"- micro_precision: {metrics['micro_precision']}",
        f"- micro_recall: {metrics['micro_recall']}",
        f"- micro_f1: {metrics['micro_f1']}",
        f"- macro_f1: {metrics['macro_f1']}",
        f"- error_count: {metrics['error_count']}",
        "",
        "## Per-class",
    ]
    for cls in CLASS_ORDER:
        m = metrics["per_class"][cls]
        lines.append(
            f"- {cls}: support={m['support']}, precision={m['precision']}, recall={m['recall']}, f1={m['f1']}, tp={m['tp']}, fp={m['fp']}, fn={m['fn']}"
        )

    markdown_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    rows = load_dataset(input_path, args.max_samples)

    print(f"[INFO] loaded_samples={len(rows)} from {input_path}")
    started = time.time()
    items: List[EvalItem] = [None] * len(rows)  # type: ignore

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(
                eval_one,
                i,
                row,
                args.base_url,
                args.api_key,
                args.model,
                args.timeout,
                args.retries,
            ): i
            for i, row in enumerate(rows)
        }
        done = 0
        for fut in as_completed(futures):
            idx = futures[fut]
            items[idx] = fut.result()
            done += 1
            if done % 10 == 0 or done == len(rows):
                print(f"[INFO] progress {done}/{len(rows)}")

    metrics = compute_metrics(items)
    elapsed = round(time.time() - started, 2)
    print(f"[INFO] elapsed_seconds={elapsed}")
    print(f"[INFO] metrics={json.dumps(metrics, ensure_ascii=False)}")

    config = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "model": args.model,
        "base_url": args.base_url,
        "workers": args.workers,
        "timeout": args.timeout,
        "retries": args.retries,
        "max_samples": args.max_samples,
        "class_order": CLASS_ORDER,
    }
    save_outputs(output_dir, items, metrics, config)
    print(f"[INFO] saved summary -> {output_dir / 'summary.json'}")
    print(f"[INFO] saved details -> {output_dir / 'predictions.jsonl'}")
    print(f"[INFO] saved report  -> {output_dir / 'report.md'}")


if __name__ == "__main__":
    main()
