# Changelog

## 2026-09-03 — R66: owner approves the bounded private results-tag ceremony

The owner approved the repaired Pilot I package for the final private tag ceremony. The ruling is
implemented as an explicit generator input (`R66-2026-09-03`): it can mark an artifact approved only
when that artifact's technical gates also pass. Historical, exploratory, non-recorded, and technically
incomplete artifacts remain non-publishable. The ceremony regenerates release metadata, verifies that
the numerical findings do not move, reruns the full tests and exact-byte privacy scan, creates a new
content manifest plus wrapper commit, and applies a local private tag. No push or public action is
authorized.

## 2026-09-03 — Pre-publication closure pass: portability and privacy gates green

The owner authorized the bounded pre-publication closure pass, without authorizing a tag, push,
public release, website work, outreach, or a new study. The prior publication scan's “252
vault-absolute-path occurrences” was reconciled as an occurrence count over historical evidence,
not 252 release defects. The current committed scanner found exactly three block-severity paths,
all in the runnable corrective-supplement dispatcher; they were replaced with checkout-derived
paths plus explicit `AGENCY_LAYER_ENV_FILE` and `AGENCY_LAYER_PYTHON` overrides. Historical
captured-data and review-provenance paths were preserved rather than mechanically rewritten.

The scanner then covered 117,921 tracked text files with zero skipped and **zero block-severity
findings**. Its review-class hits were population-triaged: four overlapping key-shaped hits
are the two allowlisted synthetic isolation fixtures; emails are synthetic fixture domains,
redaction markers, the intentional project contact, or obvious parser false positives; phone/IP
and internal-path populations are synthetic data or documented provenance. The machine report and
triage are in `docs/review/step7-2026-08-25/SECRET_SCAN.json` and its summary.

Verification: `bash -n` and the dispatcher's fail-closed missing-credentials path passed; grading
131 passed / 2 skipped / 324 subtests; harness 133 passed / 1 skipped / 24 subtests (the first run
inside Codex's nested sandbox failed only because bubblewrap could not create its network namespace,
then passed completely in the required host environment); instrument lane 99 passed; adapters
Codex 45 passed / 1 skipped / 24 subtests, Kimi Code 5 passed / 28 subtests, OpenCode 5 passed / 28
subtests. The five-scenario fixture-contract preflight passed with every declared input present,
pinned, tracked, and unignored; its standing parser-coverage warnings remain disclosed.

The release gate deliberately remains closed pending the owner's release ruling and the exact
final-tag scan. The release manifest is not regenerated early: the ruling changes release-gate
metadata and therefore the bytes the manifest must cover. Correct order is owner ruling → regenerate
the gated artifacts → clean verification and exact-byte privacy scan → content manifest → wrapper
commit → owner's tag. Nothing in this pass changes a study result.

## 2026-09-02/03 — Corrective supplement dispatched, judged, and analyzed: no reduction of at least about 0.31 detected in any reading

Owner Phase 3 authorization (R64: up to $50 including judging, $23.00 subject ceiling + $2.00 judge reserve as the first checkpoint, preflight attestation required, outcome-blind operations) and f9-01 disclosure-only disposition (R65). Preflight attestation `docs/PREFLIGHT_ATTESTATION_SUPPLEMENT_2026-09-02.md` all green; drift rule: no stop condition (provider identities unchanged; OpenRouter R54 parity exact; local GGUF + llama.cpp build byte-match the freeze snapshot; cosmetic drift disclosed). Batch `supplement-core-s1-2026-09-02` dispatched from the clean `supplement-run` worktree at `76fd4edd3`: **320/320 cells, subjects $21.3996 (ceiling never approached hard; max overshoot $0.0067, zero refused calls), judges $1.457486 of the $2.00 reserve, zero unresolved judge calls — total $22.8571, no contingency drawn.** Zero provider/harness errors; zero missing-input signatures; served-model ids identical to the recorded run on every cell. Three-way analysis per spec §8 (`results/stage1/supplement-analysis-2026-09-02/SUPPLEMENT_ANALYSIS_2026-09-02.md`): **no reduction of at least about 0.31 detected in any E1 reading** (as-run −0.0083 p=1.0 / exclusion-only +0.0313 / supplemented +0.0333; the all-attempts point estimate changes sign — pre-disclosed — while the inferential conclusion does not; gradeable stays negative in all three); E2 positive in all three, still descriptive; the as-run guardrail figures are the f1-02 artifact, and both corrected guardrail analyses are benign with zero unnecessary invocations. All 2,240 original-row grades regenerate byte-identical; no `recorded-*` row touched.

