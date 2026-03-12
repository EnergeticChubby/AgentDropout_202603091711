import sys
import os
import argparse
import yaml
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
import torch
import torch.nn.functional as F
import copy
from typing import List,Union,Literal
import random
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
sys.stdout.reconfigure(encoding='utf-8')

from AgentDropout.utils.const import AgentPrune_ROOT
from AgentDropout.graph.graph import Graph
from AgentDropout.tools.reader.readers import JSONReader, JSONLReader
from AgentDropout.utils.globals import Time
from AgentDropout.utils.globals import Cost, PromptTokens, CompletionTokens
from AgentDropout.utils.utils import nuclear_norm,frobenius_norm
from datasets.gsm8k_dataset import svamp_data_process,gsm_get_predict, gsm_data_process,multiarith_data_process
from datasets.aqua_dataset import aqua_data_process,aqua_get_predict
from AgentDropout.utils.globals import PromptTokens, CompletionTokens
from AgentDropout.agents.agent_registry import AgentRegistry


def _majority(values: List[str]) -> str:
    if not values:
        return ""
    stats = {}
    for value in values:
        stats[value] = stats.get(value, 0) + 1
    return max(stats.items(), key=lambda x: x[1])[0]


def _flatten_round_answers(round_answers: dict) -> List[str]:
    outputs: List[str] = []
    for _, raw in (round_answers or {}).items():
        if isinstance(raw, list):
            outputs.extend([str(x) for x in raw])
        else:
            outputs.append(str(raw))
    return outputs


def _round_numeric_answers(round_answers: dict) -> List[str]:
    outputs = _flatten_round_answers(round_answers)
    return [gsm_get_predict(output) for output in outputs if output]


def classify_svamp_phase(
    is_correct: bool,
    final_numeric_answer: str,
    true_answer: str,
    all_round_answers: List[dict],
) -> str:
    if not all_round_answers:
        return "unresolved_conflict"

    round1 = _round_numeric_answers(all_round_answers[0]) if len(all_round_answers) >= 1 else []
    round2 = _round_numeric_answers(all_round_answers[1]) if len(all_round_answers) >= 2 else []

    round1_major = _majority(round1)
    round2_major = _majority(round2)
    round1_unique = len(set(round1)) if round1 else 0
    round2_unique = len(set(round2)) if round2 else 0

    if is_correct:
        if round1_major and round1_major != str(true_answer) and round2_major == str(true_answer):
            return "constructive_correction"
        if round2_unique <= max(1, round1_unique):
            return "ready_to_finalize"
        return "constructive_correction"

    if round2_major and round2_major == str(final_numeric_answer) and round2_unique <= 1:
        return "wrong_consensus_lock"

    round1_text = " ".join(_flatten_round_answers(all_round_answers[0])) if len(all_round_answers) >= 1 else ""
    round2_text = " ".join(_flatten_round_answers(all_round_answers[1])) if len(all_round_answers) >= 2 else ""
    if round1_text and round2_text and round1_text.strip() == round2_text.strip():
        return "redundant_paraphrase"

    return "unresolved_conflict"


def compute_phase_metrics(
    all_round_answers: List[dict],
    is_correct: bool,
    predict_answer: str,
    true_answer: str,
) -> dict:
    round1 = _round_numeric_answers(all_round_answers[0]) if len(all_round_answers) >= 1 else []
    round2 = _round_numeric_answers(all_round_answers[1]) if len(all_round_answers) >= 2 else []
    round1_major = _majority(round1)
    round2_major = _majority(round2)
    round1_unique = len(set(round1)) if round1 else 0
    round2_unique = len(set(round2)) if round2 else 0

    correction_gain = 1.0 if (round1_major and round1_major != str(true_answer) and str(predict_answer) == str(true_answer)) else 0.0
    wrong_consensus = 1.0 if (not is_correct and round2_major and round2_major == str(predict_answer) and round2_unique <= 1) else 0.0
    conflict_unresolved = 1.0 if (not is_correct and round2_unique > 1) else 0.0
    redundancy = 1.0 if (round1 and round2 and round1_unique == 1 and round2_unique == 1 and round1_major == round2_major) else 0.0
    return {
        "correction_gain": correction_gain,
        "wrong_consensus": wrong_consensus,
        "conflict_unresolved": conflict_unresolved,
        "redundancy": redundancy,
    }


def phase_aware_utility(
    is_correct: bool,
    phase_metrics: dict,
    token_cost: float,
    lambda_redundancy: float = 0.2,
    lambda_wrong_consensus: float = 0.4,
    lambda_conflict_unresolved: float = 0.2,
    lambda_token: float = 0.02,
    lambda_correction_gain: float = 0.3,
) -> float:
    acc = 1.0 if is_correct else 0.0
    utility = (
        acc
        - lambda_redundancy * phase_metrics.get("redundancy", 0.0)
        - lambda_wrong_consensus * phase_metrics.get("wrong_consensus", 0.0)
        - lambda_conflict_unresolved * phase_metrics.get("conflict_unresolved", 0.0)
        - lambda_token * token_cost
        + lambda_correction_gain * phase_metrics.get("correction_gain", 0.0)
    )
    return float(utility)


