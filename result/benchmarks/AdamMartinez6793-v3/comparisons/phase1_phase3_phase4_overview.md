# Phase Reproduction Overview

- Branch tag: AdamMartinez6793-v3
- Protocol: fixed `test.json` (n=200), seed42, strict mode, num_rounds=2
- Phase2: skipped by user decision

## Accuracy / Tokens

- Phase1: acc=0.975, tokens_avg=2456.795
- Phase3: acc=0.96, tokens_avg=2607.52
- Phase4: acc=0.96, tokens_avg=2444.94

## Pairwise vs Phase1

- Phase1→Phase3 transitions: {'correct_to_correct': 192, 'correct_to_wrong': 3, 'wrong_to_correct': 0, 'wrong_to_wrong': 5}
- Phase1→Phase4 transitions: {'correct_to_correct': 191, 'correct_to_wrong': 4, 'wrong_to_correct': 1, 'wrong_to_wrong': 4}
