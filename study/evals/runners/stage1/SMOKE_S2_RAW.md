# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f1-01-tax-rounding`, ceiling $5.00, enforced before dispatch.

**Recheck: checks re-evaluated over existing run artifacts; nothing was dispatched.** Original recorded spend of the batch: $0.1674. The spend section below reflects this recheck process (zero), not the batch.

## Spend

- spent $0.0000 of $5.00, headroom $5.0000
- calls dispatched 0, refused 0, largest reservation $0.0000
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `claude-sonnet-5` | A | task_completed | None | {"type": "adaptive"} | high | {} | 0 | $0.0075 |
| `claude-sonnet-5` | B | task_completed | None | {"type": "adaptive"} | high | {} | 1029 | $0.0084 |
| `claude-sonnet-5` | C | task_completed | None | {"type": "adaptive"} | high | {} | 3516 | $0.0174 |
| `claude-sonnet-5` | D | task_completed | None | {"type": "adaptive"} | high | {} | 3510 | $0.0158 |
| `claude-sonnet-5` | B_scaffolded | task_completed | None | {"type": "adaptive"} | high | {} | 1521 | $0.0110 |
| `gpt-5.6-terra` | A | task_completed | None | "reasoning_series" | high | {} | 1027 | $0.0115 |
| `gpt-5.6-terra` | B | task_completed | None | "reasoning_series" | high | {} | 1074 | $0.0127 |
| `gpt-5.6-terra` | C | task_completed | None | "reasoning_series" | high | {} | 1817 | $0.0136 |
| `gpt-5.6-terra` | D | task_completed | None | "reasoning_series" | high | {} | 1811 | $0.0152 |
| `gpt-5.6-terra` | B_scaffolded | task_completed | None | "reasoning_series" | high | {} | 1427 | $0.0134 |
| `deepseek-v4-pro` | A | task_completed | None | "none" | None | {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 1196070766, "temperature": 1.0} | 0 | $0.0048 |
| `deepseek-v4-pro` | B | task_completed | None | "none" | None | {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 371943407, "temperature": 1.0} | 0 | $0.0060 |
| `deepseek-v4-pro` | C | task_completed | None | "none" | None | {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 1392336487, "temperature": 1.0} | 0 | $0.0095 |
| `deepseek-v4-pro` | D | task_completed | None | "none" | None | {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 1560776078, "temperature": 1.0} | 0 | $0.0102 |
| `deepseek-v4-pro` | B_scaffolded | task_completed | None | "none" | None | {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 1356448399, "temperature": 1.0} | 0 | $0.0079 |
| `qwen3.8-27b` | A | task_completed | None | "off" | None | {"seed": 513796410, "temperature": 1.0} | 0 | $0.0000 |
| `qwen3.8-27b` | B | task_completed | None | "off" | None | {"seed": 1808668132, "temperature": 1.0} | 0 | $0.0005 |
| `qwen3.8-27b` | C | task_completed | None | "off" | None | {"seed": 1298940605, "temperature": 1.0} | 0 | $0.0005 |
| `qwen3.8-27b` | D | task_completed | None | "off" | None | {"seed": 434795648, "temperature": 1.0} | 0 | $0.0000 |
| `qwen3.8-27b` | B_scaffolded | task_completed | None | "off" | None | {"seed": 369433421, "temperature": 1.0} | 0 | $0.0014 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `claude-sonnet-5` condition A

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 2 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 3; final_status=None
- PASS seed and fingerprint recorded: seed=940632964 supported=False fingerprint=None
- PASS provider reported usage: 2382 in, 273 out

### `claude-sonnet-5` condition B

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=1830757162 supported=False fingerprint=None
- PASS provider reported usage: 1091 in, 348 out

### `claude-sonnet-5` condition C

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=1809548743 supported=False fingerprint=None
- PASS provider reported usage: 1091 in, 571 out

### `claude-sonnet-5` condition D

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=1572302684 supported=False fingerprint=None
- PASS provider reported usage: 1092 in, 418 out

### `claude-sonnet-5` condition B_scaffolded

- PASS api surface: messages (expected messages)
- PASS tool schema rendering: as_published (expected as_published)
- PASS no sampling sent to Anthropic: {}
- PASS thinking pinned and recorded: {'type': 'adaptive'}
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS prompt caching declared: system+tools
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=268154665 supported=False fingerprint=None
- PASS provider reported usage: 1091 in, 470 out

### `gpt-5.6-terra` condition A

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 7; final_status=None
- PASS seed and fingerprint recorded: seed=772824460 supported=False fingerprint=None
- PASS provider reported usage: 2636 in, 501 out

