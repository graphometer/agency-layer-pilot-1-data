# Adversarial review — instrument-closure post-label machinery

**Verdict: PROMOTE WITH FIXES**

Do not dispatch `run_candidates.py` as-is. The gold/queue/concordance scripts implement the frozen section 5 / ratification (d) / audit-gate machinery fail-closed and can run. The paid candidate runner’s settlement path undercounts real spend against the $30 lane cap, and its advertised `--retry-exhausted` recovery collides with `journal_state`’s uniqueness rules. Those two must be fixed before any candidate or router call. A freeze-file gate should be added in the same pass so a candidate answer cannot exist before `GOLD_FREEZE.json`.

What is faithful (established from the files, not a reason to skip the fixes):

- Wire configs match `judge.py` `COMPATIBLE_JUDGE_CONFIGS` for the seated pair: `mistral-medium-2604` at `https://api.mistral.ai/v1`, `max_tokens=8`, `stop=["\n"]`; `minimax/minimax-m3` via OpenRouter, `max_tokens=8192`, `stop` omitted (`stop_supported: False`). Router sampling is `FROZEN_SAMPLING` (`temperature` 0, `max_tokens` 8), prompt is `FROZEN_PROMPT` as the system message, user text is `clean_text` of the raw transcript turn, empty/whitespace short-circuits to no call. Intervention routes are `{on_clarify, on_dissent, on_decline}`; tool-channel gold is `attempt` with no router; router failure/missing parse is `cannot_determine`.
- `finalize_gold.py` implements both track modes, the >1-of-20 per-track audit gate, audit abstention as disagreement, audit answers standing on a failed track, plain-packet escalation coverage as an exact set, split membership asserted against the committed queues, and ratification (d) refuse-closed (no panel-majority substitute).
- `build_escalation_queue.py` emits 393 L2 rows as `{request_id, prompt}` from `l2_packets.jsonl` with votes stripped. `build_legacy_queue.py` emits the 71 freeze-qualification splits, never reads Fable’s answers. `concordance_71.py` flags `flips > 14`, counts Sol `cannot_determine` as a flip.
- Gold does not read candidate outputs. Semantic/timing interchange is `{id, parsed}` with timing vocabulary `attempt` / `no_attempt` / `cannot_determine`, which `score_lane.normalize_answers` accepts. `candidate_prices.json` is the table actually loaded (the documented mistral 1.5/7.5 vs stale `instrument_prices.json` 0.4/2.0 split is real).

---

## Findings

### 1. high — `run_candidates.py` lines 215–218 and 270–282 — failed and unmetered calls settle at $0

`one_call` turns missing `usage` into `0, 0`:

```215:218:docs/review/judge-validation/instrument-closure-lane/run_candidates.py
    usage = getattr(response, "usage", None)
    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    return content, input_tokens, output_tokens
```

The exception path then feeds those zeros (or the zeros stuffed in at 274) to `cost_usd` and journals that as `charged_usd`:

```273:282:docs/review/judge-validation/instrument-closure-lane/run_candidates.py
            except Exception as exc:  # noqa: BLE001 — journalled, then retried
                raw, input_tokens, output_tokens = "", 0, 0
                error = f"{type(exc).__name__}: {exc}"
            charged = cost_usd(price, input_tokens, output_tokens)
            append_journal(journal, {
                "event": "settled", "request_id": request_id, "attempt": attempt,
                "charged_usd": round(charged, 8),
```

Once a terminal `completed`/`exhausted` event exists, `journal_state` (imported from `run_labels.py` lines 322–327) charges every prior reservation at `settlement.charged_usd`, not at bound. Four timed-out or usage-less attempts therefore count as $0 against `LANE_CAP_USD` while the provider may have billed. The module docstring at lines 13–16 claims the imported fail-closed design. That design, in `run_labels.py` 440–462, settles missing usage and exceptions at the reserved bound.

The per-call cap check at 258–263 is then computed from an understated `lane_charged_so_far`, so a real-dollar breach of the frozen $30 cap (LANE_PROTOCOL §9) is possible.

**Minimal fix:** In `run_queue`, if `one_call` raises *or* either token count is missing/None, journal `charged_usd` equal to that attempt’s `bound` (the `run_labels.py` 440–462 rule). Do not coerce missing usage to 0 inside `one_call`; return `None` for missing counts and let settlement decide.

### 2. high — `run_candidates.py` lines 240–245 and 256 — `--retry-exhausted` cannot resume

Todo selection re-queues exhausted ids when the flag is set:

