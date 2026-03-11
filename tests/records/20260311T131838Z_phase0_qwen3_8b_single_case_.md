# Test Record: phase0_qwen3_8b_single_case

## Goal
- Validate command execution and keep reproducible evidence.

## Preconditions
- Repository is clean enough for this test scope.
- Required dependencies for target command are available.

## Command
- `python3 experiments/run_mmlu.py --llm_name qwen3-8b --mode DirectAnswer --agent_names AnalyzeAgent --agent_nums 1 --batch_size 1 --num_rounds 1 --limit_questions 1 --retry_batch_size 1 --max_retry_rounds 3 --retry_delay 1`

## Environment Snapshot
- Timestamp (UTC): 20260311T131838Z
- Branch: `gz10_v2`
- Commit: `370d8594b83471df04c11548ccaa9a13739e8a52`
- Workdir: `/workspace`
- Model: `qwen3-8b`
- Base URL: `https://llm.undefined.qzz.io/v1/chat/completions`

## Output Summary
- Raw log: `tests/records/20260311T131838Z_phase0_qwen3_8b_single_case_.log`

## Exit Code
- `1`

## Reproduction Steps
1. Checkout branch `gz10_v2`.
2. Ensure `template.env` contains expected test configuration.
3. Run command:
   `python3 experiments/run_mmlu.py --llm_name qwen3-8b --mode DirectAnswer --agent_names AnalyzeAgent --agent_nums 1 --batch_size 1 --num_rounds 1 --limit_questions 1 --retry_batch_size 1 --max_retry_rounds 3 --retry_delay 1`

## Conclusion
- FAIL: command returned non-zero exit code.
