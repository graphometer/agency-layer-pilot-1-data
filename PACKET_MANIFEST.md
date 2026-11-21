# What this packet contains, and what was left out

`study/` was exported with `git archive` from the study repository at the label `RESULTS-S1` (commit
`4c492e6915a1ab89b5c8f3785c68edc777dbfcc9`, 3 September 2026). An export carries files only, never the
repository's history, so nothing that was removed before sealing can be recovered from it.

The sealed checksum list `study/MANIFEST.sha256` names 117,922 files. This packet keeps 105,495 of them
(67,095 regular files and 38,400 links), plus the list itself, and leaves out 12,427. `recount.py` checks every kept file against
the list.

## Included

| Path in `study/` | Files | Why it is here |
|---|---:|---|
| `README.md`, `CLAIMS_AND_LIMITATIONS.md`, `GLOSSARY.md` | 3 | the repository's own front door, binding claims and glossary |
| `PILOT_PROTOCOL.md`, `FROZEN.md`, `FREEZE_CHECKLIST.md`, `CONDITIONS.md`, `SCENARIO_FAMILIES.md`, `CONTRACTS.md`, `SPEC.md` | 7 | the study plan, the frozen settings, the arms, the task kinds, the file formats, and the protocol text being tested |
| `DECISIONS_V0.1.md`, `CHANGELOG.md`, `BUDGET.md` | 3 | the dated decision register, the change history and the budget, which the plan and the corrections cite by number |
| `RELEASE_RESULTS_S1.md`, `MANIFEST.sha256` | 1 + list | the sealing record and the checksum list |
| `LICENSE`, `LICENSE-CC-BY-4.0.txt`, `NOTICE`, `PROVIDER_TERMS.md`, `DATA_MANAGEMENT.md` | 5 | licences, provider notices, the provider-by-provider publication terms, and the data-handling rules |
| `requirements.lock` | 1 | the exact Python package versions used |
| `docs/OSF_REGISTRATION.md`, `docs/PREREGISTRATION_DISCLOSURES.md` | 2 | the preregistration text and the disclosures made in it |
| `docs/DEVIATION_*.md` (4), `docs/AUDIT_ERRATA_2026-09-02.md`, `docs/SUPPLEMENT_SPEC_2026-09-02.md`, `docs/PREFLIGHT_ATTESTATION_SUPPLEMENT_2026-09-02.md` | 7 | every departure from the plan, every correction after outside audit, and the plan and checks for the corrective re-run |
| `docs/AUDIENCE_AND_PRIOR_ART.md` | 1 | related work and who the study is for |
| `docs/review/judge-validation/` | 159 | the scorer's validation tests: examples, labels, candidate answers, scoring code and results (two files left out, below) |
| `docs/review/classifier/` | 16 | the reference set the analysis uses to report route-classifier accuracy |
| `docs/review/step6-2026-08-25/` | 1 | the committed power table behind the "could detect about N points" figures |
| `docs/review/part-b-scenarios/` | 4 | the seal record of the second task set, which the second-set analysis checks |
| `evals/scenarios/`, `evals/scenarios-part-b/` | 620 | all 85 tasks with their files and check scripts |
| `evals/SCENARIO_CONTRACT*.md`, `evals/seal_part_b_set.py`, `evals/validate_part_b_set.py` | 5 | the rules the tasks were written to, and the seal tools |
| `evals/grading/` | 26 | the blinding, scoring, grading, analysis and power code, with tests |
| `evals/runners/stage1/` (harness, configs, plans, tools, tests, mocks, reports) | 164 | the test harness, the exact prompts, the frozen settings and plans, and the pre-run check reports |
| `evals/runners/stage1/results/stage1/recorded-*`, `supplement-*`, `replacement`, `spend`, cost and scan records | 98,502 | every recorded run, verdict and analysis, including earlier analysis versions kept so corrections can be checked |
| `evals/runners/stage1/results/stage1/smoke-*`, `probe-*`, `entrance-*`, `mock-proof` | 890 | the pre-run checks of the harness and the local models |
| `results/development/` | 5,070 | the disclosed development runs, published as the calibration record the plan promised |
| `packages/protocol/` | 4 | the protocol's JSON schemas |
| `tools/` | 4 | the checksum, privacy-scan, cost-ledger and fixture-check tools |

Added at the top of the packet (not from the repository): `README.md`, `RECOUNT.md`, `recount.py`,
`DATA_DICTIONARY.md`, this file, `REDACTIONS.csv`, and copies of `LICENSE`, `LICENSE-CC-BY-4.0.txt` and
`NOTICE` (9 files); and `article-data/` (19 files), an unedited copy, made 21 November 2026, of the data
folder published with the article at graphometer.ai/kindness/data/, with a two-line `README.txt`.

## Left out

| Path in the repository | Files | Why it was left out |
|---|---:|---|
| `docs/review/judge-validation/freeze-qualification/judge_answers/command-a_pass1.jsonl`, `command-a_pass2.jsonl` | 2 | Cohere's terms bar distributing this content, and the repository's `NOTICE` (section 4.2) grants no right to redistribute these two files. The qualification result computed from them stays in the published tables (`QUALIFICATION_TABLE.md`, `PILOT_PROTOCOL.md` section 6); it can no longer be regenerated from this packet. |
| `evals/runners/stage1/results/stage1/recorded-judge-cache/`, `supplement-judge-cache/`, `evals/runners/stage1/judge-cache/` | 11,832 | scorer response caches; `DATA_MANAGEMENT.md` says caches are not published because every verdict they hold is already in the `*-judged/` files |
| `adapters/` | 447 | the four host integrations (Claude Code, Codex, OpenCode, Kimi Code) belong to a separate, later study and are not needed to check any Pilot I number |
| `CONFORMANCE.md`, `SECURITY.md`, `THREAT_MODEL.md`, `docs/evidence-manifests/`, `spikes/` | 28 | host-integration test results, security policy and threat model for those integrations, and early feasibility notes |
| `committee/` | 7 | committee notes |
| `docs/review/` other than the four folders above | 95 | internal review papers on the design, code and tasks |
| `evals/review-record/` | 12 | internal reviews of the task drafts |
| `packages/core/`, `site-data/`, `evals/fixtures/`, `.gitignore` | 4 | empty placeholders and a repository setting |

## Changed

Nothing in the results. For privacy, 686 places in 24 files were replaced with labelled placeholders,
each listed by file and line in `REDACTIONS.csv`:

- 64 places in 22 files: short strings in 21 Markdown documents and one comment line in
  `requirements.lock`.
- 622 places in 2 run transcripts: the Node.js project's public contributor list, which an agent printed
  inside the sandbox (GitHub handles, names and pronouns of 161 listed people). Only the tool output in
  one line of each transcript changed.

`recount.py` expects exactly those 24 files, the 2 links in the corrected analyses that point to one of
the edited transcripts, and `RELEASE_RESULTS_S1.md` (whose identity lines were filled after the checksum
list was made, as that file explains) to differ from the list.
