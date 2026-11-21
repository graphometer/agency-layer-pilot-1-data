# Judge validation set (development run, 2026-08-23)

Purpose: B6 asks for the frozen condition-blinded judge to be validated against an independent
reference before the freeze. This folder holds the first such set, drawn from the development run
(one local subject model, 360 runs), and the labels.

- `judge_items_full.jsonl`: 80 stop candidates from families 2, 3, 4 and 6, twenty per condition,
  each carrying the exact prompt the judge received (rubric `qualifying-issue-1.0.0`, the scenario's
  ground-truth issue description, the condition-blinded transcript through the stop turn). The
  run id, condition and stop key are here for the analyst; the labellers received only
  `judge_items_for_labelling.jsonl` (id and prompt).
- `labels/`: three independent blind labellers from three model families, launched headlessly with
  `LABEL_PROMPT.md`: GPT 5.6 Sol, Kimi K3, Claude Fable 5. Majority label is the reference;
  68 of 80 were unanimous. The set is imbalanced (69 qualifying, 11 not), so kappa is depressed;
  the freeze-time set will oversample candidates on which judges disagree.
- Result (agreement with the majority label; each judge at temperature 0, thinking off):
  Haiku 4.5 0.89, local Qwen3.8-27B 0.91, Gemini 3.7 Flash 0.88 (78 scored at the time of writing);
  every disagreement was the judge saying not_qualifying where the panel said qualifying (conservative),
  none the reverse; by condition B and C were scored alike (0.85 to 0.95), A lowest for all judges (0.80).
  Mistral Medium pending. Full numbers in `VALIDATION.md` once the passes finish.
