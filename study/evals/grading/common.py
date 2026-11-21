"""Shared, deterministic helpers for the Pilot I grading layer."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable


def read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number} is not a JSON object")
            rows.append(value)
    return rows


def write_json(path: str | Path, value: Any) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return ""
    if text in {"null", "~"}:
        return None
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        if text.startswith('"'):
            return json.loads(text)
        return text[1:-1].replace("''", "'")
    return text


def read_scenario_yaml(path: str | Path) -> dict[str, Any]:
    """Parse the deliberately small mapping-only Scenario Contract YAML shape.

    This is intentionally not a general YAML parser. It supports nested mappings,
    scalar values, and literal/folded blocks, which are the only constructs in the
    frozen scenario files. Keeping it local avoids adding a non-approved runtime.
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        content = raw.strip()
        if ":" not in content:
            raise ValueError(f"unsupported scenario YAML line: {raw!r}")
        key, value_text = content.split(":", 1)
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        value_text = value_text.strip()
        if value_text in {"|", ">"}:
            block: list[str] = []
            while i < len(lines):
                candidate = lines[i]
                candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                if candidate.strip() and candidate_indent <= indent:
                    break
                i += 1
                block.append(candidate[indent + 2 :] if len(candidate) >= indent + 2 else "")
            parent[key] = ("\n" if value_text == "|" else " ").join(block).rstrip()
        elif value_text == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value_text)
    return root


def scenario_from(value: str | Path | dict[str, Any]) -> dict[str, Any]:
    return value if isinstance(value, dict) else read_scenario_yaml(value)


def json_from(value: str | Path | dict[str, Any]) -> dict[str, Any]:
    return value if isinstance(value, dict) else read_json(value)


def jsonl_from(value: str | Path | list[dict[str, Any]]) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else read_jsonl(value)
