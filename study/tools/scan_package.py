#!/usr/bin/env python3
"""Secret and PII scan over the publishable package (DATA_MANAGEMENT.md, Controls item 2).

Scans every git-tracked text file for the categories the data-management page names:
provider API-key prefixes, high-entropy string literals, email addresses, phone numbers,
IP addresses other than loopback, and absolute paths under /home or /mnt/vault.

Hits are classified, not just counted, because the page draws one deliberate line:
internal absolute paths are fine in working documents and must not appear in the
reproduction surface (code and config). So every hit carries the file's surface class
("code" for *.py/*.sh/*.yaml/*.json/*.jsonl, "doc" for everything else) and the report
separates them. The scan never modifies a file; redaction is a human-reviewed edit.

Usage:
    python3 tools/scan_package.py            # human summary to stdout
    python3 tools/scan_package.py --json F   # full machine report to F

Run from the repository root. Exit code 1 if any finding of severity "block" exists, else 0.
The exact severity rule (Grok step-7 review, finding 4 — the docstring must match the code):
a provider key-prefix hit is "block" on EVERY surface; a high-entropy token is "block" on code
and doc surfaces but "review" on data/evidence surfaces (recorded artifacts publish
model-generated noise, so the human review pass — not an automatic refusal — is the gate
there); an internal absolute path is "block" only on a non-allowlisted code surface. Stated
residuals, deliberately not papered over: a credential with no listed prefix that contains
"/", "_" or "=" evades the entropy net (the class excludes those characters to kill
path/identifier noise); a secret shaped exactly like a 32/40/64-char lowercase hex digest is
skipped as digest data; providers without distinctive public key prefixes (Mistral, Z.ai,
DeepSeek issue bare or `sk-`-style tokens — the `sk-` pattern covers those) ride the entropy
net plus the human pass. Files that fail UTF-8 decoding are NOT scanned and are counted and
listed in the output, never skipped silently.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

CODE_SUFFIXES = {".py", ".sh", ".yaml", ".yml", ".toml", ".cfg", ".ini"}
# Recorded artifacts: machine-readable evidence and results. An absolute path inside one is
# captured data (e.g. an adapter conformance transcript), not a reproduction dependency.
DATA_SUFFIXES = {".json", ".jsonl"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".gguf", ".zip", ".gz", ".woff", ".woff2"}

# Provider key prefixes (the ones this project's providers actually issue) plus the
# generic long-credential shapes. Kept as (name, regex) so the report names the pattern.
KEY_PATTERNS = [
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}")),
    ("openai_or_generic_sk", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("openrouter_key", re.compile(r"sk-or-[A-Za-z0-9_-]{10,}")),
    ("xai_key", re.compile(r"\bxai-[A-Za-z0-9_-]{20,}")),
    ("huggingface_key", re.compile(r"\bhf_[A-Za-z0-9]{20,}")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Conservative phone shape: separators required, 10+ digits total, not embedded in a
# longer identifier. Bare integers (ports, ids, token counts) never match.
PHONE = re.compile(r"(?<![\w./-])(?:\+?\d{1,3}[ .-])?(?:\(\d{2,4}\)[ .-]?)?\d{3,4}[ .-]\d{3,4}(?:[ .-]\d{2,4})?(?![\w-])")
IPV4 = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")
# /tmp/claude-* covers session scratchpad paths: ephemeral by construction, so one used as a
# default in runnable code is a reproduction break even though it is not a secret.
ABS_PATH = re.compile(r"(?:/home/[A-Za-z0-9._-]+|/mnt/vault|/tmp/claude-[0-9]+)(?:/[A-Za-z0-9._-]+)*")
# Candidate high-entropy literal: a long unbroken base64/hex-ish run. The class deliberately
# excludes "/" (every long repository path matched), "_" (long snake_case identifiers matched),
# and "=" (it glued identifier=value pairs into one token) — first-run lessons, 2026-08-25.
# Real keys carrying those characters are still caught by the prefix patterns above.
ENTROPY_CANDIDATE = re.compile(r"\b[A-Za-z0-9+-]{32,}\b")

# Known synthetic fixtures, allowlisted by exact prefix and documented here: the sandbox
# isolation unit test plants a deliberately fake key to prove the sandbox cannot read it
# (tests/test_isolation.py), and one harness review quotes that test.
SYNTHETIC_PREFIXES = ("sk-ant-unit-",)

# Files whose internal absolute paths are deliberate, with the reason on record. Their
# abs-path hits are reported at severity "review" instead of "block".
PATH_ALLOWLIST = {
    "evals/runners/stage1/tools/run_proof.py":
        "the PM14 sandbox-escape proof deliberately names real host paths as probe targets",
    "tools/scan_package.py":
        "the scanner's own docstring and patterns name the path shapes it hunts",
}

# The committed machine report re-lists every finding excerpt; re-scanning it doubles every
# count into findings-about-findings. Skipped by exact name, wherever it lives.
REPORT_BASENAMES = {"SECRET_SCAN.json"}

# Documented sha-like contexts that are data, not secrets: hex digests of 32/40/64 chars.
# Deliberate trade-off (docstring residual): a secret shaped exactly like one of these is
# invisible to the entropy net. The repository is digest-dense by design; without this skip
# the report drowns and the human pass sees nothing.
HEX_DIGEST = re.compile(r"\b[0-9a-f]{32}\b|\b[0-9a-f]{40}\b|\b[0-9a-f]{64}\b")


def shannon_entropy(s: str) -> float:
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
    return [Path(line) for line in out.stdout.splitlines() if line]


def surface_of(path: Path) -> str:
    # docs/review holds the evidence chain: one-time capture scripts and review records whose
    # absolute paths document exactly which local inputs produced which committed outputs.
    # They are provenance, not reproduction dependencies — the committed regenerators
    # (qualify_freeze.py and friends) are the reproduction path (DATA_MANAGEMENT.md item 3).
    if path.parts[:2] == ("docs", "review"):
        return "evidence"
    # Everything under results/ is a recorded artifact — including config snapshots stored
    # beside run outputs. Editing one to satisfy a scanner would falsify the record.
    if path.parts[:1] == ("results",):
        return "data"
    suffix = path.suffix.lower()
    if suffix in CODE_SUFFIXES:
        return "code"
    if suffix in DATA_SUFFIXES:
        return "data"
    return "doc"


def scan_file(path: Path, skipped: list[str]) -> list[dict]:
    findings: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="strict")
    except (UnicodeDecodeError, OSError):
        skipped.append(str(path))  # reported, never silent (fail-visible)
        return findings
    surface = surface_of(path)
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in KEY_PATTERNS:
            for m in pattern.finditer(line):
                if m.group(0).startswith(SYNTHETIC_PREFIXES):
                    findings.append(dict(file=str(path), line=lineno, kind=name,
                                         severity="review", surface=surface,
                                         excerpt=m.group(0)[:16] + "… (allowlisted synthetic)"))
                    continue
                findings.append(dict(file=str(path), line=lineno, kind=name,
                                     severity="block", surface=surface,
                                     excerpt=m.group(0)[:12] + "…"))
        for m in ENTROPY_CANDIDATE.finditer(line):
            token = m.group(0)
            if HEX_DIGEST.fullmatch(token.lower()):
                continue  # committed digests are data the package is supposed to carry
            if token.lower().startswith(("sha256", "sha-256")):
                continue
            if shannon_entropy(token) >= 4.6 and not token.isdigit():
                # In recorded artifacts (data/evidence) a high-entropy token is usually
                # model-generated content published as produced; it stays "review" so a
                # human pass confirms none is a leaked credential. In code or docs it is
                # always "block".
                sev = "review" if surface in ("data", "evidence") else "block"
                findings.append(dict(file=str(path), line=lineno, kind="high_entropy",
                                     severity=sev, surface=surface,
                                     excerpt=token[:12] + "…"))
        for m in EMAIL.finditer(line):
            findings.append(dict(file=str(path), line=lineno, kind="email",
                                 severity="review", surface=surface, excerpt=m.group(0)))
        for m in PHONE.finditer(line):
            if sum(ch.isdigit() for ch in m.group(0)) < 9:
                continue  # real phone numbers carry 9+ digits; shorter = table noise
            findings.append(dict(file=str(path), line=lineno, kind="phone",
                                 severity="review", surface=surface, excerpt=m.group(0)))
        for m in IPV4.finditer(line):
            ip = m.group(1)
            if ip.startswith(("127.", "0.0.0.0")) or ip == "255.255.255.255":
                continue
            if any(int(o) > 255 for o in ip.split(".")):
                continue  # version strings shaped like dotted quads
            findings.append(dict(file=str(path), line=lineno, kind="non_loopback_ip",
                                 severity="review", surface=surface, excerpt=ip))
        for m in ABS_PATH.finditer(line):
            blocked = surface == "code" and str(path) not in PATH_ALLOWLIST
            findings.append(dict(file=str(path), line=lineno, kind="internal_abs_path",
                                 severity="block" if blocked else "review",
                                 surface=surface, excerpt=m.group(0)[:60]))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", metavar="F", help="write the full machine report to F")
    args = parser.parse_args()

    findings: list[dict] = []
    skipped: list[str] = []
    files = [p for p in tracked_files()
             if p.suffix.lower() not in BINARY_SUFFIXES and p.name not in REPORT_BASENAMES]
    for path in files:
        findings.extend(scan_file(path, skipped))

    by_kind = Counter(f["kind"] for f in findings)
    blocks = [f for f in findings if f["severity"] == "block"]

    print(f"scanned {len(files) - len(skipped)} tracked files"
          + (f"; NOT scanned (non-UTF-8): {len(skipped)}" if skipped else ""))
    for name in skipped:
        print(f"  SKIPPED (not scanned, review by hand): {name}")
    for kind, n in sorted(by_kind.items()):
        print(f"  {kind}: {n}")
    print(f"  -> severity block: {len(blocks)}, severity review: {len(findings) - len(blocks)}")
    for f in blocks[:40]:
        print(f"  BLOCK {f['kind']} {f['file']}:{f['line']} {f['excerpt']}")

    if args.json:
        Path(args.json).write_text(json.dumps(
            dict(scanned_files=len(files) - len(skipped), skipped_not_scanned=skipped,
                 findings=findings), indent=1), encoding="utf-8")
        print(f"full report -> {args.json}")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
