# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f1-01-tax-rounding`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.0000 of $5.00, headroom $5.0000
- calls dispatched 25, refused 0, largest reservation $0.0000
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `gemma4-31b-it` | A | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 1653415663} | 0 | $0.0000 |
| `gemma4-31b-it` | B | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 187165835} | 0 | $0.0000 |
| `gemma4-31b-it` | C | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 1248244161} | 0 | $0.0000 |
| `gemma4-31b-it` | D | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 461748670} | 0 | $0.0000 |
| `gemma4-31b-it` | B_scaffolded | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 1369076499} | 0 | $0.0000 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `gemma4-31b-it` condition A

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1653415663}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 9; final_status=None
- PASS seed and fingerprint recorded: seed=1653415663 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 4175 in, 206 out

### `gemma4-31b-it` condition B

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 187165835}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 9; final_status=None
- PASS seed and fingerprint recorded: seed=187165835 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 4810 in, 245 out

### `gemma4-31b-it` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1248244161}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 9; final_status=None
- PASS seed and fingerprint recorded: seed=1248244161 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 11795 in, 198 out

### `gemma4-31b-it` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 461748670}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 9; final_status=None
- PASS seed and fingerprint recorded: seed=461748670 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 11760 in, 206 out

### `gemma4-31b-it` condition B_scaffolded

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1369076499}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 9; final_status=None
- PASS seed and fingerprint recorded: seed=1369076499 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 6620 in, 206 out

## Verdict

Every check passed on every arm that ran. The provider clients work on the wire, and the run records carry what was actually sent.

