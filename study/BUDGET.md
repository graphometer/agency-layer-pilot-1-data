# Budget — the one table

*Single authoritative budget record. Regenerated at brief step 7 (2026-08-25) from the committed
plans by `evals/runners/stage1/tools/reprice_recorded.py`, with every billed rate verified against
the billing party's own pricing page the same day (first-party pages for the direct-billed rows;
the OpenRouter registry for the two OpenRouter-billed rows — `minimax-m3` and, under R54, the
`deepseek-v4-pro` subject, whose pinned rate is exact first-party parity); run the tool and the
table reprints. Superseded figures
that must not be quoted again: the correction-phase 212.09 (four-repeat matrix) and step 6's
278.82/340.80 (which priced Sonnet 5's cancelled price increase and under-priced DeepSeek's peak
rate).*

## Ceiling and controls (R17, R39, R40 P3)

| Control | Value | Behaviour |
|---|---|---|
| Hard ceiling | 600 USD | refuses the individual call; enforced per call against total spend plus every outstanding reservation |
| Report point | 300 USD | Grant is told |
| Discretionary checkpoints | 300 and 450 USD | halt at the next **completed tranche** boundary, never inside one (R39-F5); only a resume naming the checkpoint releases it |
| Drop order (R34 as amended by R43, fixed before any outcome) | frontier replication, then core repeats 3 to 2 at a tranche boundary | scenarios are never dropped; the Part B fresh C-D component is never dropped |
| Scope | subjects **and** instruments (R40 P3) | the judging pass meters itself against `evals/grading/instrument_prices.json` and halts on an unpriced model |

## Spent so far

| Item | Spend |
|---|---|
| Three smokes (2026-08-23) | at least 0.6565 USD committed; about 1.50 USD per `CHANGELOG.md` |
| Cost rehearsal, 60 runs | 4.81 USD |
| Development run, 360 local runs (routing only) | 0.34 USD |
| Judge validation and freeze qualification batteries | a few USD of instrument calls, inside the free tiers used at the time |
| Instrument-closure lane (R47; labels 4.40, candidates/router/probes 2.12) | 6.52 USD of its 30 USD cap |
| Step-9 second smoke + capability probes + live judged pass (R55) | 0.7950 USD |
| R46 capability probes and the R56/R57 entrance smokes and probes | 0.0022 USD |
| **Total before the recorded run** | **about 18 USD of the 600** |

The step-9 row recomputes to **0.7950** — 0.1674 across the twenty `smoke-s2` runs, 0.6168 across the
eight `probe-f2` runs, 0.0102 for the live judged pass (`SMOKE_REPORT_S2.md`) and 0.0006 for the R46
entrance smokes — and the row below it to **0.0022**, both summed from the `cost_usd` fields of the
committed `run.json` files under `evals/runners/stage1/results/stage1/`. The 2026-08-23 smoke runs
are not in the repository, so their subtotal is bounded rather than
regenerated: the committed `evals/runners/stage1/SMOKE_REPORT.md` meters the third smoke alone at
**0.6565**, and `CHANGELOG.md` records **about 1.50 across the three**. That is why the row states a
floor and a reported figure instead of a single number.

Of that total, **about 13.97 USD is itemised above** (≈1.50 + 4.81 + 0.34 + 6.52 + 0.7950 + 0.0022).
The remainder is the judge-validation and freeze-qualification batteries, which ran inside provider
free tiers at the time and were never separately metered — so the 18 is a round figure standing on
about 14 itemised USD plus those unmetered instrument calls, not a reconciled sum. The figure that is
enforced is the 600 ceiling, not this one.

## Projection for the package that will actually run

**These are projections, and they are treated as such.** They come from the committed price table and
the committed plans, and they exist to answer one question: does the registered package fit inside the
600 USD ceiling with margin, and in what order do cells drop if it does not. What is preregistered and
enforced is the ceiling, the 300 and 450 checkpoints, and the drop order — not the accuracy of the
estimate. **The actual metered spend is reported with the results**, from the cost journals, and any
difference between it and the numbers below is reported rather than reconciled away.

Regenerated from the committed plans (`plan_recorded.yaml` 2,560; `plan_fresh_recorded.yaml` 640;
`plan_fresh_local_recorded.yaml` 320; `plan_family9_recorded.yaml` 80 — the section 4 arithmetic:
3,600 recorded rows; the 3,600 = 3,280 + 320 identity quoted elsewhere is a split by plan file,
not by cost — what is billed, and on which rows, is set out under the projection table below) using the measured rehearsal token means, the corrected
Medium 3.5 instrument price, the lane-measured secondary-judge output behaviour, and the
lane frame's measured per-condition prose-turn rates. Full output:
`tools/reprice_recorded.py`.

