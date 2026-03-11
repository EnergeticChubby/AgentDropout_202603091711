import argparse
import ast
import asyncio
import copy
import json
import math
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union, Literal

import numpy as np
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import AgentDropout.prompt  # noqa: F401 (register prompt sets)
from AgentDropout.graph.graph import Graph
from AgentDropout.llm import gpt_chat


CLASS_ORDER = ["UE", "TX-Origin", "RENT", "ARTHM", "TimeO", "LE", "TimeM"]
CLASS_SET = set(CLASS_ORDER)
LABEL_PATTERNS = {
    "ARTHM": [r"\barthm\b", r"\barithmetic\b", r"\boverflow\b", r"\bunderflow\b"],
    "LE": [r"\ble\b", r"\blocked ether\b", r"\blocked funds\b", r"\bether lock(?:ed)?\b"],
    "RENT": [r"\brent\b", r"\breentran(?:cy|t)\b", r"\bre-entran(?:cy|t)\b"],
    "TimeM": [r"\btimem\b", r"\btime manipulation\b", r"\bblock values as a proxy for time\b"],
    "TimeO": [
        r"\btimeo\b",
        r"\btimestamp ordering\b",
        r"\btransaction order dependence\b",
        r"\btransaction ordering\b",
        r"\bfront running\b",
        r"\btod\b",
    ],
    "TX-Origin": [r"\btx-origin\b", r"\btx\.origin\b", r"\btx origin\b", r"\btxorigin\b"],
    "UE": [r"\bue\b", r"\bunhandled exception\b", r"\bunchecked return value\b", r"\bunchecked call return value\b"],
}


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AgentDropout on ScrawlD-style vulnerability classification.")
    parser.add_argument("--input_json", type=str, default="/workspace/grpo_text_classification_labeled.json")
    parser.add_argument("--output_dir", type=str, default="/workspace/result/scrawld_agentdropout_qwen3_8b")
    parser.add_argument("--llm_name", type=str, default="qwen3-8b")
    parser.add_argument("--base_url", type=str, required=True)
    parser.add_argument("--api_key", type=str, required=True)
    parser.add_argument(
        "--mode",
        type=str,
        default="FullConnected",
        choices=["DirectAnswer", "FullConnected", "Random", "Chain", "Debate", "Layered", "Star", "Mesh"],
    )
    parser.add_argument("--agent_names", nargs="+", type=str, default=["AnalyzeAgent"])
    parser.add_argument("--agent_nums", nargs="+", type=int, default=[3])
    parser.add_argument("--decision_method", type=str, default="FinalRefer")
    parser.add_argument("--num_rounds", type=int, default=1)
    parser.add_argument("--optimized_spatial", action="store_true")
    parser.add_argument("--optimized_temporal", action="store_true")
    parser.add_argument("--diff", action="store_true")
    parser.add_argument("--dec", action="store_true")
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--num_iterations", type=int, default=6)
    parser.add_argument("--train_batch_size", type=int, default=8)
    parser.add_argument("--imp_per_iterations", type=int, default=2)
    parser.add_argument("--pruning_rate", type=float, default=0.1)
    parser.add_argument("--train_ratio", type=float, default=0.2)
    parser.add_argument("--max_train_samples", type=int, default=120)
    parser.add_argument("--max_eval_samples", type=int, default=200)
    parser.add_argument("--eval_batch_size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def get_kwargs(
    mode: Union[
        Literal["DirectAnswer"],
        Literal["FullConnected"],
        Literal["Random"],
        Literal["Chain"],
        Literal["Debate"],
        Literal["Layered"],
        Literal["Star"],
        Literal["Mesh"],
    ],
    n: int,
) -> Dict[str, Any]:
    def layered_graph(size: int, layer_num: int = 2) -> List[List[int]]:
        adj = [[0] * size for _ in range(size)]
        base_size = size // layer_num
        remainder = size % layer_num
        layers = []
        for i in range(layer_num):
            cur = base_size + (1 if i < remainder else 0)
            layers.extend([i] * cur)
        for i in range(size):
            for j in range(size):
                if layers[j] == layers[i] + 1:
                    adj[i][j] = 1
        return adj

    def mesh_graph(size: int) -> List[List[int]]:
        adj = [[0] * size for _ in range(size)]
        for i in range(size):
            for j in range(i + 1, size):
                adj[i][j] = 1
        return adj

    def star_graph(size: int) -> List[List[int]]:
        adj = [[0] * size for _ in range(size)]
        for i in range(1, size):
            adj[0][i] = 1
        return adj

    fixed_spatial_masks: List[List[int]]
    fixed_temporal_masks: List[List[int]]
    node_kwargs = None

    if mode == "DirectAnswer":
        fixed_spatial_masks = [[0]]
        fixed_temporal_masks = [[0]]
        node_kwargs = [{"role": "Normal"}]
    elif mode == "FullConnected":
        fixed_spatial_masks = [[1 if i != j else 0 for i in range(n)] for j in range(n)]
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
    elif mode == "Random":
        fixed_spatial_masks = [[random.randint(0, 1) if i != j else 0 for i in range(n)] for j in range(n)]
        fixed_temporal_masks = [[random.randint(0, 1) for _ in range(n)] for _ in range(n)]
    elif mode == "Chain":
        fixed_spatial_masks = [[1 if i == j + 1 else 0 for i in range(n)] for j in range(n)]
        fixed_temporal_masks = [[1 if i == 0 and j == n - 1 else 0 for i in range(n)] for j in range(n)]
    elif mode == "Debate":
        fixed_spatial_masks = [[0 for _ in range(n)] for _ in range(n)]
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
    elif mode == "Layered":
        fixed_spatial_masks = layered_graph(n)
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
    elif mode == "Mesh":
        fixed_spatial_masks = mesh_graph(n)
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
    elif mode == "Star":
        fixed_spatial_masks = star_graph(n)
        fixed_temporal_masks = [[1 for _ in range(n)] for _ in range(n)]
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return {
        "initial_spatial_probability": 0.5,
        "fixed_spatial_masks": fixed_spatial_masks,
        "initial_temporal_probability": 0.5,
        "fixed_temporal_masks": fixed_temporal_masks,
        "node_kwargs": node_kwargs,
    }


