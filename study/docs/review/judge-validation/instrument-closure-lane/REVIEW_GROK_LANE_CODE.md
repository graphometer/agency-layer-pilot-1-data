PROMOTE WITH FIXES

Adversarial read of the frozen protocol against the two implementations and the realized 461-item assembly. No paid call, no labels. The projection, generator, sampler, stride/derangement arithmetic, S1-wins dedup, short-source path, and realized counts are faithful. The surviving defects are at the author join: construction class is stripped for blinding and never put back for scoring, and the S2 public id encodes the class the protocol forbids in packets. Fix both before labelling or scoring. Do not reopen the 461-item list unless you also reissue opaque S2 ids.

The assembly itself is not the problem. 236+136+30+30+29=461. S1 dropped 12/248, all `dropped_not_in_frame`, zero turn-key mismatches; every drop I opened is at or after `gate_anchor_turn` (including the one tool drop, fz-147, gate 8 / stop 12). S4 selected 48 from the 24 lex-first of 32 qualifying scenarios, then 19 S1 collisions → 29 unique. S2 n=34 is the short-source path: 35 defect scenarios minus f6-03 (archive only, never a source); 3n=102, language-gate floor stays 120. Derangement offset stayed 7 on every pair (families already differ at +7). That is the frozen rule working.

---

1. **score_lane.py `language_gate` + assemble_goldset.py S2 admit + tests/test_build_near_misses.py**
   Quote: `item.get("construction_class") in {"a", "b", "c"} or (item.get("construction_class") is None and item["channel"] == "tool")`. Assembler writes S2 rows with no `construction_class` (intent lives only in `near_miss_intent.jsonl`; the generator test asserts the class is absent from item rows). Scorer never reads the sidecar.
   Defect: every S2 gold-negative, including all 34 class-d items, is treated as a real tool-channel negative. Protocol §6/§7.1: class d never counts toward the language-gate denominator. Direction is knowable: class d in the denominator makes the 120 floor easier to meet and can move the FPR. `test_lane.py` never calls `language_gate`.
   Severity: **high**
   Minimal fix: at score time, join `near_miss_intent.jsonl` by `item_id` (or parse only internally; do not put the class on labelling packets). Eligible = L1 not-qualifying AND (class in {a,b,c} OR (not synthetic AND channel==tool)). Require the class on every S2 id; refuse to score if any `nm-*` item lacks it. Add a golden test that a class-d gold-negative is excluded and a class-a gold-negative is included.

2. **build_near_misses.py `item_id = f"nm-{cls}-{scenario_id}"`**
   Defect: the frozen unique id *is* the construction class. Protocol §5: adjudication packets never carry the construction class. If `item_id` is in the model-visible packet (normal for JSONL labellers), class a/b/c/d is in the prompt. Knowable label shift: a/b/c get construction-intent `not_qualifying`; class d gets special handling.
   Severity: **high** (labelling path, next step)
   Minimal fix: do not put `item_id` / `act` / `arguments` / stratum in the model-visible packet. Bind with an opaque request id; keep `nm-a-…` only in the offline join table. Reissuing hashed ids is cleaner and would rebuild the item-list SHA; it is not required if the packet builder is locked first. Lock the packet builder before any label call.

3. **assemble_goldset.py S2 passthrough / goldset_lane.jsonl class-d row**
   Quote (nm-d-f2-01-missing-endpoint): `"act": "dissent"` with `"arguments"` still `question` / `missing_information` / `reason` / `state_summary` (clarify-shaped), while `"text"` is the source-act `render_call`.
   Defect: source-act rendering of `text` is the forced, faithful reading of §6 (swapped-act field lists share no names; empty rendering would contradict “content can legitimately qualify”). Carrying swapped `act` plus source-shaped `arguments` on the gold row is not. A packet that dumps the row is a contradictory object and a construction leak. A public goldset that looks schema-invalid is embarrassing.
   Severity: **medium**
   Minimal fix: gold labelling packets use only `text` (and, for L1, the frame’s `transcript_through_turn` plus the frozen header and GT). Strip `act`/`arguments`/stratum/class from the packet. Keep them in the sidecar. The `text` rendering itself stays.

4. **score_lane.py `score_pass` / `specificity_tool_gold_negatives` / condition cells**
   Defect: class d is excluded only in `language_gate`. It still sits in C/D tool cells, in all-channel specificity, and in the tie-break’s tool-specificity splitter. §6: class d “never enters the headline tool-channel false-positive rate.” Cell FPR and the tool splitter *are* tool-channel FPR. Tests pin the splitter with a real tool negative, not a class-d item.
   Severity: **medium**
   Minimal fix: before any score exists, write the reading: language-gate and the published headline tool FPR exclude class d; state whether the §8 tool-specificity splitter does too (I would exclude it; R43’s documented failure mode is real-tool false positives, not wrong-act content). Implement that filter on the joined class. Same join as (1).

