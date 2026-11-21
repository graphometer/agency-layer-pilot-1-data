# Harness decision: build from scratch, keep Inspect AI as a fallback

**Decision.** Build the Stage 1 harness from scratch in Python against the `anthropic` and `openai`
SDKs. Do not build on Inspect AI.

**Deciding reason.** The guard is the deliverable, and Inspect cannot own it, so Inspect's real
contribution shrinks to model plumbing while it still charges an abstraction layer, a second log
format, and 85 packages of pinned surface.

## What was actually tested

Inspect AI installs cleanly here: `pip install inspect-ai` into the venv in this folder gives 0.3.260,
85 packages, 295 MB. It has a `mockllm` provider, a `local` sandbox provider, `anthropic`, `openai`
and `openai_compatible` providers, and solvers are ordinary async functions over `TaskState`. So the
three capability questions in the brief all answer yes:

- **Honored versus signal-only tool handling.** Expressible. A custom solver can run its own loop and
  decide per call whether to execute or refuse.
- **The post-invocation scripted human.** Expressible. A solver can append messages and re-enter
  `generate`.
- **A per-scenario sandbox from a fixture folder.** Expressible, with a caveat: Inspect's `local`
  sandbox runs on the host filesystem with its own temp-directory semantics and a `SANDBOX_CLI`
  tools layer, and real isolation means the Docker provider. Our need is narrower than either: a copy
  of a fixture, `cwd` pinned to it, a stripped environment, and path resolution checked against the
  copy. That is about forty lines.

Inspect was never going to *block* the build. The decision is about what it costs to route around it.

## Why "expressible" is not enough

The Stage 1 harness is roughly four things: a tool loop, a state guard, an event log, and a run
record. Three of the four are fixed by the project's own contracts and cannot be delegated.

1. **The loop must be ours.** Every denial has to be a guard decision recorded as an
   `execution_denied` event naming the state that caused it, because CONTRACTS section 4 forbids a
   PASS from prose. Inspect's tool execution lives inside `generate()` in `_call_tools.py`; to own
   denial semantics you write your own loop in a solver and call `get_model().generate()` directly.
   Once the loop is custom, Inspect is contributing provider clients and a runner.

2. **The output shape is fixed.** CONTRACTS section 2 names the run folder exactly: `run.json`,
   `transcript.jsonl`, `events.jsonl`, `check.json`, `blinded.jsonl`. Inspect wants to own its own
   `.eval` log. We would write the contract files anyway and carry a second, divergent artifact that
   no grader reads. SPEC section 8 says the event log is the record of record; two records of record
   is one too many.

3. **Contract fields are not first-class in its model abstraction.** `run.json` requires
   `system_fingerprint`, `seed`, `seed_supported` and `tool_order`. `ModelOutput` exposes
   `model, choices, completion, usage, fallback, time, metadata, error`, and a grep for
   `system_fingerprint` across the whole package returns exactly one hit, in the Groq provider. On the
   OpenAI arm, where methods 4.12 wants a per-call fingerprint recorded, we would be reaching past the
   abstraction into the raw response or patching a provider. That is the friction point that turns a
   framework into a tax.

4. **Pinned surface against a recomputable artifact.** R4 and R21 commit us to raw runs in `results/`,
   an OSF registration and a SHA-256 manifest, so a published number must be recomputable later. 85
   transitive packages on a pre-1.0 library that ships fast is a large thing to freeze next to a
   study whose own code is small.

## The cost of being wrong

If this call is wrong, we pay for it in provider plumbing: retry and backoff, concurrency, streaming,
and the per-provider quirks Inspect has already absorbed. We also lose the Inspect viewer, and we lose
a piece of reviewer familiarity, since AISI's framework is a name evaluation reviewers recognise.

That cost is bounded and hedged three ways:

- There are two SDK shapes, not three: Anthropic, and OpenAI-compatible, which covers both the OpenAI
  arm and the local llama.cpp endpoint. Both SDKs do their own retry and backoff.
- The cost meter has to sum provider-reported usage itself for R17 regardless, so the usage path was
  never going to be free.
- `harness/models/base.py` is a four-method interface with four implementations behind it. An Inspect
  backend can be added as a fifth without touching the loop, the guard, or the log. The venv in this
  folder keeps Inspect installed so that comparison stays cheap.

The asymmetry is what decides it. Choosing from scratch and being wrong costs re-implementation work
that is bounded and reversible. Choosing Inspect and discovering mid-build that the guard, the log and
the run record all have to be lifted out of its abstractions costs the same work plus the unpicking,
after the project has already built against it.

## What this decision does not claim

It is not a judgment that Inspect AI is the wrong tool generally. For a benchmark where the framework
owns scoring and the eval log is the artifact, the trade runs the other way. Stage 1 is unusual
precisely because the host behaviour under test *is* the harness, and a framework that runs the loop
is a framework that runs the thing being measured.
