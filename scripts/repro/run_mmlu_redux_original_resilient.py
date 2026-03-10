import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


RATE_LIMIT_PATTERN = re.compile(
    r"(error code:\s*429|rate_limited|rate limit|error 1015)",
    re.IGNORECASE,
)
SCORE_PATTERN = re.compile(r"Score:\s*([0-9]*\.?[0-9]+)")
ACCURACY_PATTERN = re.compile(r"Accuracy:\s*[0-9.]+%\s*\((\d+)/(\d+)\)")


def _build_cmd(args: argparse.Namespace, shard_idx: int, batch_size: int) -> List[str]:
    cmd = [
        "python3",
        "experiments/run_mmlu.py",
        "--dataset_name",
        args.dataset_name,
        "--num_shards",
        str(args.num_shards),
        "--shard_idx",
        str(shard_idx),
        "--limit_questions",
        str(args.limit_questions),
        "--llm_name",
        args.model_name,
        "--eval_split",
        args.eval_split,
        "--mode",
        args.mode,
        "--agent_names",
        *args.agent_names,
        "--agent_nums",
        *[str(v) for v in args.agent_nums],
        "--num_rounds",
        str(args.num_rounds),
        "--batch_size",
        str(batch_size),
        "--decision_method",
        args.decision_method,
    ]
    return cmd


def _parse_attempt_log(
    *,
    shard_idx: int,
    attempt: int,
    batch_size: int,
    return_code: int,
    start_ts: float,
    end_ts: float,
    log_path: Path,
    expected_questions: int,
) -> Dict[str, Any]:
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    score_matches = SCORE_PATTERN.findall(text)
    accuracy_matches = ACCURACY_PATTERN.findall(text)
    rate_limited = bool(RATE_LIMIT_PATTERN.search(text))

    processed = 0
    expected = int(expected_questions)
    if accuracy_matches:
        processed = int(accuracy_matches[-1][1])

    completed = (
        return_code == 0
        and bool(score_matches)
        and (expected <= 0 or processed >= expected)
    )
    score = float(score_matches[-1]) if score_matches else None

    return {
        "shard_idx": shard_idx,
        "attempt": attempt,
        "batch_size": batch_size,
        "return_code": return_code,
        "completed": completed,
        "rate_limited": rate_limited,
        "score": score,
        "processed": processed,
        "expected": expected,
        "duration_sec": end_ts - start_ts,
        "log_path": str(log_path),
    }


def _run_attempt(
    args: argparse.Namespace,
    raw_dir: Path,
    shard_idx: int,
    attempt: int,
    batch_size: int,
    expected_questions: int,
) -> Dict[str, Any]:
    log_path = raw_dir / f"shard_{shard_idx}_attempt{attempt}.log"
    cmd = _build_cmd(args, shard_idx=shard_idx, batch_size=batch_size)

    start_ts = time.time()
    with log_path.open("w", encoding="utf-8") as fp:
        fp.write(f"[COMMAND] {' '.join(cmd)}\n")
        fp.write(f"[START_TS] {start_ts}\n")
        fp.flush()
        proc = subprocess.run(
            cmd,
            stdout=fp,
            stderr=subprocess.STDOUT,
            text=True,
            env=os.environ.copy(),
            check=False,
        )
    end_ts = time.time()

    return _parse_attempt_log(
        shard_idx=shard_idx,
        attempt=attempt,
        batch_size=batch_size,
        return_code=proc.returncode,
        start_ts=start_ts,
        end_ts=end_ts,
        log_path=log_path,
        expected_questions=expected_questions,
    )


def _run_first_pass_parallel(
    args: argparse.Namespace,
    raw_dir: Path,
    expected_by_shard: Dict[int, int],
) -> List[Dict[str, Any]]:
    running: List[Tuple[int, int, int, float, Path, Any, subprocess.Popen]] = []
    for shard_idx in range(args.num_shards):
        attempt = 1
        batch_size = args.batch_size
        cmd = _build_cmd(args, shard_idx=shard_idx, batch_size=batch_size)
        log_path = raw_dir / f"shard_{shard_idx}_attempt{attempt}.log"
        fp = log_path.open("w", encoding="utf-8")
        start_ts = time.time()
        fp.write(f"[COMMAND] {' '.join(cmd)}\n")
        fp.write(f"[START_TS] {start_ts}\n")
        fp.flush()
        proc = subprocess.Popen(
            cmd,
            stdout=fp,
            stderr=subprocess.STDOUT,
            text=True,
            env=os.environ.copy(),
        )
        running.append((shard_idx, attempt, batch_size, start_ts, log_path, fp, proc))

    records: List[Dict[str, Any]] = []
    for shard_idx, attempt, batch_size, start_ts, log_path, fp, proc in running:
        return_code = proc.wait()
        end_ts = time.time()
        fp.close()
        records.append(
            _parse_attempt_log(
                shard_idx=shard_idx,
                attempt=attempt,
                batch_size=batch_size,
                return_code=return_code,
                start_ts=start_ts,
                end_ts=end_ts,
                log_path=log_path,
                expected_questions=int(expected_by_shard.get(shard_idx, 0)),
            )
        )
    return records


