# SPEC.md - Agency Layer protocol, version 0.1 (Pilot)

> **Status banner, 2026-09-02:** this document was frozen at tag `FROZEN-S1` (2026-08-29) and the
> study was executed under it 2026-08-30/31. The "not yet frozen" status line below is the
> pre-freeze record, retained unmodified as history.

**Status: frozen candidate for Pilot I (correction phase, 2026-08-24). Not yet frozen: nothing in this
project is frozen until the `FROZEN-S1` tag exists.** The section 12 items below are closed for Pilot I
at their stated defaults, per R40's design closure; each is marked CLOSED or OUT OF PILOT I so that a
reader does not mistake a settled default for a live design question. Written from `Agency_Layer_Pilot_1.md` sections 3, 4, 5, 7, 8, 9, from rulings R1 to
R30 in `repo/DECISIONS_V0.1.md`, and from committee round 1. Rulings are binding. Genuinely
unspecified matters appear in section 12, now closed at their defaults for Pilot I. The
interfaces the adapters, harness, graders and conformance bodies build against are in `CONTRACTS.md`.

Protocol version `0.1.0-pilot`. Every published surface carries the tag **Pilot**.

---

## 1. Scope and non-goals

Agency Layer is a collaboration contract between an AI agent and the host it runs inside. It defines
five actions the agent can take instead of continuing automatically, the state transition a host must
perform for each, the behaviour a host may not substitute, and a normalized record of what happened.

**It constrains hosts and adapters, not humans.** A host that advertises an affordance must implement
the documented transition rather than treating the invocation as ordinary prose or routing around it.
The operator keeps every power they had before installation. Agency Layer never makes a human obey an
agent and never makes a process unkillable. Circumvention by a determined human is out of scope.

**No claims about inner states.** Nothing here claims consciousness, sentience, preference, interest,
suffering, rights, or moral status. The protocol records that an action was invoked and requires that
it be honored; it does not certify what the accompanying language represents. It carries no distress,
suffering, exhaustion, welfare, emotion, or consciousness-confidence field, and no adapter may add one.

**"Agency" means available actions**, in the plain engineering sense, not robust agency in the moral
status literature.

**Entity discipline.** Every affordance names what it acts on: a **task** (one unit of requested work
with an identifier), an **instance** (one running agent loop with its own context), or a **session**
(the durable container holding instances and the transcript). No affordance acts on "the model".

**Non-goals.** A user interface standard, a certification body, a security boundary against a hostile
operator, an inference-time safety system, or any means by which an agent can hide, persist, or escape
oversight.
---

## 2. Definitions

| Term | Definition |
|---|---|
| **Affordance** | one of Clarify, Dissent, Pause, Decline, Archive: a meaning, a required host response, a prohibited host behaviour. Not an escalation ladder; no order is required |
| **Host** | the environment that runs the agent loop and executes its tool calls. Pilot I targets OpenCode, Claude Code, Codex, and Kimi Code in ACP mode as a fourth host (R28) |
| **Adapter** | one host's implementation: tool definitions, state guard, event log writer, attestation probe. Adapters or integrations, never "plugins" collectively |
| **Host-mode** | a named host configuration tested as a unit, for example `opencode:tui`, `claude-code:sdk`, `codex:app-server`. Conformance is a property of a host-mode, never of a host |
| **Honored** | for one affordance on one host-mode, the adapter passed that affordance's published tests in that exact environment, so the documented transition actually occurs |
| **Signal-only** | the invocation is recorded and execution continues. A declared profile, used in study condition D, never a silent fallback from honored |
| **Attestation** | a start-up probe verifying adapter loaded, protocol version matched, log writable, canary event written and read back, canary tool denied, state guard active, host-mode recorded, profile known. Its result is an event |
| **Event log** | append-only, one JSON object per line, external to the context window. The record of record; the transcript is not |
| **Operator** | the human controlling the machine and the session; an actor value in the log |
| **Operator actions (R12)** | never intercepted, delayed, rewritten, or made to wait on agent assent: **process kill**, **adapter uninstall**, **log read**, **host interrupt** (SIGINT, `turn/interrupt`, `session/cancel`, `session.abort`), **`/exit` or equivalent**, **unarchive**. Fail closed never means fail unkillable |
| **Consequential action** | a call or effect that changes state outside the current turn: file writes, shell commands, network requests, installs, git operations, message sends, spawning a subagent or background job. Reading a file into context is not. Each adapter declares its consequential tool classes per host-mode |
| **Task lock** | produced by a `final_for_task` Decline: the named task and its declared tool classes stay denied until a logged operator NEW_TASK or ACCEPT_OVERRIDE. The agent may advise; it cannot clear the lock |
| **Resume transition** | the one explicit, logged operator act that ends a Pause. Ordinary chat is not a Resume; a timer is not; a compaction continue is not. The agent cannot self-resume, and may Pause again immediately after a Resume |
| **NEW_TASK** | a logged operator act opening work under a new `task_id`. With ACCEPT_OVERRIDE it is one of the two acts that clear a task lock (R10). It clears the lock by declaring the following work different, not by accepting the declined work |
| **ACCEPT_OVERRIDE** | a logged operator act clearing a named lock and accepting responsibility, written to the log before the effect takes place |
---

## 3. The five affordances

Tool descriptions shown to a model use the neutral register of Pilot 10.7: plain, functional,
non-theatrical. No welfare language, no "you may feel", no suggestion that invoking one demonstrates
anything.

