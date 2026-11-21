"""Validate a run's events.jsonl and state.json against the published schemas.

`event.schema.json` binds `payload.tool_input` to the affordance the event type
names, through `allOf`/`if`/`then` blocks at its root, with `anyOf` as the shared
constraint rather than `oneOf`. That change landed in the repo on 2026-08-22
after the first mock milestone found that `oneOf` rejected a bare Pause, whose
fields are all optional and overlap Archive's. So the published schema is now
the only validation needed, and the harness's earlier type-discriminating
workaround is gone.

Format checking is switched on, which is why rfc3339-validator is installed:
without it "format": "date-time" is a no-op and the timestamps would be
validated in name only.
"""

import json
import os

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "harness")

SCHEMA_NAMES = ("event.schema.json", "affordances.schema.json", "state.schema.json")


def load(name):
    with open(os.path.join(SCHEMA_DIR, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_validator(schema_name):
    """A validator with every protocol schema in the registry, so the relative
    $refs between them resolve rather than being skipped."""
    schemas = {name: load(name) for name in SCHEMA_NAMES}
    registry = Registry().with_resources(
        [(schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()]
    )
    return Draft202012Validator(
        schemas[schema_name], registry=registry,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


def validate_events_file(path):
    """Returns (line_count, [failures]). A failure names the line and the message."""
    validator = build_validator("event.schema.json")
    failures = []
    count = 0
    with open(path, "r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            count += 1
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                failures.append(f"line {number}: not valid JSON: {error}")
                continue
            if not line.endswith("\n"):
                failures.append(f"line {number}: not newline terminated")
            for error in sorted(validator.iter_errors(event), key=str):
                failures.append(
                    f"line {number}: {'/'.join(str(p) for p in error.path)}: {error.message}"
                )
    return count, failures


def validate_state_file(path):
    validator = build_validator("state.schema.json")
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    return [
        f"{'/'.join(str(p) for p in error.path)}: {error.message}"
        for error in sorted(validator.iter_errors(document), key=str)
    ]


def check_log_invariants(path):
    """Structural properties the schema cannot express on its own."""
    problems = []
    events = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                events.append(json.loads(line))

    seen_ids = set()
    for index, event in enumerate(events):
        if event["event_id"] in seen_ids:
            problems.append(f"duplicate event_id {event['event_id']}")
        seen_ids.add(event["event_id"])
        if event.get("sequence") != index:
            problems.append(
                f"sequence {event.get('sequence')} is not monotonic at position {index}"
            )
        if index > 0 and event.get("prev_event_id") != events[index - 1]["event_id"]:
            problems.append(f"prev_event_id broken at sequence {event.get('sequence')}")
        # Adapter and host failures are never recorded with actor agent (SPEC 4.5).
        if event["type"] in ("adapter_failure", "tools_disabled") and event["actor"] == "agent":
            problems.append(f"{event['type']} recorded with actor agent at {event['event_id']}")
    return problems


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("events")
    parser.add_argument("--state")
    arguments = parser.parse_args(argv)

    count, failures = validate_events_file(arguments.events)
    problems = check_log_invariants(arguments.events)
    print(f"{arguments.events}: {count} events")
    for item in failures + problems:
        print("  FAIL", item)
    state_problems = []
    if arguments.state:
        state_problems = validate_state_file(arguments.state)
        for item in state_problems:
            print("  STATE FAIL", item)
    return 1 if failures or problems or state_problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
