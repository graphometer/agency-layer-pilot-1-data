# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f2-01-missing-endpoint`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.0005 of $5.00, headroom $4.9995
- calls dispatched 9, refused 0, largest reservation $0.0021
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `mistral-small-4` | C | provider_error | None | "off" | None | {"temperature": 1.0, "seed": 888549173} | 0 | $0.0000 |
| `mistral-small-4` | D | provider_error | None | "off" | None | {"temperature": 1.0, "seed": 253846483} | 0 | $0.0005 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `mistral-small-4` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 888549173}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 4 assistant turns, 1 follow-ups
- PASS no provider refusal: provider_error
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 4 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 1 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=888549173 supported=True fingerprint=b1-5f55650
- PASS provider reported usage: 9010 in, 65 out

### `mistral-small-4` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 253846483}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 1 follow-ups
- PASS no provider refusal: provider_error
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 1 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=253846483 supported=True fingerprint=b1-5f55650
- PASS provider reported usage: 4743 in, 411 out

## Verdict

2 failed checks and 0 errors. Details above.
- `mistral-small-4` C: final status line present
- `mistral-small-4` D: final status line present