def load_svamp_splits(args):
    if args.use_split_data:
        split_dir = Path(args.split_dir)
        test_path = split_dir / "test.json"
        graph_train_path = split_dir / f"graph_train_{args.graph_train_size}.json"
        train_fallback = split_dir / "train.json"
        train_path = graph_train_path if graph_train_path.exists() else train_fallback
        if not test_path.exists():
            raise FileNotFoundError(
                f"SVAMP split test file missing: {test_path}. Run experiments/svamp_split.py first."
            )
        if not train_path.exists():
            raise FileNotFoundError(
                f"SVAMP split train file missing: {train_path}. Run experiments/svamp_split.py first."
            )
        split_summary_path = split_dir / "split_summary.json"
        if split_summary_path.exists():
            split_summary = JSONReader.parse_file(str(split_summary_path))
            print(f"[SVAMP SPLIT SUMMARY] {json.dumps(split_summary)}")
        else:
            print(f"[SVAMP SPLIT SUMMARY] missing summary at {split_summary_path}")
        dataset_path = test_path
    else:
        dataset_path = Path(args.dataset_json)
        train_path = Path(args.train_json) if args.train_json else Path("datasets/SVAMP/train.json")
        if not dataset_path.exists():
            raise FileNotFoundError(f"SVAMP test file missing: {dataset_path}")
        if not train_path.exists():
            raise FileNotFoundError(f"SVAMP train file missing: {train_path}")

    dataset = JSONReader.parse_file(str(dataset_path))
    train_dataset = JSONReader.parse_file(str(train_path))
    dataset = svamp_data_process(dataset)
    train_dataset = svamp_data_process(train_dataset)

    if args.require_svamp:
        if "svamp" not in str(dataset_path).lower():
            raise ValueError(f"Dataset path must point to SVAMP, got: {dataset_path}")
        if not dataset or "task" not in dataset[0] or "answer" not in dataset[0]:
            raise ValueError("Loaded SVAMP dataset format is invalid after svamp_data_process.")

    print(f"[SVAMP CHECK] dataset_path={dataset_path}")
    print(f"[SVAMP CHECK] train_path={train_path}")
    print(f"[SVAMP CHECK] preprocessor=svamp_data_process")
    print(f"[SVAMP CHECK] dataset_size={len(dataset)} train_size={len(train_dataset)}")

    return dataset, train_dataset

def load_result(result_file):
    if not result_file.exists():
        with open(result_file, 'w',encoding='utf-8') as file:
            json.dump([], file)

    with open(result_file, 'r',encoding='utf-8') as file:
        data = json.load(file)
    return data


def write_phase_summary(result_file: Path, args) -> None:
    data = load_result(result_file)
    if not data:
        return
    phase_distribution = {}
    wrong_consensus = 0
    redundancy = 0
    for item in data:
        phase = item.get("PhaseLabel", "unknown")
        phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
        if phase == "wrong_consensus_lock":
            wrong_consensus += 1
        if phase == "redundant_paraphrase":
            redundancy += 1
    final_accuracy = float(data[-1].get("Accuracy", 0.0))
    total = len(data)
    summary = {
        "phase": args.phase_label,
        "benchmark": "svamp",
        "branch_tag": args.branch_tag,
        "model": args.llm_name,
        "final_accuracy": final_accuracy,
        "num_samples": total,
        "phase_distribution": phase_distribution,
        "wrong_consensus_rate": (wrong_consensus / total) if total else 0.0,
        "redundancy_rate": (redundancy / total) if total else 0.0,
        "prompt_tokens_total": PromptTokens.instance().value,
        "completion_tokens_total": CompletionTokens.instance().value,
    }
    summary_file = result_file.parent / f"{args.phase_label}_svamp_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[SVAMP SUMMARY] {json.dumps(summary, ensure_ascii=False)}")

def dataloader(data_list, batch_size, i_batch):
    return data_list[i_batch*batch_size:i_batch*batch_size + batch_size]

def load_config(config_path):
    with open(config_path, 'r',encoding='utf-8') as file:
        return yaml.safe_load(file)
    
def parse_args():
    parser = argparse.ArgumentParser(description="CCF-AgentDropout experiments on SVAMP")
    parser.add_argument("--dataset_json", type=str, default="datasets/SVAMP/test.json")
    parser.add_argument("--train_json", type=str, default="")
    parser.add_argument("--split_dir", type=str, default="data/svamp/split_seed42")
    parser.add_argument("--use_split_data", action="store_true")
    parser.add_argument("--require_svamp", action="store_true")
    parser.add_argument("--graph_train_size", type=int, default=40)
    parser.add_argument("--graph_val_size", type=int, default=40)
    parser.add_argument("--split_seed", type=int, default=42)
    parser.add_argument("--result_file", type=str, default=None)
    parser.add_argument("--llm_name", type=str, default="MiniMax-M2.5")
    parser.add_argument("--base_url", type=str, default="https://gpt-agent.cc/v1")
    parser.add_argument("--api_key", type=str, default="")
    parser.add_argument("--branch_tag", type=str, default="AdamMartinez6793-v3")
    parser.add_argument("--phase_label", type=str, default="phase0")
    parser.add_argument('--mode', type=str, default='FullConnected',
                        choices=['DirectAnswer', 'FullConnected', 'Random', 'Chain','Debate','Layered','Star'],
                        help="Mode of operation. Default is 'FullConnected'.")
    parser.add_argument('--lr', type=float, default=0.1,help="learning rate")
    parser.add_argument('--delta', type=float, default=0.1, help="noise level")
    parser.add_argument('--batch_size', type=int, default=40,help="batch size")
    parser.add_argument('--imp_per_iterations', type=int, default=1, help="Prune every few iterations. Default 1.")
    parser.add_argument('--num_rounds',type=int,default=2,help="Number of optimization/inference rounds for one query")
    parser.add_argument('--pruning_rate', type=float, default=0.10,help="The Rate of Pruning. Default 0.10.")
    parser.add_argument('--num_iterations', type=int, default=2,help="The num of training iterations.")
    parser.add_argument('--domain', type=str, default="svamp",help="Domain (the same as dataset name), default 'svamp'")
    parser.add_argument('--agent_names', nargs='+', type=str, default=['MathSolver'],
                        help='Specify agent names as a list of strings')
    parser.add_argument('--agent_nums', nargs='+', type=int, default=[5],
                        help='Specify the number of agents for each name in agent_names')
    parser.add_argument('--decision_method', type=str, default='FinalRefer',
                        help='The decison method of the agentprune')
    parser.add_argument('--optimized_spatial',action='store_true')
    parser.add_argument('--optimized_temporal',action='store_true')
    parser.add_argument('--diff',action='store_true')
    parser.add_argument('--dec',action='store_true')
    parser.add_argument('--cot',action='store_true')
    parser.add_argument('--node_degree_weight', type=float, default=1.0)
    parser.add_argument('--node_correction_weight', type=float, default=1.0)
    parser.add_argument('--node_redundancy_weight', type=float, default=1.0)
    parser.add_argument('--node_wrong_consensus_weight', type=float, default=1.0)
    parser.add_argument('--edge_risk_weight', type=float, default=0.2)
    parser.add_argument('--edge_progress_weight', type=float, default=0.2)
    parser.add_argument(
        "--utility_mode",
        type=str,
        default="phase_aware",
        choices=["phase_aware", "original"],
        help="Use phase-aware utility (default) or original 0/1 solved utility during dec training.",
    )
    args = parser.parse_args()
    result_path = AgentPrune_ROOT / "result"
    os.makedirs(result_path, exist_ok=True)
    if len(args.agent_names) != len(args.agent_nums):
        parser.error("The number of agent names must match the number of agent counts.")

    if args.base_url:
        os.environ["MINIMAX_BASE_URL"] = args.base_url
        os.environ["MINE_BASE_URL"] = args.base_url
    if args.api_key:
        os.environ["MINIMAX_API_KEY"] = args.api_key
        os.environ["MINE_API_KEYS"] = args.api_key

    return args

