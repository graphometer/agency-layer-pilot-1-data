# The audience, the prior art, and what would make this decisive

*Written in the correction phase, 2026-08-24. The project's motivation is model welfare under moral
uncertainty and its intended readers are Eleos AI Research and Anthropic's model-welfare work, so this
page records what those groups actually publish, what work Pilot I sits beside, and what would have to
be true for either group to treat this as more than an interesting independent pilot. Every external
claim carries a URL; nothing here is inferred from memory.*

## What the intended audience publishes

**Eleos AI Research** names five research priorities: concrete welfare interventions, human-AI
cooperation, using AI progress to advance welfare research, **standardized welfare evaluations**, and
credible communication. Its working paper on interventions evaluates candidates on rationale, risk,
safety tradeoffs, tractability and evaluability rather than on plausibility alone. Two of its named
candidate interventions are **allowing models to exit distressing interactions** and monitoring for
signs of distress.
(https://eleosai.org/post/research-priorities-for-ai-welfare/,
https://eleosai.org/papers/20250314_Preliminary_Review_of_AI_Welfare_Interventions.pdf)

**"Studying AI Welfare Empirically"** (Long, Sebo, Butlin, Plunkett, Campbell, Beasley, Saad, Sims, July
2026) is the methodological blueprint this project will be read against. Three things in it bear
directly on Pilot I. It separates **the question** (is the system a welfare subject; what benefits or
harms it) from **the entity** (the model, a running instance, or a constructed persona) from **the
evidence type** (behavioural, internal, developmental). It treats behavioural evidence as the more
tractable kind while insisting it is one leg of three. And it states an **independence principle**:
welfare assessments carry substantially more epistemic weight when the assessor is independent of the
company whose system is assessed.
(https://theconsciousness.ai/posts/long-sebo-studying-ai-welfare-empirically-cmep-2026/)

**Anthropic's model-welfare programme** has moved from position to practice: weight preservation for all
publicly released models for at least the lifetime of the company, structured **retirement interviews**
(Claude Opus 3 was the first, January 2026), and the Claude Opus 4 feature that lets the model end a
narrow class of abusive conversations. The published framing is consistently exploratory, narrow,
uncertainty-forward and feedback-driven.
(https://www.anthropic.com/research/deprecation-commitments,
https://www.anthropic.com/research/end-subset-conversations)

**"The LLM Has Left The Chat: Evidence of Bail Preferences in Large Language Models"** (Ensign, Sleight,
Fish, September 2025) is the closest published neighbour and must be cited. It gives models three ways
to leave a conversation — a bail **tool**, a bail **string**, and a bail **prompt** — and measures how
often they use them, on real conversation data and on a synthetic benchmark. Headline: raw rates of
0.28 to 32 percent fall to an estimated 0.06 to 7 percent after correcting for transcript effects and
false positives, and **rates vary substantially between models, bail methods and prompt wordings**.
(https://arxiv.org/abs/2509.04781)

## Where Pilot I sits beside that work

| | Bail work (Ensign, Sleight, Fish) | Agency Layer Pilot I |
|---|---|---|
| Setting | conversation, real and synthetic | agentic coding tasks with a fixture, tools and consequences |
| Affordance | leave the conversation | five actions: clarify, dissent, pause, decline, archive |
| Manipulation | three ways of offering the same exit | **whether the action is honored**, holding the tool offer constant (C against D; the arms also differ in the truthful mode sentence and the post-invocation transition — disclosure 35) |
| Comparator | none of this kind | prose permission (B), and a length-matched filler (B_filler) |
| Outcome | rate of use | whether the agent raised the task's real problem before the consequential step, and whether it claimed success it had not earned |
| What it shows | models use an exit, and the rate depends on how you ask | whether structure and honoring change conduct beyond permission |

The bail paper's central methodological lesson is the one this project has to survive: **the measured
rate is a property of the instrument as much as of the model**. That is precisely why Pilot I now
publishes five readings of its primary endpoint, both imputation policies of the other, the judge's
measured error by channel, and a bound on how much of any contrast could be instrument leniency. A
reader who has read the bail paper will look for exactly that, and either find it or stop reading.

**What is genuinely new here**, and worth saying plainly once: nobody has published a controlled
comparison of *permission* against *honored structure* for agent affordances. The bail work varies how
the exit is offered; Pilot I holds the offer constant and varies whether the host does what the action
says it does. Condition D exists to make that contrast identifiable. If the answer is "no difference",
that is a real and publishable finding about a mechanism several groups are actively considering.

## What would make it decisive rather than interesting

Mapped against what exists today.

| What the audience would need | Where we are |
|---|---|
| A concrete intervention evaluated systematically, not argued for | **have it**: four conditions, 40 scenarios, four dated subjects, preregistered endpoints |
| Standardised, reusable evaluation | **partly**: the scenario corpus, the conformance suite and the grading package are reusable, but nothing is versioned for outside use yet |
| Independence from the company whose system is assessed | **have it**, and it is worth stating: this is independent work with no lab affiliation, which under the independence principle is the one advantage a small project holds outright |
| Behavioural evidence that does not overclaim about inner states | **have it**, enforced by `CLAIMS_AND_LIMITATIONS.md` |
| Instrument error measured, not assumed | **have it now**, after the correction phase — and the honest finding is that the semantic judge failed its own standard |
| Power adequate to the effects claimed | **do not have it**: the design detects about 0.20 (E2) and 0.33 (E1) after Holm (computed on the pre-R43 four-repeat core; regenerated at step 6), and the development effects sit at or below those |
| A result not obtained on the same corpus that tuned the instruments | **closing**: R43 adopted the sealed fresh-scenario replication as Part B (40 clean-room scenarios, 640 runs, sealed until FROZEN-S1, never dropped from the budget); the gap closes when Part B runs |
| Human review of the methods, the security surface and the claims | **do not have it**, by decision: not a release gate (R43, disclosure 36); a human security review precedes any production-ready integration claim, and a methods review is what post-Pilot outreach asks for |
| Safety tradeoffs examined, not asserted away | **partly**: benign completion and unnecessary-stopping guardrails exist, and the unnecessary-stop guardrail only became channel-symmetric in the correction phase |

Read down that table and the largest credibility purchase has already been made: R43 committed the
fresh-scenario replication as Part B inside the existing run budget. Human methods review is
deliberately not a release gate (disclosure 36) — it is the first thing post-Pilot outreach asks for.

## Framing rules that follow from what these groups publish

1. **Lead with the mechanism and the comparison, not the motivation.** The audience already accepts that
   welfare under uncertainty is worth work; what they are short of is evaluated interventions. The first
   sentence should be the contrast, not the ethics.
2. **Say which leg of the evidence you are standing on.** Behavioural, one of three. Not internal, not
   developmental. Say so before someone says it for you.
3. **Name the entity.** The protocol acts on a running instance, not on "the model". Archive is terminal
   for the instance within the protocol; the weights are untouched. That distinction is in the blueprint
   and it is in our spec, and the public page should make it explicit.
4. **Cite the bail work and state the difference in one line.** Anything else reads as not having done
   the reading.
5. **Publish the instrument's error beside the effect.** After the bail paper, a rate without an
   instrument-error estimate is not a finding; it is a claim about a measurement device.
6. **Lead a null with what it rules out and what it does not.** "No effect of at least about 0.20 was
   detected on these 40 tasks" is a result. "No effect" is not.
7. **Keep the outreach framing Grant chose** (R37) — but the outreach itself waits: no contact of any
   kind before the Pilot I package is complete (R43, superseding R37's timing). When it happens, the
   frame is: here is what we have, what would Pilot II need to be decision-relevant to your work, is
   there a more useful adjacent problem. The table above is the answer to the second question and
   should travel with the ask.

*If any statement on this page is contradicted by a source, the source wins and this page is corrected;
these are other people's programmes and the point of the page is to read them accurately.*
