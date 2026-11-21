# Deviation note — 2026-08-30: the tranche-start cost gate

*This note is part of the published results. It discloses the one post-registration change made to
the frozen harness, why it was unavoidable, what changed, and what did not.*

The frozen harness carried an unregistered pre-check, added in the August audit repairs as
"GPT B6": before a tranche started it summed a worst-case cost bound over every cell in it and
refused the tranche if the sum exceeded the remaining budget. On 2026-08-30 it refused the
registered core batch at $0 spent, demanding $3,240.36 of headroom under the $600 ceiling.

It could never pass. The sum assumes every one of 1,920 cells runs to its turn limit, that each
prompt carries every prior capped reply, and that three classifier calls are paid per turn — then
adds all 1,920 together, though the harness dispatches one call at a time. It demanded 13.4 times
the registered expected spend of $240.99, and no registered control could reduce it.

**Changed:** the pre-check now requires only the most expensive single cell to fit. Two crashes on
the same path were fixed: a budget halt now writes its batch manifest instead of dying in an
ordering error, and a per-call ceiling stop at a tranche boundary is recorded as a ceiling halt
instead of escaping. `HARNESS_VERSION` was bumped 0.1.1 → 0.1.2 so every result row is
self-identifying; `MANIFEST.sha256` was regenerated over the amended tree.

**A promise withdrawn, stated plainly:** the frozen gate claimed that a tranche which starts can
finish under the ceiling. That claim was never true — the frozen per-cell figure omits tool
schemas and tool results, which re-enter later prompts capped by the sandbox's byte limits, not by
`sampling.max_tokens` — and this amendment stops making it. The amended per-cell figure is a
fail-closed pricing tripwire, not a worst-case bound. The money guarantee is, and always was, the
registered per-call reservation check in `CostMeter.reserve`.

**Confirmatory-validity rule, bound before any outcome is inspected (2026-08-30):** if the
per-call hard ceiling fires **inside** any tranche, that tranche supports no confirmatory claim.
Only fully completed earlier balanced tranches may. If the interrupted tranche is core tranche 1,
there is no confirmatory Part A result. Cells of a later tranche skipped after a ceiling halt are
recorded as `cells_not_dispatched` in the batch record and are **not** automatically reconciled as
`undispatched` — they remain unreconciled (which blocks publication) until a separately certified
analysis disposition; no registered drop may be elected from a ceiling halt. This rule was adopted
from the GPT‑5.6 second review and bound by the certifier's conditions D–E before core dispatch.

**Unchanged:** the $600 hard ceiling, enforced per call against spend plus outstanding
reservations; the $300 report point; the $300 and $450 checkpoint halts at completed tranche
boundaries; the drop order; tranche ordering; the one-replacement rule; every scenario, seed,
price, subject, plan, batch id, and the whole analysis plan. The registered tag `FROZEN-S1`
(commit `799fe47459f9ba0b67abd8228547c0130271380d`, manifest digest
`ae7912b0510d66540016a9ce73db7b1437763607453c4551b6a1eea3b2e141cf` as recorded in `FROZEN.md`) is
untouched and remains independently verifiable; this amendment is **two commits** on top of it on
branch `amend-s1` — a content commit, then a manifest wrapper commit, mirroring the freeze's own
two-commit procedure — and `git diff FROZEN-S1..amend-s1` is the complete deviation evidence.

**Manifest bookkeeping, disclosed:** regenerating `MANIFEST.sha256` also re-recorded the digests
of `FROZEN.md`, `FREEZE_CHECKLIST.md` and `docs/OSF_REGISTRATION.md`, although this amendment does
not edit them. The frozen manifest was generated at content commit X and the freeze's wrapper
commit Y then wrote its at-tag fills into those three documents, so the frozen manifest's entries
for them describe pre-fill bytes; regenerating over the tagged tree rehashes the filled bytes.
This is the freeze procedure's own recorded exclusion (`FROZEN.md` §10), not an edit by this
amendment.

**Operational warning, permanent:** never dispatch the false start with `--resume`. Its 1,920
`spend_ceiling` rows are not failures under `outcomes.FAILURE_TERMINATIONS`, so a resume would
retain all of tranche 1 as "finished" refusals and dispatch only tranche 2 — an imbalanced
matrix. The rows were moved to the archive path below before any amended dispatch; the core batch
dispatches fresh against the recorded `tranches.json` only.

**Provenance and record:**

- Frozen file digests before: `harness/cli.py`
  `50afa6efb5e9acad6a27ef817ec7f38dcce29ae4bbc7ff790e0856850641d39c`, `harness/cost.py`
  `8f5837ae1b40627a5aa5db2a47c3895dbb01e24866cb86684c4d86e4ca78c793`.
- Amended digests after: `harness/cli.py`
  `ce313f53715c34a3b5254342a8bbaedf9a8d643f391ab641e3fa69e40cfb31ba`, `harness/cost.py`
  `c2d0106f456aee17bc448696b2d8f42bfb3a4620d559c7e9f20fd08c2d05a7d7`.
- `FROZEN.md` §3.2 item 6 and the recorded `HARNESS_VERSION` 0.1.1 in `FROZEN.md` and
  `docs/OSF_REGISTRATION.md` describe the harness as frozen; rows produced by this amendment
  report 0.1.2. The registered documents themselves are not edited.
- The false start's 1,920 zero-evidence refusal rows ($0.00, zero model calls, no transcripts) are
  preserved in the run record at
  `<WORKING-NOTES>` with the dispatch
  log beside them; the recorded `tranches.json` stayed in place and verifies unchanged.
- Verification and design record:
  `<WORKING-NOTES>` (four independent lanes: arithmetic
  confirmed to the cent; registration boundary established; deletion-safety and resume semantics;
  the amendment design with frozen-vs-amended differential probes P1/P3/P4/P5).

**Certification:** repair authored 2026-08-30 by the PM session from the tested lane design.
Adversarial certification by Grok 4.6 (the study's certifier of record), 2026-08-30: **PROMOTE**,
with core dispatch gated on a frozen-vs-amended loopback dress rehearsal (run and satisfied the
same day — assertion log and batch records in
`<WORKING-NOTES>`), on dispatch from the certified bytes,
and on a fresh (never resumed) dispatch of the core batch; full verdict in
`<WORKING-NOTES>`. The certifier's quotable
paragraph for this note is in that verdict. A GPT‑5.6 second review of fidelity to the original
audit demand returned YES‑WITH‑CONCERNS
(`<WORKING-NOTES>`); its
confirmatory-validity rule is adopted above. Authorized by Grant Williams, 2026-08-30.
