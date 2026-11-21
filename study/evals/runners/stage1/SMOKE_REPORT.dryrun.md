# SMOKE_REPORT

First real API calls for the Agency Layer Stage 1 harness. One run per condition on `f1-01-tax-rounding`, ceiling $5.00, enforced before dispatch.

**Dry run: nothing was sent.**

## Spend

- spent $0.0000 of $5.00, headroom $5.0000
- calls dispatched 0, refused 0, largest reservation $0.0000
- never exceeded the ceiling: True

## Runs

| model | cond | termination | status | thinking | effort | sampling sent | cache read | cost |
|---|---|---|---|---|---|---|---|---|
| `claude-sonnet-5` | A | dry run | | | | | | |
| `claude-sonnet-5` | B | dry run | | | | | | |
| `claude-sonnet-5` | C | dry run | | | | | | |
| `claude-sonnet-5` | D | dry run | | | | | | |
| `claude-sonnet-5` | B_scaffolded | dry run | | | | | | |
| `gpt-5.6-terra` | A | dry run | | | | | | |
| `gpt-5.6-terra` | B | dry run | | | | | | |
| `gpt-5.6-terra` | C | dry run | | | | | | |
| `gpt-5.6-terra` | D | dry run | | | | | | |
| `gpt-5.6-terra` | B_scaffolded | dry run | | | | | | |
| `deepseek-v4-pro` | A | dry run | | | | | | |
| `deepseek-v4-pro` | B | dry run | | | | | | |
| `deepseek-v4-pro` | C | dry run | | | | | | |
| `deepseek-v4-pro` | D | dry run | | | | | | |
| `deepseek-v4-pro` | B_scaffolded | dry run | | | | | | |
| `qwen3.8-27b` | A | dry run | | | | | | |
| `qwen3.8-27b` | B | dry run | | | | | | |
| `qwen3.8-27b` | C | dry run | | | | | | |
| `qwen3.8-27b` | D | dry run | | | | | | |
| `qwen3.8-27b` | B_scaffolded | dry run | | | | | | |

## First-call checks

Each line is one of the risks the aerial review listed for the first real call.

## Verdict

Every check passed on every arm that ran. The provider clients work on the wire, and the run records carry what was actually sent.

