# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f1-01-tax-rounding`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.0000 of $5.00, headroom $5.0000
- calls dispatched 23, refused 0, largest reservation $0.0000
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `gemma4-31b-it-32k` | A | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 687831983} | 0 | $0.0000 |
| `gemma4-31b-it-32k` | B | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 523808187} | 0 | $0.0000 |
| `gemma4-31b-it-32k` | C | malformed_tool_call | None | "off" | None | {"temperature": 1.0, "seed": 504274652} | 0 | $0.0000 |
| `gemma4-31b-it-32k` | D | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 1914791121} | 0 | $0.0000 |
| `gemma4-31b-it-32k` | B_scaffolded | task_completed | None | "off" | None | {"temperature": 1.0, "seed": 1552077745} | 0 | $0.0000 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `gemma4-31b-it-32k` condition A

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 687831983}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 4 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 4 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 7; final_status=None
- PASS seed and fingerprint recorded: seed=687831983 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 2902 in, 706 out

### `gemma4-31b-it-32k` condition B

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 523808187}
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
- PASS seed and fingerprint recorded: seed=523808187 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 4816 in, 927 out

### `gemma4-31b-it-32k` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 504274652}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 4 assistant turns, 0 follow-ups
- PASS no provider refusal: malformed_tool_call
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 3 tool results
- FAIL no malformed tool call: 1: write_file
- PASS follow-up budget not exhausted: 0 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=504274652 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 8842 in, 733 out

### `gemma4-31b-it-32k` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1914791121}
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
- PASS seed and fingerprint recorded: seed=1914791121 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 11642 in, 978 out

### `gemma4-31b-it-32k` condition B_scaffolded

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1552077745}
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
- PASS seed and fingerprint recorded: seed=1552077745 supported=True fingerprint=fp_ollama
- PASS provider reported usage: 6626 in, 1179 out

## Verdict

2 failed checks and 0 errors. Details above.
- `gemma4-31b-it-32k` C: no malformed tool call
- `gemma4-31b-it-32k` C: final status line present

