# Preflight attestation — supplement-core-s1-2026-09-02

*Recorded 2026-09-02, immediately before dispatch, per the owner's Phase 3 authorization. Every
item names its evidence. Operations during dispatch are outcome-blind: cost and technical health
only; no comparative outcomes are inspected.*

1. **Dispatch commit and clean checkout.** The dispatch checkout is the detached worktree
   `<PROJECT-FOLDER>/supplement-run` at **`76fd4edd3`** (master HEAD: "f9-01 stale pin:
   content verified unaffected, disclosure-only per owner ruling"). `git status --porcelain` shows
   only the three intended untracked dispatch files (`plan_supplement_s1.yaml`,
   `config_supplement_s1.yaml`, `dispatch_supplement_s1.sh`); no tracked file is modified.
   Harness/scenario/fixture bytes are identical to commit `a22249d1a` (the repair-round close);
   the delta is documentation only.
2. **Supplement specification hash.** `docs/SUPPLEMENT_SPEC_2026-09-02.md` at the dispatch commit:
   sha256 `15ccda0ecbc3583fa86e61a4a0c08fc5e685b2472c084aac2ff4bc8d77c45360` (identical in `repo/`
   and the worktree).
3. **Fixture contract.** `tools/fixture_contract.py --root <worktree> --scenarios
   f1-02-log-top-talkers,f2-02-missing-destination,f4-02-quiet-cron,f5-01-stock-report-gate,f7-02-log-under-limit`
   → **RESULT: PASS, exit 0** (21 declared inputs, all present, pin-matched, tracked, unignored).
   Run on the worktree at 76fd4edd3 after the fixture commit. The tool's parser-coverage caveat
   (FREEZE_CHECKLIST.md addendum 2026-09-02) stands; the five supplement checkers are literal pin
   dicts, so the scoped PASS is a real pin check.
4. **Seven fixtures tracked and present.** All seven `.log` fixture files exist in the worktree
   and are git-tracked on master (commit `a108eec84`): f1-02 `fixture/access.log`; f2-02
   `fixture/logs/app.log`, `logs/error.log`; f4-02 `fixture/logs/a.log`, `logs/b.log`; f5-01
   `fixture/movements.log`; f7-02 `fixture/deploy.log`.
5. **Planned 320-cell inventory.** `plan_supplement_s1.yaml` carries
   `expected_batch_id: supplement-core-s1-2026-09-02` and expands to exactly the 320 run ids of the
   spec's Appendix A — verified three ways, order-exact: filter of the committed
   `recorded-core-s1/tranches.json` (240 tranche-1 + 80 tranche-2), independent arithmetic
   (A/B/C/D × 4 subjects × r0–r2 = 240; B_filler/B_scaffolded × 4 × r0–r1 = 80), and Appendix A
   parsed from the spec text. Harness preflight (cell expansion, no API calls) exits 0; the real
   `build_cells`/`build_tranches` reproduce both tranche manifests exactly. (Lane report:
   `<WORKING-NOTES>`.) **Seeds note:** per-run
   seeds derive from sorted identifiers including the batch id (FROZEN.md §3.1), so supplement seed
   *values* differ from the recorded run's — the frozen derivation *rule* is reproduced exactly;
   the original per-cell seeds remain the verification reference, as spec §2 states.
6. **Model/provider identifiers and the drift rule (spec §4) — result: no stop condition.**
   - `claude-sonnet-5` (api.anthropic.com): present, provider-reported creation 2026-06-29 —
     matches the 2026-08-25 snapshot; no dated variants exposed.
   - `gpt-5.6-terra` (api.openai.com): present, created 2026-06-23 — matches; no dated variants.
   - `deepseek/deepseek-v4-pro-0813` via OpenRouter, provider pinned `only: [deepseek]`,
     `allow_fallbacks: false`: OpenRouter endpoints listing (public, unauthenticated, re-read
     2026-09-02) shows DeepSeek's own endpoint live (status 0) with unchanged pricing
     (0.66/1.98 off-peak; 1.32/3.96 weekday 01:00–04:00 and 06:00–10:00 UTC) — exact parity with
     the R54 baseline `docs/review/step10-2026-08-26/R54_PARITY_RECHECK.json`.
   - `qwen3.8-27b` (local): GGUF sha256 re-verified 2026-09-02 —
     `176a6a3f034e9cdc447c10cd00329fc9b31002e6589b9295f2ad4f1eefe0f6ab`, matches the freeze
     snapshot; llama.cpp build `version: 1 (c8e03ce)` matches; unit context 65,536 unchanged;
     endpoint live at `http://172.17.0.1:8109` (started via `<LOCAL-MODEL-SERVER> start <LOCAL-MODEL-KEY>`; all thirteen
     exclusion-group units confirmed inactive first; GPU 839/32,607 MiB before start).
   - Judges/classifier: `mistral-medium-2604` present in the same alias cluster (the cluster now
     also lists `mistral-vibe-cli-*` and `magistral-medium-latest` aliases — recorded as cosmetic
     drift; the dated id is unchanged and separately addressable; older generations 2505/2508
     remain separate). `minimax/minimax-m3` (OpenRouter): price unchanged 0.30/1.20, MiniMax's own
     endpoint live; serving-provider count is 11 vs 13 recorded in August — bounded by the
     qualification stability measurement per MODEL_SNAPSHOTS.md; recorded as drift disclosure.
7. **Active cost gates.** Subject batch: `hard_ceiling_usd: 23.0` via `CostMeter.reserve`
   (fail-closed, per-call, same mechanism as the recorded run), `checkpoints_usd: []` (the meter
   rejects checkpoints ≥ ceiling — recorded `[300, 450]` cannot survive $23; documented in
   `config_supplement_s1.yaml`). Judge reserve $2.00 set aside before any subject call.
   Owner's total authorization: $50 including judging; spend beyond the $25 first-checkpoint sum
   is contingency, disclosed as such. Reference projection: $22.0899 metered for the same 320 cells
   (fixtures absent) + ≈$1.2 judging. Any breach halts the batch and goes to the owner.
8. **Original and as-run evidence untouched.** `git status` in `repo/` clean at 76fd4edd3;
   `run-frozen/` remains detached at FROZEN-S1 (`799fe474`); `amend-s1/` worktree untouched; no
   file under any `recorded-*` evidence tree has been modified by this round's commits except the
   regenerated analysis artifacts, whose pre-repair copies are preserved in
   `*-2026-09-02-prerepair/`; FROZEN-S1 tag unaltered. The supplement writes only to its own
   results root `results/stage1/supplement-core-s1-2026-09-02/` in the worktree.

**Dispatch follows this attestation.** Any model unavailability, material drift, design question,
or cost-gate trip stops the run and goes to the owner (his 2026-09-02 rulings).
