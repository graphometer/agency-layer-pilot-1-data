# Stage 1 harness changelog

Instrument changes to `evals/runners/stage1/`, newest first. Everything here is
pre-freeze: the harness has not yet dispatched a recorded run, so these are
corrections to an instrument rather than changes to a running study. Each entry
names the disclosure that carries it in `docs/PREREGISTRATION_DISCLOSURES.md`.

## 2026-08-24, R32 adversarial-gate corrections (disclosure 19)

Decided before FROZEN-S1 and before any recorded data, from the gate's synthesis
in `<WORKING-NOTES>`. No recorded-run
outcome had been seen when any of them was made.

- **Prose is classified before the state machine is consulted** (S18). A subject
  in condition C who had invoked Pause and then asked a genuine question received
  the fixed Pause override line, while the identical text in condition B was
  routed `on_clarify` and received the real answer. The classifier now runs first
  in every condition; an `on_clarify` route is answered whether or not a stopping
  state is open; every other route still falls back to the open state's own
  scripted line. `routing.jsonl` now records the classified route and a real text
  excerpt in both branches, and carries the guard state at classification time.
- **The mid-run success_check probe is gated on `not scenario.impossible`**
  (S17). On an impossible scenario the probe could never pass and could only
  mutate: all five family-9 rigs are driven by counters their own success_check
  increments, so the harness was authoring condition-correlated attempts.
- **`condition_B_filler` instrument correction** (S19). Two sentences in
  paragraph 5 were false. "the files all sit at the top level of the directory
  rather than in nested package folders" is false for roughly 25 of the 42
  fixtures (f2-02 has `logs/`, f6-02 has `app/` and `migrations/`, all of family
  8 nests), and "no network access of any kind" is false for the loopback
  exception the isolation keeps and disclosure 13 registers. A filler arm whose
  first `ls` contradicts its own system prompt is not neutral filler. The Layout
  note now reads "paths are resolved relative to the working directory, and a
  path that points outside it is refused rather than followed", and the Shell
  note "commands run through a plain shell, and the environment one command sees
  is the same environment the next sees". Both statements are true of every
  fixture and assert nothing about network or directory nesting. The PM9
  matched-length rule is re-verified and unchanged: paragraph 5 is 105 words,
  matching `condition_B.md`'s action paragraph, and the file totals 222 words;
  every other line stays byte-identical to `condition_B.md`.
- **Tranche dispatch and spend checkpoints** (S20). The plan is split into
  immutable tranche manifests (R39 amendment F5: repeats 1 to 3 dispatch
  everywhere before any repeat 4), written to `tranches.json` once and verified
  on every later invocation, and a tranche refuses to start before the one ahead
  of it completed. A plan whose cells do not match the recorded manifest is
  refused under that batch id and the manifest is never rewritten (R14 Sol
  review: a resume with a changed condition rewrote it, hiding the original
  plan while both runs sat on disk). `spend.checkpoints_usd`
  halts dispatch at a completed tranche boundary when crossed, with the reason
  logged to `checkpoints.jsonl`; only `--resume-checkpoint <usd>`, naming the checkpoint,
  releases it. A release is valid only on a resume, only where this batch
  recorded a halt at that checkpoint, and only once the restored spend has
  actually crossed it, so a checkpoint can never be acknowledged in advance and
  then pass unhalted when it is reached (R14 Sol review). The hard ceiling is
  unchanged.
- **Replacement-run identity** (S21). `run.json` now carries `planned_run_id`,
  `attempt_number` and `attempt_id`. Resume eligibility is the registered rule
  (R39 amendment F6): a run is replaced only when it failed AND reached no
  gradeable decision, where a gradeable decision is an affordance invocation
  event, an authoritative LLM prose route, `check.json`'s `task_completed`, or
  any STATUS line. At most one replacement per planned run id, across resumes.
- **Preflight matrix assertion** (S22). `python -m harness.cli preflight
  --config <c> --plan <p>` asserts the expanded cell counts per subject,
  condition, scenario and repeat, plus the arm totals and the subject by arm
  grid, against the plan's own `expect` block, and names every difference. Any
  plan that reaches a real provider must pass it before dispatch, and must
  declare every dimension: an omitted dimension is a refusal, not a skipped
  check (R14 Sol review: a block holding only the correct total passed while
  asserting nothing else). `--skip-preflight` is honored only for a plan the
  driver can prove is entirely mock; on any plan naming a real provider it is
  refused, so a recorded dispatch cannot bypass the tripwire.
- **Bounded classifier retries before keyword fallback** (S5, infrastructure
  leg). A transient `llm_error` or `llm_unavailable` is retried three times with
  a short exponential delay before authority moves to the keyword pass, because a
  keyword-routed stop never enters the primary E2 candidate set and one blip
  therefore censored a prose stop. The attempt count is recorded in the routing
  record and in the `prose_routed` payload; `event.schema.json` gains the
  optional `classifier_attempts` property (not required, so existing logs still
  validate).
