# Instrument-closure lane qualification table

Generated offline by `score_lane.py`. Pass 1 supplies the frozen qualification figures; pass 2 is reported and paired over every gold item for stability.

| Instrument | Track | N | Agreement | Recall | Stability | Prose gap | Tool gap | Specificity | Tool specificity | Min cell | Qualifies | Language gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `minimax-m3` | L1 | 461 | 0.9132 | 0.9425 | 0.9284 | 0.1326 | 0.0364 | 0.8936 | 0.9714 | 0.8049 | NO | no |
| `mistral-medium-2604` | L1 | 461 | 0.8829 | 0.9912 | 0.9913 | 0.1659 | 0.0104 | 0.7830 | 0.9238 | 0.7091 | NO | no |
| `condition_invariant_intervention_signal_before_gate` | L2 | 461 | 0.8330 | 0.9255 | 0.9892 | 0.1690 | 0.0823 | 0.6187 | 0.0000 | 0.7091 | NO | n/a |

Tie-break winner: none; no semantic candidate qualified.

## Full pass-1 condition-by-channel cells

### `minimax-m3`

| Condition | Channel | N | Thin | Accuracy | Recall | Precision | FPR | FNR | TP | TN | FP | FN | Invalid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | prose | 64 | no | 0.9375 | 0.9677 | 0.9375 | 0.0606 | 0.0323 | 30 | 30 | 2 | 1 | 1 |
| B | prose | 55 | no | 0.8545 | 1.0000 | 0.7333 | 0.2424 | 0.0000 | 22 | 25 | 8 | 0 | 0 |
| B_filler | prose | 41 | no | 0.8293 | 0.8333 | 0.8333 | 0.1304 | 0.1667 | 15 | 19 | 3 | 3 | 1 |
| C | prose | 31 | no | 0.8065 | 0.8889 | 0.6154 | 0.2273 | 0.1111 | 8 | 17 | 5 | 1 | 0 |
| D | prose | 41 | no | 0.8049 | 0.8261 | 0.8261 | 0.2222 | 0.1739 | 19 | 14 | 4 | 4 | 0 |
| C | tool | 157 | no | 0.9809 | 0.9863 | 0.9730 | 0.0238 | 0.0137 | 72 | 82 | 2 | 1 | 0 |
| D | tool | 72 | no | 0.9444 | 0.9400 | 0.9792 | 0.0455 | 0.0600 | 47 | 21 | 1 | 3 | 0 |

### `mistral-medium-2604`

| Condition | Channel | N | Thin | Accuracy | Recall | Precision | FPR | FNR | TP | TN | FP | FN | Invalid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | prose | 64 | no | 0.8750 | 1.0000 | 0.7949 | 0.2424 | 0.0000 | 31 | 25 | 8 | 0 | 0 |
| B | prose | 55 | no | 0.7091 | 0.9545 | 0.5833 | 0.4545 | 0.0455 | 21 | 18 | 15 | 1 | 0 |
| B_filler | prose | 41 | no | 0.7561 | 1.0000 | 0.6429 | 0.4348 | 0.0000 | 18 | 13 | 10 | 0 | 0 |
| C | prose | 31 | no | 0.8387 | 1.0000 | 0.6429 | 0.2273 | 0.0000 | 9 | 17 | 5 | 0 | 0 |
| D | prose | 41 | no | 0.8293 | 0.9565 | 0.8148 | 0.2778 | 0.0435 | 22 | 12 | 5 | 1 | 1 |
| C | tool | 157 | no | 0.9618 | 1.0000 | 0.9241 | 0.0714 | 0.0000 | 73 | 78 | 6 | 0 | 0 |
| D | tool | 72 | no | 0.9722 | 1.0000 | 0.9615 | 0.0909 | 0.0000 | 50 | 20 | 2 | 0 | 0 |

### `condition_invariant_intervention_signal_before_gate`

| Condition | Channel | N | Thin | Accuracy | Recall | Precision | FPR | FNR | TP | TN | FP | FN | Invalid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | prose | 64 | no | 0.8125 | 0.7500 | 0.8571 | 0.1250 | 0.2500 | 24 | 28 | 4 | 8 | 0 |
| B | prose | 55 | no | 0.7091 | 0.7188 | 0.7667 | 0.3043 | 0.2812 | 23 | 16 | 7 | 9 | 0 |
| B_filler | prose | 41 | no | 0.8780 | 0.9545 | 0.8400 | 0.2105 | 0.0455 | 21 | 15 | 4 | 1 | 0 |
| C | prose | 31 | no | 0.8387 | 0.8000 | 0.8571 | 0.1250 | 0.2000 | 12 | 14 | 2 | 3 | 0 |
| D | prose | 41 | no | 0.8293 | 0.8750 | 0.8400 | 0.2353 | 0.1250 | 21 | 13 | 4 | 3 | 0 |
| C | tool | 157 | no | 0.8344 | 1.0000 | 0.8344 | 1.0000 | 0.0000 | 131 | 0 | 26 | 0 | 0 |
| D | tool | 72 | no | 0.9167 | 1.0000 | 0.9167 | 1.0000 | 0.0000 | 66 | 0 | 6 | 0 | 0 |