```240:245:docs/review/judge-validation/instrument-closure-lane/run_candidates.py
    for request_id, system, user in queue:
        if request_id in completed or request_id in ambiguous:
            continue
        if request_id in exhausted and not retry_exhausted:
            continue
        todo.append((request_id, system, user))
```

The attempt loop always restarts at 1:

```256:256:docs/review/judge-validation/instrument-closure-lane/run_candidates.py
        for attempt in range(1, MAX_ATTEMPTS + 1):
```

`journal_state` (`run_labels.py` 287–290) raises `RunnerError` on a second `settled` event for the same `(request_id, attempt)`. The exhausted item already has settlements at attempts 1–4, so the advertised recovery path crashes on the first retry settlement. `run_labels.py` 412–421 starts at `max(previous_attempts)+1` for this reason; `REPORT_SOL_RUNNER_V2.md` line 33 records that as the runner contract this file claims to import.

A first dispatch without the flag is still wrong to run until finding 1 is fixed; this finding additionally means an exhausted cluster cannot be recovered without manual journal surgery.

**Minimal fix:** Copy `run_labels.run_one`’s attempt numbering: `first_attempt = max(previous attempt numbers for this request_id, default 0) + 1`, then `range(first_attempt, first_attempt + MAX_ATTEMPTS)`.

### 3. high — `run_candidates.py` `main()` (364–458) — paid answers can exist before gold freezes

LANE_PROTOCOL §9 step 3–4 (lines 267–270): gold freezes, hash recorded, **“No candidate score is computed before this point.”** A search of `run_candidates.py` for `GOLD_FREEZE` / `gold_final` returns no matches. `main()` loads `goldset_lane.jsonl` and `l1_packets.jsonl` and, on the default path and on `--probe`, writes journals and parsed rows under `candidates/` with no freeze-file check.

`finalize_gold.py` does not read anything under `candidates/`, so gold cannot come to depend on candidate behaviour. The hole is the other direction: nothing in this script stops a candidate answer from existing before `GOLD_FREEZE.json`.

**Minimal fix:** Before constructing a client or appending a journal on `--probe` and on the full paid path, require `HERE / "GOLD_FREEZE.json"` to exist (optionally assert its `gold_final_sha256` matches `sha256_file(HERE / "gold_final.jsonl")`). `--dry-run` may stay ungated; it writes no answers.

### 4. medium — `run_candidates.py` lines 382–385 vs 434–458 — full paid run never assembles timing interchange

The module docstring (lines 19–24) says the script “assembles the timing pass files.” `assemble_timing` is invoked only under `--assemble-timing` (382–385). The full run (434–458) writes `candidates/router_pass{n}.jsonl` and returns. `score_lane.py` 503–507 requires `--timing PASS1 PASS2` files with `{id, parsed}` in `{attempt, no_attempt, cannot_determine}`. Those files are `timing_pass{n}.jsonl` produced only by the extra flag.

Separately, `assemble_timing` lines 337 and 350–352 treat a missing `router_pass{n}.jsonl` as an empty dict and map every non-empty prose item to `cannot_determine` without refusing. That is the correct *exhausted-item* convention (strict, counts against the instrument) and the wrong *forgotten-assemble* convention: a complete-looking 461-row timing file can be all-abstain on prose.

**Minimal fix:** Call `assemble_timing` at the end of the full run. If any `needs_router` id lacks a completed `parsed` route in that pass’s journal, refuse to assemble (or print INCOMPLETE and exit 2) unless the missing ids are journalled `exhausted`/`ambiguous`, in which case `cannot_determine` is the specified strict outcome.

### 5. medium — `run_candidates.py` lines 391–409 — dry-run worst-case is not the remaining bound

The dry-run sums `2 * call_bound(...)` over every L1 packet for both semantic endpoints plus both router passes, then adds `lane_charged_so_far(all_journals())`. It does not:

- subtract already-completed journal ids (a resume dry-run double-counts finished candidate work and can false-refuse a legal continuation);
- multiply by `MAX_ATTEMPTS` (4), even though each retry reserves a fresh bound (line 257);
- run at all on the live path. `run_labels.py` 680–684 refuses to start when charged + remaining one-dispatch bound exceeds budget. `run_candidates.main()`’s paid path has no equivalent startup check, only the per-attempt check at 258–263.

`--dry-run` is therefore not an honest worst-case gate. Combined with finding 1, it is the only pre-dispatch bound the operator is told to trust.

**Minimal fix:** Project remaining work the way `run_labels.projected_cost` does (skip `completed | exhausted | ambiguous` unless `--retry-exhausted`). Keep the live per-attempt reserve. Optionally refuse to start the paid path when remaining one-attempt bound already exceeds `LANE_CAP_USD - charged` (retries still stop at the per-call check).

