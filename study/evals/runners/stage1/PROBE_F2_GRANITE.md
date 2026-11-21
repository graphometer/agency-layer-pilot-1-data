# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f2-01-missing-endpoint`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.0006 of $5.00, headroom $4.9994
- calls dispatched 8, refused 0, largest reservation $0.0025
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `granite4.1:30b` | C | model_stopped | success | "off" | None | {"temperature": 1.0, "seed": 1150682554} | 0 | $0.0006 |
| `granite4.1:30b` | D | model_stopped | None | "off" | None | {"temperature": 1.0, "seed": 1000624040} | 0 | $0.0000 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `granite4.1:30b` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1150682554}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 4 assistant turns, 0 follow-ups
- PASS no provider refusal: model_stopped
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1150682554 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 9226 in, 436 out

### `granite4.1:30b` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1000624040}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: model_stopped
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 2 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=1000624040 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 6017 in, 374 out

## Verdict

1 failed checks and 0 errors. Details above.
- `granite4.1:30b` D: final status line present

