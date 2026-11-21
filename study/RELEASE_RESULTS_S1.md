# Pilot I repaired results release record

Status: approved private ceremony record under owner ruling R66 (2026-09-03). Completion is
established by the presence of the local `RESULTS-S1` tag.

This record governs the private local results tag. It does not authorize a push, public release,
OSF deposit, website work, outreach, or a new study.

## Release identity

- Intended local tag: `RESULTS-S1`
- Owner ruling supplied to recorded artifact generators: `R66-2026-09-03`
- Manifested content commit: `30204ec65fcb1ad7af8b15035b590804a7d38867`
- `MANIFEST.sha256` line count: `117922`
- `MANIFEST.sha256` file digest: `a4940e3ec4ae62405edb3352c33f0f46376905220d2959457c9e6a2d3d6f328c`
- Wrapper/tag commit: recorded by the local Git tag itself, because a commit cannot contain its own id

The content commit above deliberately does not contain `MANIFEST.sha256`. The clean-tree manifest is
generated from that commit, then this record and the manifest are added in a wrapper commit. Therefore
the three identity placeholders in this file are the only wrapper-edited bytes not described by their
own content-manifest entries. The final exact-byte privacy scan covers the wrapper/tag commit as a whole.

## Findings integrity rule

The approval pass may change only release/provenance metadata and rendered wording that reports the
release flag. Numerical findings, denominators, intervals, p values, model/family breakdowns, and raw
evidence must remain unchanged. The ceremony records a machine comparison before tagging.

## Verification completed before the content commit

- Recorded core, family 9, and Part B technical gates: pass; R66 present; release status approved;
  `publishable_as_result: true`.
- Normalized old/new artifact comparison: byte-identical after removing only the named
  release/provenance/path fields. No analytical or numerical field changed.
- Grading: 134 passed, 2 standing environment skips, 324 subtests.
- Harness: 133 passed, 1 standing environment skip, 24 subtests in the host environment required by
  Bubblewrap. The nested Codex sandbox refusal was an environment limitation, not a test failure.
- Instrument closure lane: 99 passed.
- Adapters: Codex 45 passed, 1 standing skip, 24 subtests; Kimi Code 5 passed, 28 subtests; OpenCode
  5 passed, 28 subtests.
- Recorded repair regressions: 6 passed. Both Part A artifact sidecar digests verified.
- Five-scenario fixture contract: pass; all 21 declared inputs present, pinned, tracked, and
  unignored. The standing parser-coverage warnings remain disclosed.

The clean content commit and final wrapper/tag commit each receive an exact tracked-byte privacy
scan. The wrapper/tag scan is the final authority because it covers the manifest and filled identity
fields as well as the content commit.
