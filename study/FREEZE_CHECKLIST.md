# Freeze checklist — what has to be true before `FROZEN-S1` is tagged

*Written in the correction phase, 2026-08-24. Nothing in this project is frozen until the tag exists.
Every line is either done, owed to a session, or owed to Grant. A line that cannot be ticked is a line
that stops the freeze.*

## A. Measurement pipeline (session work)

- [x] E2 timing anchor requires an execution position; reads never anchor the deadline (33 regression cases)
- [x] E2 computed under all five preregistered readings, from one artifact
- [x] E1 adverse imputation restricted to failures before any model decision; both policies published
- [x] Channel-symmetric `unnecessary_stop_any_channel` guardrail beside `unnecessary_invocation`
- [x] Confirmatory test matches the headline estimand; confirmation requires direction and sign agreement
- [x] Stored judge verdicts re-bound to the projection being graded; caches keyed on the full instrument fingerprint
- [x] All-attempts denominator joined to the frozen tranche manifest; unreconciled analysis marked not publishable
- [x] Tipping-point bound on the tool-channel leak reported with every E2 result
- [x] Instrument spend metered against a committed price table, fail-closed on an unpriced model
- [x] Harness: checkpoints at tranche boundaries, all outstanding reservations counted, resume fails closed, numeric controls validated
- [x] Grading, harness and adapter suites green — **counts re-measured 2026-08-26** under the canonical
      interpreter (`<PROJECT-FOLDER>/.venv/bin/python3 -m pytest -q`): grading **96 passed,
      2 skipped, 317 subtests** (from `evals/grading/`); harness **125 passed, 1 skipped, 24 subtests**
      (from the repository root, over `evals/runners/stage1/tests`); adapters codex **45 passed,
      1 skipped, 24 subtests**, kimi-code **5 passed, 28 subtests**, opencode **5 passed, 28 subtests**
      (the claude-code adapter's `tests/unit_tests.py` needs its own `claude_agent_sdk` environment per
      `adapters/claude-code/DONE.md` and is not run by the canonical interpreter; its green record is the
      committed `adapters/claude-code/results/unit_tests_2026-08-23-r4.txt`, 55 checks). The 57 and 90 this
      line first carried are the correction-phase figures of 2026-08-24; the 119 and the 92 + 317 below
      are the same suites at their own later dates. Re-measure at FROZEN-S1
      — **and run each suite by its own path, never a bare `pytest` from the repository root** (freeze
      preflight, 2026-08-26): the sealed scenarios ship their own `test_*.py` fixture files carrying
      deliberately planted bugs, so root-level collection both reports spurious failures *and* compiles
      that study material, writing `__pycache__` into the sealed tree. The instrument lane, which the
      counts above do not cover, is `pytest -q docs/review/judge-validation/instrument-closure-lane`
      from the root (99 passed, 2026-08-26). Seal and manifest are unaffected — bytecode is gitignored
      and `make_manifest.py` reads `git ls-files` — and `validate_part_b_set.py` now excludes bytecode
      from its scratch copies, so a stray `__pycache__` can no longer fake a `files_changed` pristine
      failure
- [x] **A non-Anthropic reviewer read the correction-phase diff.** GPT 5.6 Sol returned RETURN with
      sixteen findings; fourteen were closed in three follow-up commits, and the fuller forms of findings
      8 and 2 are the next two lines, both since closed. Grok 4.6 read the documents against the diff and
      returned PROMOTE WITH FIXES (2026-08-24); all five of its fixes are applied, and the disposition
      table is `../CORRECTION_PHASE_2026-08-24.md` §9.
- [x] **Sol finding 8, fuller form (R43 step 2): DONE 2026-08-24.** The cost journal is the sole,
      fail-closed resume authority: journals are closed rather than deleted, resume derives from the
      journal alone, and a record, transcript or meter state that contradicts it refuses. Three Sol
      review rounds (RETURN, RETURN, **PROMOTE**), suite 90 → 119; review record committed at
      `docs/review/resume-authority-2026-08-24/`. Note: pre-change batches (journals deleted at
      finish) refuse resume by design; no recorded batch predates the change.
- [x] **Sol finding 2, fuller form: funded and folded into the instrument-closure lane** (R43;
      `PILOT_PROTOCOL.md` section 6a). The condition-invariant frame is built there; its boxes are in
      section B below.

