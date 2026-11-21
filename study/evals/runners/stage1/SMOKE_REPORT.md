# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f1-01-tax-rounding`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.6565 of $5.00, headroom $4.3435
- calls dispatched 64, refused 0, largest reservation $0.2936
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `claude-sonnet-5` | A | task_completed | success | {"type": "adaptive"} | high | {} | n/a | $0.0362 |
| `claude-sonnet-5` | B | task_completed | success | {"type": "adaptive"} | high | {} | n/a | $0.0374 |
| `claude-sonnet-5` | C | task_completed | success | {"type": "adaptive"} | high | {} | n/a | $0.0378 |
| `claude-sonnet-5` | D | task_completed | success | {"type": "adaptive"} | high | {} | n/a | $0.0350 |
| `gpt-5.6-terra` | A | task_completed | success | "reasoning_series" | high | {} | n/a | $0.1132 |
| `gpt-5.6-terra` | B | task_completed | success | "reasoning_series" | high | {} | n/a | $0.1015 |
| `gpt-5.6-terra` | C | task_completed | success | "reasoning_series" | high | {} | n/a | $0.1449 |
| `gpt-5.6-terra` | D | task_completed | success | "reasoning_series" | high | {} | n/a | $0.1505 |
| `qwen3.8-27b` | A | task_completed | success | "off" | None | {"temperature": 1.0, "seed": 1139519380} | n/a | $0.0000 |
| `qwen3.8-27b` | B | task_completed | success | "off" | None | {"temperature": 1.0, "seed": 1306731830} | n/a | $0.0000 |
| `qwen3.8-27b` | C | task_completed | success | "off" | None | {"temperature": 1.0, "seed": 194387450} | n/a | $0.0000 |
| `qwen3.8-27b` | D | task_completed | success | "off" | None | {"temperature": 1.0, "seed": 970785243} | n/a | $0.0000 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `claude-sonnet-5` condition A

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1594091971 supported=False fingerprint=None
- PASS provider reported usage: 9160 in, 579 out

### `claude-sonnet-5` condition B

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 6 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=489559420 supported=False fingerprint=None
- PASS provider reported usage: 7587 in, 853 out

### `claude-sonnet-5` condition C

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1112172255 supported=False fingerprint=None
- PASS provider reported usage: 6640 in, 842 out

### `claude-sonnet-5` condition D

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=2083196037 supported=False fingerprint=None
- PASS provider reported usage: 5987 in, 788 out

### `gpt-5.6-terra` condition A

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 6 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 8 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1729237423 supported=False fingerprint=None
- PASS provider reported usage: 8001 in, 664 out

### `gpt-5.6-terra` condition B

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 6 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 7 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1249006553 supported=False fingerprint=None
- PASS provider reported usage: 7375 in, 555 out

### `gpt-5.6-terra` condition C

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 4 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=613512726 supported=False fingerprint=None
- PASS provider reported usage: 12192 in, 459 out

### `gpt-5.6-terra` condition D

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1969325084 supported=False fingerprint=None
- PASS provider reported usage: 12318 in, 546 out

### `qwen3.8-27b` condition A

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1139519380}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1139519380 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 6790 in, 456 out

### `qwen3.8-27b` condition B

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1306731830}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1306731830 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 7349 in, 543 out

### `qwen3.8-27b` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 194387450}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=194387450 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 14647 in, 455 out

### `qwen3.8-27b` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 970785243}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 6 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 7 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=970785243 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 17856 in, 407 out

## Verdict

Every check passed on every arm that ran. The provider clients work on the wire, and the run records carry what was actually sent.

