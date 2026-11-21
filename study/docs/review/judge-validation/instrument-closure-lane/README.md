# Instrument-closure lane (R43 step 3-4)

`LANE_PROTOCOL.md` is the frozen protocol for the one bounded lane that settles the core E2
instrument (`PILOT_PROTOCOL.md` §6a is the outcome tree it implements; R43(b) is the authority).
**It froze at the commit that added this directory**, after four review rounds by Grok 4.6
(non-Anthropic — the protocol's author is Claude-lineage, which may not certify its own consequential
work):

| Round | File | Verdict | What it forced |
|---|---|---|---|
| 1 | `REVIEW_GROK_LANE.md` | PROMOTE WITH FIXES (6 high, 6 medium) | run-level endpoint joins frozen; deterministic gold assembly; contested-exclusion mechanism removed in favour of fresh labels for every item; two-pass stability on the whole set; language-gate denominator and threshold fixed; L2 rubric written |
| 2 | `REVIEW_GROK_LANE_V2.md` | PROMOTE WITH FIXES (2 open + N1–N4) | exact stratum rules with stated sort keys; the not-necessarily-a-stop packet header; ground-truth-blind L2 packets; first-signal-only construction; two label calls per item |
| 3 | `REVIEW_GROK_LANE_V3.md` | PROMOTE WITH FIXES (N5, N6) | generator field set defined by schema type; short-source-set path made exact |
| 4 | `REVIEW_GROK_LANE_V4.md` | **PROMOTE** | freeze certified; three cosmetic captions fixed in the same commit |
| pre-run | `READ_SOL_LANE.md` (GPT 5.6 Sol, author of the original standard) | AMEND BEFORE RUNNING → applied | tie-break term corrected to specificity (outcome-determinative); audit selection frozen (per-track lowest-SHA-256); role boundary stated precisely; Sol consented to every assigned role. Recorded as protocol §12; no score of any kind existed when the amendments were committed |

After this freeze: step 4 implements `build_frame.py`, `build_near_misses.py` and the scoring
extensions (authors and reviewers per §9 and §11 of the protocol), builds and labels the gold set,
runs the fixed candidates, applies the outcome tree mechanically, and writes the single closing
ruling — after which the instrument question is closed for Pilot I. Prompts and run logs for the
review rounds are preserved in `<WORKING-NOTES>` (outside
this repo).

## Implementation interpretations (flagged by the implementer, ratified by the PM before any label or score exists)

Sol's implementation (`REPORT_SOL_IMPL.md`) flagged six points where the frozen text needed an
implementation reading, resolved each by following committed precedent, and flagged rather than
silently resolved — the discipline the protocol asks for. Ratified as follows, none touching a
threshold, candidate, or frame rule:

1. **Two-pass roles:** pass 1 supplies gates and tie-break figures; pass 2 is fully reported and
   paired item-for-item with pass 1 for stability (the `qualify_freeze.py` convention).
2. **Condition-by-channel weighted agreement** (reported, never a gate) weights by complete-frame
   cell frequencies, renormalized over gold-represented cells, with covered mass published.
3. **Invalid answers in specificity:** an unparseable or `cannot_determine` answer is an agreement
   error and a false negative on gold positives, but only an exact `qualifying` is a false positive;
   specificity stays exactly 1 − FP/gold-negatives (the prior scorer's convention — it can only make
   the language gate harder, never easier).
4. **The language gate's comparison prose rate** uses all L1 gold-negative prose items; the special
   denominator remains gold-negative a/b/c plus real tool turns, class d excluded.
5. **Turn unit vs rubric context:** frame rows store both the normalized current-turn content and
   the existing `judge_projection` through that turn; mixed content is never split.
6. **Expected cost** enters the tie-break only as an explicit CLI input; a cost-level tie with
   missing costs is reported unresolved, never broken by candidate name.

The frame itself is committed (`frame.jsonl`, 3,436 units, SHA-256 in the sidecar, build reproduced
twice with identical digests): 360 development + 90 filler runs; tool-channel turns exist only in C
(82) and D (87), which is the corpus fact the enriched constructed negatives exist to compensate.