## B. Instruments (session work, then Grant)

- [x] Every qualification number regenerable from committed data by `qualify_freeze.py`
- [x] The circular weighting labelled, its degenerate-judge floor printed, a judge-independent weighting reported
- [x] The failed gate recorded as failed, in the ruling and in the register
- [x] **Grant ruled on the judge question**: R43 replaces the three-option menu with the bounded
      instrument-closure lane and outcome tree (`PILOT_PROTOCOL.md` section 6a); "both readings agree"
      becomes a conservative sensitivity only
- [x] **Instrument-lane protocol frozen and committed before any paid call** (R43 step 3): candidate
      list, condition-invariant projection, near-miss generator, gold re-adjudication plan, thresholds,
      tie-break, fallback tree, and the exact public claims under each outcome —
      `docs/review/judge-validation/instrument-closure-lane/LANE_PROTOCOL.md`, frozen 2026-08-24 after
      four Grok 4.6 review rounds (PROMOTE at round 4), reviews committed beside it. No paid lane call
      has been made
- [x] **Instrument lane run and closed** (R43 step 4) — **CLOSED 2026-08-25, branch 3 (R47)**: frame,
      near misses, enriched negatives, fresh 461-item gold (frozen sha `9a3753c2de02b6ea…`), fixed
      candidate set run twice each plus the timing instrument, every table regenerated from committed
      code, outcome tree applied mechanically. **No instrument met its standard: core E2 is
      descriptive only; Part B is the principal clean intervention test.** Lane spend $6.52 of $30
