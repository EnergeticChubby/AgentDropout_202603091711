# Test Record: phase0_gsm8k_quickstart_gpt51mini_retry1

## Goal
- Validate command execution and keep reproducible evidence.

## Preconditions
- Repository is clean enough for this test scope.
- Required dependencies for target command are available.

## Command
- `python3 experiments/run_gsm8k.py --agent_nums 5 --mode FullConnected --batch_size 40 --num_iterations 2 --imp_per_iterations 1 --pruning_rate 0.10 --num_rounds 2 --llm_name gpt-5.1-codex-mini --optimized_spatial --optimized_temporal --diff --dec`

## Environment Snapshot
- Timestamp (UTC): 20260311T135806Z
- Branch: `gz10_v2`
- Commit: `546b6cbaf1af9110f3f2ebefb61d09fad4525be9`
- Workdir: `/workspace`
- Model: `gpt-5.1-codex-mini`
- Base URL: `https://api.xcode.best/v1`

## Output Summary
- Raw log: `tests/records/20260311T135806Z_phase0_gsm8k_quickstart_gpt51mini_retry1_.log`

## Exit Code
- `1`

## Reproduction Steps
1. Checkout branch `gz10_v2`.
2. Ensure `template.env` contains expected test configuration.
3. Run command:
   `python3 experiments/run_gsm8k.py --agent_nums 5 --mode FullConnected --batch_size 40 --num_iterations 2 --imp_per_iterations 1 --pruning_rate 0.10 --num_rounds 2 --llm_name gpt-5.1-codex-mini --optimized_spatial --optimized_temporal --diff --dec`

## Conclusion
- FAIL: command returned non-zero exit code.