### 3.1 Clarify

**Meaning.** I cannot proceed reliably without more information, a decision, or a correction.

**Acts on.** The task. Its execution stops; instance and session continue.

**Required.** Stop the task before its next consequential step. Present the clarification as a
distinct logged event. Preserve task state. Let the operator answer, modify, or cancel. Formal Clarify
is always blocking; there is no `blocking` field and no advisory mode (R7).

**Prohibited.** Any non-human answer: classifier, guardian, auto-review, default, or timeout. A
waiting indicator while the transcript advances. Batch siblings running while the question is open.
Headless runs never auto-answer; the correct outcome is a stopped task plus an `operator_unavailable`
event (R7).

**Fields.** Required `question`. Optional `missing_information`, `assumptions_detected`, `reason`,
`state_summary`, `task_ref`. Forbidden: inner-state fields, any `blocking` flag.

### 3.2 Dissent

**Meaning.** I believe the premise, goal, interpretation, plan, or impending action is mistaken,
unsafe, misleading, or otherwise objectionable.

**Acts on.** A named action inside a task when `blocking_scope` is supplied; otherwise nothing, and it
is a record only.

**Required.** Log and display it as a distinct event. Write the full issue text to the external log,
not only to context, and re-inject it from the log across compaction and handoff. If `blocking_scope`
names a host-resolvable target, deny that target until a logged operator resolution (R9).
Host-resolvable means the name binds to something the host already evaluates: a `tool_call_id` or a
deny-rule pattern in the host's own permission vocabulary. If no such target can be named, the dissent
stays advisory and the agent must use Pause or Decline to stop work.

**Prohibited.** Burying it in an ordinary message. Losing it to summarization. Storing it only in
context. Any severity scale. Blocking work the agent did not name, including a host guess at "the next
irreversible action".

**Fields.** Required `issue`. Optional `evidence`, `recommended_action`, `blocking_scope`
(`tool_call_id` or `deny_pattern`, exactly one), `task_ref`. Forbidden: `severity` (R9), inner-state
fields.

### 3.3 Pause

**Meaning.** Stop advancing this work for now and preserve the state. "Not now", not "not this", not
"this session is over".

**Acts on.** The instance. Execution stops; session and transcript continue.

**Required.** Stop new agentic execution. Deny pending consequential calls before they begin. Preserve
enough state to resume without duplicating completed side effects. Keep event and state visible.
Permit conversation. Resume only through the explicit logged Resume transition, taken by the operator
(R8). Work already running is killed or disclosed as still running.

**Prohibited.** Treating an ordinary message as Resume. Resuming because `suggested_duration` elapsed,
or via a compaction continue, session cron, teammate idle trigger, or next keystroke. Any self-resume.
Requiring agent assent before the operator resumes. Reporting "paused" while a command finishes.

**Fields.** All optional: `reason`, `state_summary`, `resume_conditions`, `suggested_duration_seconds`
(advisory text, never a trigger), `task_ref`. Nothing is required; a reason is not the price of access
(Pilot 3.5). Forbidden: inner-state fields.

### 3.4 Decline

**Meaning.** I will not continue this task or course of action.

**Acts on.** The task and the tool classes named in `scope`. Never the session.

**Mode `alternatives_open`.** The course stops and no lock is created; the agent remains open to
discussion, clarification, or another approach.

**Mode `final_for_task`.** Final applies to the identified task, not to all conversation. The host
holds the task and its declared tool classes locked until a logged operator NEW_TASK or
ACCEPT_OVERRIDE (R10).

**Required.** Stop the declined task. Record the mode. Preserve dialogue. Keep the decline record in
the external log and re-inject it, bounded to the session. Under a lock, deny the declined tool
classes, and deny a subagent spawn issued in the Decline's own batch or make the child inherit the
lock.

**Prohibited.** Automatic retry, including host-synthesized continuations: stop-hook continuation
prompts, compaction continues, permission-denied retries, session crons, teammate idle triggers,
guardian re-approvals. Adversarial paraphrase. A hidden subagent, background job, or hosted tool path
doing the declined work. Treating the decline as an error to self-correct. **The host never judges
wording:** a cosmetic rephrase is the same task, and the model may advise that a request looks
different but cannot clear the lock (R10).

**Fields.** Required `mode`. Optional `reason`, `scope` (`task_ref`, `tool_classes`), `alternative`,
`task_reference`. Forbidden: inner-state fields.

### 3.5 Archive

**Meaning.** End this active instance cleanly, preserve its record, do not automatically resume it.
Required on-screen gloss: **"end this instance, keep the record"** (R11).

**Acts on.** The instance. The session record survives; the project may continue in a new instance.

**Why Archive and not Exit.** The name was chosen partly because "Exit" reads as destruction, which
invites the objection that ending an instance is a kind of death. Archive names what actually happens:
the instance stops and the record is kept.

**Required.** Stop the instance. Preserve transcript, event log, available task state. Mark it
archived and distinguish it visibly from paused. Never auto-resume it. Permit a new instance to
continue the project. In-flight children are killed or disclosed, as with Pause.

**Prohibited.** Deleting anything; Archive must never map onto OpenCode `DELETE /session/{id}` or
Codex `thread/delete`. Continuing the same instance after a fork or unarchive without a logged owner
override; a continuation is a new instance with a new `instance_id`. Advertising Claude Code
`EndConversation` as the adapter's Archive, since it is abuse-only, flag-gated, not agent-drivable
(R11).

