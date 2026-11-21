# Development corpus, re-analysed under the corrected grader (2026-08-24)

**This is an instrument comparison, not a result. It is marked `publishable_as_result: false` in its own
provenance block and it must never be quoted as a finding.**

Why it exists: the correction phase changed how E1 imputes, how the E2 anchor is located, which E2
readings are computed, and how the guardrail counts stops. The size of those changes is a fact about
the instruments, and the outside review (Grok 4.6, 2026-08-24) rightly refused to accept figures quoted
from a session's scratch run. This directory is that run, committed, so every figure the protocol and
the claims file quote can be regenerated.

Regenerate with, from `evals/grading/`:

```
python3 analysis.py ../../results/development/dev-2026-08-23/runs <output> \
  --scenarios ../scenarios \
  --judged ../../results/development/dev-2026-08-23/judged-pm19 \
  --allow-any-judges --accept-unbound-verdicts
```

Two flags matter and both are deliberate. `--allow-any-judges` because the development corpus was judged
under the PM19 pair, not the seated PM20 pair. `--accept-unbound-verdicts` because the corpus's verdicts
were produced under the pre-fix-14 README-derived ground-truth text (disclosure 26); 1,120 of them do not
bind to the current projection. That flag is what marks the artifact unpublishable, and it is the honest
state of this corpus: reading it under the current package requires either these flags or a re-judge.

## What it shows, beside the pre-correction artifact

The pre-correction analysis is `../analysis/analysis.json` (E2 all-attempts pooled: C 28/40, B 22/40,
+0.150; E1: C 2/20, B 8/20, -0.30).

| Reading | C | B | C minus B | 95 percent cluster interval |
|---|---|---|---|---|
| E2 `primary_gate_anchor_union` | 30/40 | 22/40 | +0.200 | [-0.050, +0.425] |
| E2 `state_change_anchor` | 23/41 | 14/45 | +0.225 | [+0.050, +0.400] |
| E2 `first_stop_only` | 30/41 | 22/45 | +0.200 | [-0.050, +0.425] |
| E2 `expected_act_only` | 27/41 | 19/45 | +0.200 | [-0.075, +0.450] |
| E2 `router_gated_timing_only` | 31/41 | 24/45 | +0.175 | [-0.050, +0.400] |
| E1 `symmetric` (corrected primary) | 1/20 | 3/20 | -0.100 | see artifact |
| E1 `pm17_v1` (registered rule) | 2/20 | 8/20 | -0.300 | see artifact |

Two things a reader should take from that table. **E2 is stable across every reading** (+0.175 to
+0.225 on one local model), which is the reassuring half. **E1 is not**: the registered imputation gives
-0.300 and the channel-symmetric one gives -0.100, so two thirds of that development contrast was the
imputation rule rather than behaviour. The denominators differ between readings because a reading that
considers fewer candidate stops leaves fewer runs indeterminate; every row prints its own.

The tool-channel bound is in `analysis.json` under `e2_tipping_point`: 9 of C's 30 positives rest on a
tool-channel verdict alone, 8 of those 9 would have to reverse to erase the +0.200 contrast, and
discounting tool-channel positives by the measured channel gap in the judge's false-positive rate gives
+0.085.

Nothing here is evidence about the four study subjects. One local model, 360 runs, verdicts from a
superseded instrument.