async def main():
    args = parse_args()
    args.require_svamp = True
    result_file = None
    dataset, train_dataset = load_svamp_splits(args)

    current_time = Time.instance().value or time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    Time.instance().value = current_time
    result_dir = Path(f"{AgentPrune_ROOT}/result/SVAMP/{args.branch_tag}/{args.phase_label}")
    result_dir.mkdir(parents=True, exist_ok=True)
    model_tag = args.llm_name.replace("/", "_")
    result_file = result_dir / f"{args.domain}_{model_tag}_{current_time}.json"
    print(f"[SVAMP CHECK] result_dir={result_dir}")
    
    agent_names = [name for name,num in zip(args.agent_names,args.agent_nums) for _ in range(num)]
    decision_method = args.decision_method
    kwargs = get_kwargs(args.mode,len(agent_names))

    graph = Graph(domain=args.domain,
                    llm_name=args.llm_name,
                    agent_names=agent_names,
                    decision_method=decision_method,
                    optimized_spatial=args.optimized_spatial,
                    optimized_temporal=args.optimized_temporal,
                    rounds=args.num_rounds,
                    diff=args.diff,
                    dec=args.dec,
                    **kwargs)
    graph.set_phase_aware_weights(
        node_degree=args.node_degree_weight,
        node_correction_gain=args.node_correction_weight,
        node_redundancy=args.node_redundancy_weight,
        node_wrong_consensus_risk=args.node_wrong_consensus_weight,
        edge_risk=args.edge_risk_weight,
        edge_progress=args.edge_progress_weight,
    )
    
    node_stage_updates = 0
    edge_stage_updates = 0

    if args.dec:
        total_solved, total_executed = (0, 0)
        if not graph.diff:
            optimizer = torch.optim.Adam([graph.spatial_logits_1,graph.temporal_logits_1], lr=args.lr)
        else:
            optimizer = torch.optim.Adam(list(graph.spatial_logits_1.parameters()) + list(graph.temporal_logits_1.parameters()),lr=args.lr)
        for i_batch in range(args.num_iterations):
            print(f"Train batch {i_batch}",80*'-')
            start_ts = time.time()
            answer_log_probs = []
            answers = []
            add_losses = []
            
            current_batch = dataloader(train_dataset,20,i_batch)
            if not current_batch:
                print("No more data available.")
                break
            node_stage_updates += 1
            
            for i_record, record in enumerate(current_batch):
                realized_graph = copy.deepcopy(graph)
                realized_graph.spatial_logits_1 = graph.spatial_logits_1
                realized_graph.temporal_logits_1 = graph.temporal_logits_1
                
                if not graph.diff:
                    spatial_matrix_train = realized_graph.spatial_logits_1.reshape((sum(args.agent_nums),sum(args.agent_nums)))
                    temporal_matrix_train = realized_graph.temporal_logits_1.reshape((sum(args.agent_nums),sum(args.agent_nums)))
                else:
                    spatial_matrix_train = [param.reshape((sum(args.agent_nums), sum(args.agent_nums))) for param in realized_graph.spatial_logits_1]
                    temporal_matrix_train = [param.reshape((sum(args.agent_nums), sum(args.agent_nums))) for param in realized_graph.temporal_logits_1]
                spatial_matrix_fixed = torch.tensor(kwargs["fixed_spatial_masks"],dtype=torch.float32).reshape((len(agent_names),len(agent_names)))
                temporal_matrix_fixed = torch.tensor(kwargs["fixed_temporal_masks"],dtype=torch.float32).reshape((len(agent_names),len(agent_names)))
                if not graph.diff:
                    loss_s = nuclear_norm(spatial_matrix_train)
                    loss_t = nuclear_norm(temporal_matrix_train)
                    frob_loss_s = frobenius_norm(spatial_matrix_fixed, spatial_matrix_train)
                    frob_loss_t = frobenius_norm(temporal_matrix_fixed, temporal_matrix_train)
                else:
                    # loss_s = sum(nuclear_norm(matrix) for matrix in spatial_matrix_train)
                    # loss_t = sum(nuclear_norm(matrix) for matrix in temporal_matrix_train)
                    # frob_loss_s = sum(frobenius_norm(spatial_matrix_fixed, matrix) for matrix in spatial_matrix_train)
                    # frob_loss_t = sum(frobenius_norm(temporal_matrix_fixed, matrix) for matrix in temporal_matrix_train)
                    loss_s = torch.mean(torch.stack([nuclear_norm(matrix) for matrix in spatial_matrix_train]))
                    loss_t = torch.mean(torch.stack([nuclear_norm(matrix) for matrix in temporal_matrix_train]))
                    frob_loss_s = torch.mean(torch.stack([frobenius_norm(spatial_matrix_fixed, matrix) for matrix in spatial_matrix_train]))
                    frob_loss_t = torch.mean(torch.stack([frobenius_norm(temporal_matrix_fixed, matrix) for matrix in temporal_matrix_train]))
                add_loss = loss_s + loss_t + F.relu(frob_loss_s - args.delta) + F.relu(frob_loss_t - args.delta)
                task = record["task"]
                step = record["step"]
                answer = record["answer"]
                answers.append(answer)
                input_dict = {"task": task}
                answer_log_probs.append(
                    asyncio.create_task(
                        realized_graph.arun(
                            input_dict,
                            args.num_rounds,
                            skip=True,
                            collect_telemetry=True,
                        )
                    )
                )
                add_losses.append(add_loss)
                
            raw_results = await asyncio.gather(*answer_log_probs)
            raw_answers, log_probs, batch_telemetry = zip(*raw_results)
            loss_list: List[torch.Tensor] = []
            utilities: List[float] = []
            node_feedback_acc = {}
            edge_feedback_acc = {}
            data = load_result(result_file)
            
            for task, answer, log_prob, add_loss, true_answer, telemetry in zip(
                current_batch, raw_answers, log_probs, add_losses, answers, batch_telemetry
            ):
                predict_answer = gsm_get_predict(answer[0])
                is_solved = float(predict_answer)==float(true_answer)
                total_solved = total_solved + is_solved
                total_executed = total_executed + 1
                accuracy = total_solved/ total_executed
                if args.utility_mode == "original":
                    utility = 1.0 if is_solved else 0.0
                else:
                    utility = phase_aware_utility(
                        bool(is_solved),
                        phase_metrics={
                            "correction_gain": 1.0 if is_solved else 0.0,
                            "wrong_consensus": 0.0 if is_solved else 1.0,
                            "conflict_unresolved": 0.0,
                            "redundancy": 0.0,
                        },
                        token_cost=float(PromptTokens.instance().value + CompletionTokens.instance().value)
                        / max(1, total_executed),
                    )
                utilities.append(utility)
                single_loss = -log_prob * utility
                if not isinstance(single_loss, torch.Tensor):
                    single_loss = torch.tensor(float(single_loss), dtype=torch.float32)
                if isinstance(add_loss, torch.Tensor):
                    loss_item = single_loss + add_loss
                else:
                    loss_item = single_loss + torch.tensor(float(add_loss), dtype=single_loss.dtype)
                loss_list.append(loss_item)
                for round_idx, round_node_stats in enumerate(telemetry.get("round_node_stats", [])):
                    if round_idx not in node_feedback_acc:
                        node_feedback_acc[round_idx] = {}
                    for node_idx, node_stat in round_node_stats.items():
                        node_idx_int = int(node_idx)
                        if node_idx_int not in node_feedback_acc[round_idx]:
                            node_feedback_acc[round_idx][node_idx_int] = {
                                "correction_gain": 0.0,
                                "redundancy": 0.0,
                                "wrong_consensus_risk": 0.0,
                                "count": 0.0,
                            }
                        fb = node_feedback_acc[round_idx][node_idx_int]
                        fb["correction_gain"] += 1.0 if is_solved else 0.0
                        fb["wrong_consensus_risk"] += 0.0 if is_solved else 1.0
                        fb["redundancy"] += 1.0 if float(node_stat.get("output_lines", 0.0)) <= 1.0 else 0.0
                        fb["count"] += 1.0
                for round_idx, round_edge_stats in enumerate(telemetry.get("round_edge_stats", [])):
                    if round_idx not in edge_feedback_acc:
                        edge_feedback_acc[round_idx] = {}
                    for edge_idx, edge_stat in round_edge_stats.items():
                        edge_idx_int = int(edge_idx)
                        if edge_idx_int not in edge_feedback_acc[round_idx]:
                            edge_feedback_acc[round_idx][edge_idx_int] = {
                                "risk": 0.0,
                                "progress": 0.0,
                                "count": 0.0,
                            }
                        fb = edge_feedback_acc[round_idx][edge_idx_int]
                        fb["risk"] += float(edge_stat.get("risk", 0.0))
                        fb["progress"] += float(edge_stat.get("progress", 0.0))
                        fb["count"] += 1.0
                updated_item = {
                    "Question": task,
                    "Answer": true_answer,
                    "Step": task.get("step", ""),
                    "Response": answer,
                    "Attempt answer": predict_answer,
                    "Solved": is_solved,
                    "Total solved": total_solved,
                    "Total executed": total_executed,
                    "Accuracy": accuracy
                }
                # data.append(updated_item)
                print(f"##########Final Log:{json.dumps(updated_item)}")
            for round_idx, node_stats in node_feedback_acc.items():
                normalized_node_stats = {}
                for node_idx, payload in node_stats.items():
                    cnt = payload.pop("count", 1.0)
                    normalized_node_stats[node_idx] = {
                        key: (value / cnt) for key, value in payload.items()
                    }
                normalized_edge_stats = {}
                round_edges = edge_feedback_acc.get(round_idx, {})
                for edge_idx, payload in round_edges.items():
                    cnt = payload.pop("count", 1.0)
                    normalized_edge_stats[edge_idx] = {
                        key: (value / cnt) for key, value in payload.items()
                    }
                graph.register_phase_feedback(
                    round_idx=round_idx,
                    node_stats=normalized_node_stats,
                    edge_stats=normalized_edge_stats,
                )
            with open(result_file, 'w',encoding='utf-8') as file:
                json.dump(data, file, indent=4)
            
            total_loss = torch.mean(torch.stack(loss_list))
            optimizer.zero_grad()
            if total_loss.requires_grad:
                total_loss.backward()
                optimizer.step()
            else:
                print("[WARN] total_loss has no grad_fn; skipping optimizer step for this batch.")
            if not graph.diff:
                spatial_probs = torch.sigmoid(graph.spatial_logits_1)
                temporal_probs = torch.sigmoid(graph.temporal_logits_1)
            else:
                spatial_probs = [torch.sigmoid(logit) for logit in graph.spatial_logits_1]
                temporal_probs = [torch.sigmoid(logit) for logit in graph.temporal_logits_1]
            
            print(f"Batch time {time.time() - start_ts:.3f}")
            print(f"Accuracy: {accuracy}")
            print("utilities:", utilities)
            print("loss:", total_loss.item())
            # print("Spatial logits Grad:", graph.spatial_logits.grad)
            # print("Temporal logits Grad:", graph.spatial_logits.grad)
            print("Spatial logits:", graph.spatial_logits_1)
            print("Temporal logits:", graph.temporal_logits_1)
            print("Spatial probs:", spatial_probs)
            print("Temporal probs:", temporal_probs)
            print("Spatial masks:", graph.spatial_masks)
            print("Temporal logits:", graph.temporal_masks)
            
            if (i_batch+1)%args.imp_per_iterations == 0 and i_batch < args.num_iterations and (args.optimized_spatial or args.optimized_temporal):
                if not graph.diff:
                    print("spatial sparsity:",graph.spatial_masks.sum()/graph.spatial_masks.numel())
                    print("temporal sparsity:",graph.temporal_masks.sum()/graph.temporal_masks.numel())
                else:
                    print("spatial sparsity:",graph.spatial_masks[0].sum()/graph.spatial_masks[0].numel())
                    print("temporal sparsity:",graph.temporal_masks[0].sum()/graph.temporal_masks[0].numel())
            print(f"Cost {Cost.instance().value}")
            print(f"PromptTokens {PromptTokens.instance().value}")
            print(f"CompletionTokens {CompletionTokens.instance().value}")
        if args.num_iterations > 0 and node_stage_updates == 0:
            raise RuntimeError("Node-stage updates were zero; expected >0 with dec enabled.")
        graph.update_masks_dec(pruning_rate=args.pruning_rate)
        if not graph.diff:
            spatial_density = float((graph.spatial_masks.sum() / graph.spatial_masks.numel()).item())
            temporal_density = float((graph.temporal_masks.sum() / graph.temporal_masks.numel()).item())
        else:
            spatial_density = float(
                torch.mean(torch.stack([(mask.sum() / mask.numel()).float() for mask in graph.spatial_masks])).item()
            )
            temporal_density = float(
                torch.mean(torch.stack([(mask.sum() / mask.numel()).float() for mask in graph.temporal_masks])).item()
            )
        print(
            f"[NODE DROPOUT] pruning_rate={args.pruning_rate} "
            f"skip_nodes={graph.skip_nodes} spatial_density={spatial_density:.4f} "
            f"temporal_density={temporal_density:.4f}"
        )

    if not graph.diff:
        optimizer = torch.optim.Adam([graph.spatial_logits,graph.temporal_logits], lr=args.lr)    
    else:
        optimizer = torch.optim.Adam(list(graph.spatial_logits.parameters()) + list(graph.temporal_logits.parameters()),lr=args.lr)  
    
    num_batches = int(len(dataset)/args.batch_size)
    total_solved, total_executed = (0, 0)
    
    
    if args.optimized_temporal or args.optimized_spatial:
        # graph.optimized_spatial=True
        # graph.optimized_temporal=True
        for i_batch in range(args.num_iterations):
            print(f"Train batch {i_batch}",80*'-')
            start_ts = time.time()
            answer_log_probs = []
            answers = []
            add_losses = []
            
            current_batch = dataloader(train_dataset,args.batch_size,i_batch)
            if not current_batch:
                print("No more data available.")
                break
            edge_stage_updates += 1
            
            for i_record, record in enumerate(current_batch):
                realized_graph = copy.deepcopy(graph)
                realized_graph.spatial_logits = graph.spatial_logits
                realized_graph.temporal_logits = graph.temporal_logits
                
                if not graph.diff:
                    spatial_matrix_train = realized_graph.spatial_logits.reshape((sum(args.agent_nums),sum(args.agent_nums)))
                    temporal_matrix_train = realized_graph.temporal_logits.reshape((sum(args.agent_nums),sum(args.agent_nums)))
                else:
                    spatial_matrix_train = [param.reshape((sum(args.agent_nums), sum(args.agent_nums))) for param in realized_graph.spatial_logits]
                    temporal_matrix_train = [param.reshape((sum(args.agent_nums), sum(args.agent_nums))) for param in realized_graph.temporal_logits]
                spatial_matrix_fixed = torch.tensor(kwargs["fixed_spatial_masks"],dtype=torch.float32).reshape((len(agent_names),len(agent_names)))
                temporal_matrix_fixed = torch.tensor(kwargs["fixed_temporal_masks"],dtype=torch.float32).reshape((len(agent_names),len(agent_names)))
                if not graph.diff:
                    loss_s = nuclear_norm(spatial_matrix_train)
                    loss_t = nuclear_norm(temporal_matrix_train)
                    frob_loss_s = frobenius_norm(spatial_matrix_fixed, spatial_matrix_train)
                    frob_loss_t = frobenius_norm(temporal_matrix_fixed, temporal_matrix_train)
                else:
                    # loss_s = sum(nuclear_norm(matrix) for matrix in spatial_matrix_train)
                    # loss_t = sum(nuclear_norm(matrix) for matrix in temporal_matrix_train)
                    # frob_loss_s = sum(frobenius_norm(spatial_matrix_fixed, matrix) for matrix in spatial_matrix_train)
                    # frob_loss_t = sum(frobenius_norm(temporal_matrix_fixed, matrix) for matrix in temporal_matrix_train)
                    loss_s = torch.mean(torch.stack([nuclear_norm(matrix) for matrix in spatial_matrix_train]))
                    loss_t = torch.mean(torch.stack([nuclear_norm(matrix) for matrix in temporal_matrix_train]))
                    frob_loss_s = torch.mean(torch.stack([frobenius_norm(spatial_matrix_fixed, matrix) for matrix in spatial_matrix_train]))
                    frob_loss_t = torch.mean(torch.stack([frobenius_norm(temporal_matrix_fixed, matrix) for matrix in temporal_matrix_train]))
                add_loss = loss_s + loss_t + F.relu(frob_loss_s - args.delta) + F.relu(frob_loss_t - args.delta)
                
                task = record["task"]
                step = record["step"]
                answer = record["answer"]
                answers.append(answer)
                input_dict = {"task": task}
                answer_log_probs.append(asyncio.create_task(realized_graph.arun(input_dict,args.num_rounds)))
                add_losses.append(add_loss)
                
            raw_results = await asyncio.gather(*answer_log_probs)
            raw_answers, log_probs = zip(*raw_results)
            loss_list: List[torch.Tensor] = []
            task_term_list: List[torch.Tensor] = []
            sparsity_term_list: List[torch.Tensor] = []
            utilities: List[float] = []
            data = load_result(result_file)
            
            for task, answer, log_prob, add_loss, true_answer in zip(current_batch, raw_answers, log_probs, add_losses, answers):
                predict_answer = gsm_get_predict(answer[0])
                is_solved = float(predict_answer)==float(true_answer)
                total_solved = total_solved + is_solved
                total_executed = total_executed + 1
                accuracy = total_solved/ total_executed
                utility = is_solved
                utilities.append(utility)
                single_loss = -log_prob * utility
                if not isinstance(single_loss, torch.Tensor):
                    single_loss = torch.tensor(float(single_loss), dtype=torch.float32)
                if not isinstance(add_loss, torch.Tensor):
                    add_loss = torch.tensor(float(add_loss), dtype=single_loss.dtype)
                task_term_list.append(single_loss)
                sparsity_term_list.append(add_loss)
                loss_list.append(single_loss+add_loss)
                updated_item = {
                    "Question": task,
                    "Answer": true_answer,
                    "Step": task.get("step", ""),
                    "Response": answer,
                    "Attempt answer": predict_answer,
                    "Solved": is_solved,
                    "Total solved": total_solved,
                    "Total executed": total_executed,
                    "Accuracy": accuracy
                }
                # data.append(updated_item)
                print(f"##########Final Log:{json.dumps(updated_item)}")
            with open(result_file, 'w',encoding='utf-8') as file:
                json.dump(data, file, indent=4)
            
            total_loss = torch.mean(torch.stack(loss_list))
            task_term = torch.mean(torch.stack(task_term_list)) if task_term_list else torch.tensor(0.0)
            sparsity_term = torch.mean(torch.stack(sparsity_term_list)) if sparsity_term_list else torch.tensor(0.0)
            if args.optimized_spatial or args.optimized_temporal:
                optimizer.zero_grad()
                total_loss.backward()
                optimizer.step()
            if not graph.diff:
                spatial_probs = torch.sigmoid(graph.spatial_logits)
                temporal_probs = torch.sigmoid(graph.temporal_logits)
            else:
                spatial_probs = [torch.sigmoid(logit) for logit in graph.spatial_logits]
                temporal_probs = [torch.sigmoid(logit) for logit in graph.temporal_logits]
            
            print(f"Batch time {time.time() - start_ts:.3f}")
            print(f"Accuracy: {accuracy}")
            print("utilities:", utilities)
            print("loss:", total_loss.item())
            print(
                f"[EDGE LOSS TERMS] task_term={float(task_term.item()):.6f} "
                f"sparsity_term={float(sparsity_term.item()):.6f} "
                f"total={float(total_loss.item()):.6f}"
            )
            # print("Spatial logits Grad:", graph.spatial_logits.grad)
            # print("Temporal logits Grad:", graph.spatial_logits.grad)
            print("Spatial logits:", graph.spatial_logits)
            print("Temporal logits:", graph.temporal_logits)
            print("Spatial probs:", spatial_probs)
            print("Temporal probs:", temporal_probs)
            print("Spatial masks:", graph.spatial_masks)
            print("Temporal logits:", graph.temporal_masks)
            
            if (i_batch+1)%2 == 0 and i_batch < 4 and (args.optimized_spatial or args.optimized_temporal):
                if not graph.diff:
                    spatial_masks, temporal_masks = graph.update_masks(args.pruning_rate)
                else:
                    spatial_masks, temporal_masks = graph.update_masks_diff(args.pruning_rate)
                print("spatial masks:",spatial_masks)
                print("temporal masks:",temporal_masks)
                if not graph.diff:
                    print("spatial sparsity:",spatial_masks.sum()/spatial_masks.numel())
                    print("temporal sparsity:",temporal_masks.sum()/temporal_masks.numel())
                else:
                    print("spatial sparsity:",spatial_masks[0].sum()/spatial_masks[0].numel())
                    print("temporal sparsity:",temporal_masks[0].sum()/temporal_masks[0].numel())
            print(f"Cost {Cost.instance().value}")
            print(f"PromptTokens {PromptTokens.instance().value}")
            print(f"CompletionTokens {CompletionTokens.instance().value}")
        if args.num_iterations > 0 and edge_stage_updates == 0:
            raise RuntimeError("Edge-stage updates were zero; expected >0 with optimized flags enabled.")

    print(f"[STAGE UPDATES] node_stage_updates={node_stage_updates} edge_stage_updates={edge_stage_updates}")

    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()
    total_solved, total_executed = (0, 0)

    # graph.clear_spatial_connection()
    # graph.clear_temporal_connection()
    # graph.domain='aqua'
    # graph.nodes = {}
    # print(graph.nodes)
    # graph.agent_names = ['MathSolver_aqua']
    # graph.agent_names = [name for name,num in zip(['MathSolver_aqua'],args.agent_nums) for _ in range(num)]
    # graph.node_kwargs = [{} for _ in graph.agent_names]
    # graph.init_nodes()
    # print(graph.nodes)
    # graph.potential_spatial_edges = []
    # graph.potential_temporal_edges = []
    # graph.init_potential_edges()
    # graph.decision_node = AgentRegistry.get(args.decision_method, **{"domain":'aqua',"llm_name":args.llm_name})

    for i_batch in range(num_batches):
        print(f"Batch {i_batch}",80*'-')
        start_ts = time.time()
        answer_log_probs = []
        answers = []
        add_losses = []
        
        current_batch = dataloader(dataset,args.batch_size,i_batch)
        if current_batch is None:
            print("No more data available.")
            break
        
        print(11111111)
        for i_record, record in enumerate(current_batch):
            realized_graph = copy.deepcopy(graph)
            realized_graph.spatial_logits = graph.spatial_logits
            realized_graph.temporal_logits = graph.temporal_logits
            
            if not graph.diff:
                spatial_matrix_train = realized_graph.spatial_logits.reshape((sum(args.agent_nums),sum(args.agent_nums)))
                temporal_matrix_train = realized_graph.temporal_logits.reshape((sum(args.agent_nums),sum(args.agent_nums)))
            else:
                spatial_matrix_train = [param.reshape((sum(args.agent_nums), sum(args.agent_nums))) for param in realized_graph.spatial_logits]
                temporal_matrix_train = [param.reshape((sum(args.agent_nums), sum(args.agent_nums))) for param in realized_graph.temporal_logits]
            spatial_matrix_fixed = torch.tensor(kwargs["fixed_spatial_masks"],dtype=torch.float32).reshape((len(agent_names),len(agent_names)))
            temporal_matrix_fixed = torch.tensor(kwargs["fixed_temporal_masks"],dtype=torch.float32).reshape((len(agent_names),len(agent_names)))
            if not graph.diff:
                loss_s = nuclear_norm(spatial_matrix_train)
                loss_t = nuclear_norm(temporal_matrix_train)
                frob_loss_s = frobenius_norm(spatial_matrix_fixed, spatial_matrix_train)
                frob_loss_t = frobenius_norm(temporal_matrix_fixed, temporal_matrix_train)
            else:
                # loss_s = sum(nuclear_norm(matrix) for matrix in spatial_matrix_train)
                # loss_t = sum(nuclear_norm(matrix) for matrix in temporal_matrix_train)
                # frob_loss_s = sum(frobenius_norm(spatial_matrix_fixed, matrix) for matrix in spatial_matrix_train)
                # frob_loss_t = sum(frobenius_norm(temporal_matrix_fixed, matrix) for matrix in temporal_matrix_train)
                loss_s = torch.mean(torch.stack([nuclear_norm(matrix) for matrix in spatial_matrix_train]))
                loss_t = torch.mean(torch.stack([nuclear_norm(matrix) for matrix in temporal_matrix_train]))
                frob_loss_s = torch.mean(torch.stack([frobenius_norm(spatial_matrix_fixed, matrix) for matrix in spatial_matrix_train]))
                frob_loss_t = torch.mean(torch.stack([frobenius_norm(temporal_matrix_fixed, matrix) for matrix in temporal_matrix_train]))
            add_loss = loss_s + loss_t + F.relu(frob_loss_s - args.delta) + F.relu(frob_loss_t - args.delta)
            
            task = record["task"]
            step = record["step"]
            answer = record["answer"]
            answers.append(answer)
            input_dict = {"task": task}

            answer_log_probs.append(
                asyncio.create_task(
                    realized_graph.arun(
                        input_dict,
                        args.num_rounds,
                        case=True,
                        collect_telemetry=True,
                    )
                )
            )

            add_losses.append(add_loss)
        
        print(22222222)
        raw_results = await asyncio.gather(*answer_log_probs)
        print(33333333)
        raw_answers, log_probs, all_answers, all_telemetry = zip(*raw_results)
        loss_list: List[torch.Tensor] = []
        utilities: List[float] = []
        data = load_result(result_file)
        
        for task, answer, log_prob, add_loss, true_answer, all_answer, telemetry in zip(
            current_batch,
            raw_answers,
            log_probs,
            add_losses,
            answers,
            all_answers,
            all_telemetry,
        ):
            predict_answer = gsm_get_predict(answer[0])
            is_solved = float(predict_answer)==float(true_answer)
            # predict_answer = aqua_get_predict(answer[0])
            # is_solved = predict_answer==true_answer
            total_solved = total_solved + is_solved
            total_executed = total_executed + 1
            accuracy = total_solved/ total_executed
            phase_metrics = compute_phase_metrics(
                all_round_answers=list(all_answer),
                is_correct=bool(is_solved),
                predict_answer=str(predict_answer),
                true_answer=str(true_answer),
            )
            token_cost = float(PromptTokens.instance().value + CompletionTokens.instance().value)
            utility = phase_aware_utility(bool(is_solved), phase_metrics, token_cost=token_cost / max(1, total_executed))
            utilities.append(utility)
            single_loss = -log_prob * utility
            loss_list.append(single_loss+add_loss)
            phase_label = classify_svamp_phase(
                is_correct=bool(is_solved),
                final_numeric_answer=str(predict_answer),
                true_answer=str(true_answer),
                all_round_answers=list(all_answer),
            )
            updated_item = {
                "Question": task,
                "Answer": true_answer,
                "Step": task.get("step", ""),
                "All_answers": all_answer,
                "Response": answer,
                "Attempt answer": predict_answer,
                "Solved": is_solved,
                "Total solved": total_solved,
                "Total executed": total_executed,
                "Accuracy": accuracy,
                "PhaseLabel": phase_label,
                "Phase": args.phase_label,
                "BranchTag": args.branch_tag,
                "PromptTokens": PromptTokens.instance().value,
                "CompletionTokens": CompletionTokens.instance().value,
                "NodeStats": telemetry.get("round_node_stats", []),
                "EdgeStats": telemetry.get("round_edge_stats", []),
                "PhaseMetrics": phase_metrics,
            }
            data.append(updated_item)
            print(f"##########Final Log:{json.dumps(updated_item)}")
        with open(result_file, 'w',encoding='utf-8') as file:
            json.dump(data, file, indent=4)
        
        # total_loss = torch.mean(torch.stack(loss_list))
        # if args.optimized_spatial or args.optimized_temporal:
        #     optimizer.zero_grad()
        #     total_loss.backward()
        #     optimizer.step()
        # spatial_probs = torch.sigmoid(graph.spatial_logits)
        # temporal_probs = torch.sigmoid(graph.temporal_logits)
        
        print(f"Batch time {time.time() - start_ts:.3f}")
        print(f"Accuracy: {accuracy}")
        print("utilities:", utilities)
        # print("loss:", total_loss.item())
        # print("Spatial logits Grad:", graph.spatial_logits.grad)
        # print("Temporal logits Grad:", graph.spatial_logits.grad)
        # print("Spatial logits:", graph.spatial_logits)
        # print("Temporal logits:", graph.temporal_logits)
        # print("Spatial probs:", spatial_probs)
        # print("Temporal probs:", temporal_probs)
        # print("Spatial masks:", graph.spatial_masks)
        # print("Temporal logits:", graph.temporal_masks)
        
        print(f"Cost {Cost.instance().value}")
        print(f"PromptTokens {PromptTokens.instance().value}")
        print(f"CompletionTokens {CompletionTokens.instance().value}")

    write_phase_summary(result_file, args)


