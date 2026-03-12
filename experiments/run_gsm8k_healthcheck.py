#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
import copy
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding="utf-8")

from AgentDropout.graph.graph import Graph
from AgentDropout.tools.reader.readers import JSONLReader, JSONReader
from AgentDropout.utils.const import AgentPrune_ROOT
from AgentDropout.utils.globals import Time
from datasets.gsm8k_dataset import gsm_data_process, gsm_get_predict
from experiments.run_svamp import get_kwargs


def parse_args():
    parser = argparse.ArgumentParser(description="Run GSM8K health benchmark with AgentDropout.")
    parser.add_argument("--dataset_json", type=str, default="datasets/gsm8k/test.jsonl")
    parser.add_argument("--train_json", type=str, default="datasets/gsm8k/train.jsonl")
    parser.add_argument("--result_dir", type=str, default="result/gz10-v3/GSM8K")
    parser.add_argument("--llm_name", type=str, default=os.getenv("DEFAULT_LLM_NAME", "MiniMax-M2.5"))
    parser.add_argument("--phase_name", type=str, default="phase0-health")
    parser.add_argument("--domain", type=str, default="gsm8k")
    parser.add_argument("--mode", type=str, default="FullConnected")
    parser.add_argument("--agent_names", nargs="+", type=str, default=["MathSolver"])
    parser.add_argument("--agent_nums", nargs="+", type=int, default=[5])
    parser.add_argument("--decision_method", type=str, default="FinalRefer")
    parser.add_argument("--num_rounds", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=20)
    parser.add_argument("--eval_sample_size", type=int, default=20)
    parser.add_argument("--train_sample_size", type=int, default=40)
    parser.add_argument("--optimized_spatial", action="store_true")
    parser.add_argument("--optimized_temporal", action="store_true")
    parser.add_argument("--diff", action="store_true")
    parser.add_argument("--dec", action="store_true")
    return parser.parse_args()


def load_records(path: str):
    suffix = Path(path).suffix.lower()
    if suffix == ".jsonl":
        return JSONLReader.parse_file(path)
    return JSONReader.parse_file(path)


def validate_gsm8k_dataset(path: str, records):
    if "gsm8k" not in path.lower():
        raise ValueError(f"GSM8K guard failed: dataset path is not gsm8k-labeled -> {path}")
    if not isinstance(records, list) or len(records) == 0:
        raise ValueError(f"GSM8K guard failed: no records loaded from {path}")
    sample = records[0]
    required = {"question", "answer"}
    if not required.issubset(sample.keys()):
        raise ValueError(f"GSM8K guard failed: missing keys {required - set(sample.keys())} in {path}")


def dataloader(data_list, batch_size, i_batch):
    return data_list[i_batch * batch_size : i_batch * batch_size + batch_size]


def build_manifest(args, result_file: Path, train_size: int, eval_size: int) -> Dict[str, Any]:
    return {
        "created_at": time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()),
        "result_file": str(result_file),
        "phase_name": args.phase_name,
        "domain": args.domain,
        "model": args.llm_name,
        "api_base_url_env": os.getenv("AGENTDROPOUT_BASE_URL") or os.getenv("MINIMAX_BASE_URL") or os.getenv("BASE_URL"),
        "dataset_json": args.dataset_json,
        "train_json": args.train_json,
        "eval_size": eval_size,
        "train_size": train_size,
        "eval_sample_size": args.eval_sample_size,
        "train_sample_size": args.train_sample_size,
        "optimized_spatial": args.optimized_spatial,
        "optimized_temporal": args.optimized_temporal,
        "diff": args.diff,
        "dec": args.dec,
    }


async def main():
    args = parse_args()
    if len(args.agent_names) != len(args.agent_nums):
        raise ValueError("The number of agent names must match the number of agent counts.")

    raw_eval = load_records(args.dataset_json)
    raw_train = load_records(args.train_json)
    validate_gsm8k_dataset(args.dataset_json, raw_eval)
    validate_gsm8k_dataset(args.train_json, raw_train)

    dataset = gsm_data_process(raw_eval)
    train_dataset = gsm_data_process(raw_train)
    if args.eval_sample_size and args.eval_sample_size > 0:
        dataset = dataset[: args.eval_sample_size]
    if args.train_sample_size and args.train_sample_size > 0:
        train_dataset = train_dataset[: args.train_sample_size]
    if not dataset:
        raise ValueError("No GSM8K eval data after sampling.")

    current_time = Time.instance().value or time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    Time.instance().value = current_time

    result_dir = Path(args.result_dir)
    if not result_dir.is_absolute():
        result_dir = Path(f"{AgentPrune_ROOT}/{result_dir}")
    result_dir.mkdir(parents=True, exist_ok=True)
    result_file = result_dir / f"gsm8k_{args.phase_name}_{current_time}.json"
    result_meta_file = result_dir / f"gsm8k_{args.phase_name}_{current_time}.meta.json"

    agent_names = [name for name, num in zip(args.agent_names, args.agent_nums) for _ in range(num)]
    kwargs = get_kwargs(args.mode, len(agent_names))
    graph = Graph(
        domain=args.domain,
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

    manifest = build_manifest(args, result_file=result_file, train_size=len(train_dataset), eval_size=len(dataset))
    with open(result_meta_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    num_batches = (len(dataset) + args.batch_size - 1) // args.batch_size
    total_solved = 0
    total_executed = 0
    results: List[Dict[str, Any]] = []

    for i_batch in range(num_batches):
        current_batch = dataloader(dataset, args.batch_size, i_batch)
        if not current_batch:
            continue
        answer_log_probs = []
        answers = []
        for record in current_batch:
            task = record["task"]
            answer = record["answer"]
            answers.append(answer)
            input_dict = {"task": task}
            realized_graph = copy.deepcopy(graph)
            answer_log_probs.append(asyncio.create_task(realized_graph.arun(input_dict, args.num_rounds, case=True)))

        raw_results = await asyncio.gather(*answer_log_probs)
        raw_answers, _, all_answers = zip(*raw_results)
        for task, answer, true_answer, all_answer in zip(current_batch, raw_answers, answers, all_answers):
            predict_answer = gsm_get_predict(answer[0])
            is_solved = float(predict_answer) == float(true_answer)
            total_solved += int(is_solved)
            total_executed += 1
            accuracy = total_solved / total_executed
            item = {
                "Question": task,
                "Answer": true_answer,
                "All_answers": all_answer,
                "Response": answer,
                "Attempt answer": predict_answer,
                "Solved": bool(is_solved),
                "Total solved": total_solved,
                "Total executed": total_executed,
                "Accuracy": accuracy,
            }
            results.append(item)
            print(f"##########Final Log:{json.dumps(item)}")

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Batch {i_batch} Accuracy: {results[-1]['Accuracy']}")


if __name__ == "__main__":
    asyncio.run(main())
