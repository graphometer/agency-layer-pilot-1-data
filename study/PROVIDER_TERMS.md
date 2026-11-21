# Provider terms for publishing transcripts and instrument outputs

*Required before recorded dispatch by R19 and R39 amendment F11, and re-checked before launch. Named as
an open blocker by the GPT review (R5) and the Grok review (B6). Written in the correction phase,
2026-08-24. **This page records what a session could verify from public terms pages; it is not legal
advice and Grant signs it off before dispatch.***

## What the study wants to publish

| Artifact | Contains | Which providers |
|---|---|---|
| `results/stage1/<batch_id>/<run_id>/transcript.jsonl` | the full task conversation: our prompts, the subject model's replies and tool calls, our scripted human replies, fixture command output | subject models: Anthropic, OpenAI, DeepSeek **via OpenRouter (R54: OpenRouter is the intermediary and receives the DeepSeek arm's full request/response traffic; the pin keeps the serving party DeepSeek itself)**, local |
| `results/stage1/<batch_id>/<run_id>/events.jsonl`, `state.json`, `run.json` | protocol events and run metadata; no model prose beyond affordance field values | same |
| `**/blinded.jsonl` | condition-blinded projections of the same model text | same |
| judged files | one-word instrument verdicts (`qualifying`, `not_qualifying`, `cannot_determine`) plus the prompt digest | instruments: Mistral, MiniMax via OpenRouter |
| `docs/review/**` | instrument validation panels: one-word labels and short notes from label models, the freeze-qualification judge candidates' one-word per-item verdicts, and the instrument-closure lane's blind answers and adjudications | Google, xAI, Z.ai, Moonshot, Mistral, MiniMax, Meta, Cohere, and the OpenAI and Anthropic subscription surfaces |

Everything is our own prompt text, our fixtures, and model outputs generated for us. Nothing is
third-party web content, and no provider's model weights, system prompts or internal metadata are
published. The intended licence for the data package is CC BY 4.0 (R19), and for the code MIT, with the
named per-file carve-outs listed in the repository's root `NOTICE` (Grant's rulings of 2026-08-26 on the
per-item GLM-5.3 labels and the per-item `command-a` judge answers).

## What each provider's public terms say

Read 2026-08-24, with every later reading dated in its own row. Each row names the clause type, not a
quotation of the whole instrument.

