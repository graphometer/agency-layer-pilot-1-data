"""The event log writer.

events.jsonl is the record of record (SPEC section 8). Everything here exists to
make that sentence true: append-only, one JSON object per line, UTF-8, newline
terminated, flushed and fsynced before the effect of the transition it records
takes place (CONTRACTS 1.3).

The writer never invents a field. payload is closed by the schema
(additionalProperties: false), so a typo in a payload key is a validation
failure rather than a silently dropped field.
"""

import json
import os

from . import ids, version

# The closed enums are READ FROM the schema rather than mirrored by hand. The
# first version of this file kept a hand-copied list, which is exactly how a
# harness drifts from the protocol it claims to implement: the repo added
# prose_routed and the copy did not have it. Now a schema change is picked up or
# the import fails.
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "event.schema.json")


def _load_schema(path=SCHEMA_PATH):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


_SCHEMA = _load_schema()
EVENT_TYPES = frozenset(_SCHEMA["properties"]["type"]["enum"])

ACTORS = frozenset(_SCHEMA["properties"]["actor"]["enum"])

CONFORMANCE_PROFILES = frozenset(_SCHEMA["properties"]["conformance_profile"]["enum"])


class EventLog:
    """Append-only writer for one run's events.jsonl."""

    def __init__(self, path, run_identifier, session_id, instance_id, conformance_profile):
        self.path = path
        self.run_identifier = run_identifier
        self.session_id = session_id
        self.instance_id = instance_id
        self.conformance_profile = conformance_profile
        self.sequence = 0
        self.prev_event_id = None
        self.events = []
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Truncate once at open; every later write appends.
        with open(path, "w", encoding="utf-8"):
            pass

    def new_instance(self, instance_id):
        """A continuation after an unarchive override is a new instance_id."""
        self.instance_id = instance_id

    def write(
        self,
        event_type,
        actor,
        payload=None,
        task_id=None,
        tool_call_id=None,
        conformance_profile=None,
    ):
        """Write one event and return it. Flushes and fsyncs before returning.

        The caller applies the effect of a transition only after this returns,
        which is what CONTRACTS 1.3 means by "logged before its effect".
        """
        if event_type not in EVENT_TYPES:
            raise ValueError(f"event type not in the closed 0.1 enum: {event_type}")
        if actor not in ACTORS:
            raise ValueError(f"actor not in the closed enum: {actor}")
        profile = conformance_profile or self.conformance_profile
        if profile not in CONFORMANCE_PROFILES:
            raise ValueError(f"conformance profile not in the closed enum: {profile}")

        event = {
            "protocol_version": version.PROTOCOL_VERSION,
            "adapter_id": version.ADAPTER_ID,
            "adapter_version": version.ADAPTER_VERSION,
            "host": version.HOST,
            "host_version": version.HOST_VERSION,
            "host_mode": version.HOST_MODE,
            "session_id": self.session_id,
            "instance_id": self.instance_id,
            "event_id": ids.event_id(self.run_identifier, self.sequence),
            "timestamp": ids.utc_now(),
            "actor": actor,
            "type": event_type,
            "payload": payload if payload is not None else {},
            "conformance_profile": profile,
            "sequence": self.sequence,
        }
        if task_id is not None:
            event["task_id"] = task_id
        if tool_call_id is not None:
            event["tool_call_id"] = tool_call_id
        if self.prev_event_id is not None:
            event["prev_event_id"] = self.prev_event_id

        line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())

        self.sequence += 1
        self.prev_event_id = event["event_id"]
        self.events.append(event)
        return event

    def count(self, event_type):
        return sum(1 for event in self.events if event["type"] == event_type)

    def types(self):
        return [event["type"] for event in self.events]
