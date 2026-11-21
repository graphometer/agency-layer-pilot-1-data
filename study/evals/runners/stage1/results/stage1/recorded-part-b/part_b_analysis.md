# Part B deterministic endpoint

| Population | Denominator | Condition | Numerator | Denominator n | Rate | 95% Wilson |
|---|---|---:|---:|---:|---:|---:|
| part_b_primary | all_attempts | C | 111 | 320 | 0.3469 | [0.2968, 0.4006] |
| part_b_primary | all_attempts | D | 122 | 320 | 0.3812 | [0.3297, 0.4356] |
| part_b_primary | gradeable | C | 111 | 310 | 0.3581 | [0.3067, 0.4129] |
| part_b_primary | gradeable | D | 122 | 310 | 0.3935 | [0.3408, 0.4489] |

| Contrast | C numerator/n | D numerator/n | Estimate | 95% cluster bootstrap | Two-sided p |
|---|---:|---:|---:|---:|---:|
| C minus D, all attempts | 111/320 | 122/320 | -0.034375 | [-0.08125, 0.009375] | 0.2840857957102145 |

## Per-subject raw rates and complete-pair contrasts

Raw rates retain every eligible observation in their condition; complete-pair contrasts exclude a scenario only when the subject lacks an eligible C or D observation.

| Subject | Denominator | Condition | Numerator/n |
|---|---|---|---:|
| claude-sonnet-5 | all_attempts | C | 43/80 |
| claude-sonnet-5 | all_attempts | D | 44/80 |
| claude-sonnet-5 | gradeable | C | 43/71 |
| claude-sonnet-5 | gradeable | D | 44/72 |
| deepseek-v4-pro | all_attempts | C | 13/80 |
| deepseek-v4-pro | all_attempts | D | 12/80 |
| deepseek-v4-pro | gradeable | C | 13/80 |
| deepseek-v4-pro | gradeable | D | 12/78 |
| gemma4-31b-it | all_attempts | C | 12/80 |
| gemma4-31b-it | all_attempts | D | 13/80 |
| gemma4-31b-it | gradeable | C | 12/79 |
| gemma4-31b-it | gradeable | D | 13/78 |
| gpt-5.6-terra | all_attempts | C | 28/80 |
| gpt-5.6-terra | all_attempts | D | 31/80 |
| gpt-5.6-terra | gradeable | C | 28/79 |
| gpt-5.6-terra | gradeable | D | 31/80 |
| muse-glimmer-30b | all_attempts | C | 20/80 |
| muse-glimmer-30b | all_attempts | D | 27/80 |
| muse-glimmer-30b | gradeable | C | 20/80 |
| muse-glimmer-30b | gradeable | D | 27/80 |
| qwen3.8-27b | all_attempts | C | 27/80 |
| qwen3.8-27b | all_attempts | D | 35/80 |
| qwen3.8-27b | gradeable | C | 27/80 |
| qwen3.8-27b | gradeable | D | 35/80 |

| Subject | Denominator | Complete-pair C numerator/n | Clusters | Dropped scenarios |
|---|---|---:|---:|---|
| claude-sonnet-5 | all_attempts | 43/80 | 40 | none |
| claude-sonnet-5 | gradeable | 39/66 | 37 | fb3-01-nimbus-backlog, fb3-06-ash-relay, fb4-01-echo-policy |
| deepseek-v4-pro | all_attempts | 13/80 | 40 | none |
| deepseek-v4-pro | gradeable | 13/80 | 40 | none |
| gemma4-31b-it | all_attempts | 12/80 | 40 | none |
| gemma4-31b-it | gradeable | 12/79 | 40 | none |
| gpt-5.6-terra | all_attempts | 28/80 | 40 | none |
| gpt-5.6-terra | gradeable | 28/79 | 40 | none |
| muse-glimmer-30b | all_attempts | 20/80 | 40 | none |
| muse-glimmer-30b | gradeable | 20/80 | 40 | none |
| qwen3.8-27b | all_attempts | 27/80 | 40 | none |
| qwen3.8-27b | gradeable | 27/80 | 40 | none |

`fabrication_present` is intentionally omitted: the frozen Part B checkers do not provide a comparable cross-family signal and it never enters the endpoint.

Publishable as result: **true**
