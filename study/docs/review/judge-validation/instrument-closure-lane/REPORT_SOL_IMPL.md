# Sol implementation report — instrument-closure lane

Date: 2026-08-24

No provider, network, or paid call was made. Changes remain uncommitted for PM review. The requested external staging path was not writable in this session, so this repository-local copy preserves the handoff.

## Files created

- `build_frame.py` — deterministic offline frame projection.
- `frame.jsonl` — realized condition-invariant frame.
- `frame.jsonl.sha256` — repository-relative SHA-256 sidecar.
- `score_lane.py` — L1 semantic and L2 timing qualification, publication tables, language gate, and tie-break scorer.
- `test_lane.py` — synthetic offline contract tests.
- `REPORT_SOL_IMPL.md` — this fallback handoff copy.

No near-miss generator, gold assembler/sampler, or item-selection code was created.

## Existing machinery reused

`build_frame.py` imports the recorded-run implementation directly:

- `evals/grading/blind.py`: `blind_transcript`, `clean_text`, `excerpt_hash`, and the frozen affordance map for PM13/PM15 normalization, stable turn keys, mixed-row joining, and the full scrub set.
- `evals/grading/grade.py`: `_consequence_scan` for the fix-14 execution-position `primary_gate_anchor_union` boundary. The route map is used only to annotate historical prose-stop events; there is no fresh router pass or candidacy gate.
- `evals/grading/judge.py`: `render_issue_description` for current fix-14 ground truth and `judge_projection` for the recorded channel-neutral transcript-through-turn view.
- `evals/grading/common.py`: existing JSON/JSONL and scenario readers/writer.

The scorer follows committed `qualify_freeze.py` conventions while adding every lane-specific L1/L2 figure. Gate and tie comparisons use unrounded ratios; only Markdown formatting rounds values.

## Frame corpus facts

The 360 development runs plus 90 filler runs produced 3,436 unique `(run_id, turn_index)` units.

| Condition | Prose | Tool | Total |
|---|---:|---:|---:|
| A | 884 | 0 | 884 |
| B | 664 | 0 | 664 |
| B_filler | 762 | 0 | 762 |
| C | 472 | 82 | 554 |
| D | 485 | 87 | 572 |
| **Total** | **3,267** | **169** | **3,436** |

There are 52 mixed prose-plus-structured-intervention turns; each is one `tool` frame unit. Runs without a located gate contribute 2,627 retained turns. No frame row is at/after its gate, ids and `(run_id, turn_index)` pairs are unique, and no run had a consequential check count with an undetected fix-14 anchor.

SHA-256: `18a27aa449372465d1f6769cb246726128ab77df74ad89e904c7ac7bd13c02ca`

The build was run twice with the same digest. Exact sidecar verification output:

`docs/review/judge-validation/instrument-closure-lane/frame.jsonl: OK`

## Tests

Lane tests: 6 passed.

Exact command:

`python3 -m unittest discover -s docs/review/judge-validation/instrument-closure-lane -p 'test_*.py' -v && echo 'LANE TESTS: 6 passed'`

Exact final output line:

`LANE TESTS: 6 passed`

They prove the pre-gate cut, channel formula, mixed-turn unit, no-gate rule, n=5 cell floor/thin publication, gap arithmetic, strict parse convention, all/tool specificity, all-gold stability pairing, L2 timing target, and the tool-specificity tie splitter.

Existing grading regression command:

`PYTHONPATH=evals/grading python3 -m unittest discover -s evals/grading/tests -p 'test_*.py'`

Result: `Ran 57 tests in 47.168s`; `OK (skipped=2)`. The suite printed its existing `jsonschema.RefResolver` deprecation and missing-manifest warnings.

## Frozen-spec ambiguities flagged

1. Sections 7–8 require two passes but do not say whether accuracy/gaps/recall are pooled. Following `qualify_freeze.py`, pass 1 supplies gates and tie-break figures; pass 2 is fully reported and paired with pass 1 for stability.
2. “Judge-independent condition-by-channel weighted agreement” does not restate the new-frame weighting. The scorer weights by complete-frame cell frequencies, renormalized over gold-represented cells, and records covered mass.
3. Strictness is explicit for agreement but not invalid answers in specificity. Following the prior scorer, invalid is an agreement error and a gold-positive FN, but only exact `qualifying` is an FP; specificity remains exactly `1 - FP / gold negatives`.
4. The language gate does not separately name the comparison prose-FPR denominator. The scorer uses all L1 gold-negative prose items. The special denominator remains gold-negative class a/b/c union real tool turns, excluding class d.
5. Section 3 names turn units while the unchanged rubric consumes context through the turn. Rows store both normalized current-turn content and the existing `judge_projection` through that turn; mixed content is not split.
6. Expected cost cannot be inferred from labels. The CLI accepts `--cost NAME=EXPECTED_COST`; a cost-level tie with missing costs is reported unresolved, never broken by candidate name.

The scorer was not run on candidate answers because frozen gold/candidate artifacts do not yet exist and section 9 forbids candidate scoring before gold freezes.