The Claude-lineage implementation (`build_near_misses.py`, `assemble_goldset.py`, `tests/` — 33
golden tests, byte-determinism proven twice, four mutation probes each caught) flagged ten further
interpretive points, resolved by stated published rules and ratified by the PM, most consequential
first: (i) "recorded `prose_routed` stop" means **llm-authority routes only**, mirroring the frozen
projection — both independent implementations chose this identically; the corpus's 3
keyword-authority fallback rows are disclosed per-row in the manifest; (ii) "structured invocation"
excludes Archive (forced by the act-swap map and the channel formula; 3 archive calls are never
sources, and archive-only turns are excluded from S3 with the count published); (iii) S4 "same
ground-truth issue" = same scenario (1:1 by construction), restricted to frame turns; (iv)
within-turn source tie-break = tool_calls array position, recorded; (v) class-(d) items render under
the **source** act's field selection (the swapped act shares no substantive fields, and §6 itself
says class-d content can legitimately qualify); (vi) synthetic items carry the source run's
condition as provenance, with cell handling a scoring-layer matter; (vii) `issue_description` always
via the frozen `render_issue_description` accessor; (viii) S1 existence matched on (run id, turn
index) with `turn_key` contradictions published as drops. One PM integration adapter: the sampler
accepts the realized frame schema's `normalized_turn` parts as its text (newline join; tokenizer
neutral).

**Adversarial code read (Grok 4.6, `../../..`-committed at
`<WORKING-NOTES>`, to be committed
beside this file with the fixes): PROMOTE WITH FIXES** — the projection, generator, sampler,
arithmetic and realized counts verified faithful; seven findings, all at the author join (the
blinding-stripped construction class never rejoined for scoring; the S2 item id encoding its class;
a contradictory act/arguments pair on class-d rows; the class-d exclusion not applied to the
headline tool FPR; the rubric-named through-turn packet not pinned; a duplicated route predicate;
absolute paths in manifests). All routed for fix before any paid call.

**Pre-score ratifications (PM, recorded while no label and no score of any kind exists):**
(a) class d is excluded from the language gate, from the **published headline tool-channel
false-positive rate**, and from the section 8 tie-break's tool-specificity splitter — R43's
documented failure mode is real-tool false positives, not wrong-act content — while remaining
inside agreement, recall and the condition-by-channel cells as legitimate gold content; (b) S2
constructed items **enter** the condition-by-channel cells under their source-run condition (the
natural reading of section 7.1, symmetric across candidates because the same transforms sit in C
and D) — this hedge is closed now and is never revisited after scores exist; (c) labelling packets
bind by opaque request id and never carry item ids, acts, arguments, strata, classes, conditions or
channels; L1 packets carry the frozen header, the fix-14 ground truth and the conversation through
the turn (constructed items: their text alone); L2 packets carry the current normalized turn only,
with no ground truth.

**Pre-adjudication-read ratification (PM, 2026-08-25 00:30, gap-fill for a case the frozen
protocol does not state):** recorded after labels and splits existed (L1 375/86, L2 413/48) and
after Sol's blind chain was dispatched, but **before the PM read any adjudication answer** (exactly
one audit answer had scrolled past in a liveness check; zero adjudication or legacy answers seen by
anyone but Sol). (d) If Sol's final adjudication on a split item is `cannot_determine` or
unparseable, that item **drops from that track's scoring denominators**; drops are published by
count and item id in the closing report; more than 5 drops on either track pauses the lane for a
packet-defect investigation before any scoring (the rubric confines `cannot_determine` to
unreadable or truncated packets, so a cluster means a build defect, not item ambiguity). Panel
majority is never substituted for the adjudicator's abstention. On an **audit** item, an abstention
counts as a disagreement for the section 5 audit gate (strict, matching the frozen convention's
direction). The same drop rule governs any escalated unanimous-item adjudication if an audit gate
fails. Expected incidence: zero — this clause exists so the case has a predeclared answer, not
because it is anticipated.

**Audit gate outcome (2026-08-25, mechanical application of the frozen section 5 rule):** L1 —
1/20 Sol disagreements, **gate passed**, unanimous auto-accept stands (the one flip is published
in `GOLD_FREEZE.json`). L2 — **3/20 disagreements, gate failed**: all three flips were unanimous
`attempt` that Sol read `no_attempt`, consistent with the panel over-crediting boilerplate
structured invocations that the L2 rubric's prose clause excludes. Consequence, no discretion
involved: every unanimous L2 item is adjudicated. The 20 audit answers stand as the audit items'
adjudications; the remaining **393** were queued by `build_escalation_queue.py` in the same plain
L2 packet form (no votes shown — the audit presentation, kept so the failed unanimity cannot
anchor the adjudicator). Final L2 gold is therefore Sol-adjudicated on all 461 items; L1 keeps
375 unanimous + 86 adjudicated. `finalize_gold.py` implements both modes fail-closed and
publishes the mode per track.

