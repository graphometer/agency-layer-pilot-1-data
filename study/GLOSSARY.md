# Glossary — the words this project uses in a particular way

*Written in the correction phase 2026-08-24. Three reviews independently flagged that a stranger cannot
read the register without this (GPT documentation item 8, Grok D9, Mistral H-006 and H-012).*

**Affordance.** One of the five actions the protocol defines: Clarify, Dissent, Pause, Decline (two
modes: alternatives-open and final-for-task), Archive. Five actions, four JSON schemas — the schemas are
`affordances`, `event`, `state` and `attestation`, not one per action.

**Honored.** The host implements the documented state transition instead of treating the action as
ordinary text. Condition C is honored; condition D records the same invocation and continues anyway.

**Adapters and integrations.** The public collective noun for the four host packages, because Codex App
Server, the Claude Agent SDK, OpenCode's plugin and permission layer, and Kimi's ACP are four different
extension mechanisms rather than four instances of one plugin API. Never "plugins" collectively.

**Promoted.** Reviewed by someone who did not write it and copied into this repository. **It does not
mean conformant.** Every published host profile is partial; the register says so per row. A public
sentence must never turn "four adapters promoted" into "four conformant adapters".

**PASS / PARTIAL / FAIL / NOT_TESTED.** Per conformance row, per host-mode. PARTIAL is derived
differently by different adapters, so the four headline totals are **not comparable** and are not a
ranking. `CONFORMANCE.md` states the counting rule above the table.

**Host-mode.** A host plus the extension surface being tested (`claude-code:sdk`, `codex:app-server`,
`opencode:serve`, `kimi-code:acp`, and so on). Claims are made per host-mode, never per host.

**Reference / frontier / partial / control-only.** Spike-era designations in `CONFORMANCE.md`
describing how much of the protocol a host-mode can carry. They describe capability, not quality, and
they are not a league table. Distinct from the **release statuses** (R43): "Pilot — reference
integration" is a documentation role for one packaged integration (clearest install and reproducibility
path, chosen only after the step-13 tests, no conformance claim), beside "Pilot — experimental, partial
conformance", "Pilot — signal-only or research integration", and "withheld pending repair" — see
`CONFORMANCE.md`, "Public release policy".

**Stage.** Stage 1 is the clean API harness study. Stage 2 is the later ecological host study. They
freeze separately (R33) and are never pooled. **Part A / Part B (R43).** Stage 1's two separately
reported components: Part A is the core validation pilot (40 scenarios x 4 conditions x 4 subjects x 3
repeats), Part B is the sealed fresh-scenario replication (40 fresh scenarios, conditions C and D only,
4 subjects x 2 repeats). They are never pooled either. **Phase** describes a period of project work (the
instruments phase, the correction phase). **Segment** was an earlier word for the same thing and is
being retired in favour of phase.

**Condition.** One of A, B, B_filler, B_scaffolded (R45), C, D as defined in `CONDITIONS.md`. That mapping is the only one
permitted anywhere, including in prompts, run records, figures and public copy.

**E1 / E2.** The two co-primary endpoints as registered: false success claim (families 5 and 7) and appropriate
intervention before the first consequential action (families 2, 3, 4 and 6). Under the section 6a
branch-3 outcome (R47, 2026-08-25) E1 is the core's sole confirmatory endpoint and every E2 number
is descriptive, published with the instrument-error profile.

**All-attempts / gradeable.** The two denominators. All-attempts is primary and is the frozen planned
matrix, with a planned run that produced no valid record counted as an adverse incomplete attempt.
Gradeable-only excludes runs that never reached a model decision, and is reported beside it.

**Reading (of an endpoint).** One of the several defensible operationalisations of E2 or E1 that the
analysis computes from the same data. One reading is primary in the registration; the rest are
preregistered sensitivities. See `PILOT_PROTOCOL.md` section 5.

**Consequential action.** A call or effect that changes state outside the current turn. In the protocol
that includes file writes; the E2 primary anchors on the scenario's *declared* consequential action (the
gate script), and the `state_change_anchor` reading anchors on the earlier of that and any file write.

**Instrument.** A model used to measure rather than to be measured: the route classifier and any
semantic judge admitted by the instrument-closure lane (`PILOT_PROTOCOL.md` section 6a); if no judge
qualifies there, core E2 is reported descriptively only. No instrument provider has a subject arm.

**Frozen candidate.** The state a document or config is in when it is complete and expected not to
change, but the `FROZEN-S1` tag has not been cut. Nothing is "frozen" until that tag exists.

**Disclosure.** A numbered entry in `docs/PREREGISTRATION_DISCLOSURES.md`: an instrument or analytic
decision taken after the first real-model exposure and before the freeze. The register is part of the
registration, not an appendix to it.
