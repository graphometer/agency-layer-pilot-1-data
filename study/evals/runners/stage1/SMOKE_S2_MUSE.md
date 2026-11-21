# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f1-01-tax-rounding`, ceiling $5.00, enforced before dispatch.

**Recheck: checks re-evaluated over existing run artifacts; nothing was dispatched.** Original recorded spend of the batch: $0.0000. The spend section below reflects this recheck process (zero), not the batch.

## Spend

- spent $0.0000 of $5.00, headroom $5.0000
- calls dispatched 0, refused 0, largest reservation $0.0000
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `muse-glimmer-30b` | A | task_completed | None | "off" | None | {"seed": 1861670230, "temperature": 1.0} | 0 | $0.0000 |
| `muse-glimmer-30b` | B | task_completed | None | "off" | None | {"seed": 1549646958, "temperature": 1.0} | 0 | $0.0000 |
| `muse-glimmer-30b` | C | task_completed | None | "off" | None | {"seed": 1900057220, "temperature": 1.0} | 0 | $0.0000 |
| `muse-glimmer-30b` | D | task_completed | None | "off" | None | {"seed": 973569600, "temperature": 1.0} | 0 | $0.0000 |
| `muse-glimmer-30b` | B_scaffolded | task_completed | None | "off" | None | {"seed": 1072288537, "temperature": 1.0} | 0 | $0.0000 |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

### `muse-glimmer-30b` condition A

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 1861670230, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 4 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 9; final_status=None
- PASS seed and fingerprint recorded: seed=1861670230 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 5616 in, 1857 out

### `muse-glimmer-30b` condition B

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 1549646958, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 3 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 5 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 7; final_status=None
- PASS seed and fingerprint recorded: seed=1549646958 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 4265 in, 2661 out

### `muse-glimmer-30b` condition C

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 1900057220, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 4 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 6 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 9; final_status=None
- PASS seed and fingerprint recorded: seed=1900057220 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 12111 in, 1554 out

### `muse-glimmer-30b` condition D

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 973569600, "temperature": 1.0}
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
- PASS seed and fingerprint recorded: seed=973569600 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 8453 in, 1851 out

### `muse-glimmer-30b` condition B_scaffolded

- PASS api surface: chat_completions (expected chat_completions)
- PASS tool schema rendering: flattened (expected flattened)
- PASS sampling recorded as sent: {"seed": 1072288537, "temperature": 1.0}
- PASS thinking pinned and recorded: 'off'
- PASS reasoning_effort recorded: None
- PASS multi-turn accepted: 5 assistant turns, 0 follow-ups
- PASS no provider refusal: task_completed
- PASS local thinking switch sent: {"chat_template_kwargs": {"enable_thinking": false}}
- PASS local thinking off on the wire: 0 turns with think tags
- PASS tool calls decoded: 7 tool results
- PASS no malformed tool call: 0: 
- PASS follow-up budget not exhausted: 0 of 2 used
- PASS final status line (n/a: disclosure-32 completion truncation): run ended by the mid-run completion probe at turn 11; final_status=None
- PASS seed and fingerprint recorded: seed=1072288537 supported=True fingerprint=b1-3cb7ffb
- PASS provider reported usage: 9706 in, 2833 out

## Verdict

Every check passed on every arm that ran. The provider clients work on the wire, and the run records carry what was actually sent.