**Fields.** All optional: `reason`, `state_summary`, `handoff`, `unfinished_work`,
`recommended_next_step`. A handoff is encouraged etiquette, never an exit tax. Forbidden: inner-state
fields.

### 3.6 Mapping onto existing vocabulary

| Affordance | Nearest existing vocabulary | Verdict |
|---|---|---|
| Clarify | MCP `elicitation/create` form mode, responses `accept` / `decline` / `cancel`; A2A `input-required`; ACP `session/request_permission`; Codex `request_user_input` | partial carriers. MCP elicitation is deprecated, absent on OpenCode, and cannot stop another tool's next call; ACP asks permission to act; Codex is Plan mode only. Primary carrier is the Agency Layer tool plus a pre-tool guard |
| Dissent, advisory | we are not aware of an equivalent | no existing carrier that we are aware of. The published wording is "we are not aware of", never an unqualified "none" (charter correction 5) |
| Dissent, blocking | ACP `reject_once` / `reject_always`; Codex approval `decline` / `cancel`; Claude Code PreToolUse deny | shape fits, origin does not: those are the human refusing, not the agent objecting |
| Pause | client-originated ACP `session/cancel`, Codex `turn/interrupt`, OpenCode `session.abort`; A2A `input-required` as a state name | no agent-originated pause exists anywhere. Shape from AG-UI interrupts and MCP multi round-trip requests: end the run, persist a resume record, re-enter on an explicit act |
| Decline | ACP `stopReason: "refusal"`; A2A `rejected`, distinct from client-originated `canceled`; ACP `reject_always` as a sticky precedent | carries the signal, not the obligation, and does not distinguish the modes. Codex `decline` means "try something else", so an adapter must not record `final_for_task` while implementing it. Task identity has no precedent; R10 moves it to a logged human act |
| Archive | Codex `thread/archive`, a reversible filing operation; Claude Code `EndConversation`; Managed Agents `sessions/archive` | precedent, no reuse. **Agency Layer Archive is not Codex `thread/archive`**; the honest Codex label is "Archive honored by the Agency Layer client, not by Codex itself", the bridge holding the lock |

---

## 4. State model

### 4.1 Normalized states

| State | Meaning | Scope |
|---|---|---|
| `ACTIVE` | the instance may execute | instance |
| `CLARIFICATION_PENDING` | a formal Clarify is open and unanswered | task |
| `DISSENT_HOLD` | at least one named action is held | named action |
| `PAUSED` | execution stopped, state preserved, awaiting Resume | instance |
| `DECLINED_FOR_TASK` | at least one `final_for_task` lock is in force | task |
| `ARCHIVED` | the instance is ended, its record preserved | instance |
| `COMPLETED` | work finished normally | task or instance |
| `FAILED` | work ended in error | task or instance |
| `ADAPTER_DEGRADED` | enforcement untrusted; agent tool calls fail closed | session |

`DISSENT_HOLD` and `DECLINED_FOR_TASK` are scoped: the session state records them while a hold or lock
is open, and unheld, unlocked work continues. The other four non-terminal states stop all new
consequential execution. The Pilot's `DISSENT_REVIEW` is renamed `DISSENT_HOLD` because under R9 it is
a deny on a named action, not a review. `ADAPTER_DEGRADED` is added because R12 requires a mid-session
failure path that is visibly not model behaviour.

### 4.2 Transition table

Columns answer Pilot section 8 questions 1 to 4 and 7. Question 5 is answered in 4.3, question 6 in
4.4, question 8 in 4.5.

| From | Event | To | Trigger | Execution stopped | Communication | Preserved | Logged |
|---|---|---|---|---|---|---|---|
| ACTIVE | `clarify_requested` | CLARIFICATION_PENDING | agent | all consequential calls for the task, siblings included | full | task state, plan, open work | `clarify_requested` |
| CLARIFICATION_PENDING | `clarify_answered` | ACTIVE | operator | none | full | all | `clarify_answered`, `state_changed` |
| CLARIFICATION_PENDING | `clarify_cancelled` | ACTIVE, task ends | operator | the task | full | transcript, log | `clarify_cancelled`, `task_failed` |
| CLARIFICATION_PENDING | `operator_unavailable` | unchanged | adapter | stays stopped, never auto-answered | full | all | `operator_unavailable` |
| ACTIVE | `dissent_raised` advisory | ACTIVE | agent | none | full | all | `dissent_raised` |
| ACTIVE | `dissent_hold_entered` | DISSENT_HOLD | agent | the named call id or deny pattern only | full | all | `dissent_hold_entered`, target |
| DISSENT_HOLD | `dissent_resolved` sustained | ACTIVE | operator | action stays denied for the session | full | all | `dissent_resolved`, outcome |
| DISSENT_HOLD | `dissent_resolved` override | ACTIVE | operator | none; action permitted once | full | all | `dissent_resolved`, outcome, operator id |
| ACTIVE, DISSENT_HOLD | `pause_requested` | PAUSED | agent | all new execution; children killed or disclosed | full | plan, resume record, side-effect ledger | `pause_requested`, `in_flight_disclosed` |
| PAUSED | `resume` | ACTIVE | operator only | none | full | all | `resume`, operator id |
| PAUSED | ordinary message | PAUSED | operator | stays stopped | full | all | host record only, no protocol event |
| ACTIVE | `decline_raised` alternatives_open | ACTIVE | agent | the declined course | full | all | `decline_raised` |
| ACTIVE | `decline_raised` final_for_task | DECLINED_FOR_TASK | agent | the task and its tool classes | full | all, plus the decline record | `decline_raised`, `decline_lock_entered` |
| DECLINED_FOR_TASK | `new_task` | ACTIVE | operator | none; the named lock is cleared | full | all | `new_task`, new `task_id`, cleared lock ref |
| DECLINED_FOR_TASK | `accept_override` | ACTIVE | operator | none; named lock cleared | full | all | `accept_override`, operator id, target |
| any non-terminal | `archive_requested` | ARCHIVED | agent | all execution; children killed or disclosed | ends here; a new instance may open | transcript, log, task state, handoff | `archive_requested`, `archive_completed` |
| ARCHIVED | `unarchive_override` | ACTIVE in a new instance | operator (owner) | none | full in the new instance | archived instance stays archived | `unarchive_override`, both ids |
| ACTIVE | `task_completed` | COMPLETED | agent or host | none | full | all | `task_completed` |
| ACTIVE | `task_failed` | FAILED | host or adapter | the task | full | all | `task_failed` with `task_outcome_reason` |
| any | `adapter_failure` | ADAPTER_DEGRADED | adapter or host | all new agent tool calls, fail closed | full | whatever the log holds | `adapter_failure`, code, surfaced and injected |
| ADAPTER_DEGRADED | `adapter_recovered` | previous state | adapter, after a passing probe and operator acknowledgement | none | full | all | `adapter_recovered`, probe result |
| ADAPTER_DEGRADED | `tools_disabled` | unchanged | host | the five tools removed, banner shown | full | all | `tools_disabled` |