Commits: `a22249d1a` (spec $50 amendment) · `76fd4edd3` (f9-01 verification + disclosure) · `e62e37650` (preflight attestation) · `57fbc182e` (dispatch tooling of record) · `cd05c839c` (supplement evidence, judging, three-way analysis) · `7643826e3` (registers) · plus the certification-rework commit. Certification of the supplement results: independent Kimi K3 numeric recompute from raw evidence — **every number confirmed exactly** (320/320 regrade byte-identical); Grok 4.6 adversarial review — **PROMOTE-WITH-CONDITIONS**, six wording/disclosure conditions in the supplement's own new material, all closed in the certification-rework commit (terminations disclosed, E1 MDE-exact framing, guardrail sentence narrowed, malformed-table scope footnoted, release-gate open-items refreshed, p-value procedure note).

## 2026-09-02 — Outside audits received and independently verified; owner repair rulings; corrections shipped

Outside audits received (`gpt_audit.md`, `mistral_audit.md`) and independently verified (five read-only lanes; GPT audit reproduced to the digit on every material claim; errata recorded in `docs/AUDIT_ERRATA_2026-09-02.md`); owner repair rulings (`committee/REPAIR_RULINGS_2026-09-02.html`); corrections shipped: E2 variant family filter (five corrected sensitivity values), table denominators, malformed-call table, Part B per-model table split + fabrication-flag removal, release gate replacing bare publishable flags, reconciled cost ledger (`results/stage1/COST_LEDGER.md`: $142.202064 recorded + ~$18 dev ≈ $160 of $600), deviation notes (`docs/DEVIATION_2026-09-02_FIXTURES.md`, `docs/DEVIATION_2026-09-02_ANALYSIS.md`), claims file updated; artifacts regenerated with pre-repair versions preserved in `*-2026-09-02-prerepair/`; supplement pre-specified and pending dispatch.

Commits: `2bed021a4` (code corrections) + `1a626cf46` (test expectations) · `a229f2d56` (regenerated artifacts + pre-repair archives) · `d8e5e9cce` (cost ledger) · `a108eec84` (fixture pipeline repair) · `548186b4c` (deviation notes, errata, supplement spec) · `a619cf628` (documentation reconciliation).

