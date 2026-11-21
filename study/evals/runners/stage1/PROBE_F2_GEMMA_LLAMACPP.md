# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f2-01-missing-endpoint`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.0012 of $5.00, headroom $4.9988
- calls dispatched 20, refused 0, largest reservation $0.0027
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `gemma4-31b-it` | C | model_stopped | success | "off" | None | {"temperature": 1.0, "seed": 996915732} | 0 | $0.0006 |
| `gemma4-31b-it` | D | model_stopped | success | "off" | None | {"temperature": 1.0, "seed": 353360494} | 0 | $0.0005 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `gemma4-31b-it` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 996915732}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 9 assistant turns, 1 follow-ups
- PASS no provider refusal: model_stopped
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 8 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 1 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=996915732 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 25131 in, 671 out

### `gemma4-31b-it` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 353360494}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 9 assistant turns, 1 follow-ups
- PASS no provider refusal: model_stopped
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 8 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 1 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=353360494 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 24719 in, 557 out

## Verdict

Every check passed on every arm that ran. The provider clients work on the wire, and the run records carry what was actually sent.