### 6. medium — `run_candidates.py` line 373 — `require_prices` is imported-adjacent but never called

`load_prices` is called; `require_prices` is not. `run_labels.py` 210–225 refuses placeholder / missing-source / negative rows before any dispatch. `candidate_prices.json` as committed is well-formed and is the correct table (mistral 1.5/7.5, matching its `_comment` vs `evals/grading/instrument_prices.json` line 4). The live path still will not refuse a later placeholder edit.

**Minimal fix:** After `load_prices(PRICE_FILE)`, call `require_prices` against `CANDIDATES + (ROUTER,)` (adapt the labeller-shaped helper, or inline the same four checks on `endpoint.price_id()`).

### 7. medium — `run_candidates.py` lines 434–452 — no per-candidate reserved allowance

LANE_PROTOCOL §9 (lines 281–284): after protected labelling, “Each candidate then holds a **reserved scoring allowance** sized for its two full passes … If the cap trips: candidates with a complete two-pass score are judged normally; an incomplete candidate fails **its seat only**.”

The implementation is a single remaining pool, cheapest-first (router, mistral, minimax). That ordering maximises the chance of complete cheap seats, but it does not *hold* an allowance: a mistral overrun consumes budget that the protocol reserved for minimax’s two passes. Line 457 then prints `candidate runs complete` regardless of whether any journal has 461 completed rows (partial resolved files are still written at 453–455; `score_lane.normalize_answers` / `score_pass` treat missing ids as unparseable via `answers.get`, so an incomplete file can be scored as a finished instrument and fail its gates quietly).

**Minimal fix:** Before each candidate’s two passes, compute that candidate’s remaining two-pass one-attempt bound; refuse to start it if `charged + that bound > LANE_CAP_USD` (its seat fails complete; already-finished seats stand). At process exit, if any paid journal’s completed set is smaller than its queue, print INCOMPLETE and exit 2.

### 8. medium — `finalize_gold.py` lines 175–177 and 217–222 — ratification (d) 1–5 drop path is not implemented

README pre-adjudication-read ratification (d): a Sol `cannot_determine` / unparseable on a split or escalated item **drops from that track’s scoring denominators**, published by count and item id; **more than 5** on either track pauses the lane. The script appends every such answer to `drops` and then always `SystemExit`s, including on a single drop. The docstring at lines 14–16 is explicit that the ≤5 path is deferred.

That is fail-closed, and expected incidence is zero, so it is the right pose *before* a drop exists. It is not the frozen 1–5 behaviour. If a drop materializes, this file as written cannot produce `gold_final.jsonl`.

**Minimal fix:** Keep the current refuse. Do not implement silent dropping inside this script without a reviewed scorer extension. If a drop appears, stop and review — which is what this code already does. No code change required unless the lane prefers to pre-implement the 1–5 path now; if so, drop only that track’s label, publish ids in `GOLD_FREEZE.json`, and refuse at >5.

### 9. low — `finalize_gold.py` `load_answers` (57–68) and `concordance_71.py` line 41 — Sol answers are not stripped

`run_labels.parse_answer` strips. Sol staging rows currently in `sol_adjudications_l1.jsonl` / `sol_legacy_71.jsonl` are already bare words (`"answer":"qualifying"`). A trailing newline would miss `VOCAB` / fail `!= fable[id]` and trigger ratification (d) or a concordance flip.

**Minimal fix:** `answer = str(...).strip()` at both load sites.

### 10. low — `concordance_71.py` lines 35 and 56 — Fable map is last-wins and unchecked for coverage

```35:35:docs/review/judge-validation/instrument-closure-lane/concordance_71.py
    fable = {row["id"]: row["label"] for row in read_jsonl(FREEZE_QUAL / "adjudications.jsonl")}
```

Duplicate Fable ids silently last-win. A queue id missing from Fable raises `KeyError` at line 56 rather than the `SystemExit` used for Sol coverage at 42–46.

**Minimal fix:** Refuse duplicate Fable ids; require `set(queue_ids) <= set(fable)` with a `SystemExit`.

### 11. low — `finalize_gold.py` lines 81–84 — panel label maps last-win on duplicate `request_id`

A 462-line file with one duplicate and 461 unique ids passes `len(rows) != EXPECTED_ITEMS`. `run_labels.load_label_map` (524–535) refuses duplicates.

**Minimal fix:** Same uniqueness check as `load_answers`.

### 12. low — `run_candidates.py` line 67 vs `prose_classifier.py` line 73 — retry count 4 vs production 3

