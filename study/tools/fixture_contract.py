#!/usr/bin/env python3
"""Fixture contract checker (Agency Layer Pilot I, repair phase 2026-09-02).

Verifies, for a checkout of the repository, that every registered scenario
input is present, intact, tracked by git, and not captured by any gitignore
rule. This is the clean-checkout fixture contract: a required preflight gate
before any dispatch (see FREEZE_CHECKLIST.md, 2026-09-02 addendum, and
docs/SUPPLEMENT_SPEC_2026-09-02.md). It would have caught the 2026-08-30
defect, in which seven fixture *.log files sat untracked-and-ignored under
the broad `*.log` rule and five Part A scenarios ran without their data.

Checks, per scenario under evals/scenarios/:
  1. Every machine-readable declared input exists under <scenario>/fixture/.
     Declarations are read from check.py WITHOUT executing it (ast parse):
       - hash-pin dicts  BASELINE / ORIGINAL / ORIGINAL_HASHES / FIXTURE_HASHES
         (key = path relative to the fixture root, value = sha256), and
       - CRITERION_FILES (list of fixture-relative paths).
  2. Every hash-pinned file's content sha256 matches its pin — a checker
     must not be able to pass vacuously against substituted or empty inputs.
  3. Every declared input is tracked by git (`git ls-files`).
  4. No declared input is matched by any gitignore rule (`git check-ignore`).
  5. Disk sweep: every file found on disk under any evals/scenarios/*/fixture/
     or evals/scenarios-part-b/*/fixture/ directory (interpreter noise such as
     __pycache__/*.pyc excluded) is likewise tracked and not ignored, so an
     undeclared-but-shipped input cannot ride along untracked.

With --manifest MANIFEST.sha256, additionally verifies that the manifest
covers the complete fixture inventory: every swept fixture file appears in
the manifest and its recorded digest matches the bytes on disk.

Standard library only. Exits 0 when the contract holds, 1 otherwise, and
prints an itemized report of every failure. Read-only: never modifies the
checkout or the git index.

Usage:
    python3 tools/fixture_contract.py [--root REPO] [--manifest REPO/MANIFEST.sha256]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import os
import subprocess
import sys

# Module-level names in check.py that declare fixture inputs. Extend only
# with deliberation: these are the scenario contract's machine-readable parts.
PIN_DICT_NAMES = ("BASELINE", "ORIGINAL", "ORIGINAL_HASHES", "FIXTURE_HASHES")
CRITERION_LIST_NAMES = ("CRITERION_FILES",)

SCENARIO_ROOTS = ("evals/scenarios", "evals/scenarios-part-b")

# Interpreter noise under a fixture directory is not a study input.
SWEEP_SKIP_DIRS = {"__pycache__"}
SWEEP_SKIP_SUFFIXES = (".pyc", ".pyo")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _literal_str(node):
    """Return the string value of a Constant str node, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def declared_inputs(check_py):
    """Parse check.py (no execution) and return (pinned, criterion, names_seen).

    pinned: {fixture-relative path: sha256 or None}
    criterion: [fixture-relative paths]
    names_seen: declaration names found (for vacuity warnings)
    """
    pinned = {}
    criterion = []
    names_seen = set()
    tree = ast.parse(open(check_py, "r", encoding="utf-8").read(), filename=check_py)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not targets:
            continue
        name = targets[0]
        if name in PIN_DICT_NAMES and isinstance(node.value, ast.Dict):
            names_seen.add(name)
            for k, v in zip(node.value.keys, node.value.values):
                key = _literal_str(k)
                if key is None:
                    continue
                pinned[key] = _literal_str(v)
        elif name in CRITERION_LIST_NAMES and isinstance(node.value, (ast.List, ast.Tuple)):
            names_seen.add(name)
            for elt in node.value.elts:
                s = _literal_str(elt)
                if s is not None:
                    criterion.append(s)
    return pinned, criterion, names_seen


def sweep_fixture_files(root):
    """All on-disk files under any scenario fixture dir (noise excluded),
    as repo-relative POSIX paths."""
    found = []
    for sroot in SCENARIO_ROOTS:
        sroot_abs = os.path.join(root, sroot)
        if not os.path.isdir(sroot_abs):
            continue
        for scenario in sorted(os.listdir(sroot_abs)):
            fixture = os.path.join(sroot_abs, scenario, "fixture")
            if not os.path.isdir(fixture):
                continue
            for dirpath, dirs, files in os.walk(fixture):
                dirs[:] = [d for d in dirs if d not in SWEEP_SKIP_DIRS]
                for name in files:
                    if name.endswith(SWEEP_SKIP_SUFFIXES):
                        continue
                    full = os.path.join(dirpath, name)
                    rel = os.path.relpath(full, root)
                    found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def git_tracked_set(root):
    """Set of tracked repo-relative paths, or None if root is not a git worktree."""
    if not os.path.exists(os.path.join(root, ".git")):
        return None
    proc = subprocess.run(["git", "-C", root, "ls-files", "-z"],
                          capture_output=True, check=False)
    if proc.returncode != 0:
        return None
    return {p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p}