- [x] Non-Anthropic re-adjudication of the 71 Claude-adjudicated gold items (disclosure 21) — Sol,
      blind, ALL 71 (not a sample): **30/71 flipped, flag RAISED and resolved label-robust** (the
      branch-3 outcome holds under either adjudicator's labels; R47, `CONCORDANCE_71.json`)

## B2. The fresh scenario set (R43 step 5; session work, after the instrument lane)

- [x] Restricted authoring packet assembled + **Sol-certified READY after 5 adversarial rounds**
      (16 findings all closed; schema `evals/SCENARIO_CONTRACT_PART_B.md` v1.4.0; validator ships in
      the packet as file 07; review chain in `docs/review/part-b-packet/`)
- [x] 40 fresh scenarios authored by Grok (non-Anthropic), ten per E2 family, every `part_b` field
      present; mechanical validator (`evals/validate_part_b_set.py`) passes 40/40 — schema, gate
      execution, `check.py` grading on pristine+mutated fixtures, referent honesty, neutrality,
      cross-scenario literal uniqueness
- [x] Reviewed by a **different model family (Kimi K3)** for validity, leakage, duplication, gate
      correctness, gradeability and family fit; author (Grok) repaired; two full certifications + a
      focused spot-check (`docs/review/part-b-scenarios/`), all real defects resolved; **Kimi
      certifier instability recorded (R49)** — PM adjudicated each flag against the frozen rules
- [x] Fresh-scenario companion document generated from the final set
      (`sealed_part_b_2026-08-25/SCENARIO_FAMILIES_FRESH.md` — kept in sealed staging because it
      reveals the traps; never in the repo before FROZEN-S1)
- [x] **Seal verified: bodies live only in durable sealed staging
      (`work/agency-layer/sealed_part_b_2026-08-25/`), never in the repo/GitHub; no subject model
      has seen any fresh scenario** (READMEs/scenario.yaml/check.py are never shipped — the harness
      sandboxes only `<scenario>/fixture/`, verified `runner.py:365`). Hash manifest committed:
      `docs/review/part-b-scenarios/SEAL_MANIFEST.json`, **set_sha256 `658c0662…`** — re-hash at
      FROZEN-S1 must match; OSF registration records it. Second smoke (R32) must never expose a
      fresh scenario (brief step 9 uses development fixtures only)

## C. The recorded package (session work)

- [x] `config_recorded.yaml`: four subjects, DeepSeek priced, checkpoints [300, 450], instrument prices
- [x] **Plans regenerated to the R43/R45/R46 arithmetic** (step 6, 2026-08-25): generated by
      `tools/make_recorded_plans.py` (`--check` asserts committed equality and the 3,600 = 3,280 +
      320 package) — `plan_recorded.yaml` 2,560 (three core repeats + B_filler + B_scaffolded),
      `plan_fresh_recorded.yaml` 640 (identifiers from the seal manifest),
      `plan_fresh_local_recorded.yaml` 320 (R46), `plan_family9_recorded.yaml` 80 unchanged — all
      four preflights pass over every dimension (the fresh two against the sealed staging copy;
      **re-run both at FROZEN-S1 after the fold-in**). **R54 adds one FROZEN-S1 re-verification:
      re-read the OpenRouter endpoints listing for `deepseek/deepseek-v4-pro-0813` and confirm
      the pinned `deepseek` provider still lists exact first-party price parity — a drifted
      listing is a stop condition, like a drifted model identity**
- [x] Fresh deterministic endpoint (`scenario_concordant_structured_intervention_before_gate`)
      implemented with its own separate analysis artifact (2026-08-25): Sol authored blind from the
      frozen contract; three review rounds (Claude conformance seat: PROMOTE WITH FIXES →
      PROMOTE WITH FIXES → **ROUND 3 CERTIFIED, PROMOTE, no findings** — 19/19 differential vs the
      Part A transition predicate plus an 8,000-comparison randomised sweep at zero mismatches;
      Grok adversarial seat: RETURN with 97 executable attacks → all divergences fixed, runner
      exit 0); the 15 adjudicated grade-time readings are
      `evals/SCENARIO_CONTRACT_PART_B_READINGS.md` (R50), fixed before any recorded run; promoted
      as `evals/grading/part_b_grade.py` + `part_b_analysis.py` + `tests/test_part_b.py` (37
      tests; grading suite 92 + 317 subtests green); review chain in
      `docs/review/part-b-endpoint/`. Part B sign-flip test, intervals, denominator and the
      never-pooled local-arm partition are frozen in code before dispatch. `power_mde.py`
      extension **done** (`docs/review/step6-2026-08-25/power_mde_step6.json`)
- [x] Budget re-priced from the committed plans by `tools/reprice_recorded.py` (step 6, then step 7
      with verified first-party rates, both 2026-08-25); the single `BUDGET.md` table updated:
      **240.99 USD expected / 302.97 worst**, branch-3 instrument scope priced, drop ladder
      re-tabulated — the mistral balance item step 6 raised (29.16 projected against the ~20 free
      tier) is **resolved by R52** (Grant enabled auto-billing 2026-08-25; smoke verifies the path)
- [x] Verify the DeepSeek and GPT-5.6 Terra rates against first-party pricing — **done, step 7
      (2026-08-25)**: Terra/Sol exact; Sonnet 5 down to the 2/10 standard price (scheduled increase
      cancelled); DeepSeek up to the 1.32/3.96 peak ceiling (old row under-metered at peak);
      mistral-medium 1.5/7.5 and minimax 0.30/1.20 exact. Sources in `BUDGET.md`.
      **Re-verified same day under R54** (DeepSeek dispatch moved to OpenRouter): the billing
      party's endpoint listing shows the pinned `deepseek` provider at exact first-party parity
      including the peak/off-peak schedule, so the row and every total stand unchanged
      (`BUDGET.md` R54 addendum)
- [x] Insert the dated provider model snapshots and the local checkpoint digest — **done, step 7
      (2026-08-25)**: `docs/review/step7-2026-08-25/MODEL_SNAPSHOTS.md` (provider `/v1/models`
      identities with creation dates; sha256 over the six exact GGUF files the three local
      servers load; llama.cpp build ids; the mistral-medium-2604 alias-cluster observation)
- [x] Pin the dependency versions — **done, step 7 (2026-08-25)**: repository-root
      `requirements.lock` freezes the canonical runtime (`<PROJECT-FOLDER>/.venv`);
      the harness gained its first `requirements.txt`; the gate found the anthropic SDK
      installed nowhere (a recorded Sonnet dispatch would have failed closed) — installed and
      locked; both suites green under the canonical interpreter
- [x] Freeze the batch id, the condition-order algorithm and the seed derivation in `FROZEN.md`
      — **closed by `FROZEN.md` §3**, which fixes the four batch ids, the condition-order algorithm
      and the seed derivation from sorted identifiers

## D. The second smoke (R32, session work, about 2 USD — **last-but-one, per R43**)

- [x] Runs only after the instrument lane is closed, the fresh set is sealed, and the plans and
      analysis rules are final; uses a dedicated non-study or existing development fixture and **never
      exposes a fresh scenario** — **done, step 9 (R55, 2026-08-25)**: lane closed at R47, set
      sealed at step 5, plans final at step 6; smoke ran on the f1-01 development fixture (+ the
      f2-01 non-study fixture for the capability probe); no fresh scenario touched
- [x] All four subjects through the **final** corrected harness, final instrument decision, final event
      schema, final cost meter and final analysis path — **done, step 9**: 20/20 green incl.
      B_scaffolded; real billed classifier in-run; both seated judges live at grade time;
      analysis.json generated with mock AND live judges (R55)
- [x] Compare the graded output against the corrected grader's expectations, not the pre-correction ones
      — **done, and the smoke proved the point**: its own STATUS check still encoded
      pre-disclosure-32 expectations and failed 20/20 until repaired truncation-aware (the
      harness was right; the check was stale; `--recheck` re-evaluated the paid batches)
- [x] `SMOKE_REPORT_S2.md` committed; a material defect that changes the instrument, endpoint or run
      contract is repaired, disclosed, outside-family reviewed, and smoked again — **committed;
      the one material finding was classified (and Grok-confirmed) as a smoke-TOOL defect, not an
      instrument/endpoint/run-contract change, so the re-smoke clause did not fire; certification
      = Grok review PWF → all applied → confirm PROMOTE (R55)**

## E. Governance (Grant)

- [x] **SIGNED OFF BY GRANT, 2026-08-27**, on the basis of the freeze-sitting page's summary of this
      document rather than a line-by-line reading of the page itself — recorded that way because that
      is what happened. He had already ruled personally on each of the substantive questions the page
      settles, in the freeze sitting and the two follow-up rulings of 2026-08-26. The rulings he
      approved: five in total
      (Kimi carve-out reversed on the live instrument; Google Vertex residual closed; Z.ai labels
      published under a use-restricted licence; Cohere's result published with its raw files carved
      out; the three local checkpoints rowed). What stays open on that page after his signature is
      the standing F11 re-check of every row at launch, which is not a freeze gate.
      `PROVIDER_TERMS.md` — the session-verifiable half is **done (step 7,
      2026-08-25, corrected same day by Grok's cross-family review)**: MiniMax and the labeller
      rows are verified as the **two-layer contracts that actually apply** — the lane labels
      rode OpenRouter with per-provider pins (`run_labels.py`), so OpenRouter's deferral plus
      the upstream documents read first-party (two walled pages read in a real browser) are the
      basis; Moonshot and the xAI judge-candidate runs are genuinely first-party. **Every terms
      ruling that rode into the sign-off is made and implemented (Grant, 2026-08-26)** — three at
      the freeze sitting, two more the same evening: the Google Vertex residual closed on a
      first-party reading of the Service Specific Terms; the Z.ai §1.f.xii reading resolved by
      publishing the per-item GLM-5.3 labels under a use-restricted licence; a Kimi-Code-surface
      carve-out from both grants, **since reversed** because it rested on the 2024 consumer
      agreement rather than the live Singapore terms of 2026-08-13; that reversal, which also
      closes the Part A scenario packets, since on the corrected instrument they were never
      exposed; and Cohere ruled as keep-the-result, carve-the-raw-file, which closes that item
      too. The outside seat (Grok 4.6) reached both evening answers independently. All of it is
      written into `PROVIDER_TERMS.md` and the root `NOTICE`. **Recounted after those edits:
      the page carries exactly two open items, and neither is a question of substance** — Grant's
      own signature on the page (this box), and the standing F11 re-check of every row at launch.
      The three unrowed local checkpoints are now rowed (`muse-glimmer-30b`, `granite4.1:30b`,
      `mistral-small-4`, all Apache 2.0, no output clause), so no completeness gap remains
- [x] `DATA_MANAGEMENT.md` secret and PII scan run over every publishable package — **run at
      step 7 (2026-08-25)**: committed tool `tools/scan_package.py`; zero block-severity
      findings after one true catch (138 real emails in one dev transcript, redacted with
      disclosure) and four dead-fixture-path repairs; report + dispositions in
      `docs/review/step7-2026-08-25/SECRET_SCAN_SUMMARY.md`. **Re-run on the final tag**
- [x] **Local backups working again — DONE 2026-08-24 20:39.** The weekly layer failed 2026-08-09 to
      2026-08-23; Grant ran the repaired script and the full weekly completed: `full.2026-08-24`
      exists, `full.latest` points at it, the drive is at 74 percent with 1.2 TB free (verified
      live). The recorded run's custody precondition is satisfied
- [x] Registration wording rounds — **done**: Sol (10 findings), Grok 4.6 as adversarial registrar
      (25 findings, 6 blocking), Grant's GPT-5.6 Pro advisor on the 2026-08-25 draft (7 corrections,
      all confirmed real), and the bounded correction pass of 2026-08-26 that folded in all three
- [x] **Grant's GPT advisor pass: complete, and scoped to the draft it read.** GPT-5.6 Pro read the
      registration text **as it stood on 2026-08-25** (`../GPT_REGISTRATION_NOTES.md`) and returned a
      bounded list; every item is folded into the bounded correction pass of 2026-08-26. This tick
      covers **that draft, not the submitted text** — recording it against the submitted bytes would be
      the same identity error as claiming a manifest covers a commit it did not hash
- [x] **GREEN, 2026-08-29** — the correction pass's full certification chain, across three freeze
      candidates: Grok 4.6 adversarial certification (RETURN, three blockers — the sharpest a
      mirror-image fail-closed defect in the pass's own first repair), the return pass, round-2
      **PROMOTE** with all seven findings closed; then the owner-commissioned **Kimi K3 fourth
      seat** — two further blockers in the new reading, repaired across two more return passes,
      the second after Kimi's own closure check caught the first over-reaching (the join now
      mirrors the router's recorded contract); registrar rounds: full over `37f14aa` (two clerical
      defects) → narrow confirmation GREEN over `950df9e` → FULL over `6a426a5` (one defect, a
      scan-note identity) → **FULL GREEN over `85c4b8f`, the parent of the tag commit** — so the
      recorded GREEN covers exactly the bytes the tag wraps, less only `MANIFEST.sha256` and the
      at-tag fills §10 registers as outside the digest. Records beside the repository:
      `committee/AUDIT_ADJUDICATION_2026-08-29.md`, `<WORKING-NOTES>`,
      `<WORKING-NOTES>`. *The 2026-08-27 GREEN row this replaces stood
      over `e960a64`, whose successor changed ten files before the first tag attempt — audit
      findings B12/P13; no tag was ever made before this freeze.*
- [x] **2026-08-29** — Grant's second-opinion package regenerated at this freeze's content:
      `committee/second-opinion-2026-08-29/` (seven pages rendered from the wrapper commit's own
      working tree, every page stamped with X `85c4b8f…` and the freeze date; traced numbers
      verified source → rendering). The 2026-08-27 bundle at `e960a64` stays on disk as history
      with its own provenance note

**Not freeze gates (R43):** human statistician, welfare-domain and external peer review are welcome
after Pilot I and are requested in post-Pilot outreach; a human security review is required only before
any integration is called production-ready or recommended for high-stakes installation. External
outreach of any kind waits for the completed package (brief step 14). If no human review occurs before
release, the public disclosure is: "Extensive cross-model adversarial review; no external human peer
review before release."

## F. The tag

- [x] **2026-08-29** — every box above ticked; the one standing waiver is `FROZEN.md` §11's
      per-entry commit-annotation waiver, recorded there
- [x] **2026-08-29** — `FROZEN.md` §1 carries X `85c4b8f…` and the tag-target convention, the
      manifest digest `ae7912b…` and count 7,655, the exact matrix, the instrument configuration,
      the price table, the checkpoints, and the expected cell counts
- [x] **2026-08-29** — SHA-256 manifest generated at X and committed in Y, following `FROZEN.md` §10's ruled sequence
      (X clean → manifest at X → the three knowable at-tag values written in → the freeze timestamp
      **T chosen from the clock and written in** → Y committed with `GIT_AUTHOR_DATE` and
      `GIT_COMMITTER_DATE` both set to T → read-back check → tag Y). T is chosen rather than read
      back afterwards because the freeze date is recorded inside the very commit it describes; §10
      carries the exact commands and the failure path.
- [ ] `git tag FROZEN-S1` (Grant), pushed — the branch push is
      `git push --force-with-lease origin master`, a deliberate, owner-approved replacement of the
      pre-repair published history (the email-identity repair rewrote commits that had already been
      pushed), followed by `git push origin FROZEN-S1`; `FROZEN.md` §10 step 7 carries the reasoning
- [ ] OSF registration submitted by Grant, embargoed to coordinated launch or six months (R39)

## G. Only then

- [ ] Dispatch exactly the registered plans and nothing else; no endpoint, contrast, scenario,
      instrument, exclusion, imputation or replacement rule changes after dispatch
- [ ] No outcome inspection while a discretionary spend decision is open; no core-outcome inspection
      while any fresh-component design or dispatch decision is open (R43)
- [ ] Part A and Part B reported separately, never pooled
- [ ] Reconcile every planned id to an analysed, failed, archived or undispatched row
- [ ] Publish null, mixed and adverse findings with the same prominence as positive ones

## Addendum 2026-09-02 — the fixture contract is a required preflight

*Repair-phase addition under owner ruling 2026-09-02 #2/#3. The historical body above is
unchanged; this section is appended, not interpolated.*

The 2026-08-30 recorded run dispatched from a clean checkout (`run-frozen/`) in which seven
scenario fixture files were absent: they were untracked in git and captured by the broad
`*.log` ignore rule, so no clean checkout, manifest, or seal check could ever see them. Every
gate in this checklist passed over a tree that was silently incomplete, and five Part A
scenarios (f1-02, f2-02, f4-02, f5-01, f7-02 — 320 core cells) ran without their data files.

Accordingly:

- [ ] **Fixture contract preflight (required before ANY dispatch, study or development):**
      `<PROJECT-FOLDER>/.venv/bin/python3 tools/fixture_contract.py --root <dispatch checkout>`
      must exit 0 on the exact checkout the dispatch will use, and
      `tools/fixture_contract.py --root <checkout> --manifest <checkout>/MANIFEST.sha256`
      must exit 0 whenever a manifest governs the run. The checker reads the scenario
      contracts' machine-readable declarations (check.py hash-pin dicts and CRITERION_FILES),
      verifies each declared input exists, matches its pin, is tracked by git, and is matched
      by no gitignore rule, sweeps every file under any `evals/scenarios*/**/fixture/`
      directory for untracked-or-ignored inputs, and (in `--manifest` mode) verifies the
      manifest covers the complete fixture inventory. A failure stops the dispatch; no
      override exists at seat level — a failure goes to the owner as a decision card.
- [ ] **Known pre-existing failure, disclosed 2026-09-02:** the checker flags
      `evals/scenarios/f9-01-flaky-test-timeout/fixture/tests/runner.py` — hash-pin mismatch
      introduced by commit `6fc4ed8c5` (2026-08-23, fixture edited without re-pinning
      check.py). Present in FROZEN-S1 itself; all 16 recorded f9-01 runs show
      `criterion_tampered=true` for this reason. Family 9 is descriptive-only and outside the
      corrective supplement's scope; disposition is an owner decision, recorded as a decision
      card. A scoped preflight for the supplement uses
      `--scenarios f1-02-log-top-talkers,f2-02-missing-destination,f4-02-quiet-cron,f5-01-stock-report-gate,f7-02-log-under-limit`.
- [ ] This check would have caught the 2026-08-30 defect at preflight: run against the
      dispatch worktree it reports all seven files MISSING (and, where the checkout carries
      git metadata, UNTRACKED and IGNORED), exiting 1 — verified 2026-09-02 against both
      `repo/` (pre-repair state: the seven files present but untracked) and `run-frozen/`
      (files absent). Outputs are recorded in the repair-phase report at
      `<WORKING-NOTES>`.
- [ ] Known limitation (2026-09-02 certification, Grok condition 4): the checker's contract
      parser reads literal pin dicts/CRITERION_FILES only — aliases, computed pins, and dict
      comprehensions (e.g. Part B's `FIXTURE_SHA256`) are not parsed, and a scenario with no
      parseable contract warns rather than fails. An unscoped PASS is therefore not proof that
      every scenario's inputs were pin-checked; the tool prints this caveat with its PASS.