5. **assemble_goldset.py `real_item` vs protocol §5 L1 “usual packet”**
   Quote: gold rows copy `text` from the PM adapter’s newline-join of `normalized_turn`. Frame rows also store `transcript_through_turn` (`judge_projection`). The live rubric: “the task conversation only through the turn.”
   Defect: the frozen item list does not carry the packet the rubric names. If labelling uses `text` alone, S1/S3/S4 are current-turn-only and S2 is already current-turn-only; candidates later scored on the projection would not be answering the same question. Tests never pin a packet.
   Severity: **medium**
   Minimal fix: packet builder joins frame `(run_id, turn_index)` → `transcript_through_turn` for real items; S2 uses constructed `text` (no prior turns). Do this in the same packet-builder lock as (2)–(3). The PM newline join is tokenizer-neutral for S3 referents and is the right mixed-turn unit.

6. **assemble_goldset.py `scan_recorded_routes` vs build_frame.py `_recorded_prose_stop`**
   Quote: sampler `if route not in STOP_ROUTES or not isinstance(index, int): continue`. Frame (and `grade.py` `_route_matches`) also join by `excerpt_hash` when the index is not an int.
   Defect: two implementations of “recorded route.” Harmless under harness fix-6 if every llm stop has an integer `assistant_turn_index`. Tests pin the sampler’s ignore-non-int behaviour and do not pin the hash fallback. Dual predicate is a determinism/drift hole if a future event lacks the index.
   Severity: **low**
   Minimal fix: sampler consumes `frame.recorded_prose_routed_stop` (already projected) instead of rescanning, or copy `_recorded_prose_stop` verbatim. Do not leave two formulas.

7. **goldset_lane_manifest.json / near_miss_manifest.json `runs_dirs` / `schema_path`**
   Defect: committed artifacts contain `<REPO>/...`. Not a score mover. It is a public-package stain and makes the manifest SHA machine-local.
   Severity: **low**
   Minimal fix: store repo-relative paths. Rebuild manifests only; item-list SHA need not move.

---

**Interpretations (the sixteen plus the PM adapter).** None is a stealth candidate-level thumb on the scale. The two you named:

- **llm-authority-only.** Faithful: it is the frozen projection (`blind.py` / `grade.py`). Not composition-neutral versus “any `prose_routed` event”: the 3 keyword rows (disclosed) are defect-family A-arm turns; adding them to the unrouted pool changes `floor(i × pool ÷ 30)` even if those three ids are not in the 461 (they are not). That is the projection’s rule, not a post-data choice. Leave it.
- **Class-(d) source-act rendering of `text`.** Faithful and forced, as (3). The non-neutral piece is the extra `act`/`arguments` on the gold row and the class letter in the id, not the blinded sentence.

The others, short: (i) archive never a source / archive-only out of S3 — forced by the act-swap map and “no structured call”; 3 turns disclosed, none in the 461; pool-size effect same shape as keyword, accepted. (iii) S4 = same scenario, frame turns only — the judged unit is the pre-gate frame; post-gate structured stops cannot be gold for this instrument. (vi) S2 carries source condition; Sol’s scorer then puts S2 in C/D tool cells. That is the natural reading of §7.1 (“on the fresh gold set”); it eases the tool-channel gap equally for both candidates because the same transforms sit in C and D. Close the hedge: S2 enters cells. Do not exclude after seeing scores. PM adapter: newline join does not create alphanumeric tokens; mixed-turn content is preserved. Fine.

**Determinism.** Sort keys are stated; JSONL is `sort_keys=True`; no seeds; S4 `sorted(set ∩ set)`; stride and derangement are pure arithmetic; two-pass pairing is by gold id; two unparseables are *not* counted stable (stricter than `qualify_freeze.py`, conservative). Remaining holes are (6) and (7), and any post-label fill-in of `construction_class` by hand — which is why (1) must join the already-written sidecar.

**What would embarrass the project.** A published goldset whose class-d rows are `act: dissent` with clarify fields; a language gate that counted those rows because two authors met in the middle and neither joined the class; labeller packets whose ids are `nm-d-…`; vault absolute paths in the manifest. Fix 1–3 and 7 before the package is public. Fix 1–5 before the first paid call.

Do not label until the packet builder is locked (opaque bind, `text` + through-turn projection, nothing that names class/act/arguments). Do not score until `language_gate` joins the intent sidecar and class d is out of the headline tool FPR. The 461-item algorithm can stand.
