# Deep Diagnostic Report (SVAMP)

## Scope

- Model: `MiniMax-M2.5`
- Endpoint: `https://gpt-agent.cc/v1`
- Split policy: SVAMP-only, fixed split (`seed=42`)
- Diagnostic subsets:
  - `test_nontrain_40.json` (40 samples, from non-training pool)
  - `test_nontrain_20_diag.json` (20 samples, from non-training pool)

## Core metric snapshots

### 40-sample diagnostic baseline pack

| Phase | Meaning | Accuracy | Total Tokens Avg |
|---|---|---:|---:|
| `diag-vanilla40` | DirectAnswer, 1 agent, 1 round | 1.0000 | 73,393 |
| `diag-cot40` | DirectAnswer + CoT | 1.0000 | 72,946 |
| `diag-mas-r1-40` | FullConnected, 5 agents, 1 round | 1.0000 | 233,845 |
| `diag-mas-r2-40` | FullConnected, 5 agents, 2 rounds | 0.9750 | 450,341 |
| `diag-hp-baseline40` | requested HP envelope | 1.0000 | 453,185 |
| `diag-hp-improved40` | same HP + phase-aware | 0.9750 | 465,620 |

### 20-sample ablation pack

| Phase | Meaning | Accuracy | Total Tokens Avg |
|---|---|---:|---:|
| `diag-agentprune-like20` | FullConnected, rounds=2, no dec/diff training | 0.9500 | 227,261 |
| `diag-ablation-single20` | single-learning style (`--optimized_* --diff`, no `--dec`) | 0.9500 | 220,511 |
| `diag-ablation-two-stage20-pr01` | two-stage attempt (`--dec --diff`, pruning=0.10) | 1.0000 | 183,576 |
| `diag-ablation-random20` | random graph (`mode=Random`) | 0.9500 | 226,686 |
| `diag-ablation-two-stage20-pr04` | two-stage attempt (`--dec --diff`, pruning=0.40) | 1.0000 | 181,620 |

## Paper-phenomena check status

1. **Original AgentDropout > AgentPrune/MASround=T**  
   - On diagnostics: often true (`1.00` vs `0.95~0.975`), but unstable across subsets and settings.

2. **Two-stage > Single learning**  
   - On 20-sample diagnostic subset: observed (`1.00` vs `0.95`).

3. **Learned dropout > Random dropout**  
   - On 20-sample diagnostic subset: observed (`1.00` vs `0.95`).

4. **Higher dropout rate should degrade performance**  
   - **Not reliably reproduced** in current runner (`pruning=0.10` and `0.40` both at `1.00` on 20-sample subset; token changed but not in expected direction pattern).

## Code-path findings (high confidence)

1. Runner creates graph with **hardcoded domain `gsm8k`** in SVAMP script:
   - `experiments/run_svamp.py` line ~321

2. In `--dec` branch, `optimized_spatial` and `optimized_temporal` are forcibly disabled:
   - `experiments/run_svamp.py` lines ~340-342

3. Non-dec optimization loop is currently disabled via `for i_batch in range(0):`
   - `experiments/run_svamp.py` line ~563

4. `add_loss` is explicitly zeroed in dec branch:
   - `experiments/run_svamp.py` line ~388

5. Dec-branch train logs are not written to result JSON (`data.append` commented):
   - `experiments/run_svamp.py` line ~488

6. Node-dropout update entrypoint does not accept/use `pruning_rate`:
   - `AgentDropout/graph/graph.py` line ~668 (`def update_masks_dec(self):`)

7. Node-only non-diff path crash reproduced:
   - `IndexError: index ... out of bounds` in `graph.py` during dec non-diff run (`diag-ablation-node-only20`).

## Diagnosis conclusion

The current runner behavior indicates that part of the intended AgentDropout two-stage chain is not consistently active in the effective training path for all configurations. Several control knobs (especially dec/non-dec, optimized flags, pruning-rate sensitivity) are not mapping cleanly to expected algorithmic behavior, which can mask or distort phase-aware gains.

