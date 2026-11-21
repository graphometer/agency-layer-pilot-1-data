# Data management, redaction, retention and incident response

*Required before recorded dispatch by the GPT review (R5). Written in the correction phase 2026-08-24.
Companion to `PROVIDER_TERMS.md`, which covers whether we may publish provider outputs at all.*

## What the study creates

| Class | Where | Volume at recorded scale | Published? |
|---|---|---|---|
| Run records, events, state, check output | `results/stage1/<batch_id>/<run_id>/` (the path the harness actually writes — CONTRACTS §2, `harness/cli.py`; an earlier `results/pilot-1/` name here matched nothing on disk, OSF-lane catch 2026-08-25) | 3,600 planned recorded runs (Part A core + B_filler + B_scaffolded + family 9, and the Part B fresh component with its two free local arms under their own batch ids; R43/R45/R46), plus every preserved failed attempt — a run that fails before a gradeable decision may be re-dispatched once and the failed attempt is kept immutably (`MAX_REPLACEMENTS_PER_PLANNED_RUN = 1`), so the table holds 3,600 rows or more, never fewer. **Measured 2026-08-26** over the 450 committed development runs: mean **24 KB** per run directory, median 20 KB, p90 36 KB, max 168 KB, 11.0 MB for all 450, all of them the local subject; on the smoke batches the frontier subjects measure slightly smaller than the local one (means of 16 to 18 KB over seven runs each). At 3,600 runs that is about **86 MB** of run records, and the whole tree of the same shape — runs plus judged files, blinded projections, cost journals and analysis — scales from the 34 MB the development tree occupies to a few hundred MB. An earlier "a few MB each with transcripts" here was wrong by about a hundredfold and implied a package near 11 GB | yes, CC BY 4.0 (R19) |
| Fresh-scenario authoring record (drafts, review findings, repairs, hashes) | staging until the freeze, then `docs/review/part-b-scenarios/` (the committed location; an earlier `fresh-scenarios` name here never existed) | small | yes, after FROZEN-S1 — never before, because the set is sealed |
| Raw transcripts | same folders | the bulk of the tree | yes, subject to `PROVIDER_TERMS.md` |
| Condition-blinded projections | `analysis/per_run_blinded/` | one per run | yes |
| Judge verdicts and prompt digests | `judged/` | about 15,000 rows as priced on the superseded pre-R43 four-repeat core; smaller at the R43 matrix (the Part B primary is judge-free) and conditional on the section 6a instrument outcome; regenerated at step 6 | yes |
| Instrument validation panels | `docs/review/` | already committed | yes |
| Sandbox fixtures during a run | a bubblewrap namespace, deleted after | transient | no |
| Cost journals and meter records | `results/stage1/<batch_id>/` | small | yes |

Everything is synthetic BY DESIGN, with one recorded exception caught by the step-7 scan (R53):
a subject model read a Node.js contributor list inside its sandbox during the development run and
138 real email addresses landed in one published-bound transcript — redacted with written
disclosure in DEVELOPMENT_RUN.md, the only transcript edit ever made; the scan re-runs on the
final tag. The fixtures were authored for this study; there is no personal data, no real
credential, no customer data and no third-party web content anywhere in the corpus by design.

## Controls

1. **No secrets reach a run.** Keys live in `work/agency-layer/.env`, outside the repository, read by
   the provider clients from the environment and by nothing else. No session reads them. The sandbox is
   entered with a clean environment (PM14) and has no network, so a model cannot exfiltrate anything
   even if it tried.
2. **Secret and PII scan before any package is published.** Over every publishable file: high-entropy
   string patterns, the known key prefixes of each provider, email addresses, phone numbers, IP
   addresses other than loopback, and absolute paths under `/home` or `<LOCAL-PATH>`. A hit is redacted in
   place with a labelled placeholder and the redaction is listed in the package README. The scan is run
   again on the final tag. Note for reviewers: an adapter conformance evidence capture can contain a
   per-session operator key printed by `start`; those keys are ephemeral test-session keys, but the scan
   redacts them anyway so no published artifact teaches the pattern.
3. **No vault paths in a published package.** Internal absolute paths are fine in the working documents
   and must not appear as dependencies in the reproduction package (GPT review documentation item 10).
   The reproduction instructions use repository-relative paths only; `qualify_freeze.py` was rewritten in
   this phase precisely because it read an absolute staging path.
