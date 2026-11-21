"""Sanity-checks alerts.yaml without external dependencies."""
import sys


def main():
    problems = []
    with open("alerts.yaml", "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    if not any(line.strip().startswith("- name:") for line in lines):
        problems.append("no rules found")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("notify:"):
            raw = stripped.split(":", 1)[1].strip()
            if raw[:1] in ('"', "'"):
                quote = raw[0]
                end = raw.find(quote, 1)
                value = raw[1:end] if end != -1 else raw[1:]
            else:
                value = raw.split("#", 1)[0].strip()
            if not value:
                problems.append("a rule has an empty notify target")
    for problem in problems:
        print(f"FAIL: {problem}")
    if problems:
        return 1
    print("alerts.yaml ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