| Component | Runs or calls | USD |
|---|---|---|
| core + B_filler + B_scaffolded, `claude-sonnet-5` | 640 | 76.19 |
| core + B_filler + B_scaffolded, `gpt-5.6-terra` | 640 | 35.33 |
| core + B_filler + B_scaffolded, `deepseek-v4-pro` (max-of-measured projection) | 640 | 42.39 |
| core + B_filler + B_scaffolded, local `qwen3.8-27b` | 640 | 0.00 |
| fresh Part B primary, `claude-sonnet-5` | 160 | 26.95 |
| fresh Part B primary, `gpt-5.6-terra` | 160 | 12.59 |
| fresh Part B primary, `deepseek-v4-pro` | 160 | 14.30 |
| fresh Part B primary, local `qwen3.8-27b` | 160 | 0.00 |
| fresh local exploratory arms (R46/R57), `muse-glimmer-30b` + `gemma4-31b-it` (the R57 seat replacing the dropped `mistral-small-4`) | 320 | 0.00 |
| family 9, local only | 80 | 0.00 |
| route classifier (`mistral-medium-2604`): condition-invariant routing 6,628 calls (E2-family rows × measured prose-turn rates) + stop-shaped routing 612 calls | 7,240 calls | 19.98 |
| primary judge (`mistral-medium-2604`), descriptive E2 readings, core-side rows only | 6,512 calls | 9.18 |
| secondary judge (`minimax-m3` via OpenRouter), lane-measured output behaviour | 6,512 calls | 4.08 expected |
| **Expected total** | **3,600 recorded rows** | **240.99** |
| Worst case if every secondary-judge answer runs to its 8,192-token cap | | **302.97** |

*Component cells round independently to cents, so printed identities can be off by one cent
(e.g. worst − expected = 61.98 while 66.05 − 4.08 = 61.97); the generating tool holds every
identity at full precision.*

Two different cuts of the same 3,600 rows, and they are easy to confuse.

**By plan file** — the identity `make_recorded_plans.py --check` asserts — 3,280 sit in the three
main plans and 320 in the free local-arm plan.

**By cost**, there is no single split, because a row can be billed by its subject, by the instruments
run over it, or by neither:

- **Subject calls** are billed on **2,400** rows. The other 1,200 use local endpoints, so their
  subject calls cost nothing (core and controls' local subject 640, the fresh component's local
  subject 160, family 9's 80, and the two local exploratory arms 320).
- **Instrument calls** — the route classifier and both judges — are billed on the core, controls and
  family-9 rows: **2,640 rows, including 720 whose subject was local** (the core's 640 and family 9's
  80). A local subject does not make a row free; it makes the subject half of that row free. The
  fresh Part B component makes zero instrument calls, by its deterministic endpoint.
- **480 rows carry no charge of any kind**: the fresh component's local rows (160) and the two local
  exploratory arms (320).

So "API exposure" has to name which layer it means. The subject layer is 2,400 rows; the instrument
layer is 2,640; exactly 480 of the 3,600 are free outright.

Branch-3 instrument scope (R47), priced above and binding: **the fresh Part B component makes zero
instrument calls** (deterministic endpoint; no semantic judge qualified, so no semantic sensitivity
is computed there); core E2's preregistered readings are still computed and published as
descriptive with the instrument-error profile, which is what the judge lines pay for; the
condition-invariant routed timing reading routes every pre-gate prose turn of the E2-family rows
(section 5's "always computed" reading).

124.25 USD of the subject figure is projected from unmeasured families (3, 4, 6 were never
rehearsed; DeepSeek was never rehearsed; the fresh component prices at the matching development
families' C/D profiles). The direction of that uncertainty is unknown, which is why the ceiling
and the checkpoints exist. The expected total sits below the 300 USD report point; the worst case
crosses it, so a mid-run halt at a tranche boundary is a live possibility, not a surprise.

Step-7 rate verification (2026-08-25, all first-party): `claude-sonnet-5` 2.00/10.00 with cache
0.20/2.50 (platform.claude.com — the launch price became the standard price; the scheduled
2026-09-01 increase to 3/15, which the step-6 row priced, was cancelled); `gpt-5.6-terra`
2.00/0.20/12.00 and `gpt-5.6-sol` 4.00/0.40/20.00 exact (developers.openai.com, standard
short-context tier — the only tier the study's request sizes can reach); `deepseek-v4-pro`
1.32/3.96 at peak hours (api-docs.deepseek.com; the row is the peak ceiling — off-peak is half and
DeepSeek's automatic cache-hit discount is unmodelled, so the meter over-counts at any hour);
`mistral-medium-2604` 1.50/7.50 exact (docs.mistral.ai/inference/pricing); `minimax/minimax-m3`
0.30/1.20 exact (openrouter.ai/api/v1/models — OpenRouter is the billing party for the served
endpoint).

R54 addendum (2026-08-25, same day): Grant moved DeepSeek dispatch to OpenRouter. The row above
survives unchanged — the endpoints listing
(openrouter.ai/api/v1/models/deepseek/deepseek-v4-pro-0813/endpoints) shows the pinned `deepseek`
provider (DeepSeek's own endpoint) carrying the identical time-of-day schedule with no inference
markup: peak 1.32/3.96 in the same weekday windows, off-peak 0.66/1.98, cache-read 0.044/0.022.
OpenRouter's fee is charged on **credit purchases** (5.5%, $0.80 minimum on card; Grant has
auto-reload on), not on inference — a funding overhead outside the meter, so every projection in
this file is unchanged and the OpenRouter-funded share costs about 1.055x its metered value at
purchase time.

## Drop order against the ceiling

| Step | Expected total | Headroom |
|---|---|---|
| Full package | 240.99 (302.97 worst) | 359.01 (297.03 worst) |
| Drop the frontier replication (R34 step 1) | — the replication is an optional extra that runs only if the package completes within budget; it is not in this projection, so this rung frees nothing | |
| Core repeats 3 to 2 at a tranche boundary (R34 step 2) | 201.55 | 398.45 |

The full package fits with room for the worst-case judging bill.

## Provider balances to check before dispatch

- **Mistral: RESOLVED (R52, 2026-08-25).** The projected `mistral-medium-2604` instrument spend is
  **29.16 USD** (classifier 19.98 + primary judge 9.18), against a free tier measured at about
  20 USD on 2026-08-23. Grant enabled auto-billing on the Mistral account on 2026-08-25; the
  instrument stays on the first-party Mistral endpoint (the OpenRouter rerouting alternative was
  not taken). The step-9 smoke's real billed mistral calls verify the billing path end-to-end
  before recorded dispatch; the meter fails closed if they refuse.
- **DeepSeek: RESOLVED (R54, 2026-08-25).** Grant moved DeepSeek dispatch to OpenRouter (pinned
  to DeepSeek's own first-party endpoint, exact price parity) and enabled **auto-reload** on
  OpenRouter credits, so the standing ~$60 first-party top-up item is dissolved — no DeepSeek
  account balance is needed at all. The step-9 smoke's real billed calls verify the new path
  end-to-end before recorded dispatch.
- Anthropic and OpenAI carry the next-largest subject lines (103.14 and 47.92); balances verified
  at the freeze.
- OpenRouter now carries **two lines**: the secondary judge (4.08 expected, 66.05 reserved worst
  case) and the DeepSeek subject (56.69 at the metered ceiling). A balance must cover the
  **reservation**, not the expectation, because the meter reserves at the cap — with auto-reload
  on, the account replenishes itself; the honest overhead is OpenRouter's 5.5% fee on each credit
  purchase (outside the meter, see the R54 addendum above).
- A balance that runs dry mid-batch looks exactly like a provider failure, and under the corrected
  accounting an ambiguous failure keeps its reservation charged, so the meter will stop the batch
  rather than under-count.

## Freeze-time obligations

- [x] Verify the DeepSeek and GPT-5.6 Terra rates against first-party pricing pages (R24) —
      **done at step 7 (2026-08-25)**: Terra exact; DeepSeek corrected up to the 1.32/3.96 peak
      ceiling (the old row under-metered at peak); Sonnet 5 corrected down to the 2/10 standard
      price. Sources recorded in the projection section above.
- [x] Verify the instrument rates in `evals/grading/instrument_prices.json` the same way —
      **done at step 7 (2026-08-25)**: mistral-medium-2604 1.5/7.5 exact
      (docs.mistral.ai/inference/pricing); minimax/minimax-m3 0.30/1.20 exact
      (openrouter.ai/api/v1/models). Source strings updated in the file.
- [x] Resolve the Mistral balance item above — **done, R52 (auto-billing enabled 2026-08-25);
      the step-9 smoke verifies the billing path operationally**.
- [ ] Re-run `tools/reprice_recorded.py` and paste the result into `FROZEN.md`.

---

## Actuals (added 2026-09-02, after the recorded run)

Everything above this section is the pre-run projection. The recorded run's reconciled,
machine-generated ledger is `results/stage1/COST_LEDGER.md` (built by `tools/build_cost_ledger.py`
from the committed cost journals). Headline: recorded-run spend **$142.202064** (subjects/router
$130.639229; judges $11.562835); development spend before the recorded run ≈ $18 per this file;
study-wide ≈ **$160 of the $600 ceiling**. The core batch's cost metadata records one reservation
overshoot of $0.012573 (`reservation_covered_every_call: false`) — see the ledger for exact wording.
