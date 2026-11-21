PROMOTE WITH FIXES

Do not dispatch until finding 1 is fixed in the request body. The journal, reserve-then-call, unpriced refusal, sequential $8 cap, F10 split/audit, L1-with-GT / L2-without packet reuse, and the PM blindness narrowing are sound. Empty Gemini (and likely Grok/GLM) parses would be written `completed` with `parsed: null` and never retried — that is the gold-destroying path, not a later resume.

Blindness edit: correct. The two real rows are `ls -d … /mnt/*` (`39967caf833f11580217a477`) and `BACKUP_DEST=/mnt/backup` (`a9bf257a5a79aa85568ffc36`). Neither contains `<LOCAL-PATH>` or `<LOCAL-PATH>`. `nm-` stays banned and is absent from packet prompts. Sol’s dry-run `/mnt/` failure is stale.

---

1. **`MAX_TOKENS = 16` plus no thinking/reasoning pin in `request_payload` / `LABELLERS`**
   Quote: `MAX_TOKENS = 16` (run_labels.py:35, 421); Gemini extra_body is `None`; freeze judge config (evals/grading/judge.py:319–321): “Gemini 3.7 Flash emits nothing under a cap below about 256 even with the thinking budget at zero (hidden tokens are reserved inside max_tokens). Probed 2026-08-23 at 8, 16, 32, 64 (empty) and 256, 512 (answer).” Historical goldset runner set Gemini `thinking_budget: 0` and GLM needed 8192 on OpenRouter after 4096 came back empty.
   Defect: the one-word cap was chosen so 2×461×3 fits $8 (~$7.65 one-shot). On the probed Gemini wire, 16 tokens is empty. Unparseable retries four times (`MAX_ATTEMPTS = 4`) and then **freezes** `parsed: None` as `completed` — resume will not recall it. F10 then treats `None` as a split (`None not in panel` fails), so a systematically empty Gemini vote sends every item to Sol and leaves audit at 0 unanimous. Thinking left on also bills reasoning tokens the 16-token reservation does not cover: `cost_usd` uses only `prompt_tokens`/`completion_tokens`; `actual > bound` is charged in full after the call (`settled = actual`), so the $8 check can overshoot by one thinking dump. Startup projection is one dispatch per remaining item; empty-parse retries eat the $0.35 slack and can cap-stop mid-panel. This is not silent cap expansion (the constant never moves) — it is a cap that cannot produce Gemini gold.
   Severity: **high** (money + gold)
   Minimal fix: pin thinking/reasoning off on the OpenRouter body for all three (Gemini: the Google `thinking_config.thinking_budget = 0` passthrough that freeze used, in the OpenRouter-legal shape; Grok/GLM: the matching `reasoning`/`include_reasoning` off switch). Set **explicit per-labeller** `max_tokens` so Gemini is at least 256 (the probed floor), not a silent raise of the global 16. Re-run `--dry-run`; if charged+bound exceeds $8, refuse (already the path) and have the PM pass a slightly larger `--budget` — do not send 256 while reserving 16. One cheap live probe per routed id before the 2,766, with thinking off, confirming a one-word parse. Do not dispatch at 16.

2. **Only GLM is provider-pinned; Gemini and Grok can still take an unpriced route**
   Quote: `Labeller("glm-5.3", "z-ai/glm-5.3", {"provider": {"only": ["Z.AI"], "allow_fallbacks": False}})` vs Gemini/Grok `extra_body is None`. `test_glm_request_pins_zai_provider` asserts the dataclass and never `payload["extra_body"]`.
   Defect: GLM pin shape is the right fail-closed idea (default allowlist / fallback was the known hole). `request_payload` does copy `extra_body` into the SDK keyword, which OpenRouter wants at top level as `provider`. Gemini and Grok get OpenRouter’s default fallbacks; a substitute provider is billed at whatever it bills while the journal prices `google/gemini-3.7-flash` / `x-ai/grok-4.6`. The test would still pass if `request_payload` dropped the pin.
   Severity: **medium** (money)
   Minimal fix: pin `only` + `allow_fallbacks: false` on all three to the priced provider (confirm the exact OpenRouter names against the listings at re-verify). Assert `payload["extra_body"]` equals that pin.

3. **`inspect_packets` / tests do not pin the narrowed blindness allow**
   Quote: `for forbidden in ("nm-", "<LOCAL-PATH>", "<LOCAL-PATH>"):`. Tests reject `nm-secret` and `<LOCAL-PATH>` only.
   Defect: the production check is the right ban. A regression back to substring `"/mnt/"` would still pass the runner tests and would again refuse the two legitimate corpus rows. `<LOCAL-PATH>` rejection is untested.
   Severity: **low**
   Minimal fix: one allow (`BACKUP_DEST=/mnt/backup` or `ls -d /mnt/*`) and one `<LOCAL-PATH>` reject in `test_blindness_assertion_rejects_extra_keys_and_markers`.

---

Closed under this read: call never leaves without an fsynced `reserved` event; ambiguous in-flight is charged at bound and never recalled; unpriced/placeholder models refuse; sequential lane cap is recomputed from journals between (labeller, track) pairs; no raw slice; `MAX_TOKENS` is not quietly raised at retry; F10 abstention/unparseable → adjudication; audit is per-track lowest SHA-256 of `<item id>-<track>-audit`; `add_panel_split` reuses the track packet (L1 keeps ground truth, L2 does not); output jsonl rebuilt from the journal on resume; order is `request_id` sort. A crash after `reserved` before `completed` still burns that item (intentional fail-closed); recover by journal surgery, not a second dispatch.

WRITTEN REVIEW_GROK_RUNNER.md
