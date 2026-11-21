# Deviation note — 2026-09-01: the terminal-turn routing join

*This note is part of the published results. It discloses the one post-run grading correction.*

Post-freeze analysis identified a grading-only mismatch at the terminal-turn boundary. In 101 of
1,280 Part A E2-family runs, the join safeguard expected a routing row for the final assistant
turn, although the frozen harness had already terminated that turn for token truncation (93 runs)
or a malformed tool call (8 runs) and therefore never invoked prose routing or delivered a
scripted continuation. We aligned the safeguard with the router's recorded contract, as
previously done for tool-only turns: these evidence-bound terminal turns are complete by
contract, while missing nonterminal routes and existing unjoinable rows still fail closed.
Reanalysis removed the sole publishability warning. No endpoint numerator, denominator, rate,
estimate, interval, p value, fit, verdict, or confirmatory conclusion changed. No routing row is
claimed to exist for the exempted turns.

**Honesty items:** the protocol's strictest wording ("every pre-gate assistant turn") supports
the original check; the instrument as deployed and the certified tool-only precedent support this
correction — both readings are recorded in the certification. The correction is post-outcome; it
was locked to an exact semantic allowlist proven over all 2,560 per-run grades (exactly the 101
evidence-bound runs change, in completeness flags only; 71 null→false normalizations on values
the analysis already imputes false), and the project manager's exposure to result fragments
during diagnosis is disclosed in the decision record.

**Record:** owner authorization 2026-09-01 (Option A,
`committee/GRADING_SITTING_2026-08-31.html`); design and 101/101 independent audit
`<WORKING-NOTES>`; implementation and differential
proof `<WORKING-NOTES>`; adversarial
certification (Grok 4.6, PROMOTE, 2026-09-01)
`<WORKING-NOTES>`. Commits on branch
`amend-s1`: content `27bfedc`, manifest `0118598` (digest `5c8010d688cf…3013`), then this
docs round. The pre-correction flagged artifact is retained beside the final one as part of the
record.