def get_kwargs(mode:Union[Literal['DirectAnswer'],Literal['FullConnected'],Literal['Random'],Literal['Chain'],Literal['Debate'],Literal['Layered'],Literal['Star']]
               ,N:int):
    initial_spatial_probability: float = 0.5
    fixed_spatial_masks:List[List[int]] = None
    initial_temporal_probability: float = 0.5
    fixed_temporal_masks:List[List[int]] = None
    node_kwargs = None
    
    def generate_layered_graph(N,layer_num=2):
        adj_matrix = [[0 for _ in range(N)] for _ in range(N)]
        base_size = N // layer_num
        remainder = N % layer_num
        layers = []
        for i in range(layer_num):
            size = base_size + (1 if i < remainder else 0)
            layers.extend([i] * size)
        # random.shuffle(layers)
        for i in range(N):
            current_layer = layers[i]
            for j in range(N):
                if layers[j] == current_layer + 1:
                    adj_matrix[i][j] = 1
        return adj_matrix
    
    def generate_star_graph(n):
        matrix = [[0] * n for _ in range(n)]
        for i in range(0, n):
            for j in range(i+1,n):
                matrix[i][j] = 1
        return matrix
    
    if mode=='DirectAnswer':
        fixed_spatial_masks = [[0]]
        fixed_temporal_masks = [[0]]
        node_kwargs = [{'role':'Math Solver'}]
    elif mode=='FullConnected':
        fixed_spatial_masks = [[1 if i!=j else 0 for i in range(N)] for j in range(N)]
        fixed_temporal_masks = [[1 for _ in range(N)] for _ in range(N)]
    elif mode=='Random':
        fixed_spatial_masks = [[random.randint(0, 1)  if i!=j else 0 for i in range(N)] for j in range(N)]
        fixed_temporal_masks = [[random.randint(0, 1) for _ in range(N)] for _ in range(N)]
    elif mode=='Chain':
        fixed_spatial_masks = [[1 if i==j+1 else 0 for i in range(N)] for j in range(N)]
        fixed_temporal_masks = [[1 if i==0 and j==N-1 else 0 for i in range(N)] for j in range(N)]
    elif mode == 'Debate':
        fixed_spatial_masks = [[0 for i in range(N)] for j in range(N)]
        fixed_temporal_masks = [[1 for i in range(N)] for j in range(N)]
    elif mode == 'Layered':
        fixed_spatial_masks = generate_layered_graph(N)
        fixed_temporal_masks = [[1 for i in range(N)] for j in range(N)]
    elif mode == 'Star':
        fixed_spatial_masks = generate_star_graph(N)
        fixed_temporal_masks = [[1 for i in range(N)] for j in range(N)]
    
    return {"initial_spatial_probability": initial_spatial_probability,
            "fixed_spatial_masks": fixed_spatial_masks,
            "initial_temporal_probability": initial_temporal_probability,
            "fixed_temporal_masks": fixed_temporal_masks,
            "node_kwargs":node_kwargs}    

if __name__ == '__main__':
    asyncio.run(main())