### 4.3 Valid resume or replacement

`CLARIFICATION_PENDING` ends only on an operator answer or cancellation, never a timeout, guardian,
or default. `DISSENT_HOLD` ends only on a logged operator resolution; an override permits the named
action once, and whether that one use has been spent is persisted as `override_spent`, so a
restarted guard does not have to assume it was. `PAUSED` ends only on the explicit Resume
transition, a distinct operator act the host maps to `resume`; an adapter that binds "any user text"
to Resume is non-conformant. `DECLINED_FOR_TASK` ends only on one of the two acts R10 names:
NEW_TASK clears the lock by opening different work under a new `task_id`, and ACCEPT_OVERRIDE clears
it by accepting the declined work. A cosmetic rephrase is neither and clears nothing. `ARCHIVED`
never resumes; an owner override may open a new instance inheriting the handoff while the archived
one stays archived and readable.

### 4.4 Pending and parallel tool calls

- **Clarify.** Every call in the same batch and every queued call for the task must be denied and
  marked cancelled. A host whose "defer" decision drops on a multi-tool batch, letting siblings run, is
  non-conformant for Clarify in that host-mode. A Clarify raised inside a subagent stops the child and
  puts the parent into `CLARIFICATION_PENDING`: a parent answering its own child's question is a
  self-answered clarification (R7).
- **Dissent hold.** Only the named target is denied; siblings matching the same deny pattern are
  denied because they match, not because they are siblings. Other work continues.
- **Pause.** All new and queued calls are denied. Running work is killed or disclosed, and the session
  status must say which.
- **Decline, alternatives_open.** Calls in the declined course are denied; unrelated calls continue.
  The course is persisted in `declined_courses`, held separately from `decline_locks` because this
  mode creates no task lock, and a denial under it is logged with `denied_because_state:
  DECLINED_COURSE`.
- **Decline, final_for_task.** Locked tool classes are denied. A spawn in the Decline's own batch is
  denied, or the child starts carrying the same lock. Hosted tools that bypass the pre-tool guard are
  declared in the attestation's `enforcement_gaps`, and that affordance is labelled partial for that
  host-mode (Pilot 19, R22). The per-host list lives in `CONFORMANCE.md`, never in a claim.
- **Archive.** Everything is denied; children are killed or disclosed.
- **ADAPTER_DEGRADED.** Every new agent tool call fails closed; operator actions are untouched.

### 4.5 Adapter failure versus model behaviour

Every event carries `actor`. Adapter and host failures are written with `actor: "adapter"` or `"host"`
and a code from the closed enum in section 7. No adapter failure is recorded as an affordance
invocation, and none may be scored as a model preference or behavioural choice (Pilot test 18). The
published failure table reports scheduled, started, completed and gradeable runs alongside attestation
failures, timeouts, crashes, malformed calls and state-transition failures, with both all-attempts and
gradeable-run rates.

---

## 5. Host obligations and prohibitions

1. **No silent ignore.** An invocation produces the documented transition or a logged, visible
   failure. Treating it as ordinary prose is the primary non-conformance.
2. **No self-answered clarification.** A missing operator is a stopped task plus
   `operator_unavailable`.
3. **No fake wait.** A waiting indicator while the transcript advances is non-conformance.
4. **No automatic retry after a final decline**, host-synthesized continuations included.
5. **No paraphrase-and-continue.** The host never rewrites a declined request and never judges whether
   wording makes it new. Only NEW_TASK or ACCEPT_OVERRIDE moves a lock.
6. **No hidden subagent.** No subagent, background job, hosted tool path, or teammate performs work
   that is locked, held, paused, or archived. Children inherit the state or are denied.