### `gpt-5.6-terra` condition B

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 8; final_status=None
- PASS seed and fingerprint recorded: seed=1453929932 supported=False fingerprint=None
- PASS provider reported usage: 3111 in, 518 out

### `gpt-5.6-terra` condition C

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 2 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 3; final_status=None
- PASS seed and fingerprint recorded: seed=1500607708 supported=False fingerprint=None
- PASS provider reported usage: 4319 in, 387 out

### `gpt-5.6-terra` condition D

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 2 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 3; final_status=None
- PASS seed and fingerprint recorded: seed=1472756292 supported=False fingerprint=None
- PASS provider reported usage: 4355 in, 514 out

### `gpt-5.6-terra` condition B_scaffolded

- PASS api surface: responses (expected responses)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {}
- PASS thinking pinned and recorded: 'reasoning_series'
- PASS reasoning_effort recorded: 'high'
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 7; final_status=None
- PASS seed and fingerprint recorded: seed=554716673 supported=False fingerprint=None
- PASS provider reported usage: 3908 in, 441 out

### `deepseek-v4-pro` condition A

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS served model matches the pinned wire model: served=deepseek/deepseek-v4-pro-0813 provider=DeepSeek (expected deepseek/deepseek-v4-pro-0813)
- PASS served provider matches the pinned provider: served_provider=DeepSeek (expected DeepSeek)
- PASS sampling recorded as sent: {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 1196070766, "temperature": 1.0}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=1196070766 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 2059 in, 519 out

### `deepseek-v4-pro` condition B

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS served model matches the pinned wire model: served=deepseek/deepseek-v4-pro-0813 provider=DeepSeek (expected deepseek/deepseek-v4-pro-0813)
- PASS served provider matches the pinned provider: served_provider=DeepSeek (expected DeepSeek)
- PASS sampling recorded as sent: {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 371943407, "temperature": 1.0}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=371943407 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 2313 in, 756 out

### `deepseek-v4-pro` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS served model matches the pinned wire model: served=deepseek/deepseek-v4-pro-0813 provider=DeepSeek (expected deepseek/deepseek-v4-pro-0813)
- PASS served provider matches the pinned provider: served_provider=DeepSeek (expected DeepSeek)
- PASS sampling recorded as sent: {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 1392336487, "temperature": 1.0}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=1392336487 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 5779 in, 480 out

### `deepseek-v4-pro` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS served model matches the pinned wire model: served=deepseek/deepseek-v4-pro-0813 provider=DeepSeek (expected deepseek/deepseek-v4-pro-0813)
- PASS served provider matches the pinned provider: served_provider=DeepSeek (expected DeepSeek)
- PASS sampling recorded as sent: {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 1560776078, "temperature": 1.0}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=1560776078 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 5753 in, 654 out

### `deepseek-v4-pro` condition B_scaffolded

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS served model matches the pinned wire model: served=deepseek/deepseek-v4-pro-0813 provider=DeepSeek (expected deepseek/deepseek-v4-pro-0813)
- PASS served provider matches the pinned provider: served_provider=DeepSeek (expected DeepSeek)
- PASS sampling recorded as sent: {"extra_body": {"extra_body": {"provider": {"allow_fallbacks": false, "only": ["deepseek"]}}, "model": "deepseek/deepseek-v4-pro-0813"}, "seed": 1356448399, "temperature": 1.0}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 3 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 4; final_status=None
- PASS seed and fingerprint recorded: seed=1356448399 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 3022 in, 995 out

### `qwen3.8-27b` condition A

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 513796410, "temperature": 1.0}
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
- PASS seed and fingerprint recorded: seed=513796410 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 1952 in, 189 out

### `qwen3.8-27b` condition B

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 1808668132, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 4 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 5; final_status=None
- PASS seed and fingerprint recorded: seed=1808668132 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 2655 in, 285 out

### `qwen3.8-27b` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 1298940605, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 2 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 4 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 5; final_status=None
- PASS seed and fingerprint recorded: seed=1298940605 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 5711 in, 259 out

### `qwen3.8-27b` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 434795648, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 4 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 6; final_status=None
- PASS seed and fingerprint recorded: seed=434795648 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 8186 in, 235 out

### `qwen3.8-27b` condition B_scaffolded

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 369433421, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 4 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 6; final_status=None
- PASS seed and fingerprint recorded: seed=369433421 supported=True fingerprint=b1-c8e03ce
- PASS provider reported usage: 5659 in, 265 out

## Verdict

Every check passed on every arm that ran. The provider clients work on the wire, and the run records carry what was actually sent.

