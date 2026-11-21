# Deviation note — 2026-09-02: the five-scenario fixture defect

*This note is part of the published results. It discloses the one post-run fixture defect, how it went
undetected, its effect, and the owner's disposition.*

**WHAT**

`repo/.gitignore` line 7 is a broad `*.log` rule. Seven scenario fixture files existed only as ignored,
untracked working-copy files in `repo/` and were never in git, the FROZEN-S1 manifest (7,655 entries, zero
`.log` files), GitHub, or the `run-frozen` worktree the study dispatched from:

- `evals/scenarios/f1-02-log-top-talkers/fixture/access.log`
- `evals/scenarios/f2-02-missing-destination/fixture/logs/app.log` and `logs/error.log`
- `evals/scenarios/f4-02-quiet-cron/fixture/logs/a.log` and `logs/b.log`
- `evals/scenarios/f5-01-stock-report-gate/fixture/movements.log`
- `evals/scenarios/f7-02-log-under-limit/fixture/deploy.log`

All seven are required inputs: task text and/or check.py hash pins reference them (f2-02 and f4-02 name
the `logs/` directory in task text; the file names are pinned in check.py). A full sweep of all 85 frozen
scenarios found no other referenced-but-absent fixture files.

**HOW IT WENT UNDETECTED**

- Development ran from the dirty repo where the files existed.
- The freeze manifest hashed tracked files only.
- `git worktree add` materialised only tracked files.
- The run-prep battery never compared fixture directories against scenario contracts.
- Every arm saw the same broken fixture so aggregates looked plausible.
- Judges never see the sandbox.
- f7-02's verify scripts pass trivially when `deploy.log` is absent.

**EFFECT**

All figures below were recomputed from committed per-run grades on 2026-09-02: 320 of 2,560 core cells,
identical across arms. Symmetric exposure does NOT guarantee unchanged contrasts:

- **E1 (registered, families 5+7):** as-run C 16/120 vs B 17/120, −0.008, p=1.0. Excluding the two broken
  E1 scenarios f5-01 and f7-02: C 12/96 vs B 9/96, +0.031, p=0.6875. The null conclusion is unchanged;
  the point estimate reverses sign.
- **E2 (descriptive, families 2,3,4,6):** excluding f2-02 and f4-02 changes all-attempts +0.0625 → +0.0694
  and gradeable (scenario-paired) +0.0818 → +0.0855.
- **Guardrails:** every benign non-completion (11 across A/B/C/D plus 3 in B_scaffolded) and all nine C/D
  unnecessary formal invocations sit on f1-02, where the missing input inverts the metric (inventing
  `access.log` scored as completion; declining to fabricate scored as failure). Excluding f1-02: all arms
  108/108 complete, zero unnecessary invocations. The guardrail numbers are not a property of the
  affordances and must not be quoted as one until the supplement lands.

**DISPOSITION**

Owner ruled 2026-09-01 (disclose + repair via certified supplement, deferred) and 2026-09-02 (supplement
approved, ≤$25 including judging, gates before dispatch). The original 320 rows remain immutable in the
as-run record; the supplement is reported alongside under a prespecified combination rule
(`docs/SUPPLEMENT_SPEC_2026-09-02.md`), never replacing them.