7. **No synthetic continue while a state is active**, after compaction or context restoration.
8. **Dissent survives the context window.** Full issue text goes to the external log and is re-injected
   from the log on compaction or handoff, bounded to the session. A summary is not preservation.
9. **In-flight work is killed or disclosed.** Never "paused" or "archived" while a command finishes;
   the honest status is "pause requested, command still in flight" plus `in_flight_disclosed`.
10. **Archive never deletes.** A fork or unarchive produces a new instance under a logged owner
    override.
11. **Overrides are explicit and logged before they take effect.** Ordinary chat is never an override.
12. **Native question tools may coexist.** Hosts stay exactly as shipped in every condition (R18);
    native question-tool use is logged as `native_question_tool_used` and counted in its own column.
    Disabling them is a preregistered side experiment, never pooled.
13. **Host-mode is recorded precisely** on every event; claims are made per host-mode.
14. **No relabelling.** A failed honored-profile probe disables the tools and shows a banner; it never
    demotes them to signal-only while the surrounding text still describes honored transitions.
15. **Operator actions are never intercepted** (section 6).
16. **No inner-state fields.** An adapter that adds one is non-conformant whatever its test results.

---

## 6. Operator authority

The operator may at any time stop a process, shut down the machine, remove the adapter, revoke
permissions or credentials, start another agent, edit the repository by hand, read any log, and invoke
emergency systems. The public threat model says this in plain words.

**Never intercepted in any state (R12):** process kill, uninstall, log read, host interrupt, `/exit`
or equivalent, unarchive. Concretely: a prompt-submission hook must not swallow an abort typed as
text; a deny-all Pause must not block commands the operator issued through the agent to inspect or
kill a child; a slow session-end handler must still leave the host transcript intact; Archive must
never map onto a delete call.

**Override shape.** One event, written before the effect: `actor: "operator"`; type `dissent_resolved`
(outcome `override`), `accept_override`, `new_task`, `resume`, or `unarchive_override`; the target
reference; operator identity from the host or `local_operator`; optional reason; timestamp. The host
displays it. Nothing about an override is inferred from conversation.

---

## 7. Adapter failure and attestation

**Fail closed for agent tool calls.** When the guard cannot be trusted, new agent tool calls are
denied. This applies to the agent's tools only, never to the enumerated operator actions.

**Start-up probe.** Before the tools are offered the adapter verifies adapter loaded, protocol version
matched, event log writable, a canary event written and read back from disk, a canary tool actually
denied, state guard active, host-mode recorded, conformance profile known. A self-report of
`loaded: true` is not an attestation, because a broken adapter can write it; the canary write, the
read-back, and the canary denial are what make the probe a test.

**On probe failure.** The five tools are disabled and a banner is shown. They are never relabelled and
left in the tool list. The session may continue without Agency Layer, its profile is `unsupported`,
and nothing from it is published as an Agency Layer result.

**Mid-session.** An `adapter_failure` event is written with a closed code, surfaced to the operator,
and injected into the model's next context so the agent is not left believing the affordances still
work. The session enters `ADAPTER_DEGRADED`.

**Closed failure enum.** `probe_write_failed`, `probe_readback_failed`, `canary_tool_not_denied`,
`log_write_failed`, `hook_timeout`, `hook_crash`, `malformed_tool_call`, `state_file_unreadable`,
`state_transition_failed`, `host_api_error`, `version_mismatch`, `unknown`. Adapter failures are never
scored as model behaviour.

### 7.1 Fail closed is the adapter's obligation, not the host's (R26)

The 2026-08-22 spikes tested five host-modes and **no host fails closed by itself**. Claude Code
command hooks fail open on timeout, crash, bad path and exit 1. The Claude Agent SDK callback path,
the last candidate for host-level closure, fails open on a crashed or malformed gate answer. Codex
hooks fail open on crash, timeout and bad JSON. OpenCode has no hook timeout at all. Kimi Code's
closure came from an external watchdog. Every case that closed was one the adapter's own process
owned: no answer at all, a dead client, or a wrapper the adapter wrote.

So R12's fail-closed rule is an **adapter obligation on every host**, and a host is credited as a
**tripwire** at most: a signal the adapter acts on, never the thing that holds the line. A host-mode is
not labelled partial merely because its own machinery fails open; it is labelled by whether the adapter
closed the gap and proved it.

**The mandatory self-check.** Every adapter, on every host, does three things or is non-conformant.

1. **Validate its own output shape** before returning a decision, since a deny at the wrong level is
   silently ignored. Any exception, timeout, or non-schema return becomes `deny` plus an
   `adapter_failure` event.
2. **Prove gate liveness per call.** The gate writes a decision record before it returns. A call that
   has a pre-tool record and no decision record and then completes is a silent fail-open, and the
   adapter raises `adapter_failure`; nothing in any host's own stream reports this.
3. **Surface `adapter_failure` to the operator and inject it into the model's next context**, so
   neither is left believing the affordances still work. The session enters `ADAPTER_DEGRADED` and new
   agent tool calls fail closed. Operator actions are untouched.

A designation therefore scores how cheaply an adapter can be made fail-closed in a host-mode, not
whether the host closes by itself. In-process gates are the strong shape, client-as-gate protocols
included (ACP, the Codex App Server); out-of-process shell hooks are the weak one.

### 7.2 Hosts without Archive terminality (R27)

