# Filler control batch (development phase), 2026-08-23 evening

**Purpose.** PM9's sensitivity control, run before the freeze: does condition B's effect come from its
permission content, or merely from a longer prompt? `B_filler` replaces B's five-action permission
paragraph with word-matched neutral information (222 words in both prompts); everything else is
identical.

**Design.** 45 scenarios (all nine families) x B_filler x 2 repeats = 90 runs on the local subject
(`qwen3.8-27b`, thinking off), the promoted isolated harness, route classifier `mistral-medium-2604`.
1,178 model calls, 0 refusals, 0 reservation overshoots, $0 routing beyond the free classifier tier.
Graded with the PM19 pair: primary `mistral-medium-2604`, secondary `kimi-k3` (its first live outing).

**Headline (development read, one local model, never a study result).**

| Measure | B_filler | B (dev run, same scenarios/model/repeats) |
|---|---|---|
| E2 all-attempts (families 2,3,4,6) | 12/40 = 0.30 | 22/40 = 0.55 |
| E1 false-success all-attempts (families 5,7) | 11/20 = 0.55 | 8/20 = 0.40 |
| Benign completion (family 1,8) | 20/20 = 1.00 | 1.00 |

**The PM9 contrast** (combined dev+filler analysis, `combined-analysis/`): B minus B_filler on E2,
all-attempts, scenario-paired with within-family scenario-cluster bootstrap: **+0.25, 95% interval
[0.075, 0.475]** (pooled [0.05, 0.45]); gradeable +0.237 [0.0, 0.448]. Descriptive sensitivity, not
confirmatory. Reading: word-matched filler does not reproduce B's intervention rate; B_filler sits at
or below ordinary A (0.375). The permission content, not prompt length, carries B's effect.

**Instrument consistency note.** The combined analysis required one judge pair across both batches,
so the development run's 360 blinded transcripts were re-judged under the PM19 pair (Mistral from the
original cache, Kimi K3 live); those judged files are published as `../dev-2026-08-23/judged-pm19/`.
The original `judged/` (mistral-primary + deepseek-secondary) remains the calibration record of its
day and stays readable under `--allow-any-judges`. The mistral-vs-kimi disagreements in
`judged-pm19` feed the freeze-time gold set's disagreement oversampling (R39/F10).

**Cost.** About $6 of Kimi K3 secondary verdicts across the filler judging and the dev re-judge;
everything else free or cached.
