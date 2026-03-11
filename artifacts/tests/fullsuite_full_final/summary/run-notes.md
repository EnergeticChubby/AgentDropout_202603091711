# Full-suite run notes

This run executes full test coverage for:

- GSM8K (`openai/gsm8k`, `main`, `test`, 1319)
- MultiArith (`ChilleD/MultiArith`, `default`, `test`, 180)
- SVAMP (`ChilleD/SVAMP`, `default`, `test`, 300)
- HumanEval (`openai/openai_humaneval`, `openai_humaneval`, `test`, 164)

Profiles:

- `agentdropout`
- `phase3` (`enable_contracts + enable_knowledge + enable_boundary`)

Execution configuration used for both profiles:

- `math_agent_count=1`
- `code_agent_count=1`
- `math_mode=DirectAnswer`
- `code_mode=DirectAnswer`
- `math_decision_method=FinalDirect`
- `code_decision_method=FinalWriteCode`
- `max_tokens=32`
- `max_retries=12`

Reasoning:

- These settings were used to make full-coverage runs tractable within endpoint latency constraints while preserving an apples-to-apples comparison between `agentdropout` and `phase3`.