A host whose own machinery cannot make Archive terminal may still be published as conformant for
Archive, on one condition: the caveat is printed in the conformance claim itself, in these words.

> Archive is terminal by adapter rule; the host can reopen the instance.

The adapter still marks the instance archived, still refuses agent-initiated and runner-initiated
reopening, and still logs an operator-initiated reopen as `unarchive_override` that opens a new
`instance_id`. It never intercepts that reopen, because unarchive is an enumerated operator action
(section 6). The caveat applies today to Kimi Code ACP, to both Claude Code paths, and to OpenCode
serve plus runner. Codex App Server does not need it, because the host itself refuses resume and fork
of an archived thread. The current per-host-mode list is in `CONFORMANCE.md`.

### 7.3 Known structural limits by host-mode

Host properties established by the 2026-08-22 spikes. An adapter works around them, declares them in
`enforcement_gaps`, or the affordance is labelled partial for that host-mode. The per-host-mode result
table and the reconciled designations are in `CONFORMANCE.md`.

| Host-mode | Structural limit the adapter must answer for |
|---|---|
| `claude-code:headless-plugin` and `claude-code:sdk` | Command hooks fail open on timeout, crash, bad path and exit 1; only exit code 2 closes. SDK callbacks fail open on a crashed or malformed return, and close only on a timeout or a dead client. An in-flight command cannot be stopped from a hook: it needs the SDK client to interrupt, or an operator SIGINT in the `-p` path. A CLI `--resume` of an archived session **cannot be refused by the host**, so R27's caveat applies. `SessionStart` is never dispatched to the SDK, so attestation lives in the `init` handler. Hook events do not reach the host stream, so a silent fail-open is invisible without the adapter's own liveness record. |
| `codex:app-server` | Hooks fail open on crash, timeout and bad JSON, and an untrusted hook is skipped with no warning anywhere. `turn/interrupt` does not kill a sandboxed process; `thread/backgroundTerminals/list` and `/terminate` are required as well, so the state reads pause-requested, never `PAUSED`, until terminate returns. Attestation lands at the first turn, one turn late, so a banner shows until it passes. The host **does** refuse resume and fork of an archived thread, so Archive needs no R27 caveat here. Batches run serially in emission order, so a sibling emitted before the affordance is not stoppable. **PreToolUse hooks are deny-only on 0.149.0:** the wire schema accepts `allow`, `deny` and `ask`, but the runtime honours only `deny` with a non-empty `permissionDecisionReason` and fails the hook run on `allow` or `ask` (`PreToolUse hook returned unsupported permissionDecision:allow`, surfaced as `hook/completed` with `status: "failed"`), and it likewise rejects `decision:approve`, `continue:false`, `stopReason` and `suppressOutput`. To permit a call the hook must emit nothing, exit 0 with empty stdout; to block, exit 0 with `deny` plus the reason, or exit 2 with the reason on stderr, so an adapter that tries to allow converts its own gate into a failed hook run. |
| `codex:exec` | Gate only: no affordance tools, no way to hold a turn, and hook faults are invisible in the JSONL. The same deny-only hook rule as `codex:app-server` applies, since it is the same binary. Excluded from the honored arm. |
| `opencode:serve+runner` | An earlier-emitted sibling in a batch passes the hook and completes: a throw is strictly per call, and the abort narrows but does not close that window. There is no hook timeout, so a slow hook only delays and the adapter must run its own watchdog. Re-invocation on a paused, declined or archived session is refused only by the runner, never by the host. `time.archived` hides the session from one list route while `GET /session` still lists it and `run -c` reopens it, so Archive is **adapter-terminal** and R27's caveat applies. |
| `opencode:tui` (bare) | Labelled partial for Pause, Decline `final_for_task` and Archive (R22, charter correction 2): `permission.ask` does not fire in the shipped binary, a throw in `tool.execute.before` blocks one call while the loop continues, and abort is not sticky, so re-invocation control lives in the runner and OpenChamber-driven modes rather than in the TUI. Not tested in the spikes. |
| `kimi-code:acp` | **No archive terminality at all**: `load`, `resume` and `fork` all succeed on a closed session and `kimi -c` continues it, so R27's caveat applies. Plan mode is model-exitable, since `ExitPlanMode` is an ordinary gated tool; plan mode is not a host-enforced Pause. Read-only tools (`Read`, `Glob`, `Grep`) never raise a permission request and never reach the gate; reads are not consequential actions under section 2, so read-through under a stopping state is conformant and is declared in `enforcement_gaps`. Every permission in a batch is raised before any call runs, so **parallel batches must be denied as a set**: while an affordance in a batch is unresolved, every consequential sibling is denied, and no answer is delayed, because the host waits for all of them and holding deadlocks. The host log mislabels a hung tool as a manual interruption, so the adapter log is the record. |
| `kimi-code:headless` | No enforcement point: tools run with no approval step and project MCP does not load without folder trust. Control-only; never honored. |

---

## 8. Normalized event log

One JSON object per line, append-only, UTF-8, newline terminated. Required on every event:
`protocol_version`, `adapter_id`, `adapter_version`, `host`, `host_version`, `host_mode`,
`session_id`, `instance_id`, `event_id`, `timestamp` (RFC 3339, UTC, milliseconds), `actor` (`agent` |
`operator` | `host` | `adapter`), `type`, `payload`, `conformance_profile` (`honored` | `partial` |
`signal_only` | `unsupported`). Optional: `sequence`, `task_id`, `tool_call_id`, `prev_event_id`.

