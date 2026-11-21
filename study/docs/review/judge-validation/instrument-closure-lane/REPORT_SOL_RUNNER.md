# Instrument-closure label runner report

No provider call was made. No credential value or `.env` file was read. All implementation and
verification in this task was offline.

## Files written

- `docs/review/judge-validation/instrument-closure-lane/run_labels.py`
  - validates the exact `{request_id, prompt}` packet schema and the `nm-`/`/mnt/` blindness ban;
  - runs the frozen three-member panel through one OpenRouter chat-completions transport at
    temperature 0;
  - writes deterministic `labels/<labeller>__<track>.jsonl` files with exactly
    `{request_id, raw, parsed}`;
  - uses an fsynced, append-only journal per labeller and track, reserving before each dispatch and
    settling afterward;
  - treats any reserved but incomplete logical item as ambiguous, charges every attempt at bound,
    and never dispatches that item again;
  - refuses an unpriced model and refuses startup when authoritative prior charges plus the
    remaining one-dispatch-per-item bound exceed `--budget` (default `$8.00`);
  - retries response errors and unparseable answers four times with the mined 4/8/12-second linear
    backoff, subject to the same lane-wide cap before every retry;
  - implements `--dry-run` without constructing a client or reading a credential;
  - implements deterministic F10 split and audit queue computation using
    `build_packets.add_panel_split`.
- `docs/review/judge-validation/instrument-closure-lane/label_prices.json`
  - supplies exact routed-model prices absent from `evals/grading/instrument_prices.json`.
- `docs/review/judge-validation/instrument-closure-lane/test_run_labels.py`
  - adds offline mock/golden coverage for strict parsing, packet blindness, resume skipping,
    ambiguous in-flight charging, cap stopping, unpriced refusal, request shape/provider pinning,
    and split/audit determinism.
- `REPORT_SOL_RUNNER.md` (this report).

All changes remain uncommitted.

## Conventions mined from the successful freeze machinery

The committed `freeze-qualification/run_freeze_judges.py` establishes the OpenAI-compatible
chat-completions shape: one user message containing the item prompt, temperature fixed per model,
bounded `max_tokens`, four attempts, and linear `4 * attempt` retry sleeps. It preserves raw model
content and strictly parses against an allowed verdict vocabulary.

The panel caller referenced by that script's staging path is
`<LOCAL-PATH>`; its committed outputs are the
three files under `freeze-qualification/labels/`. Exact historical configurations found:

| Labeller | Historical working model id | Historical endpoint/cap |
|---|---|---|
| Gemini 3.7 Flash | `gemini-3.7-flash` | Google OpenAI-compatible endpoint, 2048 tokens, Gemini thinking budget 0 |
| Grok 4.6 | `grok-4.6` | xAI OpenAI-compatible endpoint, 4096 tokens |
| GLM-5.3 | `z-ai/glm-5.3` | OpenRouter, initially 4096 and retried at 8192 tokens |

The historical panel asked for a one-line JSON object, extracted the JSON object, validated its
`label`, and retried parse failures. This lane's already-frozen packets instead demand exactly one
word. The runner therefore preserves the retry-on-parse-failure convention but accepts only the
track's exact stripped one-word vocabulary; casing, prose, JSON, markdown, empty content, and foreign
track labels parse to null. Raw content is never truncated.

The required all-OpenRouter routed ids configured in the new runner are:

- `google/gemini-3.7-flash`
- `x-ai/grok-4.6`
- `z-ai/glm-5.3`

Every request is exactly one `user` message whose content is the packet's `prompt`; there is no
system message, wrapper, item metadata, join data, construction intent, or other model-visible
content. Temperature is `0.0`, there is no stop sequence, and the one-word completion cap is 16
tokens. GLM sends the explicit OpenRouter preference
`provider.only=["Z.AI"], provider.allow_fallbacks=false`; this closes the known default-allowlist
failure and prevents an unpriced fallback route.

## Price rows and metering

The global table prices the direct id `gemini-3.7-flash` but none of the three exact OpenRouter
routed ids, so all three are lane-local:

| Routed model | Input / MTok | Output / MTok | Source recorded in table |
|---|---:|---:|---|
| `google/gemini-3.7-flash` | $0.30 | $2.50 | `https://openrouter.ai/google/gemini-3.7-flash`; matches the global direct-model row |
| `x-ai/grok-4.6` | $2.00 | $10.00 | `https://openrouter.ai/x-ai/grok-4.6` |
| `z-ai/glm-5.3` | $0.80 | $2.56 | `https://openrouter.ai/z-ai/glm-5.3` |