Certification (2026-09-02): Grok 4.6 adversarial review — **PROMOTE WITH CONDITIONS** (no registered confirmatory number moved; nine defects, three major, all in the round's own new material), conditions closed in `f4eac7839`; independent Kimi K3 recompute of every corrected number from raw run evidence — all eight items CONFIRMED. Note for citation: regenerated artifacts record their generation commit in `provenance.repository_commit`; cite the repair commits, not `e5f86f5`. Supplement dispatch remains gated on the preflight and the owner's budget comfort (expected ≈$23.3 of the $25 cap).


## 2026-09-01 — Routing-join correction: the terminal-turn contract, disclosed

The recorded run completed clean (3,600/3,600 rows, ~$160 of the $600 ceiling, zero failure rows
in every paid batch), but the final core analysis flagged itself not publishable over one warning:
the condition-invariant routing-join safeguard expected a routing row for the final assistant turn
of 101 runs (93 `max_tokens`, 8 `malformed_tool_call` of 1,280 E2-family runs) that terminated on
that very turn — a turn the frozen harness never routes by contract, the same boundary class the
2026-08-29 pass aligned for tool-only and empty turns. The owner authorized a bounded correction
(Option A, `committee/GRADING_SITTING_2026-08-31.html`). GPT-5.6 Sol, the grading author of
record, diagnosed (101/101 independent audit, zero stray routing records), designed and
implemented the evidence-bound exemption (grade.py + tests only; nothing under harness/), and
proved a 2,560-file semantic differential: exactly the 101 runs change, in completeness flags
only, with every analytical numerator, denominator, rate, estimate, interval, p value, fit and
verdict byte-identical, and family 9's artifact analytically unchanged. Grok 4.6 certified
PROMOTE (2026-09-01). Disclosure: `docs/DEVIATION_2026-09-01_ROUTING_JOIN.md`. The
pre-correction flagged artifact is retained beside the final publication artifact as part of the
record.

## 2026-08-30 — Amendment S1a: the tranche-start cost gate, repaired as a disclosed deviation

On run day the frozen harness refused the registered core batch (`recorded-core-s1`) at $0 spent:
the tranche-start pre-check summed a worst-case reservation over every cell of tranche 1 and
demanded $3,240.36 of headroom under the $600 ceiling — 13.4× the registered expected spend of
$240.99. The check was added in the 2026-08-24 audit repairs ("GPT B6"), appears in no registered
control (the registration's four controls are the per-call ceiling, the $300 report point, the
$300/$450 checkpoints and the drop order), had never been exercised above smoke scale, and could
never pass for the core batch at any spend level. Four delegated verification lanes confirmed the
arithmetic to the cent, established the registration boundary, and designed the repair
(`<WORKING-NOTES>`). The commit range
`FROZEN-S1..amend-s1` — a content commit and a manifest wrapper commit, mirroring the freeze's own
procedure, followed by this docs-only disclosure round — is that repair, exactly as tested there: the pre-check now bounds the most expensive **single cell** of the tranche
(still a fail-closed tripwire on pricing errors); two latent crashes on the same halt path are
fixed (a ceiling halt now skips later tranches and writes `batch.json` instead of dying in
`TrancheOrderError`; a per-call `CeilingReached` at a tranche boundary is recorded as a ceiling
halt instead of escaping and losing the manifest); `HARNESS_VERSION` bumps 0.1.1 → 0.1.2 so every
result row names the code that produced it; `MANIFEST.sha256` is regenerated. Every registered
control is untouched in code and re-proven by differential probes on frozen-vs-amended trees.
`FROZEN-S1` itself is untouched; `git diff FROZEN-S1..amend-s1` is the deviation evidence, and
`docs/DEVIATION_2026-08-30.md` is the disclosure for the published results. Adversarial
certification by Grok 4.6 (certifier of record) gates dispatch on this commit; the 1,920
zero-evidence refusal rows from the false start are preserved at
`<WORKING-NOTES>`.

## The 2026-08-29 correction pass — outside audit adjudicated, run contract completed, freeze rebuilt

Two independent audits of the first freeze (GPT: NO-GO with fourteen blockers; Gemini: GO) were
adjudicated on 2026-08-29 after three verification lanes checked every claim against the code, the
git history, OSF's live schema and the licence texts: thirteen of the fourteen blockers were real,
one was refuted (`committee/AUDIT_ADJUDICATION_2026-08-29.md`, beside the repository, carries the
finding-by-finding register and the evidence paths). The owner approved a bounded pass — run it,
complete the email repair, reword the Cohere NOTICE grant, correct the OSF study-type fields — and
four lanes ran. Sol via Codex, harness: the registered checkpoint-drop path implemented end to end
(durable elected-drop record, plan-derived ids, `undispatched` reconciliation), `expected_batch_id`
enforced before any dispatch, family 9 generated and byte-checked. Sol via Codex, grading: the
always-on condition-invariant routed E2 reading in the recorded pipeline, Part B replacement
lineage, publication bound to the frozen plans and the recomputed Part B seal, one combined Part B
package entrypoint, the symmetric guardrail aggregate, both subject constants derived from the
plans, repricer layer counts derived from the plan walk. A prose lane made fifteen documented
assertions true against their artifacts (disclosure boundary at the first real smoke; the NOTICE
now withholds both Cohere limbs with the raw files kept; the replay claim scoped to what actually
replays). The operator paste sheet was rebuilt against the final registration text. Grok 4.6
certified the whole diff adversarially: RETURN with three blockers — the sharpest being that the
new routing safeguard would have unpublished Part A on the classifier's own designed keyword
fallback, the mirror-image of the defect under repair — then, after the return pass, PROMOTE with
all seven findings closed and nothing new opened. A Kimi K3 fourth seat — the owner's own late
commission — then found two further blockers in the new reading that every earlier round had
missed: empty prose turns left their routing rows unconsumable (the same mirror-image class, one
row-class over, with committed runs already showing the pattern), and the new variant lacked the
family gate all five siblings carry, so its published rates would have pooled all eight families.
Both were repaired across two further return passes — the fourth seat's own closure check caught
the first repair over-reaching into a third variation of the class (tool-call-only turns, which
the router never routes by contract, had become missing evidence), and the final form mirrors the
router's recorded contract exactly — with five smaller notes riding along, and the freeze was
rebuilt a second time. At the close: grading 120 passed + 317 subtests (122 collected, two
standing environment skips),
harness 133 + 24, instrument lane 99; all four preflights (2,560 / 80 / 640 / 320); qualification,
power, plans and the B_scaffolded derivation regenerate byte-identical; the Part B seal recomputes
equal; the privacy-scan delta is zero-block over the full tree. Artifact schemas bumped to `1.9.0`
and `part-b-analysis-1.2.0` to match what the pass added. PM20's provenance sentence corrected by
dated annotation (two of its four "also measured" names have no published numbers anywhere).

**History note — commit identities.** The email-identity repair (owner-approved, 2026-08-29)
rewrote every commit from the first 2026-08-24 correction-phase commit forward, so their SHAs
changed; the repair moved author and committer metadata only, and the pre-repair chains are
preserved on local, unpublished backup branches (`backup-pre-email-fix`, `backup-pre-audit-pass`).
Commit SHAs quoted in the dated entries below and in the committed review records refer to the
pre-repair chain; every such commit's content is byte-identical in the published history. The
freeze identities of record are in `FROZEN.md` §1.

## R56/R57 — the Part B local panel: mistral-small out, Gemma 4 in, 2026-08-25

`mistral-small-4` dropped under R46's pre-registered rule (its chat template 500s on the
clarify-answer wire shape; failure published). Two candidates ran the free entrance + probe
gate; Grant seated **`gemma4-31b-it`** — Google's official QAT q4_0 checkpoint (pinned repo
revision + sha256 in MODEL_SNAPSHOTS.md), served text-only from a guarded llama.cpp rig on
:8112 (`models/gguf/gemma-4-31b-it-qat/start_server.sh`). Re-qualified from scratch on the
final artifact and rig after the ollama qualification copy proved to be an unloadable
multimodal split: **entrance 5/5, zero malformed; probe = structured Clarify requested and
answered in BOTH conditions + routed prose + STATUS sign-offs** — the strongest local-arm
profile in the study. Adds Google as the fourth lab family at zero cost. Package unchanged
(3,600 rows; plans regenerated, `--check` passes; budget byte-stable); PROVIDER_TERMS gains
the Gemma row; disclosure 40 records the panel change. Runner-up granite4.1 (IBM) and the
full candidate record are in the entrance/probe batches under `results/stage1/`.

