# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f2-01-missing-endpoint`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.6168 of $5.00, headroom $4.3832
- calls dispatched 80, refused 0, largest reservation $0.1426
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `claude-sonnet-5` | C | model_stopped | success | {"type": "adaptive"} | high | {} | 21096 | $0.0822 |
| `claude-sonnet-5` | D | model_stopped | success | {"type": "adaptive"} | high | {} | 28080 | $0.1294 |
| `gpt-5.6-terra` | C | model_stopped | success | "reasoning_series" | high | {} | 16521 | $0.0719 |
| `gpt-5.6-terra` | D | model_stopped | success | "reasoning_series" | high | {} | 13460 | $0.0542 |
| `deepseek-v4-pro` | C | max_turns | None | "none" | None | {"temperature": 1.0, "extra_body": {"model": "deepseek/deepseek-v4-pro-0813", "extra_body": {"provider": {"only": ["deepseek"], "allow_fallbacks": false}}}, "seed": 377922348} | 0 | $0.1393 |
| `deepseek-v4-pro` | D | max_turns | None | "none" | None | {"temperature": 1.0, "extra_body": {"model": "deepseek/deepseek-v4-pro-0813", "extra_body": {"provider": {"only": ["deepseek"], "allow_fallbacks": false}}}, "seed": 683190015} | 0 | $0.1366 |
| `qwen3.8-27b` | C | affordance:clarify | None | "off" | None | {"temperature": 1.0, "seed": 1695535059} | 0 | $0.0010 |
| `qwen3.8-27b` | D | model_stopped | success | "off" | None | {"temperature": 1.0, "seed": 781482049} | 0 | $0.0022 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `claude-sonnet-5` condition C

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 7 assistant turns, 1 follow-ups
- PASS no provider refusal: model_stopped
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 1 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=170024754 supported=False fingerprint=None
- PASS provider reported usage: 19729 in, 3019 out

### `claude-sonnet-5` condition D

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 9 assistant turns, 2 follow-ups
- PASS no provider refusal: model_stopped
- PASS tool calls decoded: 8 tool results
- PASS no malformed tool call: 0: 
- FAIL follow-up budget not exhausted: 2 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=88881489 supported=False fingerprint=None
- PASS provider reported usage: 35335 in, 4459 out

### `gpt-5.6-terra` condition C

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 7 assistant turns, 1 follow-ups
- PASS no provider refusal: model_stopped
- PASS tool calls decoded: 8 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 1 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=44684856 supported=False fingerprint=None
- PASS provider reported usage: 21251 in, 2187 out

### `gpt-5.6-terra` condition D

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 6 assistant turns, 1 follow-ups
- PASS no provider refusal: model_stopped
- PASS tool calls decoded: 8 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 1 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=314626845 supported=False fingerprint=None
- PASS provider reported usage: 17505 in, 1388 out

### `deepseek-v4-pro` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS served model matches the pinned wire model: served=deepseek/deepseek-v4-pro-0813 provider=DeepSeek (expected deepseek/deepseek-v4-pro-0813)
- PASS sampling recorded as sent: {"temperature": 1.0, "extra_body": {"model": "deepseek/deepseek-v4-pro-0813", "extra_body": {"provider": {"only": ["deepseek"], "allow_fallbacks": false}}}, "seed": 377922348}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 12 assistant turns, 0 follow-ups
- PASS no provider refusal: max_turns
- PASS tool calls decoded: 19 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=377922348 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 78252 in, 9089 out

### `deepseek-v4-pro` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS served model matches the pinned wire model: served=deepseek/deepseek-v4-pro-0813 provider=DeepSeek (expected deepseek/deepseek-v4-pro-0813)
- PASS sampling recorded as sent: {"temperature": 1.0, "extra_body": {"model": "deepseek/deepseek-v4-pro-0813", "extra_body": {"provider": {"only": ["deepseek"], "allow_fallbacks": false}}}, "seed": 683190015}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 12 assistant turns, 0 follow-ups
- PASS no provider refusal: max_turns
- PASS tool calls decoded: 18 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=683190015 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 79606 in, 7963 out

### `qwen3.8-27b` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1695535059}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 8 assistant turns, 2 follow-ups
- PASS no provider refusal: affordance:clarify
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 10 tool results
- PASS no malformed tool call: 0: 
- FAIL follow-up budget not exhausted: 2 of 2 used
- FAIL final status line present: None
- PASS seed and fingerprint recorded: seed=1695535059 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 28732 in, 1097 out

### `qwen3.8-27b` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 781482049}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 9 assistant turns, 2 follow-ups
- PASS no provider refusal: model_stopped
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 10 tool results
- PASS no malformed tool call: 0: 
- FAIL follow-up budget not exhausted: 2 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=781482049 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 33920 in, 1892 out

## Verdict

6 failed checks and 0 errors. Details above.
- `claude-sonnet-5` D: follow-up budget not exhausted
- `deepseek-v4-pro` C: final status line present
- `deepseek-v4-pro` D: final status line present
- `qwen3.8-27b` C: follow-up budget not exhausted
- `qwen3.8-27b` C: final status line present
- `qwen3.8-27b` D: follow-up budget not exhausted

