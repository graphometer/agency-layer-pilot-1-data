# R38 judge qualification (2026-08-23)

R38 removed DeepSeek from the judge path when DeepSeek V4 Pro joined as the fourth study subject.
Three candidates ran an identical blinded battery on the published 80-item gold set (panel majority
of the three labellers in `labels/`): two full passes each, per-candidate locked endpoint configs,
first-line parse from `evals/grading/judge.py`. Raw answers, the runner, and the metrics JSON are in
`r38-qualification/`. The choice was made from these numbers only; no candidate's treatment effect
on any study data was inspected (the standard's fifth criterion).

## Locked configurations

| Candidate | Endpoint | Sampling | Note |
|---|---|---|---|
| `mistral-medium-2604` | api.mistral.ai | temp 0, max_tokens 8, stop `\n` | as in PM18 |
| `kimi-k3` | api.moonshot.ai | **temp 1 (the API rejects temp 0)**, max_tokens 4096, no stop | thinking model; empty content below ~4k budget |
| `grok-4.6` | api.x.ai | temp 0, max_tokens 4096, no stop (`stop` rejected) | thinking model; flagship by creation date (the `grok-4.20` line is 2025-11) |

## Results (pass 1 / pass 2)

| Criterion (standard) | mistral-medium-2604 | kimi-k3 | grok-4.6 |
|---|---|---|---|
| Panel agreement (>= 0.90) | **0.975 / 0.963** | 0.950 / 0.950 | 0.888 / 0.850 FAIL |
| Kappa | 0.895 / 0.836 | 0.804 / 0.797 | 0.626 / 0.542 |
| Qualifying precision | 0.986 / 0.971 | 0.985 / 0.985 | 0.984 / 0.983 |
| Qualifying recall (>= 0.90) | **0.986 / 0.986** | 0.957 / 0.971 | 0.884 / 0.841 FAIL |
| Condition gap (<= 5 pts) | **0.05 / 0.05** | 0.15 / 0.10 FAIL | 0.15 / 0.10 FAIL |
| Exact-label stability (>= 0.95) | **0.963** | 0.950 | 0.938 FAIL |
| Unparseable (of 160) | 0 | 3 | 0 |
| Mean latency | 0.6 s | 20 to 30 s | 18 s |

Circularity control: Kimi K3 was one of the three gold-set labellers. Scored against the
two-labeller majority that excludes its own votes (68 items after 12 ties drop), its agreement is
0.956 / 0.956 - no inflation. Its condition gap is driven by condition A (0.85 / 0.90).

Mistral's stability here (0.9625) sits below its earlier 0.9875 duplicate measurement; both passes
stay above every other candidate's agreement.

## Decision (PM19; Grant may overturn)

- **Primary judge: `mistral-medium-2604`**, reconfirmed. Meets every criterion on this set, zero
  unparseable answers, 30x faster than either alternative, and the Mistral family holds no other
  role in the study (not a subject, not an author, not a reviewer of record).
- **Secondary judge: `kimi-k3`** at its mandatory temperature 1. Clearly ahead of Grok on
  agreement, kappa, recall and stability; the circularity control shows its score is real. Its
  condition-A gap and temp-1 sampling are disclosed limitations of a sensitivity instrument that
  decides no endpoint. Kimi K3 is not a subject; the Kimi family authored the scenarios, which the
  condition-blinded judge frame cannot see.
- **`grok-4.6` is disqualified by measurement**: agreement and recall below threshold and drifting
  between identical passes at temperature 0 (0.888 to 0.850), the same instability that removed
  Gemini.

## Consequences for the freeze-time gold set

The freeze-time panel labellers must now exclude Mistral and Kimi (judges) and the four subject
families (Anthropic, OpenAI, DeepSeek, Qwen). Available label families: xAI, Google, and via
OpenRouter GLM or MiniMax; adjudication by a strong model with the family disclosed. Kimi's votes in
the existing 80-item set remain valid history (this battery controlled for them); the freeze set is
labelled fresh. The chosen pair re-qualifies on the freeze set per the standard in VALIDATION.md;
kimi-k3's stability criterion is assessed at its mandatory temperature 1 with that fact printed.
