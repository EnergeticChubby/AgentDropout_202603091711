import os
import sys
import json
import types
import asyncio
import re
from types import SimpleNamespace

# Ensure project root imports work regardless of launch directory.
WORKSPACE_ROOT = '/workspace'
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

# Args
if len(sys.argv) != 4:
    raise SystemExit('Usage: run_mmlu_shard.py <shard_idx> <num_shards> <summary_out_json>')

shard_idx = int(sys.argv[1])
num_shards = int(sys.argv[2])
summary_out = sys.argv[3]

# Module aliasing for this repo
import AgentDropout
sys.modules['AgentPrune'] = AgentDropout

local_datasets_pkg = types.ModuleType('datasets')
local_datasets_pkg.__path__ = ['/workspace/datasets']
sys.modules['datasets'] = local_datasets_pkg

mmlu_pkg = types.ModuleType('datasets.MMLU')
sys.modules['datasets.MMLU'] = mmlu_pkg
mmlu_download_mod = types.ModuleType('datasets.MMLU.download')
mmlu_download_mod.download = lambda: None
sys.modules['datasets.MMLU.download'] = mmlu_download_mod

import AgentDropout.llm.gpt_chat as g
from openai import AsyncOpenAI
from AgentDropout.graph.graph import Graph
from AgentDropout.utils.globals import PromptTokens, CompletionTokens
from datasets.mmlu_dataset import MMLUDataset
from experiments.run_mmlu import get_kwargs
from experiments.train_mmlu import train
from experiments.evaluate_mmlu import evaluate

# Endpoint config (must be provided by env)
g.MINE_API_KEYS = os.environ['MMLU_API_KEY']
g.MINE_BASE_URL = os.environ['MMLU_BASE_URL']
# qwen model may not be in tiktoken mapping; disable token counting side effects
g.cost_count = lambda *args, **kwargs: None

_aclient = AsyncOpenAI(api_key=g.MINE_API_KEYS, base_url=g.MINE_BASE_URL)

def _extract_retry_after(err_text: str):
    m = re.search(r"retry_after['\"]?\s*[:=]\s*(\d+)", err_text, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

async def resilient_achat(model: str, msg):
    # Avoid failing the whole shard on transient 429/5xx.
    max_attempts = int(os.environ.get('MMLU_MAX_RETRIES', '30'))
    for attempt in range(1, max_attempts + 1):
        try:
            completion = await _aclient.chat.completions.create(model=model, messages=msg)
            response_message = completion.choices[0].message.content
            if isinstance(response_message, str):
                return response_message
            return str(response_message)
        except Exception as e:
            err = str(e)
            is_retryable = any(token in err.lower() for token in ['429', 'rate limit', '1015', 'timeout', '503', '502', 'connection'])
            if not is_retryable or attempt == max_attempts:
                raise RuntimeError(f"Failed to complete the async chat request: {e}")
            retry_after = _extract_retry_after(err)
            backoff = min(300, 5 * (2 ** min(attempt, 6)))
            wait_s = max(retry_after or 0, backoff)
            await asyncio.sleep(wait_s)

# Monkeypatch chat call used by GPTChat.
g.achat = resilient_achat

class ShardedDataset:
    def __init__(self, base_ds, shard_index: int, shard_count: int, max_total: int | None = None):
        self.base_ds = base_ds
        total = min(len(base_ds), max_total) if max_total is not None else len(base_ds)
        self.indices = [i for i in range(total) if i % shard_count == shard_index]
        self.split = f"{base_ds.split}_shard_{shard_index}_of_{shard_count}"

    def __len__(self):
        return len(self.indices)

    def __iter__(self):
        for idx in self.indices:
            yield self.base_ds[idx]

    def __getitem__(self, i):
        return self.base_ds[self.indices[i]]

    def record_to_input(self, record):
        return self.base_ds.record_to_input(record)

    def postprocess_answer(self, answer):
        return self.base_ds.postprocess_answer(answer)

    def record_to_target_answer(self, record):
        return self.base_ds.record_to_target_answer(record)

async def main():
    # AgentDropout "best" style configuration used in repo examples
    args = SimpleNamespace(
        mode='FullConnected',
        lr=0.1,
        delta=0.1,
        batch_size=int(os.environ.get('MMLU_EVAL_BATCH_SIZE', '1')),
        agent_names=['AnalyzeAgent'],
        agent_nums=[int(os.environ.get('MMLU_AGENT_COUNT', '5'))],
        num_iterations=10,
        imp_per_iterations=5,
        num_rounds=int(os.environ.get('MMLU_NUM_ROUNDS', '1')),
        pruning_rate=0.25,
        llm_name='qwen3-8b',
        domain='mmlu',
        decision_method='FinalRefer',
        optimized_spatial=True,
        optimized_temporal=True,
        diff=True,
        dec=True,
        cot=False,
    )

    expanded_agent_names = [name for name, num in zip(args.agent_names, args.agent_nums) for _ in range(num)]
    kwargs = get_kwargs(args.mode, len(expanded_agent_names))

    graph = Graph(
        domain=args.domain,
        llm_name=args.llm_name,
        agent_names=expanded_agent_names,
        decision_method=args.decision_method,
        optimized_spatial=args.optimized_spatial,
        optimized_temporal=args.optimized_temporal,
        rounds=args.num_rounds,
        diff=args.diff,
        dec=args.dec,
        **kwargs,
    )

    dataset_train = MMLUDataset('dev')
    dataset_val = MMLUDataset('val')
    global_limit_env = os.environ.get('MMLU_GLOBAL_LIMIT', '153').strip()
    global_limit = int(global_limit_env) if global_limit_env else None
    shard_dataset = ShardedDataset(dataset_val, shard_idx, num_shards, max_total=global_limit)

    # Optional control flags for faster smoke checks
    skip_train = os.environ.get('MMLU_SKIP_TRAIN', '1').strip() == '1'
    limit_questions_env = os.environ.get('MMLU_LIMIT_QUESTIONS', '').strip()
    limit_questions = int(limit_questions_env) if limit_questions_env else None

    # Train in AgentDropout mode before evaluation
    if not skip_train and (args.optimized_spatial or args.optimized_temporal):
        await train(
            graph=graph,
            dataset=dataset_train,
            num_iters=args.num_iterations,
            num_rounds=args.num_rounds,
            lr=args.lr,
            batch_size=20,
            imp_per_iters=args.imp_per_iterations,
            pruning_rate=args.pruning_rate,
            args=args,
            kwargs=kwargs,
        )

    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    score = await evaluate(
        graph=graph,
        dataset=shard_dataset,
        num_rounds=args.num_rounds,
        limit_questions=limit_questions,
        eval_batch_size=args.batch_size,
        dec=args.dec,
        args=args,
    )

    evaluated_questions = min(len(shard_dataset), limit_questions) if limit_questions is not None else len(shard_dataset)
    summary = {
        'shard_idx': shard_idx,
        'num_shards': num_shards,
        'questions': evaluated_questions,
        'score': score,
        'correct_estimate': round(score * evaluated_questions, 6),
    }
    with open(summary_out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print('SHARD_SUMMARY', json.dumps(summary, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
