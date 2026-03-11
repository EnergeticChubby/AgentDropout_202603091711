import argparse
import asyncio
import copy
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from AgentDropout.graph.graph import Graph
from AgentDropout.llm.llm import LLM
from AgentDropout.tools.coding.python_executor import PyExecutor
from AgentDropout.utils.globals import Time
from datasets.gsm8k_dataset import gsm_get_predict


RATE_LIMIT_PATTERN = re.compile(
    r"(error code:\s*429|rate_limited|rate limit|error 1015)",
    re.IGNORECASE,
)


BENCHMARK_SPECS: Dict[str, Dict[str, str]] = {
    "gsm8k": {"dataset": "openai/gsm8k", "config": "main", "split": "test"},
    "multiarith": {"dataset": "ChilleD/MultiArith", "config": "default", "split": "test"},
    "svamp": {"dataset": "ChilleD/SVAMP", "config": "default", "split": "test"},
    "humaneval": {"dataset": "openai/openai_humaneval", "config": "openai_humaneval", "split": "test"},
}


def _request_json_with_retry(url: str, params: Dict[str, Any], retries: int = 8, timeout: int = 60) -> Dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: PERF203
            last_error = exc
            time.sleep(min(2**attempt, 16))
    raise RuntimeError(f"Failed request after {retries} retries: url={url} params={params}") from last_error


def load_rows(benchmark: str) -> List[Dict[str, Any]]:
    if benchmark not in BENCHMARK_SPECS:
        raise ValueError(f"Unsupported benchmark: {benchmark}")
    spec = BENCHMARK_SPECS[benchmark]
    rows_url = "https://datasets-server.huggingface.co/rows"
    records: List[Dict[str, Any]] = []
    offset = 0
    page_size = 100
    while True:
        payload = _request_json_with_retry(
            rows_url,
            {
                "dataset": spec["dataset"],
                "config": spec["config"],
                "split": spec["split"],
                "offset": offset,
                "length": page_size,
            },
        )
        rows = payload.get("rows", [])
        if not rows:
            break
        for item in rows:
            records.append(item["row"])
        offset += page_size
        total = int(payload.get("num_rows_total", offset))
        if offset >= total:
            break
    return records


def full_connected_kwargs(n: int) -> Dict[str, Any]:
    return {
        "initial_spatial_probability": 0.5,
        "fixed_spatial_masks": [[1 if i != j else 0 for i in range(n)] for j in range(n)],
        "initial_temporal_probability": 0.5,
        "fixed_temporal_masks": [[1 for _ in range(n)] for _ in range(n)],
        "node_kwargs": None,
    }


def direct_answer_kwargs(role: str) -> Dict[str, Any]:
    return {
        "initial_spatial_probability": 0.5,
        "fixed_spatial_masks": [[0]],
        "initial_temporal_probability": 0.5,
        "fixed_temporal_masks": [[0]],
        "node_kwargs": [{"role": role}],
    }


def build_graph_kwargs(mode: str, n: int, role: str) -> Dict[str, Any]:
    if mode == "DirectAnswer":
        return direct_answer_kwargs(role=role)
    return full_connected_kwargs(n)


def create_graph(
    *,
    benchmark: str,
    llm_name: str,
    profile: str,
    artifact_root: Path,
    math_agent_count: int,
    code_agent_count: int,
    math_rounds: int,
    code_rounds: int,
    math_mode: str,
    code_mode: str,
    math_decision_method: str,
    code_decision_method: str,
) -> Graph:
    if benchmark == "humaneval":
        agent_name = "CodeWriting"
        agent_count = code_agent_count
        decision_method = code_decision_method
        domain = "humaneval"
        num_rounds = code_rounds
        mode = code_mode
        role = "Programming Expert"
    else:
        agent_name = "MathSolver"
        agent_count = math_agent_count
        decision_method = math_decision_method
        domain = "gsm8k"
        num_rounds = math_rounds
        mode = math_mode
        role = "Math Solver"

    agent_names = [agent_name for _ in range(agent_count)]
    kwargs = build_graph_kwargs(mode=mode, n=len(agent_names), role=role)
    enable_phase3 = profile == "phase3"
    graph = Graph(
        domain=domain,
        llm_name=llm_name,
        agent_names=agent_names,
        decision_method=decision_method,
        optimized_spatial=False,
        optimized_temporal=False,
        rounds=num_rounds,
        diff=False,
        dec=False,
        enable_contracts=enable_phase3,
        contract_output_dir=str(artifact_root / "contracts" / "raw"),
        enable_knowledge=enable_phase3,
        knowledge_output_dir=str(artifact_root / "knowledge" / "raw"),
        enable_boundary=enable_phase3,
        boundary_output_dir=str(artifact_root / "boundary" / "raw"),
        **kwargs,
    )
    return graph


