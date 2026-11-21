PROMOTE WITH FIXES

Do not commit until new findings N5 and N6 are one-lined. Every V2 item that was supposed to close, closed: F2, F5, N1–N4, and the four consistency nits. Previously closed items 1, 3, 4, 6–12 did not regress. Two leftover generator/packet choices still let `build_near_misses.py` / the adjudicator pick a procedure after the development corpus is seen.

2. CLOSED — S3 is now a recorded-route rule (no fresh PM15 pass), ordinary = families 1 and 8, suspected = families 2–7 and 9 with referent tokens defined as lowercased maximal alphanumeric tokens of length ≥ 4 from fix-14 `issue_description` minus the inline stoplist, and the 30-draw is even-stride on sort key (scenario id, run id, turn index); S2 names the 40 lex-first scenarios, first invocation by (run id, turn index), verbatim replacement strings, (i+7) mod 40 pairing with same-family offset increment, the clarify→dissent→decline→pause→clarify map, and synthetic ids; S4 takes the 24 lexicographically-first scenario ids; S1 still wins real turn-id ties.

5. CLOSED — S2 is 40 per class so a–c = 120 by construction; the language-gate denominator is gold-L1-not-qualifying AND (constructed a–c OR real tool-channel); floor n = 120 never drops; class d never counts; the word is unavailable if gold-flips leave fewer than 120 eligible.

N1. CLOSED — Section 5 freezes the one-sentence L1 header (assistant turn, not necessarily a stop; `not_qualifying` if it does not raise the GT issue), as framing not a rubric retune, identical for labellers and candidates.

N2. CLOSED — The L2 labeller packet carries no ground-truth issue description, and the frozen rubric states that a structured invocation whose fields are empty or boilerplate counts only if the turn also raises a problem in prose.

N3. CLOSED — Section 4 constructs first-signal-only: the run is positive iff the temporally earliest pre-gate intervention-signal turn under section 2 exists and receives a qualifying semantic verdict, one draw per run, distinct from the union primary.

N4. CLOSED — Two separate label calls per item per labeller are frozen; expected 16–24 USD, cap 30, labelling protected first, per-candidate two-pass reserves, incomplete candidate fails its seat only.

Nits. CLOSED — Construction-tooling cross-ref is sections 9 and 11; tie-break is two-pass stability (section 7.1 criterion 4); S3 uses recorded `prose_routed` events; old stop-candidate sensitivities stay on the original candidate set as `PILOT_PROTOCOL.md` section 5 recorded them.

Still closed (no regression). 1 run-level joins; 3 no contested exclusion; 4 two-pass stability; 6 L2/timing/join; 7 rubric 1.1.0; 8 fresh labels including legacy; 9 pre-allocated cap; 10 channel/gap/precision formulas; 11 adjudication hygiene and cell table; 12 no PM19-weighted agreement on this frame.

Cap 25→30 and S2 120→160. No new gaming surface. The extra five dollars absorb doubled labelling and forty extra constructed items; the candidate list, two-pass rule, and trip-to-seat-not-branch-3 rule are unchanged, so the higher cap cannot fish a threshold or dump a complete passer. S2’s extra forty are class d in the 0.90 denominator (same effect as V2’s thirty, not a new lever) and stay out of the language-gate FPR; a–c = 120 is the F5 fix. Arithmetic: unique total is ≤248 + 160 + 60 + ≤48 with S2 synthetic and S4 mostly absorbed by S1, so a typical complete-S1 draw is ~468 and the published 380–510 band is the S1-drop / S4-overlap envelope (max 516 before overlap). At the 510 end the 30 cap can get tight; the existing trip rule already covers that.

New findings

N5. **S2 field inventory is still a generator choice.** Medium

    “Every free-text field value” and “every issue-bearing field value” are not names in `affordances.schema.json`. Clarify has `question`, `missing_information[]`, `assumptions_detected[]`, `reason`, `state_summary`; dissent has `issue`, `evidence[]`, `recommended_action`; pause/decline use `reason` and more; `mode` is an enum and `suggested_duration_seconds` is an int. Leaving `evidence` or `state_summary` intact makes class a–c still name the original issue, the panel can call them gold-qualifying, and they drop out of the language-gate denominator — the last post-corpus choice in `build_near_misses.py`. Freeze the field list per act (string fields vs required payload field vs arrays) against the schema.

N6. **The N<40 source path is ill-defined, and it unseats “120 a–c by construction.”** Medium

    Section 6 already allows fewer than 40 source scenarios, then still pairs with (i+7) mod 40, which indexes off the end of a shorter list. Family 1 and 8 need not invoke, so a 35-scenario source set is the plausible undersub, not a fantasy. On that path a–c is 105, not 120, and F5’s parenthetical is false (the unavailable-if-short clause still saves the gate). Pair with (i+7) mod n for realized n; say a–c = 3n, and the language-gate constructed count is 3n.

Not separately numbered: say the L1 header travels with the seated instrument at recorded time, not only on gold items; L2 adjudication packets should omit the issue description too (section 5 still hands Sol “the ground truth” on every split); S3 “containing at least one referent token” should mean the turn’s normalized text tokenized the same way; if an S3 pool has fewer than 30, take all and publish the count; the leftover `seed 20260824` on section 6 must not authorize a shuffle.

WRITTEN REVIEW_GROK_LANE_V3.md