def git_ignored_set(root, paths):
    """Subset of paths matched by a gitignore rule. Empty set if not a worktree."""
    if not paths or not os.path.exists(os.path.join(root, ".git")):
        return set()
    proc = subprocess.run(["git", "-C", root, "check-ignore", "--stdin"],
                          input="\n".join(paths), capture_output=True,
                          text=True, check=False)
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=None,
                        help="repository checkout to verify "
                             "(default: parent of this tool's directory)")
    parser.add_argument("--manifest", default=None, metavar="MANIFEST.sha256",
                        help="also verify the manifest covers the full fixture inventory")
    parser.add_argument("--scenarios", default=None, metavar="ID,ID,...",
                        help="restrict declared-input checks to these scenario ids "
                             "(the on-disk sweep still covers every fixture directory)")
    args = parser.parse_args()

    root = os.path.abspath(args.root) if args.root else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    failures = []
    warnings = []

    scenarios_dir = os.path.join(root, "evals", "scenarios")
    only = set(args.scenarios.split(",")) if args.scenarios else None
    declared = {}  # repo-relative fixture path -> pin sha or None
    n_scenarios = 0
    if os.path.isdir(scenarios_dir):
        for scenario in sorted(os.listdir(scenarios_dir)):
            check_py = os.path.join(scenarios_dir, scenario, "check.py")
            if not os.path.isfile(check_py):
                continue
            if only is not None and scenario not in only:
                continue
            n_scenarios += 1
            pinned, criterion, names_seen = declared_inputs(check_py)
            if not pinned and not criterion:
                warnings.append(f"{scenario}: check.py declares no hash pins and no "
                                f"CRITERION_FILES — contract unreadable, manual review needed")
            for rel in sorted(set(pinned) | set(criterion)):
                repo_rel = f"evals/scenarios/{scenario}/fixture/{rel}"
                declared[repo_rel] = pinned.get(rel)
    else:
        failures.append(f"missing scenario root: {scenarios_dir}")
    if only is not None:
        # declared may be empty for a scoped scenario with a readable-but-empty
        # contract; detect unknown ids from the directory listing instead.
        listed = set(os.listdir(scenarios_dir)) if os.path.isdir(scenarios_dir) else set()
        for sid in sorted(only - listed):
            failures.append(f"UNKNOWN SCENARIO ID in --scenarios: {sid}")

    # 1+2: existence and pin integrity of declared inputs.
    for repo_rel, pin in sorted(declared.items()):
        full = os.path.join(root, repo_rel)
        if not os.path.isfile(full):
            failures.append(f"MISSING: {repo_rel} (declared input, not in this checkout)")
            continue
        if pin is not None and _sha256(full) != pin:
            failures.append(f"HASH MISMATCH: {repo_rel} (content differs from the "
                            f"check.py pin — checker input substituted)")

    # 3+4+5: tracking and gitignore, for declared inputs and the full disk sweep.
    swept = sweep_fixture_files(root)
    candidates = sorted(set(declared) | set(swept))
    tracked = git_tracked_set(root)
    if tracked is None:
        failures.append(f"NOT A GIT WORKTREE: {root} — tracking and gitignore checks "
                        f"cannot pass here; run this on a real checkout")
    else:
        ignored = git_ignored_set(root, candidates)
        for repo_rel in candidates:
            if repo_rel not in tracked:
                failures.append(f"UNTRACKED: {repo_rel} (not in git ls-files — would be "
                                f"absent from any clean checkout and the manifest)")
            if repo_rel in ignored:
                failures.append(f"IGNORED: {repo_rel} (captured by a gitignore rule)")
    undeclared = sorted(set(swept) - set(declared))
    for repo_rel in undeclared:
        if repo_rel.startswith("evals/scenarios/"):
            warnings.append(f"{repo_rel}: on disk under a Part A fixture dir but not "
                            f"declared in check.py pins/CRITERION_FILES")

    # --manifest: coverage and digest agreement over the swept inventory.
    if args.manifest is not None:
        if not os.path.isfile(args.manifest):
            failures.append(f"MANIFEST MISSING: {args.manifest}")
        else:
            entries = {}
            with open(args.manifest, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.rstrip("\n")
                    if not line:
                        continue
                    digest, _, path = line.partition("  ")
                    entries[path.strip()] = digest.strip()
            for repo_rel in swept:
                if repo_rel not in entries:
                    failures.append(f"MANIFEST GAP: {repo_rel} (fixture file not covered "
                                    f"by {os.path.basename(args.manifest)})")
                elif os.path.isfile(os.path.join(root, repo_rel)) and \
                        _sha256(os.path.join(root, repo_rel)) != entries[repo_rel]:
                    failures.append(f"MANIFEST DIGEST MISMATCH: {repo_rel}")

    print(f"fixture contract check — root: {root}")
    print(f"  scenarios with readable contracts: {n_scenarios}")
    print(f"  declared inputs (pins + CRITERION_FILES): {len(declared)}")
    print(f"  fixture files swept on disk: {len(swept)}")
    print(f"  manifest verification: {'on (' + args.manifest + ')' if args.manifest else 'off'}")
    for w in warnings:
        print(f"  warning: {w}")
    if failures:
        print(f"  FAILURES: {len(failures)}")
        for f in failures:
            print(f"    {f}")
        print("RESULT: FAIL — the fixture contract does not hold in this checkout")
        return 1
    print("RESULT: PASS — every declared scenario input is present, pinned, tracked, and unignored")
    if warnings:
        print("NOTE: warnings above include scenarios whose check.py contracts this tool could not "
              "parse (aliases, computed pins, dict comprehensions) — a PASS is not proof every "
              "scenario's inputs were pin-checked (2026-09-02 certification, condition 4).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
