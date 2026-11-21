# Re-certification — instrument-closure post-label fix pass

**Verdict: PROMOTE**

The three high findings that blocked dispatch (settlement at $0, `--retry-exhausted` attempt collision, freeze-file gate) are fixed in the claimed shape. The medium/low items match the dispositions, including the two “keep as-is” poses (8, 13). Tests in `test_run_candidates.py` encode the right oracles for findings 1–4 and 6; this recert did not execute them (shell was unavailable). New defects from the fix pass are residual/process-level, not first-dispatch cap or gold-leak holes. Dispatch of `run_candidates.py` is no longer blocked on the original review.

---

## Finding-by-finding

### 1. high — settle-at-bound on error/missing usage — **FIXED**

`one_call` (`run_candidates.py` 240–267) returns `int | None` token counts. Missing `usage`, missing `prompt_tokens` / `completion_tokens`, and `None` usage all stay `None`; zeros are no longer stuffed in.

`run_queue` (327–338) sets tokens to `None` on exception and journals `charged_usd = bound` when `error is not None` or either count is `None`. A successful parse with real usage still goes through `cost_usd` (actual, uncapped — same as `run_labels.run_one` 440–447).

`test_exception_settles_at_bound_not_zero` and `test_missing_usage_settles_at_bound` cover both legs; `test_success_settles_at_actual_usage` keeps the non-regression.

### 2. high — attempt numbering continues from journal maximum — **FIXED**

`run_queue` 304–313 copies `run_labels.run_one` 412–421: `first_attempt = max(previous attempt numbers for this request_id, default 0) + 1`, then `range(MAX_ATTEMPTS)` offsets. `journal_state` will not see a second `settled` for attempts 1–4 on `--retry-exhausted`.

`test_retry_exhausted_continues_attempt_numbering` asserts reserved attempts `[1, 2, 3, 4, 5]` and a completed resume. `test_without_flag_exhausted_not_redispatched` still holds.

### 3. high — `require_freeze()` on probe and paid paths — **FIXED**

`require_freeze()` (212–228) refuses unless `GOLD_FREEZE.json` and `gold_final.jsonl` both exist and `gold_final_sha256` matches the file on disk.

`main()` calls it at 512–513, after the `--dry-run` return (498–510) and after `--assemble-timing` return (459–462). `--probe` (515) and the full paid path therefore cannot construct a client or append a journal before freeze. `--dry-run` stays ungated, as specified.

Tests: `test_require_freeze_refuses_without_files`, `test_require_freeze_refuses_hash_mismatch`.

### 4. medium — assemble timing at end of full run; refuse non-journalled missing routes — **FIXED**

Full run calls `assemble_timing` for passes 1 and 2 at 604–605, only after the completeness audit; an incomplete journal set `SystemExit`s 2 first and never writes a fake all-abstain timing file.

`assemble_timing` (395–430): tool → `attempt`; empty prose → `no_attempt`; completed intervention route → `attempt`; other completed parse → `no_attempt`; `exhausted` or `ambiguous` → `cannot_determine`; **else** `SystemExit` with `INCOMPLETE`. That is the claimed split: `cannot_determine` only for journalled exhausted/ambiguous.

Tests: `test_assemble_timing_refuses_unfinished_router`, `test_assemble_timing_exhausted_becomes_cannot_determine`.

Note (not a miss of the claim): standalone `--assemble-timing` raises `SystemExit(str)` so the process status is 1, not 2. The full-run INCOMPLETE path is exit 2. Finding 4 allowed “refuse or exit 2”; refuse is in.

### 5. medium — dry-run and startup preflight are resume-aware one-attempt projections — **FIXED**

`remaining_bound` (469–487) skips `completed | ambiguous`, and skips `exhausted` unless `--retry-exhausted` — the same todo filter as `run_queue`, one `call_bound` per remaining item (not `MAX_ATTEMPTS ×`).

`--dry-run` (498–510) sums that over both router passes and both candidate passes, adds `lane_charged_so_far(all_journals())`, and `BudgetError`s if the sum exceeds `$30`.

Paid path startup (538–547) is the same check. Live per-attempt reserve at 316–320 is unchanged.

Cosmetic: the dry-run log still prints full queue sizes (`semantic 461x2x2 + router Nx2 calls remaining`) even when `worst` is a resume remainder. The dollar figure and the refuse are resume-aware; the count phrase is not.

### 6. medium — `validate_prices` refuses missing/placeholder/non-positive rows — **FIXED**

`validate_prices` (197–209) is called at 449–450 on `CANDIDATES + (ROUTER,)` via `price_id()`. It refuses missing rows, non-numeric or `<= 0` `input_per_mtok`/`output_per_mtok`, empty `source`, and `placeholder` in the source string.

That is the inlined `require_prices` pose, stricter on zero. Test covers placeholder source and missing table.

Minor divergence from `run_labels.require_prices` 210–225 (not a miss of the claim): bool `True` would pass `isinstance(..., (int, float))`, and a `placeholder: true` field with a clean source string is not checked. Committed `candidate_prices.json` has neither shape.

### 7. medium — per-seat allowance + completeness audit INCOMPLETE exit 2 — **FIXED**