def parse_label(raw_label: Any) -> List[int]:
    if isinstance(raw_label, str):
        values = ast.literal_eval(raw_label)
    else:
        values = raw_label
    if not isinstance(values, list) or len(values) != len(CLASS_ORDER):
        raise ValueError(f"Invalid label format: {raw_label}")
    return [int(x) for x in values]


def labels_to_vector(labels: List[str]) -> List[int]:
    label_set = set(labels)
    return [1 if c in label_set else 0 for c in CLASS_ORDER]


def vector_to_labels(vector: List[int]) -> List[str]:
    return [CLASS_ORDER[i] for i, v in enumerate(vector) if v == 1]


def extract_answer_text(raw_answer: Union[str, List[str]]) -> str:
    if isinstance(raw_answer, list):
        raw_answer = raw_answer[0] if raw_answer else ""
    if not isinstance(raw_answer, str):
        raw_answer = str(raw_answer)
    m = re.search(r"<answer>(.*?)</answer>", raw_answer, flags=re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else raw_answer.strip()


def parse_vector_from_text(text: str) -> List[int]:
    txt = text.strip()

    m = re.search(r"\[([^\]]+)\]", txt)
    if m:
        nums = re.findall(r"-?\d+", m.group(1))
        if len(nums) >= 7:
            return [1 if int(x) > 0 else 0 for x in nums[:7]]

    hex_nums = re.findall(r"0x[0-9a-fA-F]+", txt)
    if len(hex_nums) >= 7:
        return [1 if int(x, 16) > 0 else 0 for x in hex_nums[:7]]

    nums = re.findall(r"(?<!\d)(0|1)(?!\d)", txt)
    if len(nums) == 7:
        return [int(x) for x in nums]

    lowered = txt.lower()
    labels = set()
    for label, patterns in LABEL_PATTERNS.items():
        for p in patterns:
            if re.search(p, lowered, flags=re.IGNORECASE):
                labels.add(label)
                break
    return labels_to_vector([x for x in CLASS_ORDER if x in labels])


def build_task(record: Dict[str, Any]) -> str:
    contract = str(record.get("contract content", "")).strip()
    if not contract and isinstance(record.get("messages"), list) and record["messages"]:
        contract = str(record["messages"][0].get("content", "")).strip()
    return (
        "You are given a Solidity smart contract. Detect vulnerabilities among "
        "[UE, TX-Origin, RENT, ARTHM, TimeO, LE, TimeM].\n"
        "Definitions:\n"
        "- UE: unchecked external call return value.\n"
        "- TX-Origin: authorization through tx.origin.\n"
        "- RENT: reentrancy.\n"
        "- ARTHM: integer overflow/underflow.\n"
        "- TimeO: timestamp ordering / transaction order dependence.\n"
        "- LE: locked ether.\n"
        "- TimeM: block values as a proxy for time.\n"
        "Output strictly one vector in <answer> tags in this fixed order [UE, TX-Origin, RENT, ARTHM, TimeO, LE, TimeM], "
        "e.g. <answer>[0,1,0,1,0,0,0]</answer>.\n\n"
        "Contract:\n```solidity\n"
        + contract
        + "\n```"
    )


def multilabel_f1(gold: List[int], pred: List[int]) -> float:
    tp = sum(1 for g, p in zip(gold, pred) if g == 1 and p == 1)
    fp = sum(1 for g, p in zip(gold, pred) if g == 0 and p == 1)
    fn = sum(1 for g, p in zip(gold, pred) if g == 1 and p == 0)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compute_metrics(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(items)
    exact = sum(1 for x in items if x["exact_match"])
    tp = {c: 0 for c in CLASS_ORDER}
    fp = {c: 0 for c in CLASS_ORDER}
    fn = {c: 0 for c in CLASS_ORDER}
    support = {c: 0 for c in CLASS_ORDER}

    for item in items:
        gold = item["gold_vector"]
        pred = item["pred_vector"]
        for i, cls in enumerate(CLASS_ORDER):
            g, p = gold[i], pred[i]
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
    total_correct_labels = 0
    for cls in CLASS_ORDER:
        c_tp, c_fp, c_fn = tp[cls], fp[cls], fn[cls]
        c_tn = n - c_tp - c_fp - c_fn
        total_correct_labels += c_tp + c_tn
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
    label_accuracy = total_correct_labels / (n * len(CLASS_ORDER)) if n else 0.0

    return {
        "samples": n,
        "exact_match": round(exact / n if n else 0.0, 6),
        "label_accuracy": round(label_accuracy, 6),
        "micro_precision": round(micro_precision, 6),
        "micro_recall": round(micro_recall, 6),
        "micro_f1": round(micro_f1, 6),
        "macro_f1": round(macro_f1 / len(CLASS_ORDER), 6),
        "per_class": per_class,
        "error_count": sum(1 for x in items if x.get("error")),
    }


def get_train_eval_split(rows: List[Dict[str, Any]], train_ratio: float, max_train: int, max_eval: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if not rows:
        return [], []
    n_total = len(rows)
    n_train = int(n_total * train_ratio)
    n_train = min(max(1, n_train), max_train)
    n_eval = min(max_eval, n_total - n_train) if n_total > n_train else min(max_eval, n_total)

    train_rows = rows[:n_train]
    eval_rows = rows[n_train : n_train + n_eval] if n_total > n_train else rows[:n_eval]
    return train_rows, eval_rows


def wrap_batch(rows: List[Dict[str, Any]], start: int, batch_size: int) -> List[Dict[str, Any]]:
    if not rows:
        return []
    out = []
    for i in range(batch_size):
        out.append(rows[(start + i) % len(rows)])
    return out


async def train_agentdropout(graph: Graph, train_rows: List[Dict[str, Any]], args: argparse.Namespace) -> None:
    if not train_rows:
        print("[TRAIN] empty train set, skip")
        return
    if not (args.optimized_spatial or args.optimized_temporal):
        print("[TRAIN] optimized flags are off, skip training")
        return

    if not graph.diff:
        optimizer = torch.optim.Adam([graph.spatial_logits, graph.temporal_logits], lr=args.lr)
    else:
        optimizer = torch.optim.Adam(list(graph.spatial_logits.parameters()) + list(graph.temporal_logits.parameters()), lr=args.lr)

    graph.optimized_spatial = True
    graph.optimized_temporal = True

    print(f"[TRAIN] start iterations={args.num_iterations}, batch_size={args.train_batch_size}")
    for i_iter in range(args.num_iterations):
        batch_rows = wrap_batch(train_rows, i_iter * args.train_batch_size, args.train_batch_size)
        tasks = []
        golds: List[List[int]] = []

        for row in batch_rows:
            realized_graph = copy.deepcopy(graph)
            realized_graph.spatial_logits = graph.spatial_logits
            realized_graph.temporal_logits = graph.temporal_logits
            input_dict = {"task": build_task(row)}
            tasks.append(asyncio.create_task(realized_graph.arun(input_dict, args.num_rounds)))
            golds.append(parse_label(row["label"]))

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        losses: List[torch.Tensor] = []
        utility_list: List[float] = []
        valid = 0

        for result, gold in zip(raw_results, golds):
            if isinstance(result, Exception):
                continue
            raw_answer, log_prob = result
            pred_vec = parse_vector_from_text(extract_answer_text(raw_answer))
            utility = multilabel_f1(gold, pred_vec)
            utility_list.append(utility)
            if not isinstance(log_prob, torch.Tensor):
                log_prob = torch.tensor(float(log_prob), requires_grad=True)
            losses.append(-log_prob * utility)
            valid += 1

        if not losses:
            print(f"[TRAIN] iter={i_iter + 1} no valid samples")
            continue

        total_loss = torch.mean(torch.stack(losses))
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        if (i_iter + 1) % args.imp_per_iterations == 0:
            if not graph.diff:
                graph.update_masks(args.pruning_rate)
            else:
                graph.update_masks_diff(args.pruning_rate)

        print(
            f"[TRAIN] iter={i_iter + 1}/{args.num_iterations}, valid={valid}, "
            f"avg_utility={sum(utility_list) / len(utility_list):.4f}, loss={float(total_loss.item()):.4f}"
        )


async def evaluate_agentdropout(graph: Graph, eval_rows: List[Dict[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not eval_rows:
        return items

    batches = int(math.ceil(len(eval_rows) / args.eval_batch_size))
    for i_batch in range(batches):
        start = i_batch * args.eval_batch_size
        cur_rows = eval_rows[start : start + args.eval_batch_size]
        tasks = []

        for row in cur_rows:
            realized_graph = copy.deepcopy(graph)
            realized_graph.spatial_logits = graph.spatial_logits
            realized_graph.temporal_logits = graph.temporal_logits
            input_dict = {"task": build_task(row)}
            tasks.append(asyncio.create_task(realized_graph.arun(input_dict, args.num_rounds)))

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        for row, result in zip(cur_rows, raw_results):
            gold_vec = parse_label(row["label"])
            file_path = str(row.get("file_path", ""))
            if isinstance(result, Exception):
                pred_vec = [0] * len(CLASS_ORDER)
                raw_text = ""
                error = str(result)
            else:
                raw_answer, _ = result
                raw_text = extract_answer_text(raw_answer)
                pred_vec = parse_vector_from_text(raw_text)
                error = ""
            items.append(
                {
                    "file_path": file_path,
                    "gold_vector": gold_vec,
                    "pred_vector": pred_vec,
                    "gold_labels": vector_to_labels(gold_vec),
                    "pred_labels": vector_to_labels(pred_vec),
                    "exact_match": gold_vec == pred_vec,
                    "answer_text": raw_text,
                    "error": error,
                }
            )
        print(f"[EVAL] progress={len(items)}/{len(eval_rows)}")
    return items


def save_results(output_dir: Path, config: Dict[str, Any], metrics: Dict[str, Any], items: List[Dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary_agentdropout.json"
    detail_path = output_dir / "predictions_agentdropout.jsonl"

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump({"config": config, "metrics": metrics}, f, ensure_ascii=False, indent=2)

    with detail_path.open("w", encoding="utf-8") as f:
        for row in items:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[SAVE] {summary_path}")
    print(f"[SAVE] {detail_path}")


async def main() -> None:
    args = parse_args()
    if len(args.agent_names) != len(args.agent_nums):
        raise ValueError("agent_names count must match agent_nums count")
    set_seed(args.seed)

    # Inject endpoint config into AgentDropout's OpenAI client wrapper.
    gpt_chat.MINE_BASE_URL = args.base_url
    gpt_chat.MINE_API_KEYS = args.api_key

    rows = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    train_rows, eval_rows = get_train_eval_split(
        rows, args.train_ratio, args.max_train_samples, args.max_eval_samples
    )

    agent_names = [name for name, num in zip(args.agent_names, args.agent_nums) for _ in range(num)]
    kwargs = get_kwargs(args.mode, len(agent_names))
    graph = Graph(
        domain="scrawld",
        llm_name=args.llm_name,
        agent_names=agent_names,
        decision_method=args.decision_method,
        optimized_spatial=args.optimized_spatial,
        optimized_temporal=args.optimized_temporal,
        rounds=args.num_rounds,
        diff=args.diff,
        dec=args.dec,
        **kwargs,
    )

    started = time.time()
    await train_agentdropout(graph, train_rows, args)
    eval_started = time.time()
    items = await evaluate_agentdropout(graph, eval_rows, args)
    eval_elapsed = time.time() - eval_started
    total_elapsed = time.time() - started

    metrics = compute_metrics(items)
    metrics["eval_seconds"] = round(eval_elapsed, 2)
    metrics["total_seconds"] = round(total_elapsed, 2)
    metrics["throughput_samples_per_sec"] = round(len(eval_rows) / eval_elapsed, 4) if eval_elapsed > 0 else 0.0

    if not graph.diff:
        metrics["spatial_sparsity"] = round(float((graph.spatial_masks.sum() / graph.spatial_masks.numel()).item()), 6)
        metrics["temporal_sparsity"] = round(float((graph.temporal_masks.sum() / graph.temporal_masks.numel()).item()), 6)

    config = vars(args).copy()
    if "api_key" in config:
        config["api_key"] = "[REDACTED]"
    config["class_order"] = CLASS_ORDER
    config["train_samples"] = len(train_rows)
    config["eval_samples"] = len(eval_rows)
    config["is_agentdropout"] = True

    output_dir = Path(args.output_dir)
    save_results(output_dir, config, metrics, items)
    print(f"[DONE] metrics={json.dumps(metrics, ensure_ascii=False)}")


if __name__ == "__main__":
    asyncio.run(main())
