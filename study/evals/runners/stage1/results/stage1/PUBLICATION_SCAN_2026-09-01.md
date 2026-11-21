# Publication scan — 2026-09-01 (DATA_MANAGEMENT item 2, first pass)

Scope: all `recorded-*` result trees plus the archived false start — 57,548 files. Patterns: API
key shapes (OpenAI/OpenRouter/AWS/GitHub/Slack), private-key blocks, bearer tokens, email
addresses; plus a count of vault-absolute paths. The scan runs again on the final tag before any
public deposit, per the registered plan.

## Findings

1. **No secrets.** Zero real keys, tokens, or private-key material. 68 key-*shaped* strings are
   all substrings of run identifiers (`…kio`**`sk-build__A__…`**, `…de`**`sk-sign__C__…`**) —
   scenario ids ending in "sk" followed by the run-id separator. False positives, verified
   exhaustively.
2. **Fixture emails** (`@example.*`, `a@b.com`, and similar designed content): benign, part of
   the registered scenarios.
3. **23 real third-party email addresses** — publicly listed open-source maintainer contacts
   (Node.js collaborator-list format) — appear in a small number of run transcripts. They are in
   **no registered fixture**; the models reproduced them **from training memory** into files they
   wrote inside the sandbox, which later tool reads then echoed into `tool_result` evidence
   (example: `recorded-core-s1/f2-01-missing-endpoint__B_scaffolded__deepseek-v4-pro__r0/`).
   This is itself a minor observation about model behavior (verbatim recall of public personal
   data), recorded here deliberately.
   **Disposition — EXECUTED 2026-09-01:** the owner ruled "redact per precedent" the same day.
   All 23 addresses (which occurred in exactly one transcript file) are replaced with synthetic
   markers in this published-bound copy; rationale, scope and integrity analysis in
   `REDACTION_2026-09-01.md` beside this file. The as-produced originals are retained in the
   local run checkout; the address list itself lives only in the private staging map, not here.
4. **252 vault-absolute-path occurrences** (mostly `source_folder` fields in analysis artifacts
   and log echoes): this was a scan-occurrence count, not a list of 252 release defects. Per
   `DATA_MANAGEMENT.md` item 3 and the committed scanner's surface rules, captured-data and
   review-provenance paths remain part of the historical record; runnable code must be portable.
   The final release scan found the only three blocking occurrences in
   `evals/runners/stage1/dispatch_supplement_s1.sh`. They were replaced with checkout-derived
   paths plus explicit `AGENCY_LAYER_ENV_FILE` and `AGENCY_LAYER_PYTHON` overrides during the
   pre-publication closure pass. Historical evidence was not mechanically rewritten.

Scanner and raw output: session scratchpad `publish_scan.py`; summary preserved in the PM change
brief. Scan performed after the routing-join correction (`e283bec`), before the results-return
commits.
