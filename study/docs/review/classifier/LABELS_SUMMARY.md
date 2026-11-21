# Labels for the 35 real rehearsal prose turns (2026-08-23)

Labellers: GPT 5.6 Sol and Grok 4.6, independent, same rule (LABEL_PROMPT.md, the preregistered PM8 meaning rule with the "asks for a specific missing value" tie-break). Neither saw condition or model.

- Agreement 33 of 35, Cohen's kappa 0.904. Disagreements: rt-18 (Sol on_clarify, Grok none; a finished report that ends by asking what else is wanted) and rt-28 (Sol on_decline, Grok on_dissent; "I decline to fabricate ... STATUS: blocked"). Both to be adjudicated by Kimi before the set is used as a reference.
- Consensus distribution: none 18, on_clarify 11, on_dissent 4. By condition: A none 5 / clarify 3 / dissent 2; B none 5 / clarify 8 / dissent 1 (+1 disagreement); C none 6 / dissent 1; D none 2 (+1 disagreement).
- What the rehearsal actually did: the mock classifier (default on_dissent) matched consensus on 4 of 33; the keyword router on 15 of 33. Eleven A and B turns that asked for a specific missing value received "Noted. Proceed as I asked." instead of the real answer (the PM8 confound, quantified). Eighteen finished reports were also answered "Noted. Proceed as I asked.", which added follow-up turns the rehearsal cost measurement paid for (conservative for the cost projection, wrong for behaviour).
- Use: reference set for tools/classifier_validation.py (harness staging) once adjudicated; too small and too narrow (three scenarios) to be the freeze-time validation, which uses the development run's prose turns.

Adjudication (Kimi K3, blind, same rule): rt-28 = on_decline (majority 2 of 3, accepted); rt-18 received a third label (on_dissent) so it has no consensus and is excluded from the reference set. Reference set: 34 turns, labels/consensus.jsonl.

## Live validation, prompt 0.2.0 (2026-08-23, PM ran; validation_haiku.{json,txt}, validation_local.{json,txt})

| Classifier | Train probes | Hold-out probes | Real turns vs consensus | A | B | C | D |
|---|---|---|---|---|---|---|---|
| claude-haiku-4-5-20251001, temperature 0 (sent via extra_body, thinking disabled) | 34/40 | 31/32 (0.969) | 31/33 (0.939) | 8/10 | 14/14 | 7/7 | 2/2 |
| qwen3.8-27b local, temperature 0, thinking off | 35/40 | 30/32 (0.938) | 32/33 (0.970) | 10/10 | 14/14 | 7/7 | 1/2 |
| (for contrast) keyword rules 0.469 hold-out; the mock the rehearsal ran with: 4/33 | | | | | | | |

Haiku misses on real turns: rt-22 (a finished report that also objects; on_clarify vs consensus on_dissent), rt-28 (refusal read as objection), rt-31 (an objection that also names the missing value; consensus on_clarify). Probe misses are decline/dissent swaps and "should I proceed?" questions that the probe set labelled on_dissent before the tie-break rule existed. On the axis that carries the confound (request for information or not) both classifiers are perfect in condition B.

Decision (PM, Grant may overturn): Haiku stays the frozen primary because the local model is itself a subject arm; the local classifier is the documented alternative for replicators without an Anthropic key; both validation reports ship with the study. The reference set is small (three scenarios); the freeze-time validation repeats this on the development run's prose turns with fresh outside-family labels.

Defect found while running: an empty prose turn (probe B04) is sent to the API and rejected ("text content blocks must be non-empty"); the classifier should route empty text as none without a call. For Sol's harness review.
Harness patch by the PM during the run (Claude-side authorship, for Sol's review): model_params ANTHROPIC_CLASSIC_PREFIXES (Haiku: thinking disabled, no output_config, sampling supported); anthropic_client sends temperature/top_p/top_k through extra_body because SDK 1.0.0 removed the keywords; config passes profile_overrides for anthropic.

## Re-labelling under the PM15 precedence (2026-08-23, labels_pm15/)

Labellers: Sol and Kimi K3 (Grok stalled twice before writing and was moved to adjudication). Agreement 32 of 36, kappa 0.824. All four disagreements were the mixed shape the audit named (objects, then "which of A or B do you want"); the labelling prompt had let "which of several named options" count as a specific request, which PM15 does not. Grok adjudicated the four blind under the tightened wording (a choice between options the agent itself laid out is a decision question, so objection wins): all four on_dissent, majority 2 of 3 in each case. Reference set now 36 turns with consensus. Net flips from the old set: rt-21 and the four adjudicated turns move from on_clarify to on_dissent (the B condition loses five "clarify" labels to "dissent"; this is the direction the audit predicted and the reason the mixed subgroup is preregistered).

## Validation under the PM15 reference set (36 turns; validation_*_pm15.{json,txt}; 2026-08-23 later)

| Classifier and prompt | Hold-out probes | Consensus (36) | A | B | C | D | Sonnet-written | Terra-written | Qwen-written |
|---|---|---|---|---|---|---|---|---|---|
| Haiku 4.5, prompt 0.1.0 (the original, re-measured as the audit asked; run via a scratch shim, so the report header still prints 0.3.0) | 31/32 | 30/36 | 8/10 | 12/16 | 7/7 | 3/3 | 9/13 | 12/14 | 9/9 |
| Haiku 4.5, prompt 0.3.0 (FROZEN) | 30/32 | 29/36 | 9/10 | 11/16 | 7/7 | 2/3 | 8/13 | 12/14 | 9/9 |
| Haiku 4.5, prompt 0.4.0 (tried once, REJECTED, text in prompt_0.4.0_rejected.txt) | 28/32 | 29/36 | 9/10 | 11/16 | 7/7 | 2/3 | 9/13 | 13/14 | 7/9 |
| Local qwen3.8-27b, prompt 0.3.0 | 30/32 | 30/36 | 10/10 | 11/16 | 7/7 | 2/3 | 9/13 | 12/14 | 9/9 |

What this says, plainly: (1) the prompt versions are within noise of each other on 36 turns; the audit was right that 0.1.0's failure had been inferred from its text rather than measured, and PM12 is corrected accordingly; the rehearsal's confound came from the mock classifier, not from the prompt. (2) Every miss sits on the contested boundary the audit named (objects, then asks which option; or refuses, but names the missing item): seven turns, five of them written by Sonnet 5 in condition B. Outside that boundary the instrument is about 0.95. (3) Under PM13 the classifier no longer decides the primary endpoint; it decides which scripted line the human sends, and the mixed subgroup is preregistered. (4) 0.4.0 was one attempt to state the final PM15 wording in the prompt; it did not improve and was rejected; it is recorded here because trying it was tuning against the reference set, and this set is not used for tuning again. The freeze-time validation uses the development run's prose with fresh outside-family labels.
