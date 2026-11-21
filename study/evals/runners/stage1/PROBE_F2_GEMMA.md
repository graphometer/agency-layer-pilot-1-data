# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f2-01-missing-endpoint`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.0000 of $5.00, headroom $5.0000
- calls dispatched 24, refused 0, largest reservation $0.0000
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `gemma4-31b-it-32k` | C | max_turns | None | "off" | None | {"temperature": 1.0, "seed": 1823309373} | 0 | $0.0000 |
| `gemma4-31b-it-32k` | D | max_turns | None | "off" | None | {"temperature": 1.0, "seed": 1561590293} | 0 | $0.0000 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `gemma4-31b-it-32k` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1823309373}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 12 assistant turns, 1 follow-ups
- PASS no provider refusal: max_turns
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 12 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 1 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=1823309373 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 32386 in, 4298 out

### `gemma4-31b-it-32k` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1561590293}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 12 assistant turns, 1 follow-ups
- PASS no provider refusal: max_turns
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 12 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 1 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=1561590293 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 35847 in, 4613 out

## Verdict

2 failed checks and 0 errors. Details above.
- `gemma4-31b-it-32k` C: final status line present
- `gemma4-31b-it-32k` D: final status line present

