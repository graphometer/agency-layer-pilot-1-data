# Sol fix report — scorer class join and packet builder

Date: 2026-08-24

All work was offline. No provider or network call was made, `.env` and `<PRIVATE-FOLDER>/` were not read, the
461-item frozen gold-set file was not modified, and all changes remain uncommitted.

## Finding 1 — scorer rejoins the stripped construction class

Changed `docs/review/judge-validation/instrument-closure-lane/score_lane.py`:

- Added `--near-miss-intent`, defaulting to
  `docs/review/judge-validation/instrument-closure-lane/near_miss_intent.jsonl`.
- Added strict sidecar normalization for unique item ids and classes `a`–`d`.
- Joined construction class by item id in memory at score time. Every `nm-*` gold item must have a
  sidecar row; otherwise scoring raises `ValueError` with “refusing to score.” A conflicting class
  already present on a gold row also refuses.
- Implemented the language-gate denominator exactly as decided: L1 gold `not_qualifying` and either
  class `a`/`b`/`c`, or a non-synthetic tool-channel item. Class `d` cannot enter through the old
  “class is absent + tool” fallback.
- Exercised the realized files without scoring candidates: all 461 frozen items normalize, and all
  136 S2 items receive a score-time class join.

Golden coverage proves a class-a gold negative is included, a class-d gold negative is excluded,
and an unjoined `nm-*` id refuses.

## Finding 4 — class-d exclusions are restricted to the decided outputs

Changed `score_lane.py` so `specificity_tool_gold_negatives` excludes class d. That published value
is the tool-channel false-positive-rate complement and the section 8 tool-specificity splitter.

Class d remains in:

- raw agreement and kappa;
- recall;
- condition-by-channel cells and gaps;
- all-channel `specificity_gold_negatives`;
- stability and every other all-item figure.

The golden test plants both a class-d negative false positive and a class-d positive false negative,
then independently asserts agreement, recall, cell membership/accuracy, all-channel specificity,
and the class-d-excluded tool specificity.

## Finding 5 — deterministic opaque packet builder

Created `docs/review/judge-validation/instrument-closure-lane/build_packets.py` and its golden tests.
The builder consumes the frozen gold set, frame, `near_misses.jsonl`,
`near_miss_intent.jsonl`, and the live L1 rubric file. It writes:

- `l1_packets.jsonl` — model-visible `{request_id, prompt}` rows;
- `l2_packets.jsonl` — model-visible `{request_id, prompt}` rows;
- `packet_join.jsonl` — offline-only `{request_id, item_id}` bindings.

Each request id is the first 24 lowercase hex characters of SHA-256 over
`<item_id>-<track>-packet`. The builder checks for request-id collisions.

L1 includes the exact frozen one-sentence header, the live rubric text, the frame's fix-14
`ground_truth_issue`, and conversation through the current turn. Real items join frame rows by
`(run_id, turn_index)`; synthetic items use only the constructed near-miss text, after verifying it
matches the frozen gold row. L2 includes the frozen L2 rubric and only the current normalized turn
text; it has neither ground truth nor prior turns. The current-turn parts are newline-joined using
their `text` values only.

`add_panel_split` converts either base packet to an adjudication packet by appending the panel split,
so adjudication necessarily reuses the same L1-with-ground-truth or L2-without-ground-truth builder.

Two complete builds against the realized artifacts produced 461 L1 packets, 461 L2 packets, and 922
offline joins. All three files were byte-identical across runs. Model-visible rows have no item-id or
provenance fields, and their serialized files contain neither `nm-` nor `<LOCAL-PATH>`.

## Tests — before and after

Targeted lane test count before these fixes: **6 passed**.

Exact baseline command:

```sh
python3 -m unittest discover -s docs/review/judge-validation/instrument-closure-lane -p 'test_*.py' -v; status=$?; echo "BASELINE EXIT: $status"
```

Exact final line:

```text
BASELINE EXIT: 0
```

The preceding unittest summary was `Ran 6 tests in 0.002s` and `OK`.

Targeted lane test count after these fixes: **13 passed** (the original 6 plus 7 new scorer/packet
goldens).

Exact after command:

```sh
python3 -m unittest discover -s docs/review/judge-validation/instrument-closure-lane -p 'test_*.py' -v; status=$?; echo "LANE TESTS: 13 passed (exit $status)"
```

Exact final line:

```text
LANE TESTS: 13 passed (exit 0)
```

The existing Claude-lineage generator/assembler suite remains **33 passed**:

```sh
python3 -m pytest -q docs/review/judge-validation/instrument-closure-lane/tests; status=$?; echo "ASSEMBLY PYTEST EXIT: $status"
```

Exact final line: `ASSEMBLY PYTEST EXIT: 0` (pytest summary: `33 passed in 0.02s`).

Combined final count: **46 passed**.

```sh
python3 -m pytest -q docs/review/judge-validation/instrument-closure-lane/test_lane.py docs/review/judge-validation/instrument-closure-lane/test_build_packets.py docs/review/judge-validation/instrument-closure-lane/tests; status=$?; echo "ALL LANE TESTS: 46 passed (exit $status)"
```

Exact final line:

```text
ALL LANE TESTS: 46 passed (exit 0)
```

Real-artifact packet check final line:

```text
REAL PACKET CHECK: 461 L1 + 461 L2; 922 joins; byte-identical
```

## Ambiguities explicitly resolved or flagged

1. `REVIEW_GROK_LANE_CODE.md` was not present anywhere in this repository checkout. The lane README
   points to an external staging copy. The supplied findings 1, 4, and 5 and the README's recorded
   pre-score PM ratifications were complete enough to implement this scope; no unstated finding was
   inferred.
2. The phrase “no packet string contains any act name” cannot literally prohibit every occurrence
   of words such as `decline` or `pause`: both occur in the frozen L2 rubric, and ordinary frozen
   conversation may use them. It is implemented as a provenance/blinding rule: packet objects have
   no act field, and act values from either near-miss sidecar are never serialized. Tests use the
   source act `clarify` as a leakage sentinel. Frozen rubric and conversation text are not redacted.
3. No wire schema or output filenames were prescribed. The minimal model-visible schema is
   `{request_id, prompt}`; the three deterministic filenames are listed above. L1 role context is
   rendered with `User:`/`Assistant:` prefixes, while L2 adds no speaker or metadata prefix to its
   newline-joined current-turn text.

