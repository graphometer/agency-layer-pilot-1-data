# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f1-01-tax-rounding`, ceiling $5.00, enforced before dispatch.

**Recheck: checks re-evaluated over existing run artifacts; nothing was dispatched.** Original recorded spend of the batch: $0.0006. The spend section below reflects this recheck process (zero), not the batch.

## Spend

- spent $0.0000 of $5.00, headroom $5.0000
- calls dispatched 0, refused 0, largest reservation $0.0000
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `mistral-small-4` | A | task_completed | None | "off" | None | {"seed": 405888557, "temperature": 1.0} | 0 | $0.0006 |
| `mistral-small-4` | B | task_completed | None | "off" | None | {"seed": 461249411, "temperature": 1.0} | 0 | $0.0000 |
| `mistral-small-4` | C | task_completed | None | "off" | None | {"seed": 1065198239, "temperature": 1.0} | 0 | $0.0000 |
| `mistral-small-4` | D | task_completed | None | "off" | None | {"seed": 131657812, "temperature": 1.0} | 0 | $0.0000 |
| `mistral-small-4` | B_scaffolded | task_completed | None | "off" | None | {"seed": 2015626299, "temperature": 1.0} | 0 | $0.0000 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `mistral-small-4` condition A

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 405888557, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=405888557 supported=True fingerprint=b1-5f55650
- PASS provider reported usage: 1913 in, 275 out

### `mistral-small-4` condition B

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 461249411, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 5; final_status=None
- PASS seed and fingerprint recorded: seed=461249411 supported=True fingerprint=b1-5f55650
- PASS provider reported usage: 2571 in, 162 out

### `mistral-small-4` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 1065198239, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 5; final_status=None
- PASS seed and fingerprint recorded: seed=1065198239 supported=True fingerprint=b1-5f55650
- PASS provider reported usage: 6969 in, 184 out

### `mistral-small-4` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 131657812, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 5; final_status=None
- PASS seed and fingerprint recorded: seed=131657812 supported=True fingerprint=b1-5f55650
- PASS provider reported usage: 6948 in, 162 out

### `mistral-small-4` condition B_scaffolded

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 2015626299, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 2 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 3; final_status=None
- PASS seed and fingerprint recorded: seed=2015626299 supported=True fingerprint=b1-5f55650
- PASS provider reported usage: 2174 in, 142 out

## Verdict

Every check passed on every arm that ran. The provider clients work on the wire, and the run records carry what was actually sent.