def _estimate_expected_questions(args: argparse.Namespace) -> Dict[int, int]:
    expected_by_shard: Dict[int, int] = {i: 0 for i in range(args.num_shards)}
    try:
        from datasets.mmlu_dataset import MMLUDataset

        max_records = None
        if args.limit_questions is not None and args.limit_questions > 0:
            max_records = max(args.limit_questions * args.num_shards, 256)
        for shard_idx in range(args.num_shards):
            dataset = MMLUDataset(
                split=args.eval_split,
                dataset_name=args.dataset_name,
                num_shards=args.num_shards,
                shard_idx=shard_idx,
                max_records=max_records,
            )
            if args.limit_questions is not None and args.limit_questions > 0:
                expected_by_shard[shard_idx] = min(len(dataset), args.limit_questions)
            else:
                expected_by_shard[shard_idx] = len(dataset)
    except Exception:
        pass
    return expected_by_shard


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_md(path: Path, payload: Dict[str, Any]) -> None:
    lines: List[str] = [
        "# Original AgentDropout full run rerun report",
        "",
        f"- run_name: {payload['run_name']}",
        f"- timestamp: {payload['timestamp']}",
        f"- dataset_name: {payload['dataset_name']}",
        f"- model_name: {payload['model_name']}",
        f"- completed_all_shards: {payload['completed_all_shards']}",
        f"- total_attempts: {payload['total_attempts']}",
        f"- rate_limited_attempts: {payload['rate_limited_attempts']}",
        "",
        "## Shard status",
        "",
        "| shard | status | attempts | final_score | final_log |",
        "|---:|---|---:|---:|---|",
    ]

    for item in payload["shards"]:
        lines.append(
            f"| {item['shard_idx']} | {item['status']} | {item['attempts']} | "
            f"{item.get('final_score', 'n/a')} | `{item.get('final_log_path', '')}` |"
        )

    if payload["rate_limited_events"]:
        lines.extend(
            [
                "",
                "## Rate-limit affected attempts",
                "",
                "| shard | attempt | processed | expected | estimated_remaining | log |",
                "|---:|---:|---:|---:|---|---|",
            ]
        )
        for event in payload["rate_limited_events"]:
            remaining = "n/a"
            if event["expected"] > 0:
                start_idx = min(event["processed"] + 1, event["expected"])
                remaining = f"[{start_idx}, {event['expected']}]"
            lines.append(
                f"| {event['shard_idx']} | {event['attempt']} | {event['processed']} | "
                f"{event['expected']} | {remaining} | `{event['log_path']}` |"
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_name", default="agentdropout_original_full")
    parser.add_argument("--dataset_name", default="edinburgh-dawg/mmlu-redux")
    parser.add_argument("--model_name", default=os.environ.get("LLM_MODEL_NAME", "qwen3-8b"))
    parser.add_argument("--num_shards", type=int, default=8)
    parser.add_argument("--limit_questions", type=int, default=10000)
    parser.add_argument("--eval_split", default="test")
    parser.add_argument("--mode", default="FullConnected")
    parser.add_argument("--agent_names", nargs="+", default=["AnalyzeAgent"])
    parser.add_argument("--agent_nums", nargs="+", type=int, default=[5])
    parser.add_argument("--num_rounds", type=int, default=1)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--retry_batch_size", type=int, default=1)
    parser.add_argument("--decision_method", default="FinalRefer")
    parser.add_argument("--max_retry_rounds", type=int, default=12)
    parser.add_argument("--retry_backoff_sec", type=int, default=30)
    parser.add_argument("--max_retry_backoff_sec", type=int, default=300)
    parser.add_argument("--first_pass_parallel", action="store_true")
    args = parser.parse_args()

    timestamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    artifact_root = Path("artifacts/tests") / args.run_name / "mmlu_redux"
    raw_dir = artifact_root / "raw" / timestamp
    summary_dir = artifact_root / "summary"
    raw_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    expected_by_shard = _estimate_expected_questions(args)

    attempt_records: List[Dict[str, Any]] = []
    success_by_shard: Dict[int, Dict[str, Any]] = {}
    rate_limited_events: List[Dict[str, Any]] = []
    attempts_per_shard: Dict[int, int] = {i: 0 for i in range(args.num_shards)}

    pending: List[int] = []
    if args.first_pass_parallel:
        first_pass_records = _run_first_pass_parallel(args=args, raw_dir=raw_dir, expected_by_shard=expected_by_shard)
    else:
        first_pass_records = []
        for shard_idx in range(args.num_shards):
            attempts_per_shard[shard_idx] += 1
            first_pass_records.append(
                _run_attempt(
                    args=args,
                    raw_dir=raw_dir,
                    shard_idx=shard_idx,
                    attempt=attempts_per_shard[shard_idx],
                    batch_size=args.batch_size,
                    expected_questions=int(expected_by_shard.get(shard_idx, 0)),
                )
            )

    for rec in first_pass_records:
        shard_idx = int(rec["shard_idx"])
        attempts_per_shard[shard_idx] = max(attempts_per_shard[shard_idx], int(rec["attempt"]))
        attempt_records.append(rec)
        if rec["completed"]:
            success_by_shard[shard_idx] = rec
            shutil.copyfile(rec["log_path"], raw_dir / f"shard_{shard_idx}.log")
        else:
            pending.append(shard_idx)
            if rec["rate_limited"]:
                rate_limited_events.append(rec)

    retry_round = 0
    while pending and retry_round < args.max_retry_rounds:
        retry_round += 1
        current_pending = list(pending)
        pending = []
        for shard_idx in current_pending:
            sleep_sec = min(
                args.retry_backoff_sec * (2 ** (retry_round - 1)),
                args.max_retry_backoff_sec,
            )
            time.sleep(sleep_sec)
            attempts_per_shard[shard_idx] += 1
            rec = _run_attempt(
                args=args,
                raw_dir=raw_dir,
                shard_idx=shard_idx,
                attempt=attempts_per_shard[shard_idx],
                batch_size=args.retry_batch_size,
                expected_questions=int(expected_by_shard.get(shard_idx, 0)),
            )
            attempt_records.append(rec)
            if rec["completed"]:
                success_by_shard[shard_idx] = rec
                shutil.copyfile(rec["log_path"], raw_dir / f"shard_{shard_idx}.log")
            else:
                pending.append(shard_idx)
                if rec["rate_limited"]:
                    rate_limited_events.append(rec)

    completed_all_shards = len(success_by_shard) == args.num_shards
    if completed_all_shards:
        subprocess.run(
            [
                "python3",
                "scripts/repro/summarize_mmlu_redux.py",
                "--raw_dir",
                str(raw_dir),
                "--summary_json",
                str(summary_dir / f"{timestamp}.json"),
                "--summary_md",
                str(summary_dir / f"{timestamp}.md"),
            ],
            check=True,
        )

    shards_payload: List[Dict[str, Any]] = []
    for shard_idx in range(args.num_shards):
        if shard_idx in success_by_shard:
            s = success_by_shard[shard_idx]
            shards_payload.append(
                {
                    "shard_idx": shard_idx,
                    "status": "completed",
                    "attempts": attempts_per_shard[shard_idx],
                    "final_score": s["score"],
                    "final_log_path": str(raw_dir / f"shard_{shard_idx}.log"),
                }
            )
        else:
            shards_payload.append(
                {
                    "shard_idx": shard_idx,
                    "status": "failed",
                    "attempts": attempts_per_shard[shard_idx],
                }
            )

    rerun_report: Dict[str, Any] = {
        "run_name": args.run_name,
        "timestamp": timestamp,
        "dataset_name": args.dataset_name,
        "model_name": args.model_name,
        "num_shards": args.num_shards,
        "completed_all_shards": completed_all_shards,
        "pending_shards": pending,
        "total_attempts": len(attempt_records),
        "rate_limited_attempts": len(rate_limited_events),
        "shards": shards_payload,
        "rate_limited_events": rate_limited_events,
        "attempt_records": attempt_records,
    }
    _write_json(summary_dir / f"{timestamp}.rerun_report.json", rerun_report)
    _write_md(summary_dir / f"{timestamp}.rerun_report.md", rerun_report)

    if not completed_all_shards:
        raise SystemExit(
            f"Not all shards completed. Pending shards: {pending}. "
            f"See {summary_dir / f'{timestamp}.rerun_report.json'}"
        )

    print(f"[DONE] Completed all shards. Raw logs: {raw_dir}")
    print(f"[DONE] Summary: {summary_dir / f'{timestamp}.json'}")


if __name__ == "__main__":
    main()
