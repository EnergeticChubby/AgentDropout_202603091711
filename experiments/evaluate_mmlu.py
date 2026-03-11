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

async def _run_single_question_with_retry(
        graph: Graph,
        dataset,
        record,
        record_idx: int,
        num_rounds: int,
        max_retries_per_question: int,
        retry_backoff_sec: float,
        ) -> Dict[str, Any]:
    last_error = ""
    for attempt in range(1, max_retries_per_question + 1):
        try:
            realized_graph = copy.deepcopy(graph)
            realized_graph.spatial_logits = graph.spatial_logits
            realized_graph.temporal_logits = graph.temporal_logits
            input_dict = dataset.record_to_input(record)
            raw_answer, log_prob, all_answers = await realized_graph.arun(input_dict, num_rounds, case=True)
            return {
                "ok": True,
                "record_idx": record_idx,
                "record": record,
                "raw_answer": raw_answer,
                "log_prob": log_prob,
                "all_answers": all_answers,
                "attempts": attempt,
                "error": "",
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < max_retries_per_question:
                await asyncio.sleep(retry_backoff_sec * attempt)
    return {
        "ok": False,
        "record_idx": record_idx,
        "record": record,
        "raw_answer": None,
        "log_prob": None,
        "all_answers": None,
        "attempts": max_retries_per_question,
        "error": last_error,
    }

async def evaluate(
        graph:Graph,
        dataset,
        num_rounds:int = 1,
        limit_questions: Optional[int] = None,
        eval_batch_size: int = 4,
        dec: bool = False,
        args=None,
        max_retries_per_question: int = 6,
        retry_backoff_sec: float = 2.0,
        rerun_failed_rounds: int = 3,
        ) -> float:

    print(f"Evaluating AgentDropout on {dataset.__class__.__name__} split {dataset.split}")
    
    graph.spatial_logits.requires_grad_ = False
    graph.temporal_logits.requires_grad_ = False
    
    accuracy = Accuracy()
    def eval_loader(batch_size: int) -> Iterator[List[Any]]:
        records = []
        for i_record, record in enumerate(dataset):
            if limit_questions is not None:
                if i_record >= limit_questions:
                    break
            records.append((i_record, record))
            if len(records) >= batch_size:
                yield records
                records = []
        if len(records) > 0:
            yield records
        return
    data_len = min(len(dataset), limit_questions) if limit_questions is not None else len(dataset)
    num_batches = int(math.ceil(data_len / eval_batch_size))

    data=[]
    current_time = Time.instance().value or time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    result_dir = Path(f"{AgentPrune_ROOT}/result/mmlu")
    result_dir.mkdir(parents=True, exist_ok=True)
    result_file = result_dir / f"{args.domain}_llama3_{current_time}.json"
    unresolved_records: List[Dict[str, Any]] = []

    for i_batch, record_batch in tqdm(enumerate(eval_loader(batch_size=eval_batch_size)), total=num_batches):
        print(80*'-')

        start_ts = time.time()
        answer_tasks = []
        for record_idx, record in record_batch:
            answer_tasks.append(
                asyncio.create_task(
                    _run_single_question_with_retry(
                        graph=graph,
                        dataset=dataset,
                        record=record,
                        record_idx=record_idx,
                        num_rounds=num_rounds,
                        max_retries_per_question=max_retries_per_question,
                        retry_backoff_sec=retry_backoff_sec,
                    )
                )
            )
        question_results = await asyncio.gather(*answer_tasks)
        
        print(f"Batch time {time.time() - start_ts:.3f}")
        for result in question_results:
            record_idx = result["record_idx"]
            record = result["record"]
            if not result["ok"]:
                unresolved_records.append({
                    "record_idx": record_idx,
                    "record": record,
                    "error": result["error"],
                })
                updated_item = {
                    "RecordIndex": int(record_idx),
                    "Question": dataset.record_to_input(record)['task'],
                    "Answer": dataset.record_to_target_answer(record),
                    "All_answers": None,
                    "Response": None,
                    "Status": "failed_after_retries",
                    "Attempts": int(result["attempts"]),
                    "Error": result["error"],
                }
                data.append(updated_item)
                continue

            raw_answer = result["raw_answer"]
            all_answer = result["all_answers"]
            print("Raw answer:", raw_answer)
            answer = dataset.postprocess_answer(raw_answer)
            print("Postprocessed answer:", answer)
            correct_answer = dataset.record_to_target_answer(record)
            print("Correct answer:", correct_answer)
            accuracy.update(answer, correct_answer)
            accuracy.print()
            updated_item = {
                "RecordIndex": int(record_idx),
                "Question": dataset.record_to_input(record)['task'],
                "Answer": correct_answer,
                "All_answers": all_answer,
                "Response": raw_answer,
                "Status": "success",
                "Attempts": int(result["attempts"]),
            }
            data.append(updated_item)
        with open(result_file, 'w',encoding='utf-8') as file:
            json.dump(data, file, indent=4)
        print(f"Cost {Cost.instance().value}")
        print(f"PromptTokens {PromptTokens.instance().value}")
        print(f"CompletionTokens {CompletionTokens.instance().value}")
        # if 'deepseek' in args.llm_name:
        #     print('sleep')
        #     time.sleep(60)
    if len(unresolved_records) > 0:
        print(f"Retrying unresolved questions in sequential rounds: {len(unresolved_records)}")
        for retry_round in range(1, rerun_failed_rounds + 1):
            if len(unresolved_records) == 0:
                break
            print(f"Sequential rerun round {retry_round}, unresolved={len(unresolved_records)}")
            next_unresolved: List[Dict[str, Any]] = []
            for failed_item in unresolved_records:
                record_idx = failed_item["record_idx"]
                record = failed_item["record"]
                result = await _run_single_question_with_retry(
                    graph=graph,
                    dataset=dataset,
                    record=record,
                    record_idx=record_idx,
                    num_rounds=num_rounds,
                    max_retries_per_question=max_retries_per_question,
                    retry_backoff_sec=retry_backoff_sec,
                )
                if not result["ok"]:
                    next_unresolved.append({
                        "record_idx": record_idx,
                        "record": record,
                        "error": result["error"],
                    })
                    data.append({
                        "RecordIndex": int(record_idx),
                        "Question": dataset.record_to_input(record)['task'],
                        "Answer": dataset.record_to_target_answer(record),
                        "All_answers": None,
                        "Response": None,
                        "Status": "failed_after_sequential_rerun",
                        "RerunRound": int(retry_round),
                        "Attempts": int(result["attempts"]),
                        "Error": result["error"],
                    })
                    continue
                raw_answer = result["raw_answer"]
                all_answer = result["all_answers"]
                answer = dataset.postprocess_answer(raw_answer)
                correct_answer = dataset.record_to_target_answer(record)
                accuracy.update(answer, correct_answer)
                data.append({
                    "RecordIndex": int(record_idx),
                    "Question": dataset.record_to_input(record)['task'],
                    "Answer": correct_answer,
                    "All_answers": all_answer,
                    "Response": raw_answer,
                    "Status": "success_after_sequential_rerun",
                    "RerunRound": int(retry_round),
                    "Attempts": int(result["attempts"]),
                })
            unresolved_records = next_unresolved
            with open(result_file, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)

    if len(unresolved_records) > 0:
        unresolved_count = len(unresolved_records)
        print(f"Done with unresolved records: {unresolved_count}")
        raise RuntimeError(
            f"MMLU full-val evaluation incomplete: {unresolved_count} questions still failed after retries."
        )

    accuracy.print()
    print("Done! All full-val questions completed successfully.")

    return accuracy.get()


def dump_eval_results(self, dct: Dict[str, Any]) -> None:
    if self._art_dir_name is not None:
        eval_json_name = os.path.join(self._art_dir_name, "evaluation.json")
        with open(eval_json_name, "w") as f:
            json.dump(dct, f)
