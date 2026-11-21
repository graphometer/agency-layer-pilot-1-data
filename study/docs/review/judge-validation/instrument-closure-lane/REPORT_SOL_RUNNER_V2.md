# Label runner fix report V2

No provider call was made. No `.env` value or file was read, and `<PRIVATE-FOLDER>/` was not
accessed. All changes and verification were offline, and the lane remains
uncommitted.

`REVIEW_GROK_RUNNER.md` was not present anywhere under the repository during this
fix round, so the three findings embedded in the PM task were treated as the
authoritative review text.

## Changes

- Replaced the global 16-token completion cap with an explicit `max_tokens` on
  each `Labeller`. The same per-labeller value is used in the OpenRouter payload,
  the pre-dispatch reservation, and the dry-run projection.
- Gemini uses 256 tokens, Grok uses 256, and GLM uses the mined 8192-token
  recovery floor. The GLM exception is deliberate: the historical run used 4096
  and its null rows were retried at 8192, while the current model listing says
  reasoning is mandatory and cannot be disabled.
- Added a priced-provider pin to every request with fallbacks disabled. The
  exact OpenRouter provider slugs are `google-vertex`, `xai`, and `z-ai`.
- Added `--probe`. It uses one embedded synthetic one-word packet for each of L1
  and L2, sends that fixed shape to each of the three labellers (six calls), and
  does not read or reuse a gold packet. Probe journals live below
  `labels/probe/`; each call goes through the normal reserve, dispatch, settle,
  parse, and terminal-journal path. It prints raw content, parsed value, and
  metered cost for every labeller/track pair and returns nonzero if any result is
  unparseable. Probe behavior was tested only with an injected offline transport;
  `--probe` was not invoked against OpenRouter in this task.
- A final empty or unparseable result is now journalled as `exhausted`, never
  `completed`, and is omitted from the materialized label file. Ordinary resume
  skips it. `--retry-exhausted` selects exactly exhausted IDs, excluding untouched,
  completed, and ambiguous IDs, and starts at the next monotonically increasing
  attempt number so settlements remain unique. Every retry remains reserved and
  settled through the existing cost authority.
- Existing ambiguous-reservation behavior remains unchanged: an interrupted
  logical item is conservatively charged and is never automatically recalled.
- Added payload tests for all three provider pins and reasoning/thinking shapes,
  including assertions that `payload["extra_body"]` contains each pin and that
  payload and reservation use the same per-labeller cap.
- Added probe success/failure and metering tests, exhausted/retry recovery tests,
  and an exhausted-only selection regression with an untouched neighboring item.
- Added the requested blindness cases: `BACKUP_DEST=/mnt/backup` is allowed and
  `<LOCAL-PATH>` is rejected.

## Mined wire shapes and sources

| Labeller | Sent cap and body additions | Source and rationale |
|---|---|---|
| Gemini 3.7 Flash | `max_tokens: 256`; `extra_body.google.thinking_config.thinking_budget: 0`; provider only `google-vertex`, fallbacks false | `evals/grading/judge.py:315-321` records the Google passthrough nesting and the live probe result: empty at 8/16/32/64, answer at 256+. `<LOCAL-PATH>` records the historical working Google thinking-budget-zero body. The current OpenRouter listing price for the committed $0.375/$1.875 row is the Google Vertex route. |
| Grok 4.6 | `max_tokens: 256`; `reasoning.effort: "none"`; provider only `xai`, fallbacks false | OpenRouter's reasoning documentation defines `effort: "none"` as the Grok-capable reasoning-off switch. The provider-selection listing slug is `xai`. No mined history established a higher floor with reasoning off. |
| GLM-5.3 | `max_tokens: 8192`; `reasoning.effort: "low"`, `reasoning.exclude: true`; provider only `z-ai`, fallbacks false | `<LOCAL-PATH>` used 4096. `retry_glm.py:15-26` retried its null rows at 8192. The current OpenRouter GLM-5.3 listing states that reasoning is always on, cannot be disabled, and supports only low/high/max, so a literal off body would be invalid; low is the closest legal effort and exclude suppresses returned reasoning text, not reasoning generation. The listing provider slug is `z-ai`. |

This GLM shape is an explicit incompatibility disclosure, not a claim that GLM
reasoning was turned off. The PM's live `--probe` is required to confirm all six
routed shapes before panel dispatch.

Current OpenRouter sources consulted for the routing/shape check:

- <https://openrouter.ai/google/gemini-3.7-flash/providers>
- <https://openrouter.ai/x-ai/grok-4.6/providers>
- <https://openrouter.ai/z-ai/glm-5.3>
- <https://openrouter.ai/docs/guides/best-practices/reasoning-tokens>

## Offline verification

From `docs/review/judge-validation/instrument-closure-lane`:

```text
python3 -m py_compile run_labels.py test_run_labels.py
```

Exit status: 0.

Full lane suite:

```text
python3 -m pytest -q
....................................................................     [100%]
68 passed in 0.15s
```

The test suite uses injected transports and made no network or provider call.

## Dry run against the real packets

The dry run used the real 461-packet L1 and L2 files and the current
`label_prices.json`. Command and exact output:

```text
python3 run_labels.py --dry-run
gemini-3.7-flash l1: items=461 remaining=461 ambiguous=0 exhausted=0 worst_case=$0.881525
gemini-3.7-flash l2: items=461 remaining=461 ambiguous=0 exhausted=0 worst_case=$0.459928
grok-4.6 l1: items=461 remaining=461 ambiguous=0 exhausted=0 worst_case=$4.229400
grok-4.6 l2: items=461 remaining=461 ambiguous=0 exhausted=0 worst_case=$1.980886
glm-5.3 l1: items=461 remaining=461 ambiguous=0 exhausted=0 worst_case=$19.081566
glm-5.3 l2: items=461 remaining=461 ambiguous=0 exhausted=0 worst_case=$17.507606
charged=$0.000000 remaining_worst_case=$44.140910 budget=$8.00
ERROR: refusing to start: charged plus remaining worst-case $44.140910 exceeds budget $8.00
```

Exit status: 2. The updated one-dispatch-per-remaining-item bound is
**$44.140910**. As before, every parse retry requires a fresh reservation and
the live runner stops cleanly before the lane-wide budget can be exceeded. The
default $8 budget therefore fails closed with the necessary GLM cap; the PM must
set a reviewed sufficient budget only after the live probe succeeds.

WRITTEN REPORT_SOL_RUNNER_V2.md
