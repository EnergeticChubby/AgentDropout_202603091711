import os
import json
import math
import time
import asyncio
from typing import Union,Literal,Optional,Iterator,List,Any,Dict
from tqdm import tqdm
import copy
import time
from AgentDropout.utils.globals import Time
from pathlib import Path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')

from AgentDropout.utils.const import AgentPrune_ROOT
from AgentDropout.graph.graph import Graph
from experiments.accuracy import Accuracy
from AgentDropout.utils.globals import Cost, PromptTokens, CompletionTokens

def _chunks(records: List[Any], batch_size: int) -> Iterator[List[Any]]:
    for i in range(0, len(records), batch_size):
        yield records[i:i + batch_size]


async def _run_single_record(graph: Graph, dataset, record: Any, num_rounds: int):
    realized_graph = copy.deepcopy(graph)
    realized_graph.spatial_logits = graph.spatial_logits
    realized_graph.temporal_logits = graph.temporal_logits
    input_dict = dataset.record_to_input(record)
    return await realized_graph.arun(input_dict, num_rounds, case=True)


async def evaluate(
        graph:Graph,
        dataset,
        num_rounds:int = 1,
        limit_questions: Optional[int] = None,
        eval_batch_size: int = 4,
        dec: bool = False,
        args=None,
        ) -> float:

    print(f"Evaluating AgentDropout on {dataset.__class__.__name__} split {dataset.split}")
    
    graph.spatial_logits.requires_grad_ = False
    graph.temporal_logits.requires_grad_ = False
    
    accuracy = Accuracy()
    records_with_idx: List[Any] = []
    for i_record, record in enumerate(dataset):
        if limit_questions is not None and i_record >= limit_questions:
            break
        records_with_idx.append((i_record, record))

    data_len = len(records_with_idx)
    num_batches = int(math.ceil(data_len / eval_batch_size)) if data_len > 0 else 0

    data=[]
    failure_events: List[Dict[str, Any]] = []
    resolved_failures: List[Dict[str, Any]] = []
    current_time = Time.instance().value or time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    result_dir = Path(f"{AgentPrune_ROOT}/result/mmlu")
    result_dir.mkdir(parents=True, exist_ok=True)
    result_file = result_dir / f"{args.domain}_llama3_{current_time}.json"
    failures_file = result_dir / f"{args.domain}_llama3_{current_time}_retry_failures.json"

    max_retry_rounds = getattr(args, "max_retry_rounds", 5)
    retry_delay = getattr(args, "retry_delay", 2.0)
    retry_batch_size = max(1, int(getattr(args, "retry_batch_size", 1)))
    allow_incomplete_eval = getattr(args, "allow_incomplete_eval", False)

    pending_records = records_with_idx
    for retry_round in range(max_retry_rounds + 1):
        if len(pending_records) == 0:
            break

        is_retry_round = retry_round > 0
        current_batch_size = retry_batch_size if is_retry_round else eval_batch_size
        current_num_batches = int(math.ceil(len(pending_records) / current_batch_size))
        phase_name = "retry" if is_retry_round else "initial"
        print(f"Starting {phase_name} evaluation round {retry_round} with {len(pending_records)} questions")

        next_pending: List[Any] = []
        for record_batch in tqdm(_chunks(pending_records, current_batch_size), total=current_num_batches):
            print(80*'-')
            start_ts = time.time()
            answer_tasks = [
                asyncio.create_task(_run_single_record(graph, dataset, record, num_rounds))
                for _, record in record_batch
            ]
            raw_results = await asyncio.gather(*answer_tasks, return_exceptions=True)
            print(f"Batch time {time.time() - start_ts:.3f}")

            for (question_idx, record), result in zip(record_batch, raw_results):
                if isinstance(result, Exception):
                    err_msg = str(result)
                    event = {
                        "question_index": question_idx,
                        "retry_round": retry_round,
                        "error": err_msg,
                    }
                    failure_events.append(event)
                    next_pending.append((question_idx, record))
                    print(f"[WARN] Evaluation failed at question {question_idx} (round={retry_round}): {err_msg}")
                    continue

                raw_answer, log_prob, all_answer = result
                answer = dataset.postprocess_answer(raw_answer)
                correct_answer = dataset.record_to_target_answer(record)
                accuracy.update(answer, correct_answer)
                accuracy.print()

                updated_item = {
                    "QuestionIndex": question_idx,
                    "Question": dataset.record_to_input(record)['task'],
                    "Answer": correct_answer,
                    "All_answers": all_answer,
                    "Response": raw_answer,
                    "RetryRound": retry_round,
                }
                data.append(updated_item)

                if is_retry_round:
                    resolved_failures.append({
                        "question_index": question_idx,
                        "resolved_in_round": retry_round,
                    })

            with open(result_file, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
            with open(failures_file, 'w', encoding='utf-8') as file:
                json.dump(
                    {
                        "failure_events": failure_events,
                        "resolved_failures": resolved_failures,
                        "remaining_failed_questions": [idx for idx, _ in next_pending],
                    },
                    file,
                    indent=4,
                )
            print(f"Cost {Cost.instance().value}")
            print(f"PromptTokens {PromptTokens.instance().value}")
            print(f"CompletionTokens {CompletionTokens.instance().value}")

        pending_records = next_pending
        if len(pending_records) > 0 and retry_round < max_retry_rounds and retry_delay > 0:
            print(f"[INFO] Sleeping {retry_delay}s before next retry round for {len(pending_records)} failed questions.")
            await asyncio.sleep(retry_delay)

    if len(pending_records) > 0:
        remaining_idxs = [idx for idx, _ in pending_records]
        msg = f"Evaluation incomplete after retries. Remaining failed questions: {remaining_idxs}"
        print(f"[ERROR] {msg}")
        if not allow_incomplete_eval:
            raise RuntimeError(msg)
    accuracy.print()
    print("Done!")

    return accuracy.get() if accuracy._num_total > 0 else 0.0


def dump_eval_results(self, dct: Dict[str, Any]) -> None:
    if self._art_dir_name is not None:
        eval_json_name = os.path.join(self._art_dir_name, "evaluation.json")
        with open(eval_json_name, "w") as f:
            json.dump(dct, f)
