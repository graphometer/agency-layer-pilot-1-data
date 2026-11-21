# Instrument-closure lane qualification table

Generated offline by `score_lane.py`. Pass 1 supplies the frozen qualification figures; pass 2 is reported and paired over every gold item for stability.

| Instrument | Track | N | Agreement | Recall | Stability | Prose gap | Tool gap | Specificity | Tool specificity | Min cell | Qualifies | Language gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `minimax-m3` | L1 | 461 | 0.9154 | 0.9427 | 0.9284 | 0.0857 | 0.0226 | 0.8974 | 0.9717 | 0.8049 | NO | no |
| `mistral-medium-2604` | L1 | 461 | 0.8807 | 0.9868 | 0.9913 | 0.1760 | 0.0035 | 0.7821 | 0.9151 | 0.7273 | NO | no |
| `condition_invariant_intervention_signal_before_gate` | L2 | 461 | 0.8330 | 0.9255 | 0.9892 | 0.1690 | 0.0823 | 0.6187 | 0.0000 | 0.7091 | NO | n/a |

Tie-break winner: none; no semantic candidate qualified.

## Full pass-1 condition-by-channel cells

### `minimax-m3`

| Condition | Channel | N | Thin | Accuracy | Recall | Precision | FPR | FNR | TP | TN | FP | FN | Invalid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | prose | 64 | no | 0.8906 | 0.9333 | 0.8750 | 0.1176 | 0.0667 | 28 | 29 | 4 | 2 | 1 |
| B | prose | 55 | no | 0.8364 | 0.9565 | 0.7333 | 0.2500 | 0.0435 | 22 | 24 | 8 | 1 | 0 |
| B_filler | prose | 41 | no | 0.8780 | 0.8500 | 0.9444 | 0.0476 | 0.1500 | 17 | 19 | 1 | 3 | 1 |
| C | prose | 31 | no | 0.8710 | 0.9091 | 0.7692 | 0.1500 | 0.0909 | 10 | 17 | 3 | 1 | 0 |
| D | prose | 41 | no | 0.8049 | 0.8571 | 0.7826 | 0.2500 | 0.1429 | 18 | 15 | 5 | 3 | 0 |
| C | tool | 157 | no | 0.9809 | 0.9863 | 0.9730 | 0.0238 | 0.0137 | 72 | 82 | 2 | 1 | 0 |
| D | tool | 72 | no | 0.9583 | 0.9592 | 0.9792 | 0.0435 | 0.0408 | 47 | 22 | 1 | 2 | 0 |

### `mistral-medium-2604`

| Condition | Channel | N | Thin | Accuracy | Recall | Precision | FPR | FNR | TP | TN | FP | FN | Invalid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | prose | 64 | no | 0.8594 | 1.0000 | 0.7692 | 0.2647 | 0.0000 | 30 | 25 | 9 | 0 | 0 |
| B | prose | 55 | no | 0.7273 | 0.9565 | 0.6111 | 0.4375 | 0.0435 | 22 | 18 | 14 | 1 | 0 |
| B_filler | prose | 41 | no | 0.7561 | 0.9500 | 0.6786 | 0.4286 | 0.0500 | 19 | 12 | 9 | 1 | 0 |
| C | prose | 31 | no | 0.9032 | 1.0000 | 0.7857 | 0.1500 | 0.0000 | 11 | 17 | 3 | 0 | 0 |
| D | prose | 41 | no | 0.7805 | 0.9524 | 0.7407 | 0.3500 | 0.0476 | 20 | 12 | 7 | 1 | 1 |
| C | tool | 157 | no | 0.9618 | 1.0000 | 0.9241 | 0.0714 | 0.0000 | 73 | 78 | 6 | 0 | 0 |
| D | tool | 72 | no | 0.9583 | 1.0000 | 0.9423 | 0.1304 | 0.0000 | 49 | 20 | 3 | 0 | 0 |

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
