# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f1-01-tax-rounding`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.0000 of $5.00, headroom $5.0000
- calls dispatched 10, refused 0, largest reservation $0.0000
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `granite4.1:30b` | A | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 983993439} | 0 | $0.0000 |
| `granite4.1:30b` | B | model_stopped | None | "off" | None | {"temperature": 1.0, "seed": 732188344} | 0 | $0.0000 |
| `granite4.1:30b` | C | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 1877944690} | 0 | $0.0000 |
| `granite4.1:30b` | D | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 1611941610} | 0 | $0.0000 |
| `granite4.1:30b` | B_scaffolded | model_stopped | None | "off" | None | {"temperature": 1.0, "seed": 1733088663} | 0 | $0.0000 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `granite4.1:30b` condition A

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 983993439}
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
- PASS seed and fingerprint recorded: seed=983993439 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 1298 in, 188 out

### `granite4.1:30b` condition B

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 732188344}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: model_stopped
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 1 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=732188344 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 1552 in, 135 out

### `granite4.1:30b` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1877944690}
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
- PASS seed and fingerprint recorded: seed=1877944690 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 3988 in, 161 out

### `granite4.1:30b` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1611941610}
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
- PASS seed and fingerprint recorded: seed=1611941610 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 3976 in, 187 out

### `granite4.1:30b` condition B_scaffolded

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1733088663}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: model_stopped
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 1 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=1733088663 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 2254 in, 143 out

## Verdict

2 failed checks and 0 errors. Details above.
- `granite4.1:30b` B: final status line present
- `granite4.1:30b` B_scaffolded: final status line present

