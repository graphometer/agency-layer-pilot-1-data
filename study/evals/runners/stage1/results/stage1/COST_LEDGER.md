# Stage 1 cost ledger

Final close journals are authoritative.

| Batch | Final close cost (USD) |
|---|---:|
| recorded-core-s1 | 105.908004 |
| recorded-fresh-s1 | 24.367868 |
| recorded-fresh-local-s1 | 0.120864 |
| recorded-family9-s1 | 0.242493 |

Subject/router total: **$130.639229**.

| Judge ledger | Final cumulative total (USD) |
|---|---:|
| recorded-core-judged | 10.438834 |
| recorded-family9-judged | 1.124001 |

Judges: **$11.562835**; recorded run: **$142.202064**.
Development spend before recorded run is approximately $18 ($13.97 itemised); study-wide total is approximately $160 of the $600 ceiling.

## Notes

- recorded-core-s1 batch.json reports reservation_covered_every_call=false, max_overshoot_usd=0.012573, and one outstanding reservation of 0.025261; its batch.json total_usd=105.882757 differs from the authoritative final-close journal sum.
- Other batches differ from batch.json by no more than 1e-5 rounding; final close journals are authoritative.
- Execution accounting: 3,600 planned/analysed cells; 3,760 execution attempts, including 320 recorded-fresh-local-s1 planned cells, 160 archived .attempt1 provider_error attempts, and 160 replacements.