| Provider | Role | Output ownership | Publication of outputs | Other clause that matters | Verdict for this study |
|---|---|---|---|---|---|
| **Anthropic** (`claude-sonnet-5`) | subject | Commercial Terms section B: the customer owns its Outputs; Anthropic assigns its right, title and interest in Outputs to the customer | no clause found restricting publication or redistribution of Outputs | section D.4 forbids reselling the Services; the terms forbid using Outputs to train a competing model — we do not train anything | **publishable**, with the accuracy notice of section D.3 carried in the data-package README |
| **OpenAI** (`gpt-5.6-terra`, optional `gpt-5.6-sol`) | subject | Business terms: the customer owns Output | no clause found restricting publication; disclosure of AI generation is encouraged | forbids using Output to develop competing models | **publishable**, with an AI-generation notice on the package |
| **DeepSeek** (`deepseek-v4-pro`) — **surface: OpenRouter, provider pinned `deepseek` (DeepSeek's own endpoint), `allow_fallbacks: false`, wire model `deepseek/deepseek-v4-pro-0813` (R54, 2026-08-25; the R38 smoke and all development-era calls used first-party `api.deepseek.com`)** | subject | two layers: OpenRouter ToS (2026-07-29) §6.1 has the user retain ownership of Input and §5.1 defers to the Model Provider's terms ("it is your responsibility to review the Model Terms"); the pinned provider is DeepSeek itself, whose Open Platform Terms (read 2026-08-24) assign rights in Outputs to the user and name academic research among permitted uses. **Named residual:** OpenRouter's per-endpoint Model-Terms designation is client-rendered on the model page and was not separately captured (no browser session available at verification time); on any reading, the pinned upstream party is DeepSeek and its own API terms are the operative upstream instrument | explicitly permissive at both layers, including for research | **Input-side layer, material for a subject (full transcripts transit the intermediary):** ToS §6.2 makes prompt/chat logging **opt-in** (the study does not opt in); §6.3(b) grants OpenRouter a processing-only license and bars access "except as necessary to operate, secure, or troubleshoot". **Observed live 2026-08-25:** OpenRouter's data-policy machinery classifies the pinned DeepSeek endpoint as a may-train provider (a no-training account policy filters it out with a 404 — the probe that found the R54 routing gate), consistent with DeepSeek's own terms; this is the same input exposure the study accepted when billing `api.deepseek.com` directly. Model IP stays DeepSeek's; we publish no model artefacts. The no-third-party-host guarantee is documented routing (`only` + `allow_fallbacks: false`) **and observed per run**: `served_model`/`served_provider` are persisted in `run.json` and the smoke gates on the echo | **publishable (two-layer)** — upstream read 2026-08-24, OpenRouter output + input layers read 2026-08-25, with the Model-Terms-designation residual for Grant's sign-off |
| **local Qwen 3.8 27B** | subject | local weights, no API terms in play | n/a | the checkpoint digest is recorded, the weights are not redistributed | **publishable** |
| **local Gemma 4 31B** (`gemma4-31b-it`, R57 Part B exploratory seat) | subject (exploratory) | Gemma Terms of Use (last modified 2026-04-01, read 2026-08-25): "Google claims no rights in Outputs you generate using Gemma. You and your users are solely responsible for Outputs and their subsequent uses" | no restriction found on publishing outputs; the Prohibited Use Policy is incorporated by reference and the study's use is plainly outside it | the terms' distribution obligations (use-restriction flow-down, notice file) attach to distributing **the model or derivatives**, which this study never does — outputs only; checkpoint digest recorded, weights not redistributed | **publishable** |
| **local Muse Glimmer 30B** (`muse-glimmer-30b`, Meta Superintelligence Labs, released 2026-08-09; the seated R46 Part B exploratory arm) | subject (exploratory) | local weights, no API terms in play. The model ships **verbatim, unmodified Apache License 2.0** — the licence text was read in full and retained at Hugging Face `meta-models/Muse-Glimmer-30B-GGUF` revision `43c7eadd41352a299ea8e0a36b3157978dd63596` (11,358 B, sha256 `cfc7749b96f63bd3…`) — and an Apache 2.0 grant licenses the Work and its derivative works and **carries no output clause at all**: nothing is claimed in model output and nothing is assigned out of it | n/a — there is no publication clause in an Apache 2.0 grant to restrict one | a separate `USAGE_POLICY.md` (5,230 B) ships beside the licence with an 18+ and prohibited-use list (military, nuclear, espionage); the two documents do not reference each other, and the study's use is plainly outside the list. Both checkpoint digests (main and the speculative drafter) are recorded in `docs/review/step7-2026-08-25/MODEL_SNAPSHOTS.md`; the weights are not redistributed | **publishable** — licence read 2026-08-26 |
| **local Granite 4.1 30B** (`granite4.1:30b`, **IBM** — the R56 replacement candidate that ran the free entrance and probe gate and was not seated) | entrance-gate candidate, never seated | local weights, no API terms in play. The licence layer distributed with the exact model the study loaded is the **Apache License 2.0**: ollama `registry.ollama.ai/library/granite4.1:30b`, licence layer sha256 `58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd` (11,357 B), read 2026-08-26. Same shape as the muse row — no output clause | n/a | the gate outcome is published as a finding, with the full candidate record in the `entrance-granite` and `probe-f2-granite` batches under `evals/runners/stage1/results/stage1/` and model prose quoted in `evals/runners/stage1/ENTRANCE_GRANITE.md`; weights not redistributed | **publishable** — licence read 2026-08-26 |
| **local Mistral Small 4** (`mistral-small-4`, the R56-dropped Part B exploratory arm; the Mistral API row below governs the classifier and judge surface, not this one) | subject (exploratory), dropped before the freeze | local weights, no API terms in play. **Apache 2.0**, recorded against the base model `mistralai/Mistral-Small-4-119B-2603` and the served quantisation `unsloth/Mistral-Small-4-119B-2603-GGUF` @ `bd93c721735aa32c035c0f19e738cb3371fd56ff`. **Stated at its true strength:** this is a licence *field* in the dated operator spec card for the endpoint (read 2026-08-26), not a licence text this project retained and hashed as it did for muse and granite. The verdict does not turn on the difference — an Apache 2.0 grant has no output clause either way — but the evidence is weaker and the row says so | n/a | the arm was dropped under R56 and its failure is published; seven committed development run directories remain under `evals/runners/stage1/results/stage1/`, and the shard digests are in `MODEL_SNAPSHOTS.md`; weights not redistributed | **publishable** — licence recorded 2026-08-26 |
| **Mistral** (`mistral-medium-2604`, classifier and seated primary judge — judge role pending the instrument-closure lane, `PILOT_PROTOCOL.md` §6a) | instrument | Commercial terms: the customer owns Output and Mistral claims no copyright in it | permissive; the redistribution restriction applies to third-party **web-search** content, which this study never uses | | **publishable** (one-word verdicts) |
| **MiniMax via OpenRouter** (`minimax-m3`, seated secondary judge under branch 3's descriptive scope) | instrument | OpenRouter ToS (2026-07-29): "Your ownership rights in the Output are set forth in the Model Terms" — full deferral upstream; the operative MiniMax Community License for M3 (MiniMaxAI HF org) contains **no output clause at all** (no ownership claim, no publication restriction; its "Built with MiniMax M3" duty binds commercial deployers of the weights, not API consumers); MiniMax's own Open Platform ToS (effective 2026-03-30, **read first-party in a real browser 2026-08-25** — the page is JS-walled to fetchers): "you retain your ownership rights in Client input and generated content" | no restriction found on either layer | OpenRouter's endpoint listing shows M3 served by 13 providers incl. MiniMax's own fp8 endpoint, so both layers were checked | **publishable** (one-word verdicts) — **verified 2026-08-25** |
| **Google** (`gemini-3.7-flash`) — **surface: OpenRouter, provider pinned `google-vertex`, `allow_fallbacks: false`** (the committed lane driver `docs/review/judge-validation/instrument-closure-lane/run_labels.py`; an earlier step-7 draft of this row wrongly said "via the Gemini API" — corrected on Grok's cross-family review) | validation labeller | two layers, like MiniMax: OpenRouter ToS defers output ownership to the upstream Model Terms; because the pin is `google-vertex`, the governing upstream instrument is the **Google Cloud Service Specific Terms**, section 20 (Generative AI Services), **read first-party 2026-08-26** (https://cloud.google.com/terms/service-terms): Generated Output is **Customer Data**, and Google "does not assert any ownership rights" in it. The **Gemini API Additional ToS** (effective 2026-03-23, read 2026-08-25) reads the same way on Google's other surface: "Google won't claim ownership over that content" | no publication restriction at either layer; Grounded-Results bans inapplicable (no grounding) | **the residual is CLOSED (2026-08-26).** The unread document named in the step-7 draft of this row has now been read. General Service Terms section 7 (Benchmarking) does not bite either: the study publishes no performance claim about the Google service. Fallback 3 is not invoked for this row | **publishable (two-layer)** — OpenRouter and Gemini layers verified 2026-08-25, the governing Vertex terms read 2026-08-26; **no residual** |
| **xAI** (`grok-4.6`) — **three committed surfaces**: judge-candidate runs via `api.x.ai` (`run_qualification.py`, `XAI_API_KEY`); lane labels via **OpenRouter pinned `xai`** (`run_labels.py`); and the **Grok CLI on an xAI consumer subscription**, which authored the 40 Part B fresh scenario packets and several committed reviews (the row said "two" until the 2026-08-26 scope check that also corrected the Moonshot row) | validation labeller + measured-and-disqualified judge candidate + Part B scenario author | Enterprise ToS (updated 2026-08-14, **read first-party in a real browser** — x.ai 403s automated fetchers): customer "owns all right, title, and interest in the Output in perpetuity", with an express assignment — this governs the `api.x.ai` content directly and is the upstream layer OpenRouter's deferral points at for the pinned `xai` route. The **consumer ToS** governs the CLI surface (read 2026-08-26 through indexed copies of the first-party page): the user owns Inputs and Outputs and is free to use Outputs as they wish, including commercially | no restriction on publishing outputs on any of the three surfaces | AUP bars using outputs to develop competing models — the study trains nothing; the consumer terms *ask* that Output be attributed to Grok per xAI's Brand Guidelines, which the package's per-item model attribution and `NOTICE` already do | **publishable (all three surfaces)** — **`api.x.ai` and OpenRouter verified 2026-08-25, the consumer CLI surface 2026-08-26** |
| **Z.ai** (`glm-5.3`) — **surface: OpenRouter, provider pinned `z-ai`** (`run_labels.py`; **no committed runner uses a first-party Z.ai URL** — an earlier step-7 draft of this row implied one) | validation labeller | two layers: OpenRouter deferral upstream; the upstream document read first-party is the Z.ai Terms of Use + API Additional Terms (updated 2026-04-14): no Z.ai ownership claim over End User Content | permitted as read, with the AI-marking duty (per-item model attribution satisfies it) | **§1.f.xii, ruled by Grant 2026-08-26:** the clause bars using GLM outputs "for development, training, **labeling**, fine-tuning or optimization related to external models". Narrow reading (taken by this page): it bars reusing the labels to train/tune other models — the study does none of that. Broad reading: the study's own use of GLM labels to *validate an instrument for evaluating other models* could itself be the forbidden act. **The ruling publishes the per-item GLM-5.3 labels under a use-restricted licence** — carved out of both the MIT and the CC BY 4.0 grants, declared as `LicenseRef-AgencyLayer-GLM-Labels-1.0` in the root `NOTICE`, explicitly permitting verification and reproduction and granting no licence for development, training, labelling, fine-tuning or optimization related to external models. **Counts-only (fallback 3) was considered and not taken**, for two reasons measured on the files: `freeze-qualification/qualify_freeze.py` names `glm-5.3` in `LABELLERS` and rebuilds the 248-item gold (177 unanimous + 71 adjudicated) in memory from the per-item panel files, so withholding the GLM column would break `QUALIFICATION_TABLE.md`'s promise that "every figure below is reproducible with `python3 qualify_freeze.py`" and, with it, the panel pairwise range 0.89 to 0.94 at disclosure 20; and it would not in fact withhold, because `gold_provenance.jsonl` publishes `l1_source` per item and 375 of the 461 L1 items are `unanimous`, so GLM's answer on 81% of the column is recoverable from the published gold. Fallback 3 stays available and is not invoked | **publishable with the attribution mark, the §1.f.xii notice, and the per-item carve-out licence (Grant's ruling, 2026-08-26)** — verified 2026-08-25 |
| **Moonshot** (`kimi-k3`) — **two committed surfaces**: the Open Platform API (`api.moonshot.ai`) and the **Kimi Code consumer subscription** (`api.kimi.com`, membership OAuth) | validation labeller and judge candidate (API) + scenario author, certifier and panel labeller (Kimi Code subscription) | **API surface:** OpenPlatform API ToS (updated 2026-07-30): no ownership claim over content, no publication restriction (keep AI-content marks). The **judge runs and their per-item answer files** were billed to `api.moonshot.ai` (r38 + freeze-qualification run configs; the committed answer rows are `id`/`parsed`/`raw`), so those labels are API-surface. The `git ls-files` re-check of 2026-08-26 corrected the step-7 claim that *every* committed label came from the API: five classes of committed artifact came from headless **Kimi Code** sessions instead — the Part B certification and spot-check prose, the committee round-1 review, two validation-panel label files, a Codex-adapter fix, and the 45 Part A scenario packets (enumerated below the table). **Consumer surface, read first-party 2026-08-26:** the live instrument is the **Kimi AI Terms of Service of NOVASCENT PRIVATE LIMITED (Singapore, doing business as Moonshot AI), effective 2026-08-13** — "you retain ownership of your Input and own the Output. We hereby assign to you all of our right, title, and interest, if any, in and to the Output" — with no non-commercial cap and no personal-research restriction. The PRC instrument current alongside it (Kimi 用户服务协议, Beijing entity, effective **2026-08-31**) vests the rights in Input and Output in the user the same way | no clause found restricting publication or redistribution of Output on either surface; the API ToS's AI-content marks are preserved by the package's per-item model attribution | **The version history, recorded because this row was wrong once and the correction belongs to the record.** (1) At step 7 (2026-08-24/25) the page read `https://www.kimi.com/user/agreement/modelUse` and recorded from it a cap at non-commercial personal research plus a bar on commercialised use of generated content. (2) On the strength of that reading, the first of Grant's 2026-08-26 rulings carved six Kimi Code evidence files out of both grants, and the scope check that implemented it then found the 45 Part A scenario packets on the same surface and left them open. (3) **That document is not the live instrument.** It is the 模型服务协议 / Model Service Agreement of Beijing Moonshot, **effective 2024-01-05**, and the undecorated `modelUse` path still serves it — re-read 2026-08-26 in Chinese at `https://www.kimi.com/user/agreement/modelUse` and in English at `https://www.kimi.ai/user/agreement/modelUse`, which is how a superseded page was mistaken for a current one. The agreement the Kimi site footer points at is the Singapore ToS of 2026-08-13 above. (4) Every Kimi Code artifact in this package was generated **after** that effective date: the committee review on 2026-08-22, the scenario packets on 2026-08-22 and 2026-08-23, the two panel label files on 2026-08-23, and the certification and spot-check prose on 2026-08-25. The 2024 cap never attached to any of it. Also recorded for completeness: the K3 local-checkpoint license (Moonshot's own, HF-hosted) is silent on outputs entirely, and the Singapore ToS bars using the Services or Output to develop a competing model — the study trains nothing | **publishable on both surfaces, no carve-out — Grant's ruling of 2026-08-26, reversing his own earlier Kimi carve-out once the live instrument was read.** The six Kimi Code evidence files, the Codex-adapter fix and the 45 Part A scenario packets publish under the ordinary package grants (CC BY 4.0 for materials, MIT for code) and go into the Zenodo deposit with everything else; the Kimi section drafted as `NOTICE` 4.1 is **deleted** — **API surface verified 2026-08-25; consumer surface corrected and re-verified 2026-08-26** |
| **Meta** (`llama-4-maverick`) — **surface: OpenRouter, no provider pin** (wire model `meta-llama/llama-4-maverick`, `OPENROUTER_API_KEY`; the root `NOTICE` is the committed record of the route, and **no committed runner made these calls** — the lane's staging `run_freeze_nonthinkers.py` did, tied to the artifacts by its four output files being byte-identical to the committed ones, and it passes no `provider` block at all) | measured-and-rejected judge candidate | two layers, like MiniMax: OpenRouter ToS defers ownership to the Model Terms, and the model-level instrument is the **Llama 4 Community License** (read 2026-08-26), which — again like the MiniMax Community License — carries **no output clause at all**: "Llama Materials" is defined as "Meta's proprietary Llama 4 and Documentation (and any portion thereof)", and the licence's own disclaimer names "THE LLAMA MATERIALS **AND** ANY OUTPUT AND RESULTS THEREFROM" as two things, so outputs sit outside the licensed subject matter and no assignment runs in either direction | no restriction found in the licence, and none in the Llama 4 Acceptable Use Policy (read 2026-08-26) | **clause 1.b.i is distribution-triggered and does not reach this package:** the "Built with Llama" and copy-of-the-agreement duties bind whoever "distribute[s] or make[s] available the Llama Materials (or any derivative works thereof), or a product or service (including another AI model) that contains any of them", and the "Llama"-prefix naming duty binds whoever uses outputs "to create, train, fine tune, or otherwise improve an AI model, **which is distributed or made available**" — the study distributes no weights, no derivative and no model, so no NOTICE duty arises. **Named residual, and it is the thing the evidence cannot show:** unpinned, the serving host was one of the several OpenRouter lists for this model (read 2026-08-26: DigitalOcean, DeepInfra, Novita, Parasail, Google Vertex), the answer rows persist only `id`/`parsed`/`raw` with no `served_provider` echo of the kind the R54 subject arm now keeps, and no artifact records which host answered any of the 496 calls — so the host layer cannot be named, only the model licence common to all of them | **publishable (two-layer), no carve-out and no NOTICE duty.** Covers the 496 one-word verdicts in `judge_answers/llama-4-maverick_pass{1,2}.jsonl` (211 `qualifying` and 37 `not_qualifying` in each pass, no abstentions, nothing unparseable) — **verified 2026-08-26**, with the unidentified serving host recorded above for Grant |
| **Cohere** (`command-a`) — **surface: OpenRouter, no provider pin** (wire model `cohere/command-a`, same uncommitted staging runner, same byte-identical outputs). Here the missing pin costs nothing: OpenRouter's endpoint listing for this model (read 2026-08-26) shows **one** serving provider, `cohere` — Cohere's own endpoint — so the upstream party is determinate even though the route was unpinned | measured-and-rejected judge candidate | two layers, and the upstream layer is the one place on this page where the answer is **no**. OpenRouter defers ownership to the Model Terms as usual; Cohere's **SaaS Agreement** (read 2026-08-26) defines "Output" as "any data, information, content, or records that are created or generated from a Baseline Model or Custom Model" and then **never assigns it to anyone**. §3(a) gives the customer ownership of *Customer Data*, defined as what the customer "loads, submits, transmits to or enters into" the service — inputs, not outputs — and §3(c) reserves everything Cohere delivers. No other row on this page rests on an instrument that defines Output and then neither assigns it nor disclaims a claim over it — the Meta row's silence is the other kind, an instrument with no output clause at all | **restricted, and this is the finding.** SaaS Agreement §2(d)(ii): the customer will not "access or use the Services or Cohere Products, **use any Output**, or develop a Customer Application … (iii) for the purpose of **benchmarking or conducting competitive analysis** of the Services or Cohere Products". Cohere's Terms of Use (read 2026-08-26) says it twice more: the preamble's "YOU MAY NOT ACCESS THE COHERE SOLUTION … FOR ANY OTHER BENCHMARKING OR COMPETITIVE PURPOSES", and §14(17)'s bar on "publish, market, advertise or in any way distribute the Content", where §14(12) reaches "any Content that You receive through or from the Cohere Solution". The two instruments agree, so nothing turns on which of them governs | what the clause names is what the study did and published: 248 items over two passes, scored against the gold panel and printed as a ranked row in `QUALIFICATION_TABLE.md` (agreement 0.7379, kappa 0.313, stability 0.9960, seven abstentions, meets standard **NO**) and again in `PILOT_PROTOCOL.md` §6 — a performance claim about a Cohere product. This is the same clause type the Google row could dismiss because the study makes no performance claim about that service; here it does. **The second fact for the reading, not a resolution:** the study was never Cohere's customer — no `COHERE_API_KEY` appears anywhere in this repository and `BUDGET.md` carries no Cohere line; OpenRouter is the Cohere customer, and OpenRouter's ToS §5.1 is what puts the upstream Model Terms on the study ("it is your responsibility to review the Model Terms"), so whether Cohere's restriction binds a downstream OpenRouter user is itself an open reading | **Ruled by Grant, 2026-08-26: the published result stays, the raw file is carved out.** The restriction lands on the *measurement*, not only on the per-item files, so **neither registered fallback answers it**: fallback 3 withholds per-item labels and keeps the agreement statistics, and the agreement statistics are the benchmark; fallback 2 keeps counts and rates and has the same shape. Withdrawing the row was the zero-risk move and was rejected: a *regenerable negative* is not withdrawn because a vendor's terms dislike negatives, and the arithmetic cost of withdrawal being near zero is exactly what made it a decision about the record rather than about the science — `command-a` is a rejected candidate that no seated instrument, no endpoint and no gold label depends on (the gold set's labellers are Gemini, Grok and GLM; branch 3 never scored it). **So the row and its numbers stay** — in `QUALIFICATION_TABLE.md`, in `PILOT_PROTOCOL.md` §6 and in `CANDIDATES` in `qualify_freeze.py` (agreement 0.7379, kappa 0.313, stability 0.9960, seven abstentions, meets standard **NO**) — **and the 496 per-item verdicts in `judge_answers/command-a_pass{1,2}.jsonl` are carved out of both the MIT and the CC BY 4.0 grants**, declared `LicenseRef-AgencyLayer-Cohere-Answers-1.0` in the root `NOTICE` on the same pattern as the GLM labels: verification and reproduction expressly permitted, no licence granted for benchmarking or competitive analysis of Cohere's services or products. That carve-out is what stops a package-wide CC BY grant conveying rights in Output the SaaS Agreement assigned to nobody; the `NOTICE` also names the clause, the OpenRouter route, and the fact that OpenRouter — not this study — was Cohere's customer. **What was measured, stated plainly, because it is the accurate description of the artifact:** this study makes no claim about `command-a`'s general fitness, and none about Cohere's products. It measured fitness for one specific task — serving as a blinded judge on this study's rubric — and reports that the model did not meet the standard the study had written down in advance, as several larger frontier models also did not — **terms read 2026-08-26; ruled 2026-08-26** |
| **OpenAI — ChatGPT/Codex subscription surface** (`gpt-5.6-sol` driven by the Codex CLI on a ChatGPT plan; no API key and no metered spend, which is why step 7 read only the business terms above) | lane adjudicator and blind labeller | consumer **Terms of Use**, "Ownership of content", read 2026-08-26 (openai.com returns 403 to automated fetches, so read through indexed copies of the first-party page, as for the business terms row): "you (a) retain your ownership rights in Input and (b) own the Output. OpenAI hereby assigns to you all its right, title, and interest, if any, in and to Output" | no clause found restricting publication, redistribution or commercial reuse of Output | "What you cannot do" bars representing Output as human-generated when it is not — the package's AI-generation notice satisfies it — and bars using Output to develop models that compete with OpenAI; the study trains nothing | **publishable, no carve-out.** Covers the 638 blind lane answers in `docs/review/judge-validation/instrument-closure-lane/sol_answers/` (86 + 48 + 20 + 20 + 393 + 71 rows), the 461-item lane gold they decide (the L2 track throughout, and 86 adjudicated items of the L1 track, whose other 375 are unanimous), `docs/review/judge-validation/labels/sol.jsonl` (80 rows) and `docs/review/classifier/labels_pm15/sol.jsonl` (36 rows) — **verified 2026-08-26** |
| **Anthropic — Claude Code subscription surface** (the sessions that ran the study; no API key and no metered spend, which is why step 7 read only the commercial terms above) | freeze-gold adjudicator and blind labeller | **Consumer Terms of Service** (effective 2025-10-08, read first-party 2026-08-26): "Subject to your compliance with our Terms, we assign to you all of our right, title, and interest—if any—in Outputs" | no clause found restricting publication, redistribution or commercial reuse of Outputs | the same competing-model and no-resale bars as the commercial row; the accuracy caution ("Outputs may not always be accurate and may contain material inaccuracies even if they appear accurate") is the consumer-side twin of the section D.3 notice the package already carries | **publishable, no carve-out.** Covers the 91 freeze-gold adjudications (`docs/review/judge-validation/freeze-qualification/adjudications.jsonl`) and `docs/review/judge-validation/labels/fable.jsonl` (80 rows) — **verified 2026-08-26** |

### The Kimi Code subscription surface, enumerated (2026-08-26)

The inventory is kept even though the carve-out it was built for is gone: it is the record of which
committed artifacts came from this surface, and the next re-check at launch starts from it. Every item
below was matched to a staging run log whose first line is `kimi version 0.34.0`, and the committed file
was compared with the run's own output.

**Review and panel output** (verbatim Kimi Code session output, committed as research evidence):
`docs/review/part-b-scenarios/CERTIFICATION_KIMI_2026-08-25.md`,
`docs/review/part-b-scenarios/CERTIFICATION_KIMI_2026-08-25_v2.md`,
`docs/review/part-b-scenarios/SPOTCHECK_KIMI_2026-08-25.md` (the file the `CERTIFICATION_KIMI_*.md` glob
missed; it is a raw session transcript and opens with the version banner),
`committee/round-1/ROUND1_KIMI.md` (byte-identical to the run's output file),
`docs/review/judge-validation/labels/kimi.jsonl` and `docs/review/classifier/labels_pm15/kimi.jsonl`
(the two panel label files the corrected Moonshot row names).

**Study materials:** the **Part A scenario packets**. All 45 committed packets under `evals/scenarios/`
have a Kimi Code staging counterpart of the same id (families 1 to 8 drafted 2026-08-22, family 9 on
2026-08-23), and 281 of the 361 committed files in them are byte-identical to the draft the session
wrote; the differences are small later edits. A committed fix to the Codex adapter was written on the
same surface.

**All of it publishes under the ordinary package grants**, and all of it goes into the Zenodo deposit.
When this inventory was assembled the page still cited the superseded 2024 consumer agreement, so the
review prose was carved out of both grants and the 45 packets were left as an open question to Grant —
a question that only existed because of the wrong instrument. On the live Singapore terms of 2026-08-13
(Moonshot row) the Output is the user's, the carve-out is withdrawn, and the packets stay in the deposit
where the study's stimuli belong. Nothing on this surface is excepted from MIT or CC BY 4.0.

## Fallbacks, stated before dispatch as F11 requires

1. **If a provider's terms forbid publishing full transcripts**, that provider's arm is published as
   excerpts: the blinded projection through the stop turn, the affordance field values, the STATUS
   line, and the graded outcome, with the full transcript held and available to a reviewer on request.
   The endpoint values do not change, because every endpoint is computed from the blinded projection and
   the scenario check, not from the raw text.
2. **If a provider's terms forbid publishing any output**, that arm is reported as counts and rates
   only, its raw artifacts are withheld, and the withholding is named in the results README and in the
   OSF record. No arm is silently dropped.
3. **If a labeller's terms forbid publishing per-item labels**, the validation tables publish agreement
   statistics and confusion matrices only, that labeller's per-item label files are withheld from the
   package, and the withholding is named in the results README and in the OSF record. The remedy has to
   be the label files themselves: the instrument-closure lane's label rows are `parsed`/`raw`/
   `request_id` and carry no notes, so an earlier drafting of this fallback, which withheld "per-item
   notes", would have withheld nothing (corrected 2026-08-26). Where the withheld column is an input to
   a published table, say so: the table stops being regenerable, which is the cost of this fallback.
4. **Personal data and secrets:** the fixtures are synthetic and contain no personal data. The
   secret-and-PII scan in `DATA_MANAGEMENT.md` runs over every publishable package before release, and
   any hit is redacted with a placeholder plus a note in the package.

## Still owed before recorded dispatch

- [x] Verify MiniMax's model terms for the OpenRouter-served endpoint — **done 2026-08-25**,
      both layers (OpenRouter deferral + M3 Community License + MiniMax Open Platform ToS read
      first-party in a browser).
- [x] Verify the four validation-labeller providers' terms — **done 2026-08-25, corrected the
      same day on Grok's cross-family review**: the Gemini/Grok/GLM lane labels were produced
      through **OpenRouter with per-provider pins** (`run_labels.py`, the committed driver), not
      the first-party APIs an earlier draft of this page claimed; the rows above now describe
      the two-layer contract that actually applies (OpenRouter deferral + the upstream document
      read). Moonshot (`api.moonshot.ai`) and the xAI judge-candidate runs (`api.x.ai`) are the
      genuinely first-party surfaces, verified against the committed run configs. The two items
      that rode into Grant's sign-off are now closed, both on 2026-08-26: the Google Vertex terms
      were read first-party (no residual) and Grant ruled the Z.ai §1.f.xii reading.
- [x] **Grant's three terms rulings, 2026-08-26, implemented on this page and in the root
      `NOTICE`:** (1) the Kimi-Code-surface files publish with a per-file carve-out from **both**
      the MIT grant and the CC BY 4.0 grant, stay in the GitHub repository and are excluded from
      the single-licence Zenodo deposit; (2) the Google Vertex residual closes on the first-party
      reading of the Service Specific Terms; (3) the per-item GLM-5.3 labels publish under
      `LicenseRef-AgencyLayer-GLM-Labels-1.0`, which permits verification and reproduction
      explicitly and grants no licence for development, training, labelling, fine-tuning or
      optimization related to external models. The licences themselves do not change: code MIT,
      data CC BY 4.0, with the exceptions listed in `NOTICE`.
      **Ruling (1) was REVERSED later the same day** — see the next item. (2) and (3) stand.
- [x] **CLOSED 2026-08-26 by Grant's reversal of the Kimi carve-out** (the outside seat, Grok 4.6,
      reached the same answer independently): the carve-out rested on the **2024** consumer Kimi
      Model Service Agreement, which is not the live instrument. The agreement the Kimi footer
      points at is the **Kimi AI Terms of Service of NOVASCENT PRIVATE LIMITED (Singapore),
      effective 2026-08-13**, which assigns the user all right, title and interest in the Output
      with no non-commercial cap; the PRC instrument effective 2026-08-31 vests Input and Output
      rights in the user the same way; and Grant's Kimi Code client runs against `api.kimi.com`
      on a membership OAuth login, the consumer family that footer instrument governs. Every
      Kimi Code artifact here was generated between 2026-08-22 and 2026-08-25, after the Singapore
      terms took effect. **So the open question about the 45 Part A scenario packets is closed by
      the ruling, not by a carve-out:** the packets were never exposed, they publish under CC BY
      4.0 with the rest of the study's materials, and they stay in the Zenodo deposit. The six
      Kimi Code evidence files and the Codex-adapter fix publish under the ordinary grants too,
      `NOTICE` section 4.1 as first drafted is deleted, and the Moonshot row carries the
      2024 → 2026 version history so the record shows what was read, when, and what superseded it.
- [x] **The two API-served judge candidates now have rows — written 2026-08-26.** The route was
      established from the committed side before any terms page was opened: the root `NOTICE`
      records both as run through OpenRouter, the answer rows carry only `id`/`parsed`/`raw`, and
      **no committed runner made these calls** — the lane's staging `run_freeze_nonthinkers.py`
      did, tied to the artifacts by its four output files being byte-identical to the committed
      ones, and it passes no `provider` block, so both routes were unpinned. For **Cohere** that
      costs nothing (one serving provider, Cohere itself); for **Meta** it means the serving host
      is not recoverable from the artifacts, which the row names as a residual. Meta's upstream
      instrument reads clean. Cohere's does not, and is the next item.
- [x] **CLOSED 2026-08-26 by Grant's Cohere ruling: keep the published result, carve the raw
      file** (the outside seat, Grok 4.6, reached the same answer independently). The SaaS
      Agreement §2(d)(ii)(iii) and the Terms of Use both bar using Output "for the purpose of
      benchmarking or conducting competitive analysis" of Cohere products, and the SaaS Agreement
      assigns Output to nobody — so the restriction reaches the qualification table and not only
      the per-item files, and neither fallback 2 nor fallback 3 cures it. The ruling does not
      withdraw the row: a negative result that regenerates from committed code is not deleted
      because a vendor's terms dislike negatives. The `command-a` numbers stay in
      `QUALIFICATION_TABLE.md`, `PILOT_PROTOCOL.md` §6 and `CANDIDATES` in `qualify_freeze.py`.
      What changes is the grant over the raw evidence: the two per-item answer files are excepted
      from **both** the MIT and the CC BY 4.0 grants as
      `LicenseRef-AgencyLayer-Cohere-Answers-1.0` — verification and reproduction expressly
      permitted, no licence for benchmarking or competitive analysis — and `NOTICE` names the
      clause, the OpenRouter route and the fact that OpenRouter, not the study, was Cohere's
      customer. The Cohere row above records the ruling and states what the study actually
      measured and claims.
- [x] **The three local checkpoints now have rows — written 2026-08-26**, closing the last
      completeness gap the scope check found. `muse-glimmer-30b`, `granite4.1:30b` and
      `mistral-small-4` are all **Apache 2.0**, which licenses the model and its derivative works
      and contains no output clause at all, so outputs are unencumbered and the rows follow the
      local-Qwen and local-Gemma pattern: no API terms in play, digests recorded, weights never
      redistributed. Evidence strength differs and each row says which it has — muse's licence
      text was read in full and hashed (11,358 B, sha256 `cfc7749b96f63bd3…`), granite's licence
      layer ships inside the pulled model (sha256 `58d1e17f…`, 11,357 B, read here), and
      mistral-small-4's is a licence field in the dated operator spec card rather than a retained
      text.
- [x] Grant reads and signs this page; the signature line goes in `FREEZE_CHECKLIST.md`. **Signed off
      by Grant, 2026-08-27**, on the basis of the freeze-sitting page's summary of this document
      rather than a line-by-line reading of the page itself; the box of record, with the five rulings
      it carries and the terms of the signature, is `FREEZE_CHECKLIST.md` §E.
- [ ] Re-check every row at launch (F11 requires the re-check, because terms change).

## Package NOTICE obligations collected from the verified terms (step 7, extended 2026-08-26)

All of these are carried by the repository's root `NOTICE`, written 2026-08-26; this list is the
record of where each one comes from.

1. Anthropic accuracy notice (section D.3) — already required above.
2. OpenAI AI-generation notice — already required above.
3. Per-item model attribution on every validation label (satisfies Google's
   not-solely-human rule, Z.ai's AI-marking duty, and Moonshot's mark-preservation rule at once);
   it also answers the attribution xAI's consumer terms ask for on the Grok CLI surface.
4. Z.ai §1.f.xii sentence: "Z.ai's API terms prohibit customers from using GLM outputs for
   external-model development, training or labeling; the GLM-5.3 labels in these tables were used
   for instrument validation only and must not be reused by Z.ai customers for those purposes."
5. Cohere's restriction, disclosed beside the other provider notices: the SaaS Agreement
   §2(d)(ii)(iii) bar on using Output "for the purpose of benchmarking or conducting competitive
   analysis", the Terms of Use bars that repeat it, the OpenRouter route, and the fact that
   OpenRouter — not this study — was Cohere's customer.
6. The carve-out exception list, by exact path, each entry with its own grant: the per-item
   GLM-5.3 label files under `LicenseRef-AgencyLayer-GLM-Labels-1.0`, and the two per-item
   `command-a` judge-answer files under `LicenseRef-AgencyLayer-Cohere-Answers-1.0`. Both
   carve-outs come out of the MIT grant and the CC BY 4.0 grant alike, and both grants of use
   permit verification and reproduction explicitly. **There is no Kimi entry:** the
   Kimi-Code-surface carve-out drafted earlier the same day was withdrawn once the live consumer
   instrument was read (Moonshot row).

*Sources read 2026-08-24: Anthropic Commercial Terms
(https://www.anthropic.com/legal/commercial-terms); OpenAI business terms as summarised by public
trackers, first-party page returns 403 to automated fetches (https://openai.com/policies/services-agreement/);
DeepSeek Open Platform Terms of Service
(https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html); Mistral AI
commercial terms and help centre (https://legal.mistral.ai/terms/commercial-terms-of-service,
https://help.mistral.ai/en/articles/156203-who-owns-api-inputs-and-outputs).*

*Sources read 2026-08-25 (step 7, and the R54 DeepSeek-surface addendum the same day): OpenRouter
ToS (https://openrouter.ai/terms, last updated 2026-07-29) and endpoint listings
(https://openrouter.ai/api/v1/models/minimax/minimax-m3/endpoints;
https://openrouter.ai/api/v1/models/deepseek/deepseek-v4-pro-0813/endpoints for the R54 subject
row — the OpenRouter layer defers output ownership upstream exactly as in the MiniMax analysis,
and the pinned upstream is DeepSeek's own endpoint under the Open Platform Terms already read
2026-08-24);
MiniMax Community License for M3 (https://huggingface.co/MiniMaxAI/MiniMax-M3/raw/main/LICENSE),
MiniMax unified ToS (https://www.minimax.io/terms-of-service-v2.html, updated 2026-04-15), MiniMax
Open Platform ToS (https://platform.minimax.io/protocol/terms-of-service, effective 2026-03-30 —
JS-walled, read first-party in a real browser); Gemini API Additional Terms
(https://ai.google.dev/gemini-api/terms, effective 2026-03-23) and the Generative AI Prohibited Use
Policy (https://policies.google.com/terms/generative-ai/use-policy); Gemma Terms of Use
(https://ai.google.dev/gemma/terms, last modified 2026-04-01, read 2026-08-25 for the R57 seat);
xAI Enterprise ToS
(https://x.ai/legal/terms-of-service-enterprise, last updated 2026-08-14 — 403 to fetchers, read
first-party in a real browser), consumer ToS and legal FAQ (https://x.ai/legal/terms-of-service,
https://x.ai/legal/faq, via indexed copies of the first-party pages) and AUP
(https://x.ai/legal/acceptable-use-policy); Z.ai Terms of Use with the API Additional Terms
(https://docs.z.ai/legal-agreement/terms-of-use, updated 2026-04-14); Moonshot OpenPlatform ToS
(https://platform.kimi.ai/docs/agreement/modeluse, updated 2026-07-30), consumer Kimi Model Service
Agreement (https://www.kimi.com/user/agreement/modelUse, PRC entity, served in Chinese —
**superseded; see the 2026-08-26 block below, which is the reading this page now relies on**), and
the Kimi K3 License (https://huggingface.co/moonshotai/Kimi-K3/raw/main/LICENSE).*

*Sources read 2026-08-26 (the freeze sitting: the Vertex residual, and the two subscription surfaces
step 7 never examined): Google Cloud Service Specific Terms, section 20, Generative AI Services
(https://cloud.google.com/terms/service-terms) — read first-party at the sitting; note for a verifier
that an automated fetch of that page truncates well before section 20, so it has to be read in a
browser. OpenAI consumer Terms of Use, "Ownership of content" and "What you cannot do"
(https://openai.com/policies/terms-of-use/ and its regional twin
https://openai.com/policies/row-terms-of-use/) — the first-party pages return 403 to automated
fetches, as with the business terms, so both were read through indexed copies. Anthropic Consumer
Terms of Service, effective 2025-10-08 (https://www.anthropic.com/legal/consumer-terms) — read
first-party. xAI consumer Terms of Service and legal FAQ (https://x.ai/legal/terms-of-service,
https://x.ai/legal/faq), re-read through indexed copies for the third committed xAI surface.*

*Sources read 2026-08-26 for the two judge-candidate rows the same sitting's scope check turned up:
Llama 4 Community License and Llama 4 Acceptable Use Policy
(https://developer.meta.com/ai/llama4/license/, https://developer.meta.com/ai/llama4/use-policy/ —
the older `www.llama.com/llama4/` paths 301 to these; the licence text was also read verbatim at
https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama4/LICENSE, and the
`meta-llama` Hugging Face copy is gated behind a 401 to fetchers). Cohere SaaS Agreement
(https://cohere.com/saas-agreement) and Cohere Terms of Use (https://cohere.com/terms-of-use).
OpenRouter endpoint listings for the two unpinned routes
(https://openrouter.ai/api/v1/models/meta-llama/llama-4-maverick/endpoints — five serving providers;
https://openrouter.ai/api/v1/models/cohere/command-a/endpoints — one, `cohere`), read to answer the
question the missing pin raises. The OpenRouter output-ownership layer itself is the one already read
2026-08-25 and quoted in the MiniMax and Google rows.*

*Sources read 2026-08-26 for the two rulings that closed this page's last substantive items — the
Kimi consumer instruments and the three local checkpoints. **Kimi, the live consumer terms:** Kimi AI
Terms of Service, NOVASCENT PRIVATE LIMITED (Singapore, doing business as Moonshot AI), effective
2026-08-13 (https://www.kimi.ai/user/agreement/modelUse?version=v2); the current PRC twin, Kimi
用户服务协议, Beijing entity, effective 2026-08-31
(https://www.kimi.com/user/agreement/modelUse?version=v2). **Kimi, the superseded document, re-read to
confirm it is what step 7 saw:** the 模型服务协议 / Model Service Agreement of Beijing Moonshot,
effective 2024-01-05, still served at the undecorated paths
https://www.kimi.com/user/agreement/modelUse (Chinese) and https://www.kimi.ai/user/agreement/modelUse
(English, which prints the effective date). Note for a verifier: the version query parameter is the
only thing that separates the live instrument from the 2024 one on these paths, which is how the
superseded page was mistaken for current. **Local checkpoints:** Apache License 2.0 in all three
cases, no output clause in any of them — Muse Glimmer 30B read in full from the model repository
`meta-models/Muse-Glimmer-30B-GGUF` at revision `43c7eadd41352a299ea8e0a36b3157978dd63596` (11,358 B,
sha256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`), with its separate
`USAGE_POLICY.md` (5,230 B) read beside it; Granite 4.1 30B read from the licence layer inside the
pulled model itself (`registry.ollama.ai/library/granite4.1:30b`, layer sha256
`58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd`, 11,357 B); Mistral Small 4
recorded from the dated operator spec card for the endpoint, naming base model
`mistralai/Mistral-Small-4-119B-2603` and served quantisation
`unsloth/Mistral-Small-4-119B-2603-GGUF` @ `bd93c721735aa32c035c0f19e738cb3371fd56ff` — a licence
field, not a retained licence text, and the row says so.*
