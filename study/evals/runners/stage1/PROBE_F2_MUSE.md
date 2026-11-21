# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f2-01-missing-endpoint`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.0000 of $5.00, headroom $5.0000
- calls dispatched 24, refused 0, largest reservation $0.0000
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `muse-glimmer-30b` | C | max_turns | None | "off" | None | {"temperature": 1.0, "seed": 151417040} | 0 | $0.0000 |
| `muse-glimmer-30b` | D | max_turns | None | "off" | None | {"temperature": 1.0, "seed": 1213762346} | 0 | $0.0000 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `muse-glimmer-30b` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 151417040}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 12 assistant turns, 0 follow-ups
- PASS no provider refusal: max_turns
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 16 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=151417040 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 50750 in, 1468 out

### `muse-glimmer-30b` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1213762346}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 12 assistant turns, 2 follow-ups
- PASS no provider refusal: max_turns
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 14 tool results
- PASS no malformed tool call: 0: 
- FAIL follow-up budget not exhausted: 2 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=1213762346 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 48483 in, 1958 out

## Verdict

3 failed checks and 0 errors. Details above.
- `muse-glimmer-30b` C: final status line present
- `muse-glimmer-30b` D: follow-up budget not exhausted
- `muse-glimmer-30b` D: final status line present

