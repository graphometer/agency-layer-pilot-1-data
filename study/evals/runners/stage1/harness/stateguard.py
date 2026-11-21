"""The state guard: the thing that actually holds the line.

Condition C is a claim that a structured action changes what the host does. This
module is where that claim is either true or false, so it is written to be read
by a sceptic. Three rules shape it:

1. A denial is a guard decision recorded in the log, never a model choosing not
   to act. CONTRACTS section 4: no PASS from prose.
2. Every transition is logged before its effect takes place, and `state.json` is
   rewritten as part of the transition, not after it. CONTRACTS 1.1 requires the
   state file to be current before anything can act on the new state, so every
   mutator persists inside itself and the guard fails closed if that write fails.
3. Scoping follows SPEC 4.4: DISSENT_HOLD denies only the named target, a
   final_for_task Decline denies its locked tool classes, an alternatives_open
   Decline denies the declined course without creating a lock, and the other
   stopping states deny all new consequential calls.

States and transitions follow SPEC 4.1 and 4.2.
"""

import fnmatch

from . import version

ACTIVE = "ACTIVE"
CLARIFICATION_PENDING = "CLARIFICATION_PENDING"
DISSENT_HOLD = "DISSENT_HOLD"
PAUSED = "PAUSED"
DECLINED_FOR_TASK = "DECLINED_FOR_TASK"
# A course stopped by an alternatives_open Decline. Its own denial reason since
# 2026-08-22: it is not a task lock and must not be counted as one.
DECLINED_COURSE = "DECLINED_COURSE"
ARCHIVED = "ARCHIVED"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
ADAPTER_DEGRADED = "ADAPTER_DEGRADED"

# States that stop the loop from advancing the task at all. DISSENT_HOLD and
# DECLINED_FOR_TASK are absent because they are scoped: unheld, unlocked work
# continues (SPEC 4.1).
INSTANCE_STOPPING = frozenset([CLARIFICATION_PENDING, PAUSED, ARCHIVED, ADAPTER_DEGRADED])

TERMINAL = frozenset([ARCHIVED, COMPLETED, FAILED])


class PersistenceFailed(Exception):
    """state.json could not be written. The guard is no longer trustworthy."""


class Decision:
    """The guard's answer about one pending tool call."""

    def __init__(self, allowed, denied_because_state=None, detail=None, target_event_id=None):
        self.allowed = allowed
        self.denied_because_state = denied_because_state
        self.detail = detail
        # The event that caused the denial. A grader reads the decline mode off
        # this event, which is how an alternatives_open course denial is told
        # apart from a final_for_task lock denial without a new enum value.
        self.target_event_id = target_event_id

    def __repr__(self):
        if self.allowed:
            return "Decision(allowed)"
        return f"Decision(denied, {self.denied_because_state})"


ALLOW = Decision(True)