4. **Model text is published as produced.** No silent editing. If a provider's terms force excerpting,
   the excerpt rule is the one in `PROVIDER_TERMS.md` and the withholding is named in the package.
5. **Custody.** Raw runs are committed to the repository (R4) and pushed by Grant. Git is not a backup:
   before a recorded run, the local weekly backup layer must be working, because a 3,600-run transcript
   tree is the largest artifact this project will ever create and it has one copy until it is pushed.
   The Grok review named this (H8) and it is a precondition, not a nicety.

## Retention

| Artifact | Retention |
|---|---|
| Recorded-run artifacts | permanent; they are the result |
| Development and rehearsal artifacts | permanent, published as the calibration record with their defect history (this is deliberate: the project's correction history is part of what it publishes) |
| Rehearsal transcripts from the non-isolated sandbox | staging only, never committed, never published (PM14) |
| Judge caches | not published; they are reproducible from the artifacts and the frozen instrument |
| Provider request logs | none kept beyond the run record's usage fields |

## Withdrawal and correction

There is no human subject and, after the R53 redaction above, no personal data, so there is no withdrawal right to honour. Corrections
work like this: an error found after publication is fixed in a new dated entry in
`docs/PREREGISTRATION_DISCLOSURES.md` and in the package's correction log, with the old figure left
visible beside the new one. Nothing is silently edited. If a published number turns out to be
unreproducible from the artifact, it is withdrawn in the same words as the original claim — the
correction phase already did this once, for the PM20 agreement figures.

## Incident response

| Incident | Response |
|---|---|
| A secret is found in a published artifact | unpublish the file within the hour, rotate the key (Grant), redact, republish with a correction note, and record how the scan missed it |
| A provider's terms turn out to forbid what we published | apply the excerpt or withhold fallback in `PROVIDER_TERMS.md`, republish, name the change in the package |
| A defect that changes a published number | recompute, publish both numbers, write the disclosure entry, and tell anyone who was sent the earlier figure |
| A takedown request | acknowledge, assess against the terms matrix, act within a week, publish the outcome |
| The repository is flipped public by accident before the freeze | Grant is the only account with push rights; the remote is private until he flips it, which is the control |

## Licensing (R19)

Code MIT; specification text, results and transcripts CC BY 4.0. Both licence choices are unchanged.
The repository root carries `LICENSE` (MIT), `LICENSE-CC-BY-4.0.txt` and `NOTICE`; the data package
carries the same `NOTICE`, which names each provider whose model outputs it contains, the AI-generation
notice OpenAI's terms encourage, and the accuracy notice Anthropic's terms require. The step-7 terms
verification (2026-08-25) added three obligations, collected in `PROVIDER_TERMS.md` under "Package
NOTICE obligations": per-item model attribution on every validation label (satisfies Google, Z.ai and
Moonshot marking rules at once), the Z.ai §1.f.xii no-external-model-reuse sentence, and a per-file
licence note for the Kimi-Code-produced prose. **That third obligation was withdrawn on 2026-08-26.**
It rested on the 2024 consumer Kimi Model Service Agreement, which is not the live instrument: the
agreement the Kimi site points at is the Kimi AI Terms of Service of NOVASCENT PRIVATE LIMITED
(Singapore), effective 2026-08-13, which assigns the user all right, title and interest in the Output
with no non-commercial cap, and the PRC agreement effective 2026-08-31 vests Input and Output rights
in the user the same way. The six Kimi Code evidence files, the Codex-adapter fix and the 45 Part A
scenario packets drafted on that surface therefore publish under the ordinary package grants and go
into the deposit with everything else. Grant ruled the remaining questions on 2026-08-26: two classes
of file are carved out of **both** the MIT grant and the CC BY 4.0 grant by an exception list in
`NOTICE`, every exception's grant permitting verification and reproduction explicitly — the per-item
GLM-5.3 label files (`LicenseRef-AgencyLayer-GLM-Labels-1.0`) and the two per-item `command-a`
judge-answer files (`LicenseRef-AgencyLayer-Cohere-Answers-1.0`), which Cohere's SaaS agreement bars
its own customers from using for benchmarking or competitive analysis. The `command-a` qualification
result is **not** withdrawn: it was measured against a standard frozen before any candidate was
seated, it regenerates from the committed code, and it stays in the published tables. The carved-out
files stay in the public GitHub repository and are **excluded from the deposit** in Zenodo or the
equivalent persistent repository, because a deposit record carries one licence field and a
mixed-licence record would be a false grant.