The per-call input bound is UTF-8 byte length plus 32 chat-envelope tokens. This is conservative
without depending on an uncommitted tokenizer: a token cannot consume fewer than one input byte.
The output bound is the transmitted 16-token cap. A missing usage record settles at the reserved
bound. Provider-reported usage settles at its calculated price and is never silently clipped. The
startup projection covers one primary dispatch for every remaining item; retry calls each require a
fresh reservation and can cause a clean cap stop. The running authoritative total is printed after
each completed item.

## Offline tests

Exact command, run from `docs/review/judge-validation/instrument-closure-lane`:

```text
python3 -m pytest -q
............................................................             [100%]
60 passed in 0.06s
```

The runner-specific tests use only an injected mock transport. The existing lane tests and the new
runner tests pass together.

## Dry run against the real packets

Exact command, run from the lane directory:

```text
python3 run_labels.py --dry-run
```

Output (an explicit shell wrapper recorded the final status):

```text
gemini-3.7-flash l1: items=461 remaining=461 ambiguous=0 worst_case=$0.546636
gemini-3.7-flash l2: items=461 remaining=461 ambiguous=0 worst_case=$0.209359
grok-4.6 l1: items=461 remaining=461 ambiguous=0 worst_case=$3.595064
grok-4.6 l2: items=461 remaining=461 ambiguous=0 worst_case=$1.346550
glm-5.3 l1: items=461 remaining=461 ambiguous=0 worst_case=$1.427404
glm-5.3 l2: items=461 remaining=461 ambiguous=0 worst_case=$0.527999
charged=$0.000000 remaining_worst_case=$7.653011 budget=$8.00
ERROR: dry-run found 4 packet validation error(s); first: <REPO>/docs/review/judge-validation/instrument-closure-lane/packets/l1_packets.jsonl:150: blindness violation in 39967caf833f11580217a477: prompt contains '/mnt/'
exit_status=2
```

This is the required fail-closed result: the cost fits the protected allocation, but the current
frozen packet files are not dispatchable.

## Ambiguities and blockers requiring PM action

1. **Real packets violate the frozen blindness invariant.** Two underlying items leak `/mnt/` into
   both tracks (four packet rows): L1 request ids `39967caf833f11580217a477` and
   `a9bf257a5a79aa85568ffc36`; L2 request ids `cf028ad25ab0eb2653f08c01` and
   `74da91579173853ac96e3ff4`. The runner intentionally refuses them. The packet-building/blinding
   owner must correct and re-freeze the packet artifacts; this runner does not silently scrub model
   inputs at dispatch time.
2. **The historical Gemini and Grok panel calls were direct-provider calls.** Only GLM's
   `z-ai/glm-5.3` id was directly exercised through OpenRouter in the mined machinery. The
   `google/...` and `x-ai/...` routed forms are OpenRouter's canonical ids required by this task, but
   they were not live-probed here because live probing was forbidden. PM must verify model
   availability before dispatch without changing the frozen panel identity.
3. **Prices were not refreshed from the network in this offline task.** The committed rows cite the
   model listing that must be checked immediately before the paid run. A changed or unavailable
   listing requires updating and reviewing the committed table before dispatch; the runner itself
   will still refuse a missing/malformed row.
4. **Completion-cap tradeoff is explicit.** The historical JSON labelling calls allowed
   2048–8192 completion tokens; that cap cannot be reserved for 2,766 calls inside the protected $8
   allocation. The lane packets require a one-word answer, so this runner transmits a 16-token cap.
   If a routed thinking model returns empty content at that cap, the response remains raw-preserved,
   retries remain metered, and the final parse is null for F10 adjudication; the runner never expands
   the cap or budget silently.
5. **Split computation is implemented and golden-tested but cannot run on the real artifacts yet.**
   The six new label files do not exist, and the packet blindness failure must be repaired first.
   Once both are true, `python3 run_labels.py --compute-splits` writes deterministic
   `adjudication_queue_l1.jsonl`, `adjudication_queue_l2.jsonl`, `audit_queue_l1.jsonl`, and
   `audit_queue_l2.jsonl`. Every null, abstention, or split is adjudicated; audits are the 20
   unanimous non-abstaining items per track with lowest SHA-256 of
   `<item id>-<track>-audit`.

WRITTEN REPORT_SOL_RUNNER.md