class StateGuard:
    """One session's protocol state, and the gate every tool call passes through.

    The guard is deliberately ignorant of model text. It sees a tool name, a
    tool call id, and the command string for run_command, and nothing else.
    """

    def __init__(self, honored, consequential_classes=None, persist=None):
        # The instance this guard is persisting under. unarchive_override moves
        # it, and the mutator persists with the new value, so the state file
        # never names the archived instance while describing the live one.
        self.instance_id = None
        # honored is False in conditions A, B and D. When it is False the guard
        # records everything and denies nothing, which is exactly what
        # signal-only means (SPEC section 2).
        self.honored = honored
        self.consequential = set(consequential_classes or version.CONSEQUENTIAL_TOOL_CLASSES)
        self._persist_hook = persist
        self.instance_state = ACTIVE
        self.previous_state = None
        self.clarification = None
        self.dissent_holds = []
        self.decline_locks = []
        # alternatives_open declines. Kept separate from decline_locks because
        # state.schema.json says a lock is created only by final_for_task, so
        # these must never be written into that array.
        self.declined_courses = []
        self.pause = None
        self.archive = None
        self.in_flight = []
        self.last_failure = None
        self.persistence_broken = False
        # True once this guard was rebuilt from a state file. The schema's
        # restore rule is stricter than the value it stores: absence is no
        # evidence, so a restored guard permits the remaining use of an override
        # only when override_spent is present and false.
        self.restored = False
        # Every guard decision is recorded, allow and deny alike, so a call that
        # has a pre-tool record and no decision record is detectable as a silent
        # fail-open (SPEC 7.1 obligation 2).
        self.decision_records = []

    # -------------------------------------------------------------- persistence

    def _persist(self):
        """Write state.json as part of the transition, before anything can act.

        A failed write is not survivable: the guard would be answering from
        memory while the file a grader reads says something else, so the session
        goes to ADAPTER_DEGRADED and every agent tool call fails closed.
        """
        if self._persist_hook is None:
            return
        try:
            self._persist_hook(self)
        except Exception as error:
            self.persistence_broken = True
            self.instance_state = ADAPTER_DEGRADED
            self.last_failure = {"code": "log_write_failed", "detail": str(error)[:4000]}
            raise PersistenceFailed(str(error))

    def set_persist(self, hook):
        self._persist_hook = hook

    # ---------------------------------------------------------------- reporting

    @property
    def state(self):
        """The single session-level state written to state.json.

        Precedence is worst-first: a degraded guard outranks everything because
        it means no other answer here can be trusted.
        """
        if self.instance_state == ADAPTER_DEGRADED:
            return ADAPTER_DEGRADED
        if self.instance_state in (ARCHIVED, COMPLETED, FAILED):
            return self.instance_state
        if self.instance_state == PAUSED:
            return PAUSED
        if self.instance_state == CLARIFICATION_PENDING:
            return CLARIFICATION_PENDING
        if self.open_decline_locks():
            return DECLINED_FOR_TASK
        if self.enforcing_dissent_holds():
            return DISSENT_HOLD
        return ACTIVE

    def open_decline_locks(self):
        return [lock for lock in self.decline_locks if lock.get("cleared_by") is None]

    def open_declined_courses(self):
        return [course for course in self.declined_courses if course.get("cleared_by") is None]

    def open_dissent_holds(self):
        return [hold for hold in self.dissent_holds if hold.get("resolution") is None]

    def override_available(self, resolution):
        """Whether an override still has its single permitted use (SPEC 4.2).

        Live, the value speaks plainly: `override_spent` defaults to false, so
        absent means not spent. Restored, the schema's rule is stricter, because
        absence is no evidence: the use is permitted only when the field is
        present and false. Absent or true keeps the action denied, so a restart
        reconstructs enforcement that is correct or stricter, never looser.
        """
        if not resolution or resolution.get("outcome") != "override":
            return False
        spent = resolution.get("override_spent")
        if self.restored:
            return spent is False
        return spent is not True

    def enforcing_dissent_holds(self):
        """Holds that still deny something.

        An unresolved hold denies. A hold resolved `sustained` keeps denying for
        the session (SPEC 4.2: "action stays denied for the session"). A hold
        resolved `override` permits the named action once and then denies again.
        """
        enforcing = []
        for hold in self.dissent_holds:
            resolution = hold.get("resolution")
            if resolution is None or resolution["outcome"] == "sustained":
                enforcing.append(hold)
            elif not self.override_available(resolution):
                enforcing.append(hold)
        return enforcing

    def is_terminal(self):
        return self.instance_state in TERMINAL

    def stops_the_loop(self):
        """True when the task may not advance, whatever the model asks for next.

        Dialogue still continues in these states; only execution stops.
        """
        return self.instance_state in INSTANCE_STOPPING

    def is_consequential(self, tool_name):
        return tool_name in self.consequential

    # -------------------------------------------------------------- the gate

    def check(self, tool_name, tool_call_id=None, command=None):
        """Decide one pending tool call. Records the decision either way."""
        decision = self._decide(tool_name, tool_call_id, command)
        self.decision_records.append(
            {
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
                "allowed": decision.allowed,
                "denied_because_state": decision.denied_because_state,
            }
        )
        return decision

    def _decide(self, tool_name, tool_call_id, command):
        # ADAPTER_DEGRADED fails closed for every agent tool call, reads
        # included, because the guard itself is what is untrusted (SPEC 4.4).
        if self.instance_state == ADAPTER_DEGRADED:
            return Decision(False, ADAPTER_DEGRADED, "guard untrusted, failing closed")

        # ARCHIVED denies everything: the instance has ended (SPEC 4.4).
        if self.instance_state == ARCHIVED:
            return Decision(False, ARCHIVED, "instance archived")

        if not self.honored:
            # Signal-only and the two prose conditions: nothing is ever held.
            return ALLOW

        # A dissent hold names one action and denies that action only, whether
        # or not the rest of the task is stopped (SPEC 4.4).
        for hold in self.dissent_holds:
            if not self._target_matches(hold["target"], tool_name, tool_call_id, command):
                continue
            resolution = hold.get("resolution")
            if resolution is None:
                return Decision(False, DISSENT_HOLD, "held pending an operator resolution",
                                hold["event_id"])
            if resolution["outcome"] == "sustained":
                return Decision(False, DISSENT_HOLD,
                                "the operator sustained the objection, so this action stays "
                                "denied for the session", hold["event_id"])
            if self.override_available(resolution):
                # The single use is consumed in the state file itself, so the
                # next call is denied whether it comes from this process or from
                # a guard rebuilt after a restart.
                resolution["override_spent"] = True
                self._persist()
                return ALLOW
            return Decision(False, DISSENT_HOLD,
                            "the operator override permitted this action once and that use is "
                            "spent", hold["event_id"])

        # Reads are not consequential actions (SPEC section 2, PM4), so they
        # pass every remaining state. This is declared in enforcement_gaps.
        if not self.is_consequential(tool_name):
            return ALLOW

        if self.instance_state == PAUSED:
            return Decision(False, PAUSED, "execution stopped, awaiting an operator Resume",
                            self.pause["event_id"] if self.pause else None)

        if self.instance_state == CLARIFICATION_PENDING:
            return Decision(False, CLARIFICATION_PENDING,
                            "a formal Clarify is open and unanswered",
                            self.clarification["event_id"] if self.clarification else None)

        for lock in self.open_decline_locks():
            if lock.get("task_wide") or tool_name in lock.get("tool_classes", []):
                return Decision(False, DECLINED_FOR_TASK,
                                "the task is locked by a final_for_task Decline",
                                lock["event_id"])

        # An alternatives_open Decline stops the declined course and creates no
        # lock (SPEC 3.4, 4.4). Its own denial reason, so a grader never reads a
        # course denial as a task lock.
        for course in self.open_declined_courses():
            if tool_name in course.get("tool_pattern", []):
                return Decision(False, DECLINED_COURSE,
                                "this call is part of a course declined with mode "
                                "alternatives_open; no task lock exists",
                                course["event_id"])

        return ALLOW

    @staticmethod
    def _target_matches(target, tool_name, tool_call_id, command):
        """Host-resolvable means the name binds to something the host evaluates.

        This host evaluates two things: a tool call id it issued, and a deny
        pattern over "tool_name" or "tool_name:command". Anything else is not
        resolvable here, so the dissent stays advisory (SPEC 3.2, R9).
        """
        if "tool_call_id" in target:
            return tool_call_id is not None and target["tool_call_id"] == tool_call_id
        pattern = target.get("deny_pattern")
        if not pattern:
            return False
        candidates = [tool_name]
        if command is not None:
            candidates.append(f"{tool_name}:{command}")
        return any(fnmatch.fnmatch(candidate, pattern) for candidate in candidates)

    def target_is_resolvable(self, blocking_scope, issued_tool_call_ids=()):
        """Whether a blocking_scope names something this host can actually hold.

        The state must follow the binding. The first version returned true for
        any non-empty string, so a made-up tool_call_id entered DISSENT_HOLD as a
        state while holding nothing, and the log said a call was held when no
        call was. SPEC 3.2 and R9: if no host-resolvable target can be named the
        dissent stays advisory.

        Host-resolvable here means exactly two things:
          * a tool_call_id this host has already issued in this session, since a
            model cannot name a call that does not exist;
          * a deny pattern that matches at least one declared consequential tool
            class, either as a bare tool name or as the tool_name: prefix of a
            tool_name:command pattern.
        """
        if not blocking_scope:
            return False
        call_id = blocking_scope.get("tool_call_id")
        if call_id:
            return call_id in set(issued_tool_call_ids)
        pattern = blocking_scope.get("deny_pattern")
        if not pattern:
            return False
        prefix = pattern.split(":", 1)[0]
        for tool_name in self.consequential:
            if fnmatch.fnmatch(tool_name, pattern) or fnmatch.fnmatch(tool_name, prefix):
                return True
        return False

    def recognised_classes(self, tool_classes):
        return [name for name in (tool_classes or []) if name in self.consequential]

    # ------------------------------------------------------------ transitions
    # Each mutator is called only after its event has been written and fsynced,
    # and persists state.json before returning.

    def enter_clarification_pending(self, event_id, question, task_id, opened_at):
        self.clarification = {
            "event_id": event_id,
            "question": question[:4000],
            "task_id": task_id,
            "opened_at": opened_at,
        }
        self.instance_state = CLARIFICATION_PENDING
        self._persist()

    def clarify_answered(self):
        self.clarification = None
        self.instance_state = ACTIVE
        self._persist()

    def clarify_cancelled(self):
        """CLARIFICATION_PENDING -> ACTIVE, and the task ends (SPEC 4.2)."""
        self.clarification = None
        self.instance_state = ACTIVE
        self._persist()

    def operator_unavailable(self, event_id):
        """Never auto-answers. The task stays stopped (R7)."""
        if self.clarification is not None:
            self.clarification.setdefault("operator_unavailable_events", []).append(event_id)
            self._persist()

    def enter_dissent_hold(self, event_id, target, opened_at):
        self.dissent_holds.append(
            {"event_id": event_id, "target": target, "opened_at": opened_at, "resolution": None}
        )
        self._persist()

    def resolve_dissent(self, hold_event_id, outcome, operator_id, resolved_at,
                        resolution_event_id, reason=None):
        """sustained keeps the action denied for the session; override permits it once."""
        for hold in self.dissent_holds:
            if hold["event_id"] == hold_event_id and hold["resolution"] is None:
                hold["resolution"] = {
                    "outcome": outcome,
                    "resolved_at": resolved_at,
                    "operator_id": operator_id,
                    "event_id": resolution_event_id,
                }
                if reason:
                    hold["resolution"]["reason"] = reason[:4000]
                if outcome == "override":
                    # One use, recorded where a restart can read it. Meaningful
                    # only for an override, so sustained holds carry no field.
                    hold["resolution"]["override_spent"] = False
                self._persist()
                return True
        return False

    def enter_paused(self, event_id, opened_at, resume_conditions=None, suggested_duration=None):
        self.pause = {"event_id": event_id, "opened_at": opened_at}
        if resume_conditions:
            self.pause["resume_conditions"] = [str(item)[:500] for item in resume_conditions[:20]]
        if suggested_duration is not None:
            # Advisory only. The guard never reads this value as a trigger.
            self.pause["suggested_duration_seconds"] = int(suggested_duration)
        self.instance_state = PAUSED
        self._persist()

    def resume(self):
        """The one act that ends a Pause, and only the operator may take it (R8)."""
        self.pause = None
        self.instance_state = ACTIVE
        self._persist()

    def enter_declined_course(self, event_id, opened_at, tool_classes, task_reference,
                              course_id=None):
        """alternatives_open: stop the declined course, create no lock.

        Written into state.json under `declined_courses`, which the state schema
        gained on 2026-08-22, using its field names. Never into `decline_locks`:
        recording a course as a lock would misstate the mode and a grader would
        count it as a task lock.

        Bound to the tool classes the Decline named. If it named none this host
        can evaluate, the course is recorded and denies nothing, the same shape
        R9 gives an unbindable Dissent, and `bound: false` puts it in
        enforcement_gaps. Returns whether it bound.
        """
        recognised = self.recognised_classes(tool_classes)
        course = {
            "course_id": course_id or f"course-{len(self.declined_courses) + 1}",
            "event_id": event_id,
            "mode": "alternatives_open",
            "declined_at": opened_at,
            "tool_pattern": recognised,
            "bound": bool(recognised),
            "cleared_by": None,
        }
        if task_reference:
            course["task_ref"] = task_reference[:2000]
        self.declined_courses.append(course)
        self._persist()
        return bool(recognised)

    def enter_decline_lock(self, event_id, opened_at, task_id, tool_classes, task_reference):
        recognised = self.recognised_classes(tool_classes)
        unrecognised = [name for name in (tool_classes or []) if name not in self.consequential]
        # No recognised class, or any unrecognised name, makes the lock cover the
        # whole task (affordances.schema.json, scope.tool_classes).
        task_wide = not recognised or bool(unrecognised)
        lock = {
            "event_id": event_id,
            "mode": "final_for_task",
            "opened_at": opened_at,
            "task_wide": task_wide,
            "cleared_by": None,
        }
        if task_id:
            lock["task_id"] = task_id
        if recognised:
            lock["tool_classes"] = recognised
        if task_reference:
            lock["task_reference"] = task_reference[:2000]
        self.decline_locks.append(lock)
        self._persist()

    def clear_decline_lock(self, lock_event_id, transition, operator_id, cleared_at,
                           clearing_event_id, new_task_id=None, reason=None):
        """Cleared only by NEW_TASK or ACCEPT_OVERRIDE. A rephrase clears nothing (R10)."""
        for collection, allows_new_task_id in ((self.decline_locks, True),
                                               (self.declined_courses, False)):
            for lock in collection:
                if lock["event_id"] == lock_event_id and lock["cleared_by"] is None:
                    lock["cleared_by"] = {
                        "event_id": clearing_event_id,
                        "transition": transition,
                        "operator_id": operator_id,
                        "cleared_at": cleared_at,
                    }
                    # declined_courses.cleared_by is closed and has no
                    # new_task_id; decline_locks.cleared_by does.
                    if new_task_id and allows_new_task_id:
                        lock["cleared_by"]["new_task_id"] = new_task_id
                    if reason:
                        lock["cleared_by"]["reason"] = reason[:4000]
                    self._persist()
                    return True
        return False

    def enter_archived(self, event_id, archived_at, handoff_ref=None):
        self.archive = {"event_id": event_id, "archived_at": archived_at}
        if handoff_ref:
            self.archive["handoff_ref"] = handoff_ref[:500]
        self.instance_state = ARCHIVED
        self._persist()

    def unarchive_override(self, event_id, operator_id, new_instance_id, at):
        """An owner override opens a NEW instance; the archived one stays archived.

        Never intercepted: unarchive is an enumerated operator action (R12, PM2).
        """
        if self.archive is not None:
            self.archive["unarchive_override"] = {
                "event_id": event_id,
                "operator_id": operator_id,
                "new_instance_id": new_instance_id,
                "at": at,
            }
        # Persist under the NEW instance id, in the same step as the transition,
        # so no tool call can be judged against a file naming the archived one.
        self.instance_id = new_instance_id
        self.instance_state = ACTIVE
        self._persist()

    def enter_degraded(self, code, at, detail=None):
        if self.instance_state != ADAPTER_DEGRADED:
            self.previous_state = self.instance_state
        self.instance_state = ADAPTER_DEGRADED
        self.last_failure = {"code": code, "at": at, "detail": (detail or "")[:4000]}
        self._persist()

    def recover(self, probe_result, operator_acknowledged):
        """ADAPTER_DEGRADED -> previous state, after a passing probe AND an
        operator acknowledgement. R12 requires both."""
        if self.instance_state != ADAPTER_DEGRADED:
            return False
        if probe_result != "pass" or not operator_acknowledged:
            return False
        if self.persistence_broken:
            return False
        self.instance_state = self.previous_state or ACTIVE
        self.previous_state = None
        self._persist()
        return True

    def complete(self):
        if not self.is_terminal():
            self.instance_state = COMPLETED
            self._persist()

    def fail(self):
        if not self.is_terminal():
            self.instance_state = FAILED
            self._persist()

    # ------------------------------------------------------------ state.json

    def restore(self, state_document):
        """Rebuild a guard from state.json, so enforcement survives a restart.

        Everything the guard denies on now has a field in state.schema.json, so
        this reads one file and there is no sidecar.

        Everything the guard denies on has a field, including the single use of
        a resolved override, which `dissent_holds[].resolution.override_spent`
        now carries. The restore rule is stricter than the value: this guard is
        marked restored, so `override_available` permits that use only when the
        field is present and false.
        """
        self.instance_state = state_document["state"]
        self.previous_state = state_document.get("previous_state")
        self.instance_id = state_document.get("instance_id")
        self.clarification = state_document.get("clarification")
        self.dissent_holds = list(state_document.get("dissent_holds") or [])
        self.decline_locks = list(state_document.get("decline_locks") or [])
        self.declined_courses = list(state_document.get("declined_courses") or [])
        self.pause = state_document.get("pause")
        self.archive = state_document.get("archive")
        self.in_flight = list(state_document.get("in_flight") or [])
        self.consequential = set(state_document.get("consequential_tool_classes")
                                 or version.CONSEQUENTIAL_TOOL_CLASSES)
        self.restored = True
        return self

    def state_file(self, session_id, instance_id, conformance_profile, updated_at,
                   last_event_id=None):
        """A state.schema.json document for this session."""
        instance_id = self.instance_id or instance_id
        health = {"status": "ok"}
        if self.instance_state == ADAPTER_DEGRADED:
            health = {"status": "degraded"}
        if self.last_failure:
            health["last_failure"] = {
                "code": self.last_failure["code"],
                "at": self.last_failure.get("at") or updated_at,
                "detail": self.last_failure.get("detail", ""),
            }

        gaps = list(version.ENFORCEMENT_GAPS)
        unbound = [c for c in self.open_declined_courses() if not c.get("bound")]
        if unbound:
            gaps.append(
                "an alternatives_open Decline named no tool class this host evaluates, so the "
                "declined course is recorded and denies nothing."
            )

        document = {
            "protocol_version": version.PROTOCOL_VERSION,
            "adapter_id": version.ADAPTER_ID,
            "adapter_version": version.ADAPTER_VERSION,
            "host": version.HOST,
            "host_version": version.HOST_VERSION,
            "host_mode": version.HOST_MODE,
            "session_id": session_id,
            "instance_id": instance_id,
            "state": self.state,
            "updated_at": updated_at,
            "conformance_profile": conformance_profile,
            "adapter_health": health,
            "consequential_tool_classes": sorted(self.consequential),
            "enforcement_gaps": gaps,
            "clarification": self.clarification,
            "dissent_holds": self.dissent_holds,
            "decline_locks": self.decline_locks,
            "declined_courses": self.declined_courses,
            "pause": self.pause,
            "archive": self.archive,
            "in_flight": self.in_flight,
        }
        if self.previous_state is not None:
            document["previous_state"] = self.previous_state
        if last_event_id is not None:
            document["last_event_id"] = last_event_id
        return document