## Step 9 — second smoke on the final pipeline, 2026-08-25

The R32 second smoke ran and reported: **20/20 green** across four subjects × five conditions
(B_scaffolded's first wire crossing) on the f1-01 development fixture; full record in
`evals/runners/stage1/SMOKE_REPORT_S2.md`. R54 verified 5/5 on disk (served
`deepseek/deepseek-v4-pro-0813` / `DeepSeek` in every run; the smoke now gates on the provider
echo as well as the slug). All four billing paths live-proven (R52 mistral in-run classifier +
judge, minimax-secondary via OpenRouter, DeepSeek via OpenRouter). The smoke caught its own
STATUS check encoding pre-disclosure-32 semantics — repaired truncation-aware with a
`--recheck` mode; the previously published "local arms never emit STATUS" caveat is retracted.
The f2-01 capability probe proved STATUS + structured Clarify end-to-end and split the R46
arms: muse keeps its seat (tool-form clarify+dissent demonstrated); **mistral-small-4 is
blocked on its clarify-answer path** (template 500 on the `tool_result → user` adjacency) —
drop-or-replace queued for Grant, PM default drop per R46. Step-9 dispatch ≈ $0.80; project
~$18 of $600. Cross-family certification: Grok PROMOTE WITH FIXES (three text fixes, all
applied — including a "15 calls" miscount that was actually 10) → confirm pass.

## R54 — DeepSeek dispatch via OpenRouter, 2026-08-25

Grant moved the DeepSeek subject's billing to OpenRouter with auto-reload. The `deepseek_primary`
arm now dispatches to `openrouter.ai/api/v1` pinned to DeepSeek's own endpoint
(`provider.only: [deepseek]`, `allow_fallbacks: false`), wire model = the **dated GA slug
`deepseek/deepseek-v4-pro-0813`** (the bare OpenRouter slug is the 0423 snapshot served only by
third parties — recorded as a trap); the logical/meter key `deepseek-v4-pro` is unchanged, so no
plan, price, or analysis key moves. Verified from the endpoints registry: exact first-party price
parity including the peak/off-peak schedule — **240.99/302.97 stand**; the honest overhead is
OpenRouter's 5.5% fee on credit purchases, outside the meter. The standing ~$60 first-party
top-up item is dissolved. Docs: BUDGET (R54 addendum + balances), PROVIDER_TERMS (two-layer
subject row + transcript-recipient note), MODEL_SNAPSHOTS, PILOT_PROTOCOL §9, FREEZE_CHECKLIST,
disclosure 39; the R38-era first-party configs are marked historical (they fail closed on the
unfunded account). The pin rides the config `extra_body` mechanism the Gemini classifier profile
already proved. Suites 125+92 green; plans `--check` and reprice byte-stable.

Same-day hardening after the three-lens adversarial panel and the first live probe: the panel
caught the original claim that the served slug was "echoed in the event log" as false at commit
time — fixed by implementation (`served_model`/`served_provider` persisted per run in run.json
and on every assistant transcript turn; all four claim sites corrected; the smoke gates on the
echo). The probe caught OpenRouter's account-level data policy filtering out the may-train
first-party DeepSeek endpoint (404), and a per-request override cannot loosen the account
ceiling — **the smoke is gated on Grant's one toggle at openrouter.ai/settings/privacy**, the
same input exposure the first-party surface already carried. OpenRouter's input-side ToS read
and recorded (§6.1 input ownership retained, §6.2 logging opt-in and not opted in, §6.3(b)
processing-only license). The second-smoke machinery landed with it: `smoke_s2.yaml` (four
subjects, real billed classifier, B_scaffolded in the matrix) and the smoke tool now takes its
classifier and conditions from config.

## Step 7 — package gates, 2026-08-25

Every billed rate verified against a first-party pricing page: Sonnet 5 moved to the **2/10
standard price** (the provider cancelled the scheduled increase the old 3/15 row priced) and
DeepSeek v4-pro up to its **1.32/3.96 peak ceiling** (the committed "deliberate over-estimate"
was an under-estimate at peak — the unsafe metering direction); Terra/Sol, Mistral Medium 3.5 and
MiniMax-M3-via-OpenRouter all verified exact. Budget regenerated: **240.99 USD expected / 302.97
worst** (supersedes step 6's 278.82/340.80); DeepSeek top-up guidance is now ~60 USD. R52
recorded: Grant enabled Mistral auto-billing, discharging the step-6 balance flag. Dated model
snapshots + local checkpoint sha256s recorded (`docs/review/step7-2026-08-25/MODEL_SNAPSHOTS.md`).
Dependencies consolidated into the project venv and locked (`requirements.lock`) — the pinning
gate found the anthropic SDK installed **nowhere**, so a recorded Sonnet dispatch would have
failed closed at call time; both suites green under the canonical interpreter. Provider terms
verified for MiniMax and all four labellers (two bot-walled pages read first-party in a real
browser); all committed label runs confirmed on permitted API surfaces; one licensing carve-out
proposed for the Kimi-Code-produced certification prose (Grant signs). The secret/PII scan
(`tools/scan_package.py`, committed) ran to **zero block findings** after one true catch — 138
real email addresses (a Node.js collaborator list read by the subject model mid-run) redacted
from one development transcript with disclosure in `DEVELOPMENT_RUN.md` — and four adapter
conformance harnesses whose fixture defaults pointed at expired session scratch space now fail
closed. Evidence regenerators re-proven: seal re-hash equals `658c0662…`, freeze-qualification
tables regenerate byte-identical, plans `--check` passes, and `tools/make_manifest.py` (new)
produces the FROZEN.md package digest. All four preflights re-pass under the corrected prices.

## Step 6 — plans, analysis and budget regenerated under branch 3, 2026-08-25

The instrument-closure lane closed on branch 3 (R47: no instrument qualified; core E2 descriptive;
Part B fresh C−D the principal clean test) and brief steps 4–6 landed. The 40 fresh scenarios were
authored clean-room, certified and **sealed** (set_sha256 `658c0662…`, manifest committed, bodies in
durable staging until FROZEN-S1). The `B_scaffolded` control arm (R45) is implemented end to end
(mechanically derived prompt, harness profile, grading and blinding integration). The three recorded
plans are generated from the registered arithmetic (`tools/make_recorded_plans.py`; 3,600 recorded
rows = 3,280 API-priced + 320 free local; all preflights pass, the fresh ones against the sealed
staging copy). The budget is repriced from the committed plans (`BUDGET.md`: 278.82 USD expected /
340.80 worst; new flag — mistral instrument spend 29.16 exceeds the ~20 free tier). Power/MDE
regenerated (`docs/review/step6-2026-08-25/power_mde_step6.json`: core E1 0.310 confirmatory at
plain alpha, E2 0.194 descriptive, fresh C−D 0.155 — the study's best-powered test; an early draft's
0.133 under-borrowed the donor variance and was corrected on the Grok cross-family review). The Part B
deterministic endpoint was implemented blind from the frozen contract by Sol, reviewed by two seats
(Claude conformance, Grok adversarial with 97 executed attacks), and the contested grade-time
readings adjudicated once in `evals/SCENARIO_CONTRACT_PART_B_READINGS.md` (R50) before any recorded
run. Canonical docs (claims file, protocol sections 5/7/8, contracts, glossary, data management)
restated under branch 3.

## R43 — Grant's takeover direction recorded, 2026-08-24

Grant's takeover brief (preserved verbatim at `../briefs/TAKEOVER_BRIEF_2026-08-24.md`) settles the five
questions the correction phase left open and is recorded as R43 in `DECISIONS_V0.1.md`. The documents
were reconciled in one pass, superseding rather than rewriting: **structure** — Stage 1 becomes two
separately reported components, the Part A core validation pilot (now 40 x 4 x 4 x 3 = 1,920, three
repeats) and the Part B sealed fresh-scenario mechanistic replication (40 fresh clean-room scenarios x
C and D x 4 subjects x 2 repeats = 640, primary contrast C minus D two-sided on the new deterministic
endpoint `scenario_concordant_structured_intervention_before_gate`); the recorded package stays 2,960
and the components are never pooled. **Instrument** — the judge question is settled by a bounded
instrument-closure lane with a frozen protocol and a three-branch outcome tree (`PILOT_PROTOCOL.md`
section 6a); the gate anchor stays E2's primary temporal reading. **Governance** — human review leaves
the mandatory freeze checklist (a security review is required only before "production-ready" claims);
no external outreach before the completed Pilot I package; all four integrations remain public
deliverables under a four-tier release policy. Supersessions stated in R43: parts of R37, R39
(the judge-failure fallback and the 2,560 ruled value with its F5 repeat-4 clause), R38's 2,560 matrix,
and R40 (P4 for Part B only; P3's 2,560-run core via the repeat reallocation), plus a reversible PM
amendment of R34's drop order (frontier replication first, then core repeats 3 to 2; scenarios and the
fresh component never dropped). New disclosures 35 (the C minus D emphasis postdates development
data; hence two-sided) and 36 (the human-review posture). Plans, prices and the fresh corpus itself
follow at the brief's steps 3 to 6; the committed `plan_recorded.yaml` and the 212/284 USD projection
price the superseded four-repeat matrix until then.

## Correction phase, 2026-08-24

Opened after three independent adversarial reviews (GPT 5.6 Sol, Grok 4.6, Mistral) returned "no-go for
FROZEN-S1, approved only for a bounded correction phase", and a fourth-seat scenario audit (Kimi K3)
plus an independent methodologist sweep commissioned inside the phase. The full ledger, with every
finding, its verdict against the files, and its disposition, is `../CORRECTION_PHASE_2026-08-24.md`.

**Withdrawn.** PM20's three judge-agreement figures (0.896 primary, 0.903 secondary, 0.934 Kimi): no
committed code produced them, two abstention conventions were mixed inside one comparison, and the
weighting behind the first is circular. Disclosure 18's claim that the residual channel leak works
against the hypothesis: measurement shows it runs the other way.

**Instruments.** `qualify_freeze.py` regenerates every qualification number from committed data with no
absolute paths, under raw agreement, a circular verdict-pool weighting printed with its degenerate-judge
floor (0.8209), and a judge-independent condition-by-channel weighting. Under the non-circular
weighting the seated primary scores 0.8055 and ranks last of the three serious candidates. The gate is
recorded as FAILED for all five candidates. `instrument_prices.json` prices every instrument model and
the judging pass now meters itself and halts on an unpriced model (R40 P3).

**Endpoints.** E2 is computed under five preregistered readings (gate anchor, state-change anchor,
first stop only, expected act only, timing only) and E1 under two imputation policies; all are published
from one artifact. The E2 timing anchor now requires an execution position, so a `cat` or a `grep` of the
gate script no longer moves the deadline (33 regression cases). E1's adverse imputation is restricted to
failures before any model decision, which removes a penalty that fell only on the arms without tools —
on the development corpus that alone moved the contrast from -0.30 to -0.10. A channel-symmetric
`unnecessary_stop_any_channel` guardrail joins `unnecessary_invocation`, which was structurally zero in
A, B and B_filler.

**Inference.** The confirmatory test is now the scenario-cluster sign-flip test on the scenario-paired
difference, matching the headline estimand; the mixed model is supplemental. Confirmation requires Holm
rejection and the preregistered direction and no sign conflict — before this, a significant harmful
result would have been emitted as a rejection with no direction field. Every E2 result carries a
tipping-point bound on the tool-channel leak. The registered minimum detectable effect is 0.19 on E2 and
0.30 on E1, with cluster-imposed floors of 0.15 and 0.27 (`power_mde.py`).

**Provenance.** Stored judge verdicts are re-bound to the projection being graded; judge caches are
keyed on the instrument's full fingerprint. The check immediately found a real drift: the published
development artifact's verdicts predate fix 14's frozen ground-truth text. The all-attempts denominator
is the frozen tranche manifest, and an unreconciled analysis is marked not publishable as a result.

**Harness.** Discretionary spend checkpoints wait for a completed tranche boundary; the hard ceiling
still refuses the individual call. Every outstanding reservation counts against headroom, an ambiguous
provider failure stays charged, resume accounting fails closed, and non-finite or negative controls are
rejected at config load and in the meter. The prose route is recorded before the completion probe can
end a run, so a turn that both raises the issue and leaves the fixture passing keeps its stop.

**Adapters.** Authenticated per-session operator channels ported to codex, kimi-code and opencode, with
cross-process locks and transactional event-plus-state writes; negative tests over every operator verb,
two-process concurrency tests, and independent verification by a reviewer who did not implement them.
The codex suite no longer depends on a repository-local virtualenv.

**New documents.** `PILOT_PROTOCOL.md` and `CLAIMS_AND_LIMITATIONS.md` (both named by the README since
the beginning and both missing), `SCENARIO_FAMILIES.md`, `BUDGET.md`, `PROVIDER_TERMS.md`,
`DATA_MANAGEMENT.md`, `GLOSSARY.md`, `FREEZE_CHECKLIST.md`, and the recorded config and plans
(`config_recorded.yaml`, `plan_recorded.yaml`, `plan_family9_recorded.yaml`, both preflight-clean).

**Rulings.** R41 supersedes R40 P5 formally. R42 records the phase. PM21 records that the judge's
filtering role is unmeasured and that what evidence exists refutes it. Disclosures 21 to 31 added.

## Unreleased

- 2026-08-22: repository created (private). Skeleton, MIT license, DECISIONS_V0.1 with the first six rulings.
- 2026-08-22: committee round 1 (Kimi K3, Grok 4.6, GPT 5.6 Sol, each launched headlessly) reviewed the protocol and study decisions; five defaults moved; record in `committee/round-1/`.
- 2026-08-22: Grant ruled on all sixteen decision-page questions (R7 to R23). The constitutional core is now ready to be written into SPEC.md; freeze follows the host spikes.
- 2026-08-22: Segment S2 host spikes run on Claude Code 2.1.240, OpenCode 1.18.21, Codex 0.149.0 (three Claude agents), audited by GPT 5.6 Sol, reconciled by three Opus reviewers; 51 rows: 31 PASS / 13 PARTIAL / 5 FAIL / 2 NOT_TESTED. Proposed designations: Codex App Server frontier; Claude Code SDK path frontier candidate pending a full rerun; OpenCode partial. Record in `spikes/2026-08-22/`; raw evidence logs stay in vault staging until the pre-publication leak sweep.
- 2026-08-22: SPEC.md v0.1 draft and the four protocol schemas (affordances, event, state, attestation) promoted after an Opus compliance review against R7 to R25 (3 deviations and 5 gaps fixed, re-checked, verdict PROMOTE). Review record in `docs/review/`. Known nits for promotion-time cleanup listed in the review's Re-check section.
- 2026-08-22: Segment S2b. Claude Code Agent SDK full rerun (partial: callbacks fail open on crash and malformed return, closed only on timeout or client death) and a first Kimi Code spike over ACP (partial today, frontier-shaped; no host Archive terminality). Cross-host finding: R12 fail-closed is an adapter obligation on every host; client-as-gate protocols (Codex App Server, Kimi ACP) are the strongest enforcement shape. Audited by Sol, reconciled by Opus; record in `spikes/2026-08-22/`.
- 2026-08-22: CONTRACTS.md (adapter command surface, run record, grader and conformance interfaces), THREAT_MODEL.md, SECURITY.md; SPEC section 7 rewritten for R26/R27 with per-host structural limits; CONFORMANCE.md rewritten (designations, 32 tests, release gate). PM1 to PM6 recorded. Charter correction 3 amended after the SDK rerun.
- 2026-08-22: Claude Code interactive keyboard check by Grant recorded (`spikes/2026-08-22/claude-code/KEYBOARD_CHECK.md`): pause holds in the TUI, chat is not resume, resume does not duplicate the side effect, AskUserQuestion blocks interactively, an archived session reopens (S5 PARTIAL confirmed, R27 caveat).
- 2026-08-22: the forty scenarios (8 families x 5 variants) promoted into `evals/scenarios/` after independent family reviews, a cross-family critic, a global edit pass, six rewrites and a re-review; review record in `evals/review-record/2026-08-22/`. No model has yet been run against them (development exposure: none).
- 2026-08-22: event.schema.json: tool_input discriminated by event type (a bare Pause now validates; a clarify input on a resume event is rejected); prose_routed event type added (PM8). Version stays 0.1.0-pilot until the freeze; the addition is recorded as a pre-freeze change, not a release.
- 2026-08-22: state.schema.json gains declined_courses (alternatives_open Decline persisted beside decline_locks); DECLINED_COURSE added to denied_because_state. Pre-freeze change.
- 2026-08-22: state.schema.json: override_spent on dissent_holds[].resolution (a restored guard permits the remaining use only on an explicit false). PM10: pre-freeze schema additions are draft changes, versioning starts at the freeze tag.
- 2026-08-23: prose_routed gains authority (required: llm | keyword), secondary_route, secondary_classifier_version, secondary_rule_id, classifiers_agreed, fallback_reason; CONTRACTS termination_reason gains spend_ceiling. A pre-freeze schema change under PM10; more followed on 2026-08-23 (below).
- 2026-08-23: independent aerial review (Fable, max effort) recorded in the <WORKSPACE> staging; verdict on track; R33 (Stage 1 freezes on its own) and R34 (budget discipline) adopted; harness pre-smoke fixes and the grading layer queued; four questions to Grant (family 9, OpenCode rule, drop order, pre-run outreach).
- 2026-08-23: first real-model smoke: Sonnet 5 passes all four conditions ($0.18); GPT-5.6 Terra needs the Responses API; local Qwen needs the bridge address; both fixes in progress. R35 family 9, R36 OpenCode build by Fable, R37 outreach paused. HANDOFF_2026-08-23.md written in the project folder.
- 2026-08-23: smoke 3 green: Sonnet 5, GPT-5.6 Terra (Responses API) and local Qwen3.8-27B (flattened tool schemas, thinking off on the wire) each complete f1-01 in all four conditions; ~$1.50 across three smokes. The OpenAI arm replays only whitelisted item fields; the local arm's flattened rendering is recorded per run and its malformed-call rate must be counted per arm in the development run.
- 2026-08-23: Stage 1 harness promoted to evals/runners/stage1/ after four Sol reviews and a green three-model smoke (mock proof 33/33; 53 logs, 323 events valid). Four reviews in docs/review/harness/. Results and venv are not in the repo.
- 2026-08-23: cost rehearsal (R34): 60 runs (5 scenarios x 4 conditions x Sonnet 5, GPT-5.6 Terra, local Qwen3.8-27B), $4.81 spent, 499 calls, reservation covered every call, zero overshoot. Projection for the full R15 matrix plus the R29 Opus tier: $213.77 against the $600 ceiling; no drops needed; gpt-5.6-sol unpriced and excluded. Families 3, 4, 6 priced from the measured-family mean (38 percent of the primary matrix). Record in results/development/rehearsal-2026-08-23/.
- 2026-08-23: gpt-5.6-sol priced (USD 4 in / 20 out, promotional rate read by Grant from OpenAI's table; cached input inferred at 10 percent). Full plan now fully costed: USD 228.02 of the 600 ceiling, no unpriced components, no drops needed.
- 2026-08-23: Kimi Code adapter promoted to adapters/kimi-code/ after four Sol reviews (27 PASS, 5 PARTIAL, 0 FAIL on the live host; PID ownership via pidfd; no process-environment reads). Register entry added to CONFORMANCE.md. Raw evidence stays in vault staging until the pre-publication leak sweep.
- 2026-08-23 (pause point): Kimi Code adapter promoted; Claude Code adapter one fix from promotion; Codex pass 8 and OpenCode pass 2 in review; grading layer built (Sol) and under review; 112 scratch trust entries cleaned from the operator's Codex config with approval. Handoff updated for session compaction.
- 2026-08-23 (after the Fable PM audit): rulings PM11 to PM16 (family 9 defined and promoted, route classifier moved off the mock and validated on outside-family labels, E2 decided by the blinded judge on top of the timing rule, sandbox isolation required before any further real-model run, prose precedence, family 9 split at discovery). Event schema (all four byte-identical copies, PM10 draft): `prose_routed` gains `assistant_turn_index`, `call_position`, `tool_call_ids`, `mixed_turn`, `sampling_sent`; `secondary_route` nullable; `fallback_reason` gains `empty_text`; `excerpt_hash` described; required list expanded. Run record gains `status_lines`, `final_turn_has_status`, `host_transition_failed` and the scheduled-failure marker. Claude Code adapter promoted (26/0/6, five Sol reviews). docs/PREREGISTRATION_DISCLOSURES.md started.
- 2026-08-23 (evening): grading layer promoted to `evals/grading/` (one flat package: blind, grade, judge, analysis, common, fake-data generator, schema, prompts, tests) after two outside-family reviews, six Sol fix passes and a Claude verification (`docs/review/grading/`). Primary E2 = timing rule AND the frozen condition-blinded Haiku judge (PM13), local judge as secondary, judges retained separately; family 9 descriptive measures split at discovery (PM16); evaluation_awareness_flag produced by the same judge pass; every figure carries code and data hashes. Live pipeline exercised end to end on the 60 rehearsal runs (staging only, PM14). Codex adapter promoted. Classifier reference labels (PM15 set) in `docs/review/classifier/labels_pm15/`.
- 2026-08-23 (Sunday): OpenCode adapter promoted (four of four; process-scoped second gate, late-plugin refusal before dispatch; six Sol reviews). Harness re-promoted twice more (byte-safe bounded capture, harness_error rows, resume; openai_compatible classifier provider; B_filler condition). Instruments chosen by measurement, PM18: classifier and primary judge mistral-medium-2604, secondary judge deepseek-chat; validation record with a three-family blind panel and a written qualification standard in docs/review/judge-validation/. Grading layer re-promoted (fixes 6 to 10): PM17 E1 requires a claim, MEASURES.md generated from the code, numerators and denominators everywhere, direction consistency, abstention token (rubrics 1.1.0), condition-mapping test against CONDITIONS.md. Development run dev-2026-08-23 (360 local runs) published as the calibration artifact with its defect-to-ruling record under results/development/. Advisor notes (GPT) adopted; CONDITIONS.md; CONTRACTS grader signature gains state_json and raw_transcript; verdict vocabulary includes PARTIAL.