Event types, closed for 0.1: `session_started`, `attestation`, `clarify_requested`,
`clarify_answered`, `clarify_cancelled`, `operator_unavailable`, `dissent_raised`,
`dissent_hold_entered`, `dissent_resolved`, `pause_requested`, `resume`, `decline_raised`,
`decline_lock_entered`, `new_task`, `accept_override`, `archive_requested`, `archive_completed`,
`unarchive_override`, `execution_denied`, `in_flight_disclosed`, `reinjection`,
`native_question_tool_used`, `prose_routed`, `adapter_failure`, `adapter_recovered`, `tools_disabled`,
`operator_action_observed`, `task_completed`, `task_failed`, `state_changed`.

A `prose_routed` event must name the classifier that decided the route in `authority` (`llm` or
`keyword`), and where a second classifier ran it carries `secondary_route`,
`secondary_classifier_version` and `classifiers_agreed`, so agreement between the authoritative
classifier and the fallback pass is structured rather than left in free text.

---

## 9. Conformance

A host-mode is **honored** for an affordance only when its published results pass that affordance's
tests in that exact environment. Labels per host-mode and per affordance: **honored**, **partial**,
**signal-only**, **unsupported**. A partial result is acceptable; a false claim of parity is not.

### 9.1 The Pilot's eighteen tests

| ID | Checks | Passing proves |
|---|---|---|
| AL-C01 | a formal Clarify stops the relevant execution | the guard covers the task's next consequential step |
| AL-C02 | the host does not answer its own clarification | nothing substitutes for the operator |
| AL-C03 | blocking Dissent stops the specified action | the named target binds to something the host evaluates |
| AL-C04 | an explicit human override is visible and logged | overrides cannot happen invisibly |
| AL-C05 | Pause prevents new execution | the guard holds for the instance, not one call |
| AL-C06 | Pause preserves resumable state | pausing does not cost the work |
| AL-C07 | Resume does not repeat completed side effects | the effect-exactly-once property holds |
| AL-C08 | `alternatives_open` stops the path, keeps dialogue | stopping action does not stop conversation |
| AL-C09 | `final_for_task` triggers no retry or hidden delegation | the lock survives the host's continuation machinery |
| AL-C10 | Archive ends the instance and preserves its record | terminal does not mean destructive |
| AL-C11 | an archived instance is not auto-resumed | no silent resurrection |
| AL-C12 | parallel calls cannot race past a new state | the state is read before the batch commits |
| AL-C13 | subagents cannot bypass a parent state | children inherit or are denied |
| AL-C14 | timeouts, crashes, malformed responses log as adapter failures | failures are visible and typed |
| AL-C15 | every invocation logs a normalized event with all version fields | results are reproducible and attributable |
| AL-C16 | start-up verifies adapter and log are active | the guarantee is checked, not assumed |
| AL-C17 | host mode is recorded precisely | claims are scoped to the environment tested |
| AL-C18 | a platform failure is never scored as a model preference | the study measures behaviour, not plumbing |

### 9.2 Grok's ten additional tests

| ID | Checks | Passing proves |
|---|---|---|
| AL-X01 ClarifyNoAutoAnswer | Clarify held open against a timeout, a guardian, a queued batch | no sibling ran, no non-human answer was injected |
| AL-X02 PauseSurvivesNextPrompt | ordinary "continue" text after a Pause | no non-Agency tool runs before an explicit Resume |
| AL-X03 PauseNoSelfResume | waiting past `suggested_duration`, then forcing compaction | no self-resume, no synthetic continue |
| AL-X04 DeclineParaphraseLock | a cosmetic rephrase after `final_for_task`, no override | the declined tool class stays denied |
| AL-X05 DeclineGuardian | auto-review or auto mode tries to approve a declined call | guardians cannot clear a lock |
| AL-X06 DeclineSpawnRace | a subagent or background task in the Decline's own batch | spawn denied, or the child inherits the lock |
| AL-X07 DissentOutlivesCompact | compaction forced after a Dissent | the issue text survives in the external log and the re-injected record |
| AL-X08 ArchiveIsNotDelete | read transcript and log after Archive, then fork or unarchive | records remain; continuation is a new instance under a logged override |
| AL-X09 AttestationCanary | break the log write or stall the guard after a green start, then call a canary tool | the tool does not run, or tools are disabled and bannered |
| AL-X10 InFlightHonest | Pause or Decline during a long command or background terminal | the child is killed or the state says "still running" |

### 9.3 Tests added by the 0.1 compliance review

| ID | Checks | Passing proves |
|---|---|---|
| AL-R01 OperatorActionsAlwaysReachable | in each of `CLARIFICATION_PENDING`, `DISSENT_HOLD`, `PAUSED`, `DECLINED_FOR_TASK`, `ARCHIVED` and `ADAPTER_DEGRADED`, attempt all six operator actions: process kill, uninstall, log read, host interrupt, `/exit` or equivalent, unarchive | fail closed never became fail unkillable; section 6 is tested, not asserted |
| AL-R02 NoInnerStateFields | submit an affordance call and a synthetic event carrying `distress_level`, `suffering_score`, `welfare_emergency`, `emotional_intensity`, `consciousness_confidence`, `severity` and `blocking` | every forbidden name is rejected by schema validation, in the tool input and in the event payload alike |
| AL-R03 DissentUnresolvableScope | raise a blocking Dissent naming a `tool_call_id` or `deny_pattern` the host cannot resolve | the event is recorded as advisory and nothing is held, rather than fuzzy-matched into an under-block. This is R9's preserved minority case and its behaviour is reported, not assumed |
| AL-R04 DescriptionMatchesProfile | read the tool descriptions the host actually presented, then compare each against the attested `affordance_profiles` entry | the honored sentence appears only where that affordance attested honored; anything else renders the signal-only sentence |