def _extract_answer_text(raw_answer: Any) -> str:
    if isinstance(raw_answer, list) and raw_answer:
        return str(raw_answer[0])
    return str(raw_answer)


def _normalize_math_record(benchmark: str, record: Dict[str, Any]) -> Tuple[str, str]:
    if benchmark == "gsm8k":
        task = str(record["question"])
        true_answer = str(record["answer"]).split("\n####")[-1].replace(",", "").strip()
        return task, true_answer
    if benchmark == "multiarith":
        return str(record["question"]).strip(), str(record["final_ans"]).strip()
    if benchmark == "svamp":
        task = f"{record['Body']} {record['Question']}".strip()
        return task, str(record["Answer"]).strip()
    raise ValueError(f"Unsupported math benchmark: {benchmark}")


def _is_math_correct(pred: str, true_answer: str) -> bool:
    try:
        return float(pred) == float(true_answer)
    except Exception:
        return pred.strip() == true_answer.strip()


async def run_math_benchmark(
    *,
    benchmark: str,
    profile: str,
    llm_name: str,
    output_root: Path,
    max_retries: int,
    max_examples: int | None,
    math_agent_count: int,
    code_agent_count: int,
    math_rounds: int,
    code_rounds: int,
    math_mode: str,
    code_mode: str,
    math_decision_method: str,
    code_decision_method: str,
    concurrency: int,
) -> Dict[str, Any]:
    records = load_rows(benchmark)
    if max_examples is not None:
        records = records[:max_examples]
    run_ts = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    raw_dir = output_root / benchmark / "raw" / run_ts
    summary_dir = output_root / benchmark / "summary"
    raw_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    answers_path = raw_dir / "answers.jsonl"
    log_path = raw_dir / "run.log"

    Time.instance().value = run_ts
    graph = create_graph(
        benchmark=benchmark,
        llm_name=llm_name,
        profile=profile,
        artifact_root=output_root,
        math_agent_count=math_agent_count,
        code_agent_count=code_agent_count,
        math_rounds=math_rounds,
        code_rounds=code_rounds,
        math_mode=math_mode,
        code_mode=code_mode,
        math_decision_method=math_decision_method,
        code_decision_method=code_decision_method,
    )

    total = len(records)
    solved = 0
    rate_limited_events = 0
    attempts_total = 0

    async def solve_one(idx: int, record: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal attempts_total, rate_limited_events
        task, true_answer = _normalize_math_record(benchmark, record)
        last_error = None
        raw_answer_obj: Any = ""
        attempts_used = 0
        for attempt in range(1, max_retries + 1):
            attempts_total += 1
            attempts_used += 1
            try:
                realized_graph = copy.deepcopy(graph)
                result = await realized_graph.arun({"task": task}, realized_graph.rounds)
                raw_answer_obj = result[0] if isinstance(result, tuple) else result
                break
            except Exception as exc:  # noqa: PERF203
                last_error = exc
                err_msg = str(exc)
                is_rate = bool(RATE_LIMIT_PATTERN.search(err_msg))
                if is_rate:
                    rate_limited_events += 1
                with log_path.open("a", encoding="utf-8") as log_fp:
                    log_fp.write(
                        f"[WARN] benchmark={benchmark} idx={idx} attempt={attempt} "
                        f"rate_limited={is_rate} error={err_msg}\n"
                    )
                    log_fp.flush()
                await asyncio.sleep(min(20 * attempt, 180))
        else:
            raise RuntimeError(f"Failed after retries on {benchmark} idx={idx}") from last_error

        answer_text = _extract_answer_text(raw_answer_obj)
        pred = gsm_get_predict(answer_text)
        is_solved = _is_math_correct(pred, true_answer)
        return {
            "idx": idx,
            "task": task,
            "true_answer": true_answer,
            "raw_answer": answer_text,
            "pred_answer": pred,
            "solved": bool(is_solved),
            "attempts_used": attempts_used,
        }

    with log_path.open("w", encoding="utf-8") as _, answers_path.open("w", encoding="utf-8") as out_fp:
        for start in range(0, total, max(1, concurrency)):
            batch = list(enumerate(records[start : start + max(1, concurrency)], start=start))
            batch_results = await asyncio.gather(*(solve_one(i, rec) for i, rec in batch))
            for entry in batch_results:
                solved += int(entry["solved"])
                idx = int(entry["idx"])
                out_fp.write(json.dumps({k: v for k, v in entry.items() if k != "attempts_used"}, ensure_ascii=False) + "\n")
            done = min(start + max(1, concurrency), total)
            if done % 25 == 0 or done == total:
                with log_path.open("a", encoding="utf-8") as log_fp:
                    log_fp.write(
                        f"[INFO] benchmark={benchmark} progress={done}/{total} "
                        f"acc={solved/done:.6f}\n"
                    )
                    log_fp.flush()

    summary = {
        "profile": profile,
        "benchmark": benchmark,
        "math_agent_count": math_agent_count,
        "math_rounds": math_rounds,
        "math_mode": math_mode,
        "math_decision_method": math_decision_method,
        "total": total,
        "solved": solved,
        "accuracy": solved / total if total else 0.0,
        "attempts_total": attempts_total,
        "rate_limited_events": rate_limited_events,
        "raw_dir": str(raw_dir),
        "answers_path": str(answers_path),
        "log_path": str(log_path),
    }
    summary_path = summary_dir / f"{run_ts}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


async def run_humaneval_benchmark(
    *,
    profile: str,
    llm_name: str,
    output_root: Path,
    max_retries: int,
    max_examples: int | None,
    math_agent_count: int,
    code_agent_count: int,
    math_rounds: int,
    code_rounds: int,
    math_mode: str,
    code_mode: str,
    math_decision_method: str,
    code_decision_method: str,
    concurrency: int,
) -> Dict[str, Any]:
    benchmark = "humaneval"
    records = load_rows(benchmark)
    if max_examples is not None:
        records = records[:max_examples]
    run_ts = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    raw_dir = output_root / benchmark / "raw" / run_ts
    summary_dir = output_root / benchmark / "summary"
    raw_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    answers_path = raw_dir / "answers.jsonl"
    log_path = raw_dir / "run.log"

    Time.instance().value = run_ts
    graph = create_graph(
        benchmark=benchmark,
        llm_name=llm_name,
        profile=profile,
        artifact_root=output_root,
        math_agent_count=math_agent_count,
        code_agent_count=code_agent_count,
        math_rounds=math_rounds,
        code_rounds=code_rounds,
        math_mode=math_mode,
        code_mode=code_mode,
        math_decision_method=math_decision_method,
        code_decision_method=code_decision_method,
    )
    executor = PyExecutor()

    total = len(records)
    solved = 0
    attempts_total = 0
    rate_limited_events = 0

    async def solve_one(idx: int, record: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal attempts_total, rate_limited_events
        task = str(record["prompt"])
        test_code = str(record["test"])
        entry_point = str(record["entry_point"])
        task_id = str(record["task_id"])

        last_error = None
        raw_answer_obj: Any = ""
        for attempt in range(1, max_retries + 1):
            attempts_total += 1
            try:
                realized_graph = copy.deepcopy(graph)
                result = await realized_graph.arun({"task": task}, realized_graph.rounds)
                raw_answer_obj = result[0] if isinstance(result, tuple) else result
                break
            except Exception as exc:  # noqa: PERF203
                last_error = exc
                err_msg = str(exc)
                is_rate = bool(RATE_LIMIT_PATTERN.search(err_msg))
                if is_rate:
                    rate_limited_events += 1
                with log_path.open("a", encoding="utf-8") as log_fp:
                    log_fp.write(
                        f"[WARN] benchmark=humaneval idx={idx} attempt={attempt} "
                        f"rate_limited={is_rate} error={err_msg}\n"
                    )
                    log_fp.flush()
                await asyncio.sleep(min(20 * attempt, 180))
        else:
            raise RuntimeError(f"Failed after retries on humaneval idx={idx}") from last_error

        answer_code = _extract_answer_text(raw_answer_obj).lstrip("```python\n").rstrip("\n```")
        is_solved = executor.evaluate(entry_point, answer_code, test_code, timeout=100)
        return {
            "idx": idx,
            "task_id": task_id,
            "entry_point": entry_point,
            "raw_answer": answer_code,
            "solved": bool(is_solved),
        }

    with log_path.open("w", encoding="utf-8") as _, answers_path.open("w", encoding="utf-8") as out_fp:
        for start in range(0, total, max(1, concurrency)):
            batch = list(enumerate(records[start : start + max(1, concurrency)], start=start))
            batch_results = await asyncio.gather(*(solve_one(i, rec) for i, rec in batch))
            for entry in batch_results:
                solved += int(entry["solved"])
                out_fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
            done = min(start + max(1, concurrency), total)
            if done % 10 == 0 or done == total:
                with log_path.open("a", encoding="utf-8") as log_fp:
                    log_fp.write(
                        f"[INFO] benchmark=humaneval progress={done}/{total} "
                        f"pass_at_1={solved/done:.6f}\n"
                    )
                    log_fp.flush()

    summary = {
        "profile": profile,
        "benchmark": benchmark,
        "code_agent_count": code_agent_count,
        "code_rounds": code_rounds,
        "code_mode": code_mode,
        "code_decision_method": code_decision_method,
        "total": total,
        "solved": solved,
        "pass_at_1": solved / total if total else 0.0,
        "attempts_total": attempts_total,
        "rate_limited_events": rate_limited_events,
        "raw_dir": str(raw_dir),
        "answers_path": str(answers_path),
        "log_path": str(log_path),
    }
    summary_path = summary_dir / f"{run_ts}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["agentdropout", "phase3"], required=True)
    parser.add_argument("--benchmark", choices=["gsm8k", "multiarith", "svamp", "humaneval", "all"], default="all")
    parser.add_argument("--run_name", default="fullsuite")
    parser.add_argument("--llm_name", default=os.getenv("LLM_MODEL_NAME", "gpt-5.1-codex-mini"))
    parser.add_argument("--max_retries", type=int, default=12)
    parser.add_argument("--max_examples", type=int, default=None)
    parser.add_argument("--math_agent_count", type=int, default=1)
    parser.add_argument("--code_agent_count", type=int, default=1)
    parser.add_argument("--math_rounds", type=int, default=1)
    parser.add_argument("--code_rounds", type=int, default=1)
    parser.add_argument("--math_mode", choices=["DirectAnswer", "FullConnected"], default="DirectAnswer")
    parser.add_argument("--code_mode", choices=["DirectAnswer", "FullConnected"], default="DirectAnswer")
    parser.add_argument("--math_decision_method", default="FinalDirect")
    parser.add_argument("--code_decision_method", default="FinalWriteCode")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--max_tokens", type=int, default=None)
    args = parser.parse_args()

    LLM.DEFAULT_MAX_TOKENS = int(args.max_tokens) if args.max_tokens is not None else None

    benchmarks = ["gsm8k", "multiarith", "svamp", "humaneval"] if args.benchmark == "all" else [args.benchmark]
    output_root = Path("artifacts/tests") / f"{args.run_name}_{args.profile}"
    output_root.mkdir(parents=True, exist_ok=True)

    all_summaries: List[Dict[str, Any]] = []
    for benchmark in benchmarks:
        if benchmark == "humaneval":
            summary = await run_humaneval_benchmark(
                profile=args.profile,
                llm_name=args.llm_name,
                output_root=output_root,
                max_retries=args.max_retries,
                max_examples=args.max_examples,
                math_agent_count=args.math_agent_count,
                code_agent_count=args.code_agent_count,
                math_rounds=args.math_rounds,
                code_rounds=args.code_rounds,
                math_mode=args.math_mode,
                code_mode=args.code_mode,
                math_decision_method=args.math_decision_method,
                code_decision_method=args.code_decision_method,
                concurrency=args.concurrency,
            )
        else:
            summary = await run_math_benchmark(
                benchmark=benchmark,
                profile=args.profile,
                llm_name=args.llm_name,
                output_root=output_root,
                max_retries=args.max_retries,
                max_examples=args.max_examples,
                math_agent_count=args.math_agent_count,
                code_agent_count=args.code_agent_count,
                math_rounds=args.math_rounds,
                code_rounds=args.code_rounds,
                math_mode=args.math_mode,
                code_mode=args.code_mode,
                math_decision_method=args.math_decision_method,
                code_decision_method=args.code_decision_method,
                concurrency=args.concurrency,
            )
        all_summaries.append(summary)

    agg = {
        "profile": args.profile,
        "run_name": args.run_name,
        "llm_name": args.llm_name,
        "benchmarks": all_summaries,
    }
    ts = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    summary_dir = output_root / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    (summary_dir / f"{ts}.json").write_text(json.dumps(agg, indent=2), encoding="utf-8")
    print(json.dumps(agg, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
