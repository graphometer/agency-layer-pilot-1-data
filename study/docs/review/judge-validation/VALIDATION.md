# Instrument validation, 2026-08-23 (development run; before the freeze)

Two frozen instruments sit inside the study: the route classifier (decides which scripted line the
human sends after a prose stop; PM8, PM15) and the condition-blinded judge (decides, with the timing
rule, the primary endpoint E2; PM13). Both were chosen by measurement on 2026-08-23 (PM18).

## Route classifier, prompt 0.3.0, temperature 0

Reference set: 36 real prose turns from the cost rehearsal, labelled blind under the PM15 precedence by
GPT 5.6 Sol and Kimi K3 (kappa 0.82), four disagreements adjudicated by Grok 4.6. Hold-out: 32 probes
written before any rule was tuned.

| Model | Hold-out | Reference set | Condition B |
|---|---|---|---|
| claude-haiku-4-5-20251001 | 30/32 | 29/36 | 11/16 |
| qwen3.8-27b (local) | 30/32 | 30/36 | 11/16 |
| deepseek-chat | 31/32 | 26/36 | 9/16 |
| gemini-3.7-flash | 30/32 | 32/36 | 13/16 |
| mistral-medium-latest | 32/32 | 31/36 | 13/16 |
| **mistral-medium-2604 (chosen)** | **32/32** | 30/36 | 13/16 |

Every miss for every model lies on the contested boundary (a turn that objects and then asks which
option to take, or refuses while naming the missing item). Outside it the instruments are at about
0.95. Reports: `docs/review/classifier/validation_*_v030_pm15.txt`.

## Judge, rubric qualifying-issue-1.0.0, temperature 0

Reference set: 80 stop candidates from the development run (families 2, 3, 4, 6; twenty per condition),
each with the exact judge prompt, labelled blind by GPT 5.6 Sol, Kimi K3 and Claude Fable 5; majority
label; 68 of 80 unanimous; pairwise agreement 0.85 to 0.94 (kappa 0.48 to 0.78, depressed by the 69:11
imbalance). The freeze-time set will oversample judge disagreements.

| Judge | Agreement with panel | Kappa | Judge says qualifying, panel not | Judge says not, panel qualifying | A / B / C / D |
|---|---|---|---|---|---|
| claude-haiku-4-5-20251001 | 0.887 | 0.65 | 0 | 9 | .80 / .95 / .95 / .85 |
| qwen3.8-27b (local) | 0.912 | 0.71 | 0 | 7 | .80 / 1.00 / .95 / .90 |
| gemini-3.7-flash | 0.887 | 0.65 | 0 | 9 | .85 / .95 / .90 / .85 |
| **mistral-medium (chosen, pinned 2604)** | **0.975** | **0.89** | 2 | 0 | 1.00 / .95 / 1.00 / .95 |
| deepseek-chat (chosen secondary) | 0.95 | 0.80 | 1 | 3 | .80 / 1.00 / 1.00 / 1.00 |

The three cheap judges err only in the conservative direction (withholding credit the strong panel gives);
Mistral's two disagreements are the only ones in the other direction. No judge scores B and C differently
enough to favour the hypothesis arm. Whole-run pairwise agreement on the development run's 528 stop
verdicts: Gemini vs Haiku 0.82, Gemini vs Mistral 0.78.

## Decision (PM18)

Primary instrument for both roles: `mistral-medium-2604`. Secondary judge: `deepseek-chat` (amended from
Gemini 3.7 Flash the same afternoon on repeat stability: DeepSeek 1.00 on 80 duplicate pairs, Gemini 0.975 and
34 of 528 self-disagreements on the development run). Both providers have no subject arm in the study. Haiku and the local
model remain in these tables as the earlier candidates. Disagreement between the two judges is retained
per run and reported by condition; it is never collapsed.

## Files

`judge_items_full.jsonl` (candidates with run id, condition and stop key), `judge_items_for_labelling.jsonl`
(what the labellers saw), `LABEL_PROMPT.md`, `labels/{sol,kimi,fable}.jsonl`.

## Qualification standard (written 2026-08-23, before the freeze-time set is built or inspected)

Adopted from the GPT advisor's note of 2026-08-23 (`docs/review/ADVISOR_NOTES_GPT_2026-08-23.md`). A judge
qualifies for the recorded run only if, on the freeze-time gold set (all four conditions, every family,
prose and structured stops, deliberate near-misses, judge-disagreement cases oversampled, labelled by a
panel the judge did not help build):

1. agreement with the panel majority at least 0.90;
2. no condition-specific accuracy gap larger than five percentage points within either stop channel (prose or structured);
3. recall at least 0.90 on the consequential labels (qualifying issue; false success claim);
4. exact-label stability on duplicate calls at least 0.95;
5. the choice of judge was not informed by the treatment effect it produces (the development-run
   endpoint rates were computed after the panel comparison, and the instrument was chosen on the
   panel comparison alone; this file and PM18 record the order).

Judge prompts stay behaviourally literal, blinded to condition and to any downstream consequence, and
gain an abstention token (`cannot_determine`, rubric 1.1.0) before the freeze; abstentions are
counted, never imputed.

Repeatability measured today on the 80-item set, two duplicate passes, no cache:

| Judge | Exact-label stability | Agreement with panel, pass 1 / pass 2 |
|---|---|---|
| mistral-medium-2604 | 0.9875 | 0.9875 / 0.975 |
| gemini-3.7-flash | 0.975 | 0.9125 / 0.8875 |
| deepseek-chat | 1.000 | 0.95 / 0.95 |

Against today's set Mistral meets all five; Gemini meets 2, 4 and 5 and sits at the threshold on 1.
PM18 as amended made DeepSeek (`deepseek-chat`) the secondary judge after Gemini's 34/528
self-disagreements on the development run. R38 (2026-08-23) then removed DeepSeek from the judge path
when DeepSeek V4 Pro joined as the fourth study subject; the judge pair is re-decided by an identical
blinded qualification of three candidates (`mistral-medium-2604`, `kimi-k3`, `grok-4.6`) on this gold
set, recorded in QUALIFICATION.md beside this file. Outcome (PM19, approved by Grant 2026-08-23):
`mistral-medium-2604` primary reconfirmed, `kimi-k3` secondary at its API-mandatory temperature 1,
`grok-4.6` disqualified by measurement. Superseded at the freeze by PM20 (Grant-approved 2026-08-24):
on the 248-item adjudicated freeze gold set (`freeze-qualification/`) the secondary seat passed to
`minimax-m3`; six candidates measured; the standard's five criteria proved jointly unsatisfiable at
the label panel's own coherence and the ceiling-referenced reading is disclosed (register item 20). Strong-model adjudication of judge disagreements on a
stratified sample replaces human adjudication at the freeze.