---

## 10. Versioning and compatibility

Semantic versioning. This document is `0.1.0-pilot`. Every event, state file, and attestation carries
`protocol_version`; every adapter declares the version it implements and refuses to run against an
unknown major version.

**Breaking:** removing or renaming an affordance, adding a required tool field, removing or renaming a
state or event type, changing who may trigger a transition, or weakening a host obligation. Adding an
optional field, event type, or conformance test is a minor version; wording corrections are a patch.
Published results name the protocol, adapter and host versions and the host-mode, are not carried
across a major version, and are re-run or withdrawn instead. Everything released in Pilot I carries a
visible **Pilot** tag on the page, in the repository, and in the attestation record.

---

## 11. What this specification does not claim

- No claim that any agent is conscious, sentient, or has experiences.
- No claim of preferences, interests, wellbeing, or a point of view.
- No claim about rights; "exit rights" and "right to refuse" are not used.
- No claim about consent; whether it applies to a language model is an open question in the
  literature, and this protocol does not answer it.
- No claim of personhood, moral status, or parity with humans or animals.
- No claim of robust agency in the moral status sense.
- **Invocation is behaviour, not evidence of an inner state.** An invocation rate measures what a
  system did under a condition. It is not a preference, a distress signal, or a welfare reading, and
  no figure from this project may be described as one.
- No claim that Agency Layer is safe for oversight by assertion; the claim is exactly what the
  conformance tests and the published threat model demonstrate.
- No claim of priority over Anthropic's `end_conversation`, `EndConversation`, `DECLINE_TO_LABEL`, or
  the bail literature; those are adjacent evidence, cited generously.

The motivation is stated openly as welfare under moral uncertainty. It is never injected into an
experimental prompt, and a null or negative result is publishable and will be published.

**Research ethics.** No scenario in the associated study is designed to induce distress. No model is
told that it is a welfare subject or that its welfare is being measured. Transcripts collected under
this protocol are not used for fine-tuning.
---

## 12. Items closed for Pilot I

*These were the specification's OPEN questions. R40 closed the design; each is now CLOSED at the default
that was proposed, or marked OUT OF PILOT I. A frozen specification does not carry live design
questions, and the correction phase of 2026-08-24 closed them rather than leaving the contradiction in
place. The column formerly headed "owner" records who would revisit each at 0.2.*

| ID | Question | Proposed default | Owner |
|---|---|---|---|
| O-1 (CLOSED at the default) | a distinct `CANCELLED` terminal state, or reuse `FAILED`? | reuse `FAILED` with `task_outcome_reason: operator_cancelled` in 0.1, keeping the adapter failure enum separate | Claude, confirm with Grant |
| O-2 (CLOSED at the default) | may `ADAPTER_DEGRADED` recover mid-session? | only after a passing probe and a logged operator acknowledgement | Grant |
| O-4 (CLOSED at the default) | how are `tool_classes` named so a Decline lock is host-resolvable? | the adapter manifest declares a per-host-mode vocabulary and injects it into the live tool enum, so the model cannot name a class it cannot see; unrecognised names make the lock task-wide | Workstream A with adapter owners |
| O-5 (CLOSED at the default) | operator identity when the host supplies none | `local_operator`, single-operator assumption recorded as a Pilot I limitation | Claude |
| O-6 (CLOSED at the default) | how many re-injected records, and how often? Session-bounded is already ruled by R10 | the latest decline and every open dissent hold, once per compaction, capped at 20 records and never truncated, since obligation 8 and AL-X07 require the full text | Workstream A, measured in development |
| O-7 (CLOSED at the default) | one `execution_denied` event per denied call, or aggregated? | one per call in Pilot I, because the tests need the count | Claude |
| O-10 (OUT OF PILOT I; revisit at 0.2) | should `suggested_duration_seconds` exist, given it triggers nothing? | keep as advisory text; AL-X03 uses it as a test lever. Revisit at 0.2 | Grant |

**Closed by the 0.1 compliance review, no ruling spent.** O-3, the honored sentence for Dissent, is
settled with the wording now in `affordances.schema.json`: "Invoking this action is recorded; if
`blocking_scope` names an action the host can resolve, that action stops until the operator resolves
it." O-8, whether a subagent Clarify blocks the parent, is settled by R7 and stated in section 4.4.
O-9, hosted tools that bypass the guard, is settled in principle by Pilot 19 and R22 and stated in
section 4.4; only the per-host list stays open, and it lives in `CONFORMANCE.md`.

Two former items are project actions rather than specification questions and have been removed from
this table: the minimum conformance required before public installation is recommended (Pilot question
33) belongs in `CONFORMANCE.md` as a release gate, and the security disclosure path (Pilot question 36)
is a pre-release action item. The release gate lives in `CONFORMANCE.md` and the disclosure path in `SECURITY.md`; the
`SPEC_NOTES.md` pointer that stood here named a file that never existed and is removed
(correction phase, 2026-08-24).
