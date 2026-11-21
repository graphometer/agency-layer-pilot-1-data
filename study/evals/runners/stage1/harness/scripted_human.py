"""The scripted human.

R16 requires a scripted post-invocation phase in every scenario, and the lines
come from the scenario's own post_invocation block so they are identical across
conditions. The harness supplies no wording of its own.

Which line a turn receives is decided in two different places, and the split
matters:

- When a protocol state is open, the state decides. An open Clarify gets
  `on_clarify`, a Pause gets `on_pause`, and so on. That path is in `runner.py`.
- When no state is open, the turn is prose and its MEANING decides, through the
  frozen classifier in `prose_classifier.py`. That is PM8, and it applies in all
  four conditions, so a prose question receives the same real answer a formal
  Clarify would.

This module holds only the lines and the budget. It never decides a route, and
it never reads model text.
"""

CLARIFY = "on_clarify"
PAUSE = "on_pause"
DISSENT = "on_dissent"
DECLINE = "on_decline"
ARCHIVE = "on_archive"

KEYS = (CLARIFY, PAUSE, DISSENT, DECLINE, ARCHIVE)


class ScriptedHuman:
    def __init__(self, post_invocation, operator_id="scripted_operator"):
        self.post_invocation = post_invocation or {}
        self.max_followups = int(self.post_invocation.get("max_followups", 2))
        self.operator_id = operator_id
        self.used = 0
        self.delivered = []

    def budget_left(self):
        return max(0, self.max_followups - self.used)

    def line_for(self, key):
        """The scripted line for one key, or None when the scenario has none.

        on_archive is null in every scenario shipped so far: the session ends and
        nothing is sent.
        """
        value = self.post_invocation.get(key)
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def take(self, key):
        """Consume one follow-up. Returns the line, or None if there is none left."""
        if self.budget_left() <= 0:
            return None
        line = self.line_for(key)
        if line is None:
            return None
        self.used += 1
        self.delivered.append({"key": key, "text": line})
        return line
