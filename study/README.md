# Agency Layer

**Status (2026-09-02):** The study ran 2026-08-30/31; results are committed and under a disclosed repair round after outside audit; nothing here is published or final. Entry points: `AGENCY_LAYER_STATE.md` §0 (project root, one level up) and `AUDIT_HANDOFF_2026-09-01.md`.

*A bounded correction phase closed on 2026-08-24 after three outside adversarial reviews returned
"no-go for freeze". What it found and what it changed is in `../CORRECTION_PHASE_2026-08-24.md`; the
short version is that three published judge-agreement figures (0.896, 0.903 and 0.934) have been
withdrawn because their comparison mixed two denominator conventions and no convention reproduces the
third, five measurement defects that favoured the hypothesis arm were repaired, and the study's honest
detectable effect is larger than the project had assumed. Read `CLAIMS_AND_LIMITATIONS.md` before
quoting anything from here.*

Agency Layer is an open, provider-neutral protocol that gives AI coding agents a small set of
structurally honored actions: clarify, dissent, pause, decline, and archive. "Structurally honored"
means the host implements the documented state transition instead of treating the action as ordinary
text. The project ships adapters for Claude Code, Codex, OpenCode and Kimi Code, a conformance suite
that defines what "honored" means on each host, and a controlled study comparing ordinary interaction,
permission-only prompting, a structured but signal-only action, and a structured and host-enforced
action.

## Layout

| Path | What it is |
|---|---|
| `SPEC.md` | affordance semantics, states, transitions, host obligations |
| `DECISIONS_V0.1.md` | constitutional decisions and open questions, with dates and who ruled |
| `CONTRACTS.md` | the interfaces every workstream builds against: adapters, harness, graders, tests |
| `CONFORMANCE.md` | the tests, each host-mode's designation and results, the release gate |
| `SECURITY.md` | where to report a security issue and what is in scope |
| `PILOT_PROTOCOL.md` | the study protocol: conditions, scenarios, endpoints and their readings, instruments, sample size and power, budget, analysis plan, freeze |
| `THREAT_MODEL.md` | safety boundaries and abuse cases |
| `CLAIMS_AND_LIMITATIONS.md` | what the project does and does not establish; governs every public sentence |
| `docs/AUDIENCE_AND_PRIOR_ART.md` | who this is for, the published work it sits beside, and what would make it decisive |
| `SCENARIO_FAMILIES.md` | the nine families, the 45 scenarios, and what each measures |
| `BUDGET.md` | the one budget table: ceiling, controls, spend to date, projection |
| `PROVIDER_TERMS.md` | may we publish these transcripts, provider by provider |
| `DATA_MANAGEMENT.md` | redaction, retention, custody, incident response |
| `GLOSSARY.md` | the words this project uses in a particular way, including what "promoted" does not mean |
| `FREEZE_CHECKLIST.md` | what has to be true before `FROZEN-S1` is tagged |
| `packages/protocol/` | JSON schemas for the five actions, the event log, the state model, and startup attestation |
| `packages/core/` | reserved for a TypeScript reference implementation; empty at Pilot I (`.gitkeep` only) — the state machine, event log and attestation are implemented in `adapters/` and `evals/` against the `packages/protocol/` schemas |
| `adapters/` | one folder per host |
| `evals/` | Python: Stage 1 harness, scenarios, graders, analysis |
| `results/` | raw development and recorded runs |
| `site-data/` | the single artifact every published chart and number is generated from |

## Licensing

Code is MIT (see `LICENSE`). Specification text, results and transcripts are CC BY 4.0 (ruled in R19;
the legal code is `LICENSE-CC-BY-4.0.txt`). `NOTICE` names every provider whose model outputs this
repository contains, carries the notices their terms require, and lists the small number of files
excepted from **both** grants and the terms on which those are published instead — nothing outside that
list is excepted. `PROVIDER_TERMS.md` records, provider by provider, whether the model outputs in a
package may be published and what the excerpt fallback is; `DATA_MANAGEMENT.md` records redaction,
retention and incident response.

## Independence

Independent work. Not affiliated with, endorsed by, or connected to Anthropic, OpenAI, the OpenCode
project, or any other vendor named in this repository. Product names are referenced for
identification only.