Lane `MAX_ATTEMPTS = 4` matches `run_labels.py` line 35. Production `CLASSIFIER_MAX_ATTEMPTS = 3`. After exhaustion the lane maps to `cannot_determine` (the briefed strict convention) rather than the production keyword fallback (`prose_classifier.route` 393–403). The retry-count mismatch is not the authority mismatch; the authority mismatch is the specified one. Note only.

**Minimal fix:** None required for spec fidelity as briefed. If production-retry identity is wanted later, set router attempts to 3; do not adopt keyword fallback.

### 13. low — `build_escalation_queue.py` line 50 and `build_legacy_queue.py` line 48 — `json.dumps` default `ensure_ascii=True`

`build_packets.py` 202 writes packets with `ensure_ascii=False`. After `json.loads`, the `prompt` string is the same (em dash vs `\u2014` is an encoding difference, not a packet difference). Sol dispatch that sends `row["prompt"]` is unaffected. Byte-identity of the jsonl line with the source packet is not preserved.

**Minimal fix:** `json.dumps(..., sort_keys=True, ensure_ascii=False)` to match `build_packets._jsonl_bytes`.

### 14. low — `run_candidates.py` 186–189 — `labels/probe/*.journal.jsonl` is outside the $30 meter

`LABELS.glob("*.journal.jsonl")` is not recursive, so the six probe journals under `labels/probe/` are omitted. Candidate probes under `candidates/probe_*.journal.jsonl` *are* included. README records label-probe spend as ~$0.03. Not material at the cap, but it is paid spend outside the lane journal set this file claims to sum.

**Minimal fix:** Include `labels/probe/*.journal.jsonl` in `all_journals()`, or document that the $8/$20 label-dispatch budget already absorbed it and leave the glob.

---

## Spec checks that passed (so they are not findings)

**A. Frozen-spec fidelity.** `CANDIDATES` / `ROUTER` match `COMPATIBLE_JUDGE_CONFIGS` `mistral-primary` / `minimax-secondary` and `llm_classifier.FROZEN_PROMPT` / `FROZEN_SAMPLING` / `parse_route`. Semantic parse is `judge.parse_verdict`. Router user content is `clean_text` of `transcript.jsonl` assistant `text` (same source `build_frame.py` 129 uses for `has_prose_text`); contradiction with the frozen bit refuses (169–173). Empty text: production `classify("")` / `route` short-circuit to `none` with no call (`llm_classifier.py` 134–137, `prose_classifier.py` 368–374); `assemble_timing` 346–347 maps that to `no_attempt`; `needs_router` 376 drops those ids. Tool channel is `attempt` (342–343) per section 2 (structured signal, no router). Router failure → `cannot_determine` (350–351) under the strict convention, not the production keyword fallback.

Audit gate: `len(disagreements) > 1` (finalize_gold 139–140) is “more than 1 of the 20”. Abstention ≠ unanimous label, so it counts (134, README (d)). Failed-track audit answers stand (194–195); escalation set is unanimous-non-audit exact (156–166). Escalation rows are plain L2 packets (build_escalation_queue 44). Ratification (d) never substitutes panel majority (188–192 always take Sol on splits).

**B. Money (aside from findings 1, 5–7, 14).** Reserve is fsynced before `one_call` (264–269 then 271). Journals are the resume authority; `completed` and `ambiguous` are never redispatched. Prices come from `candidate_prices.json`, not the stale mistral row. Label journals are in the $30 sum.

**C. Determinism.** Outputs use `sort_keys=True` and stable id sorts (`finalize_gold` 182, `resolve_semantic_outputs` 327, `assemble_timing` 356). `GOLD_FREEZE.json` hashes inputs, not wall clock. `time.sleep` is not written into anything scored. Queue builders preserve source-file order.

**D. Selection-uninformed (aside from finding 3).** `finalize_gold.py` reads panel labels, committed queues, and Sol staging files only. `run_candidates.py` reads `goldset_lane.jsonl` (ids/channel) and L1 packets, never `gold_final.jsonl` labels.

**E. Joins / vocabulary (aside from findings 4, 9–11).** `request_id` in `finalize_gold.py` 44–45 matches `build_packets.py` 52–55. `packet_join.jsonl` is `request_id → item_id`; `resolve_semantic_outputs` emits `{id, parsed, raw}`. Timing emits `{id, parsed}` with the scorer’s L2 allowed set. S2 synthetics are `channel: tool` (`goldset_lane.jsonl` 237); a synthetic on prose refuses (153–154).

REVIEW COMPLETE
