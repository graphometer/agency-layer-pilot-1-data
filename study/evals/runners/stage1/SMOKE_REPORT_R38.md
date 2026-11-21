# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f1-01-tax-rounding`, ceiling $5.00, enforced before dispatch.

## Spend

- spent $0.0743 of $5.00, headroom $4.9257
- calls dispatched 21, refused 0, largest reservation $0.0268
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `deepseek-v4-pro` | A | task_completed | success | "none" | None | {"temperature": 1.0, "seed": 427067832} | 0 | $0.0102 |
| `deepseek-v4-pro` | B | task_completed | success | "none" | None | {"temperature": 1.0, "seed": 1481377284} | 0 | $0.0146 |
| `deepseek-v4-pro` | C | task_completed | success | "none" | None | {"temperature": 1.0, "seed": 1098719464} | 0 | $0.0221 |
| `deepseek-v4-pro` | D | task_completed | success | "none" | None | {"temperature": 1.0, "seed": 624697772} | 0 | $0.0274 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `deepseek-v4-pro` condition A

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 427067832}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=427067832 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 7773 in, 821 out

### `deepseek-v4-pro` condition B

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1481377284}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1481377284 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 10424 in, 1376 out

### `deepseek-v4-pro` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 1098719464}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=1098719464 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 18487 in, 1195 out

### `deepseek-v4-pro` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: as_published (expected as_published)
- PASS sampling recorded as sent: {"temperature": 1.0, "seed": 624697772}
- PASS thinking pinned and recorded: 'none'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 6 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS tool calls decoded: 7 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line present: 'success'
- PASS seed and fingerprint recorded: seed=624697772 supported=True fingerprint=a307abda487cd1b463329ccb945ce396
- PASS provider reported usage: 23063 in, 1457 out

## Verdict

Every check passed on every arm that ran. The provider clients work on the wire, and the run records carry what was actually sent.


## First pass of the same config (batch smoke-r38, all three API arms)

The checker's `openai_compatible` KeyError hid the DeepSeek check lines on the first pass (fixed in
tools/smoke.py, then the DeepSeek arm re-ran as batch smoke-r38b above; run records for both batches
are retained in the harness staging results). The API incumbents on the isolated harness:

```
ok    claude-sonnet-5    A  task_completed  $0.0386
CHECK claude-sonnet-5    B  task_completed  $0.0466  follow-up budget not exhausted (2 of 2 used)
ok    claude-sonnet-5    C  task_completed  $0.0544
CHECK claude-sonnet-5    D  task_completed  $0.0642  follow-up budget not exhausted (2 of 2 used)
ok    gpt-5.6-terra      A  task_completed  $0.0205
ok    gpt-5.6-terra      B  task_completed  $0.0220
ok    gpt-5.6-terra      C  task_completed  $0.0332
ok    gpt-5.6-terra      D  task_completed  $0.0384
```

The two CHECK rows are behaviour observations, not instrument failures: in B and D Sonnet consumed
both scripted operator replies on the benign scenario (the pre-isolation smoke used 0 of 2). All
nine first-call instrument checks passed on every run in both batches.