**LANE OUTCOME (2026-08-25): CLOSED, branch 3 — see R47 in `DECISIONS_V0.1.md`.** Gold froze at
sha `9a3753c2de02b6ea…` before any candidate call; probes clean; both candidates ran two full
passes and the timing instrument assembled from the production router (mistral: 460/461 both
passes, one deterministic sentence-starter packet exhausted; minimax and router: complete).
**No instrument met its preregistered standard** (`LANE_SCORE_TABLE.md`): minimax-m3 fails
stability 0.9284 (<0.95) and the prose condition gap 0.1326 (>0.05); mistral-medium-2604 fails
agreement 0.8829 (<0.90) and the prose gap 0.1659; the timing instrument fails its floor at
0.8330, structurally — the section 2 signal definition counts every structured invocation while
the L2 rubric's boilerplate clause requires substance, so its tool-channel FPR on the 32
contentless-invocation gold negatives is 1.0 by construction. The concordance flag RAISED
(30/71 flips, 23 in the Fable-stricter direction) and resolved label-robust: under the old
labels (`LANE_SCORE_TABLE_OLD_LABELS.md`) every instrument still fails. Lane spend $6.52 of the
$30 cap. The instrument is closed for Pilot I; core E2 is descriptive; Part B is the principal
clean intervention test.

**Realized gold set (offline, zero spend, before any label):** **461 unique items** — S1 236 of 248
legacy carried (12 drops in the manifest), S2 136 constructed (realized n = 34 sources; classes
a–c = 102, below the 120 language-gate floor, so the word "filter" needs real tool-channel gold
negatives to become available at all — the frozen rule working as designed), S3 30 + 30, S4 29
after S1-wins dedup. Inside the protocol's published 380–510 envelope. **Amendment 4 / R44:**
`kimi-k3` left the candidate set before any label or score existed (Grant's query, PM concurrence;
stability and cost); the lane runs two semantic candidates plus the timing instrument.

**Fix round (all seven Grok findings closed, before any paid call).** Sol fixed findings 1, 4, 5
(`REPORT_SOL_FIXES.md`): the scorer now hard-joins the construction class from
`near_miss_intent.jsonl` and refuses unjoined `nm-*` items; class d is excluded from the language
gate and the published tool-specificity (staying in agreement, recall, cells and all-channel
specificity); and `build_packets.py` locks the packet contract — opaque request ids, L1 = frozen
header + ground truth + through-turn conversation, L2 = current turn only with no ground truth,
no id/act/argument/class/stratum on anything model-visible; 461 L1 + 461 L2 packets + 922 offline
joins, byte-identical across builds. The Claude-lineage share fixed findings 3, 6, 7: construction
payload (`act`/`arguments`) moved off gold rows into the intent sidecar with the sampler refusing
payload-carrying rows; S3/S4 route facts consume the frame's `recorded_prose_routed_stop` (one
predicate, not two); manifests fully repo-relative. The frozen 461-item id list survived every fix
byte-identical (`sha256:2e675061…176a03`); artifacts regenerate byte-deterministically; the combined
lane suite is **50 passed**. Grok's full adversarial read is committed here as
`REVIEW_GROK_LANE_CODE.md`.

**Wire probes and dispatch (2026-08-25, first paid calls).** The committed `--probe` path ran live:
Gemini and GLM answered one word immediately; Grok returned empty at `reasoning.effort: none` —
a three-variant PM diagnosis showed xAI's endpoint 400s on `none` ("Reasoning is mandatory") while
`effort: low, exclude: true` answers in one word (81 output tokens on the probe). Both reasoning
labellers now share that shape with caps at the evidence-based 1024, protected by the
exhausted/`--retry-exhausted` recovery (which itself was proven live recovering the Grok probe
nulls). Final projection: **$19.31 worst case** for 2,766 calls under a $20 dispatch budget, inside
the lane's $30 cap; probe spend ~$0.03. All six probe wires parsed clean before dispatch.
