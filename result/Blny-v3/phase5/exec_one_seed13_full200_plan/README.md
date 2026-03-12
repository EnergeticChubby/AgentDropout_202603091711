# One-seed SVAMP full200 run plan (not executed)

- seed: 13
- total planned runs: 10
- test split: svamp_test_200.json

| Config | Mode | Rounds | Agents |
|---|---|---:|---:|
| Vanilla | DirectAnswer | 1 | 1 |
| MASround_T | FullConnected | 2 | 5 |
| AgentPrune | FullConnected | 2 | 5 |
| AgentDropout | FullConnected | 2 | 5 |
| AgentDropout_Ours | FullConnected | 2 | 5 |
| Ablation_state_only | FullConnected | 2 | 5 |
| Ablation_barrier_no_intervention | FullConnected | 2 | 5 |
| Ablation_intervention_no_barrier | FullConnected | 2 | 5 |
| Ablation_random_intervention | FullConnected | 2 | 5 |
| Ablation_full_method | FullConnected | 2 | 5 |