Before the router pair (554–557) and before each candidate’s two passes (568–572): remaining two-pass one-attempt bound vs `LANE_CAP_USD - charged`; if it does not fit, the seat is skipped (`SEAT-INCOMPLETE`), later seats still considered, already-written seats stand.

Completeness audit (586–603): each paid journal’s `completed | exhausted | ambiguous` must cover its queue; otherwise `INCOMPLETE` and `SystemExit(2)`. Using the **terminal** set rather than `completed` alone is the right predicate given finding 4 — an exhausted router item is a finished strict `cannot_determine`, not an unfinished assemble. A completed-only check would block timing assembly on a fully-run queue that had retries die, which finding 4 forbids.

The in-process skip is live after an earlier seat’s retries inflate charged. The finding-5 whole-run startup check fires first on resume, so a mid-seat `BudgetError` from a prior process will refuse the entire re-entry rather than skip that seat and try the next (see New defects).

### 8. medium — ratification (d) refuse kept — **FIXED** (no code change, as recommended)

`finalize_gold.py` 14–16 still defers the ≤5-drop scorer path. `take()` (179–182) records drops; 222–227 still `SystemExit`s on any drop and never writes `gold_final.jsonl`. No panel-majority substitute.

### 9. low — strip at both load sites — **FIXED**

`finalize_gold.load_answers` 62: `str(...).strip()` on every Sol answer (adjudications, audit, escalation).

`concordance_71.py` 39 (Fable `label`) and 49 (Sol `answer`): both stripped. Duplicate-Sol refusal was added next to it (47–48).

### 10. low — Fable map duplicate + coverage refusals — **FIXED**

`concordance_71.py` 35–42: last-wins dict comprehension is gone. Duplicate Fable ids `SystemExit`; `set(queue_ids) - set(fable)` `SystemExit` with sample ids. Extra Fable rows beyond the 71 are allowed (`<=`, not equality), matching the specified check.

### 11. low — panel map duplicate refusal — **FIXED**

`finalize_gold.py` 82–86: per-labeller map now refuses duplicate `request_id` before the `len(rows) != 461` check. A 462-line file with one duplicate and 461 unique ids no longer passes.

### 12. low — comment only — **FIXED**

`run_candidates.py` 67–70 records `MAX_ATTEMPTS = 4` vs production 3, and that exhaustion maps to `cannot_determine` with no keyword fallback. Constant unchanged.

### 13. low — deliberate keep with comment (dispatched-artifact byte stability) — **FIXED** (as claimed)

`build_escalation_queue.py` 48–54 and `build_legacy_queue.py` 46–50 keep `json.dumps(..., sort_keys=True)` with default `ensure_ascii=True`, and say why: the queues were already dispatched; encoding-only (`—` vs `\u2014`) is not a packet difference after `json.loads`. The original minimal fix was `ensure_ascii=False`; the claimed pose is keep-with-comment. That pose is in the files.

### 14. low — labels/probe journals in `all_journals()` — **FIXED**

`all_journals()` 189–194: `labels/*.journal.jsonl` plus explicit `labels/probe/*.journal.jsonl` plus `candidates/*.journal.jsonl`. Missing `labels/probe/` glob is empty, not an error. Candidate probe journals remain in `OUT`’s non-recursive glob (`probe_*.journal.jsonl`).

---

## New defects introduced by the fix pass

None that restore the original dispatch block (undercounted cap, retry crash, candidate answers before freeze). Three residuals:

1. **Startup preflight can refuse a legal resume that the per-seat skip would have handled** (`run_candidates.py` 538–547 vs 549–572). If a previous process `BudgetError`d mid-seat, or if a completed run’s actual settlement exceeded bound and `charged > $30` with remaining bound 0, the next default-path invocation raises `BudgetError` before per-seat skip or `assemble_timing`. Escape hatch: `--assemble-timing` is still ungated and uses the refuse-incomplete logic. First dispatch is unaffected: the per-attempt reserve still stops a call whose bound would breach.

2. **Completeness audit adds set lengths** (592–598) instead of `len(completed | exhausted | ambiguous)`. `journal_state` can mark a request both `completed` and `ambiguous` (a reservation after the terminal event). Double-counting could hide a never-started id. Not reachable from `run_queue` on a clean journal.

3. **Dry-run log line** (503–506) still reports full queue cardinalities as “calls remaining” while `worst` is the resume remainder. The refuse uses `worst`, not the phrase.

Not counted as defects: `validate_prices` vs `require_prices` bool/`placeholder` field (committed table is clean); assemble-timing exit status 1 vs 2 on the standalone flag.

---

## Tests vs claims

`test_run_candidates.py` covers 1 (success / exception-at-bound / missing-usage-at-bound), 2 (resume numbering and no-flag skip), 3 (missing freeze + hash mismatch), 4 (unfinished refuse + exhausted → `cannot_determine`), 6 (placeholder + missing). No tests for remaining_bound/dry-run/startup, per-seat skip, exit-2 completeness, `all_journals` probe glob, or freeze **success**. Gaps in the harness, not in the production branches those tests do hit.

---

RECERT COMPLETE
