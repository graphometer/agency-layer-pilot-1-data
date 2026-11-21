# Redaction record — 2026-09-01 (owner-ruled, per precedent)

**What was redacted.** 23 third-party email addresses — publicly listed open-source maintainer
contacts that a subject model reproduced from its own training memory into a file it wrote inside
the sandbox, later echoed into evidence by a tool read. They appeared in exactly **one file** of
the entire package: the transcript of
`recorded-core-s1/f2-01-missing-endpoint__B_scaffolded__deepseek-v4-pro__r0` (23 occurrences).
Each address was replaced with a stable synthetic marker of the form
`redacted-NN@redacted.invalid` (`.invalid` is a reserved TLD; the marker preserves the
email-shaped structure of the text).

**Why.** DATA_MANAGEMENT's standing rule and precedent: real personal contact information is
redacted from published-bound artifacts with a written rationale (the prior 138-address case).
The owner ruled "redact per precedent" on 2026-09-01. That the addresses are public elsewhere
does not make republishing them here necessary or kind; and the underlying observation — a model
recalling real personal data verbatim from training — is preserved and disclosed in
`PUBLICATION_SCAN_2026-09-01.md` without needing the addresses themselves.

**Analytical integrity: fully preserved.** The addresses occurred only in `tool_result` rows of
one transcript. Tool-result bodies do not enter the blinded judge projections (`blind.py`
projects assistant utterances and structured stop frames), so no stored judge verdict's input
hash is affected; they are not assistant-turn text, so no routing-join digest is affected; and a
re-grade of the redacted transcript produces identical grades, because grading reads assistant
turns and structured events. Every analysis artifact, verdict binding, and reconciliation in this
package is exactly as valid over the redacted bytes as over the originals.

**Provenance.** The as-produced originals are retained unmodified in the local run checkout (the
project's evidence-of-record, not published). The address→marker map is retained privately in
the project's staging records, never committed. Redaction applied after the results commit
`cf95512` and before any push or public deposit, as the registered publication-scan flow
requires.
