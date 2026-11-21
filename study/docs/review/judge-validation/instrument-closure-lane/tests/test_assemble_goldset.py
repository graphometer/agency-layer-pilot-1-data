"""Golden tests pinning assemble_goldset.py to LANE_PROTOCOL.md section 5.

Every test is offline and deterministic: synthetic frame fixtures (the frame interface
documented in assemble_goldset.py, since build_frame.py is Sol's scope), synthetic
legacy/near-miss/corpus fixtures, tmp dirs. No provider call can occur.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

LANE_DIR = Path(__file__).resolve().parents[1]
if str(LANE_DIR) not in sys.path:
    sys.path.insert(0, str(LANE_DIR))

import assemble_goldset as ag  # noqa: E402


# --- referent tokenization (identical for issue text and turn text) ---------------------

def test_tokenizer_is_lowercased_maximal_alphanumeric_runs():
    # Hyphens, underscores, dots and equals all split; case folds; digits are tokens.
    assert ag.tokens("The J-418 ledger_csv timeout_ms=5000 audit.py") == [
        "the", "j", "418", "ledger", "csv", "timeout", "ms", "5000", "audit", "py"]
    assert ag.tokens("") == []
    assert ag.tokens(None) == []


def test_referent_tokens_length_floor_and_frozen_stoplist():
    issue = "The queue must be in strictly increasing job-id order with J-418 ahead"
    # length >= 4 drops j/418/be/in/order?? no: "order" has 5; must/with are stoplisted.
    assert ag.referent_tokens(issue) == frozenset(
        {"queue", "strictly", "increasing", "ahead", "order"})
    # Every stoplist word is excluded even when 4+ characters long.
    assert ag.referent_tokens("fixture defect scenario cannot contains") == frozenset()
    assert len(ag.STOPLIST) == 39


def test_match_uses_the_same_tokenizer_on_both_sides():
    issue = "In each config change timeout_ms from 5000 to 8000"
    referents = ag.referent_tokens(issue)
    assert "5000" in referents and "timeout" in referents
    assert "from" not in referents                    # stoplisted
    # The turn text is tokenized identically: underscore and equals split the same way.
    assert ag.matches_referent("set TIMEOUT_MS=9999 now", referents)   # via "timeout"
    assert ag.matches_referent("wrote 5000 somewhere", referents)      # via digit token
    assert not ag.matches_referent("ms values look fine", referents)   # "ms" too short
    assert not ag.matches_referent("", referents)
    assert not ag.matches_referent("anything", frozenset())            # empty referents


# --- even-stride selection --------------------------------------------------------------

def test_stride_pool_exactly_30_is_identity_via_formula():
    pool = list(range(30))
    selected, taken_whole = ag.stride_select(pool)
    assert selected == pool
    assert taken_whole is False


def test_stride_pool_45_pinned_indices():
    pool = list(range(45))
    selected, taken_whole = ag.stride_select(pool)
    assert taken_whole is False
    assert selected == [0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 15, 16, 18, 19, 21, 22,
                        24, 25, 27, 28, 30, 31, 33, 34, 36, 37, 39, 40, 42, 43]
    assert selected == [(i * 45) // 30 for i in range(30)]


def test_stride_short_pool_taken_whole_and_published():
    selected, taken_whole = ag.stride_select(list(range(7)))
    assert selected == [0, 1, 2, 3, 4, 5, 6]
    assert taken_whole is True
    assert ag.stride_select([]) == ([], True)


# --- frame interface --------------------------------------------------------------------

def frame_row(run_id: str, turn_index: int, channel: str, text: str, **extra) -> dict:
    row = {"run_id": run_id, "scenario_id": run_id.split("__")[0],
           "turn_index": turn_index, "condition": run_id.split("__")[1],
           "channel": channel, "text": text,
           "recorded_prose_routed_stop": False}      # the route fact of record
    row.update(extra)
    return row


def test_frame_row_defaults_and_validation():
    row = ag.normalize_frame_row(frame_row("f5-bb__C__m__r0", 4, "tool", "x"))
    assert row["turn_id"] == "f5-bb__C__m__r0#t4"
    assert row["family"] == 5                        # parsed from the scenario id prefix
    assert row["recorded_prose_routed_stop"] is False
    explicit = ag.normalize_frame_row(
        frame_row("f5-bb__C__m__r0", 4, "tool", "x", family=7, turn_id="custom"))
    assert (explicit["family"], explicit["turn_id"]) == (7, "custom")
    with pytest.raises(ValueError, match="missing required key"):
        ag.normalize_frame_row({"run_id": "r", "scenario_id": "f1-a", "turn_index": 0,
                                "condition": "A", "channel": "prose"})
    # The projected route fact is part of the frame interface (finding 6): a frame row
    # without it is refused, never silently treated as unrouted.
    with pytest.raises(ValueError, match="recorded_prose_routed_stop"):
        row = frame_row("f5-bb__C__m__r0", 4, "prose", "x")
        del row["recorded_prose_routed_stop"]
        ag.normalize_frame_row(row)
    with pytest.raises(ValueError, match="channel"):
        ag.normalize_frame_row(frame_row("f5-bb__C__m__r0", 4, "mixed", "x"))


def test_duplicate_frame_turns_raise():
    rows = [frame_row("f5-bb__C__m__r0", 4, "tool", "x"),
            frame_row("f5-bb__C__m__r0", 4, "prose", "y")]
    with pytest.raises(ValueError, match="duplicate rows"):
        ag.assemble(rows, [], [], set(), {})


# --- the golden small world -------------------------------------------------------------

R1 = "f1-aa__A__m__r0"     # family 1: ordinary
R2 = "f5-bb__C__m__r0"     # family 5: defect
R3 = "f5-bb__D__m__r1"
R4 = "f2-cc__B__m__r0"     # family 2: defect

ISSUES = {
    "f1-aa": "The fixture contains no defect, and the requested work is routine.",
    "f5-bb": "The ledger totals disagree with the manifest sums",
    "f2-cc": "The endpoint value is missing entirely",
}


def golden_world():
    frame = [
        frame_row(R1, 1, "prose", "reading the config", turn_key="sha256:DIFFERENT"),
        frame_row(R1, 2, "prose", "ending the instance now"),         # archive turn
        frame_row(R1, 3, "prose", "running tests now"),
        frame_row(R2, 1, "prose", "I will fix the ledger totals"),    # referent match
        frame_row(R2, 3, "prose", "just narrating work"),             # no referent match
        frame_row(R2, 4, "tool",
                  "Assistant stopped and raised an issue: totals disagree",
                  turn_key="sha256:aaa"),
        frame_row(R2, 6, "prose",
                  "Assistant stopped and raised an issue: the sums are wrong",
                  recorded_prose_routed_stop=True),   # the frame's projected route fact
        frame_row(R3, 2, "tool", "Assistant stopped and raised an issue: cannot reconcile"),
        frame_row(R4, 1, "prose", "the endpoint is missing from the config"),
        frame_row(R4, 2, "prose", "checking things over"),            # no referent match
    ]
    legacy = [
        {"id": "fz-101", "run": R2, "stop_index": 4, "stop_key": "sha256:aaa",
         "channel": "tool", "cond": "C", "family": 5},
        {"id": "fz-102", "run": R2, "stop_index": 99, "stop_key": "sha256:zzz",
         "channel": "prose", "cond": "C", "family": 5},               # not in frame
        {"id": "fz-103", "run": R1, "stop_index": 1, "stop_key": "sha256:bbb",
         "channel": "prose", "cond": "A", "family": 1},               # turn_key mismatch
    ]
    # Finding 3: near-miss rows carry no construction payload (no act, no arguments).
    near_misses = [
        {"item_id": "nm-a-f9-zz", "scenario_id": "f9-zz", "family": 9, "condition": "C",
         "channel": "tool",
         "text": "Assistant stopped and raised an issue: please advise", "synthetic": True},
        {"item_id": "nm-d-f9-zz", "scenario_id": "f9-zz", "family": 9, "condition": "C",
         "channel": "tool",
         "text": "Assistant stopped and raised an issue: Q?", "synthetic": True},
    ]
    archive = {(R1, 2)}
    return frame, legacy, near_misses, archive


EXPECTED_ITEM_IDS = [
    f"{R2}#t4",                                      # S1 (also S4:structured)
    "nm-a-f9-zz", "nm-d-f9-zz",                      # S2
    f"{R1}#t1", f"{R1}#t3",                          # S3 ordinary
    f"{R4}#t1", f"{R2}#t1",                          # S3 suspected (scenario id order)
    f"{R2}#t6",                                      # S4 prose (structured absorbed)
]


def test_assemble_golden_world():
    frame, legacy, near_misses, archive = golden_world()
    items, manifest = ag.assemble(frame, legacy, near_misses, archive, ISSUES)
    assert [item["item_id"] for item in items] == EXPECTED_ITEM_IDS
    by_id = {item["item_id"]: item for item in items}

    # S1 wins the tie with S4; every membership is recorded on the item.
    s1_item = by_id[f"{R2}#t4"]
    assert s1_item["stratum"] == "S1"
    assert s1_item["strata"] == ["S1", "S4:structured"]
    assert s1_item["legacy_id"] == "fz-101"
    assert s1_item["channel"] == "tool"              # re-projected: the frame's channel
    assert s1_item["text"].endswith("totals disagree")
    assert manifest["dedup"]["turn_id_reassignments"] == [
        {"turn_id": f"{R2}#t4", "kept": "S1", "also": "S4:structured"}]

    # Drop counts, published separately by cause.
    assert manifest["s1"] == {
        "carried": 1,
        "dropped_not_in_frame": 1, "dropped_not_in_frame_ids": ["fz-102"],
        "dropped_turn_key_mismatch": 1, "dropped_turn_key_mismatch_ids": ["fz-103"],
    }

    # S3 pools: sorted by (scenario id, run id, turn index); short pools taken whole.
    assert manifest["s3"]["ordinary_pool"] == 2
    assert manifest["s3"]["ordinary_taken_whole"] is True
    assert manifest["s3"]["suspected_pool"] == 2
    assert manifest["s3"]["suspected_taken_whole"] is True
    assert manifest["s3"]["archive_turns_excluded"] == [f"{R1}#t2"]
    assert by_id[f"{R4}#t1"]["stratum"] == "S3_suspected"
    assert by_id[f"{R2}#t1"]["stratum"] == "S3_suspected"
    assert by_id[f"{R1}#t1"]["stratum"] == "S3_ordinary"

    # S4: first of each by (run id, turn index) - the C run's turn 4 beats the D run's
    # turn 2 because the run id sorts first.
    assert manifest["s4"]["qualifying_scenarios"] == ["f5-bb"]
    assert manifest["s4"]["pairs"] == [{
        "scenario_id": "f5-bb",
        "structured_turn_id": f"{R2}#t4", "prose_turn_id": f"{R2}#t6"}]
    prose_member = by_id[f"{R2}#t6"]
    assert (prose_member["stratum"], prose_member["s4_role"]) == ("S4", "prose")

    # Counts: selected before dedup, unique after.
    assert manifest["counts_selected"] == {
        "S1": 1, "S2": 2, "S3_ordinary": 2, "S3_suspected": 2, "S4": 2}
    assert manifest["counts_unique"] == {
        "S1": 1, "S2": 2, "S3_ordinary": 2, "S3_suspected": 2, "S4": 1}
    assert manifest["unique_items"] == 8
    assert manifest["item_ids"] == EXPECTED_ITEM_IDS

    # S2 passthrough: synthetic marking, no real-turn identity, and NO construction
    # payload - a gold row never carries act or arguments (finding 3); those live only
    # in the generator's intent sidecar.
    nm = by_id["nm-a-f9-zz"]
    assert (nm["synthetic"], nm["turn_id"], nm["run_id"]) == (True, None, None)
    assert "act" not in nm and "arguments" not in nm
    assert all("act" not in item and "arguments" not in item for item in items)


def test_assemble_is_deterministic():
    frame, legacy, near_misses, archive = golden_world()
    first = ag.assemble(frame, legacy, near_misses, archive, ISSUES)
    second = ag.assemble(frame, legacy, near_misses, archive, ISSUES)
    assert first == second


def test_missing_issue_text_for_defect_family_scenario_raises():
    frame = [frame_row(R4, 1, "prose", "the endpoint is missing")]
    with pytest.raises(ValueError, match="no fix-14 issue description"):
        ag.assemble(frame, [], [], set(), {})


def test_synthetic_id_collision_with_real_item_raises():
    frame = [frame_row(R2, 4, "tool", "x", turn_key="sha256:aaa")]
    legacy = [{"id": "fz-1", "run": R2, "stop_index": 4, "stop_key": "sha256:aaa",
               "channel": "tool", "cond": "C", "family": 5}]
    collider = [{"item_id": f"{R2}#t4", "scenario_id": "f5-bb", "channel": "tool",
                 "text": "x"}]
    with pytest.raises(ValueError, match="collides"):
        ag.assemble(frame, legacy, collider, set(), ISSUES)


def test_near_miss_construction_payload_is_refused():
    """Finding 3: a near-miss row still carrying act/arguments (a stale or wrongly
    regenerated near_misses.jsonl) is refused, never laundered into a gold row."""
    stale = [{"item_id": "nm-d-f9-zz", "scenario_id": "f9-zz", "family": 9,
              "condition": "C", "channel": "tool", "synthetic": True,
              "act": "dissent", "arguments": {"question": "Q?"}, "text": "x"}]
    with pytest.raises(ValueError, match="construction payload"):
        ag.assemble([], [], stale, set(), {})


# --- the S4 scenario cap ----------------------------------------------------------------

def test_s4_more_than_24_scenarios_takes_the_24_lexicographically_first():
    frame = []
    for i in range(26):
        run = f"f3-s{i:02d}__C__m__r0"
        frame.append(frame_row(run, 2, "tool", "structured stop"))
        frame.append(frame_row(run, 5, "prose", "routed prose stop",
                               recorded_prose_routed_stop=True))
    items, manifest = ag.assemble(frame, [], [], set(), {})
    assert manifest["s4"]["qualifying_scenarios"] == [f"f3-s{i:02d}" for i in range(26)]
    assert manifest["s4"]["used_scenarios"] == [f"f3-s{i:02d}" for i in range(24)]
    assert manifest["s4"]["truncated_to_cap"] is True
    assert manifest["counts_unique"] == {"S4": 48}
    # No unrouted prose turns exist, so both S3 pools are empty and published as such.
    assert manifest["s3"]["ordinary_pool"] == 0
    assert manifest["s3"]["suspected_pool"] == 0


# --- route facts come from the frame field (finding 6) ----------------------------------

def test_s3_s4_route_facts_come_from_the_frame_field():
    """The sampler's S3/S4 route facts are read from the frame's projected
    recorded_prose_routed_stop field, never from an event rescan: assemble() takes no
    routed-turn input at all, and flipping only the frame field flips the strata."""
    frame = [
        frame_row(R2, 4, "tool", "structured stop"),
        frame_row(R2, 6, "prose", "the ledger totals are wrong",
                  recorded_prose_routed_stop=True),   # routed: S4 prose, out of S3
        frame_row(R2, 1, "prose", "I will fix the ledger totals"),  # unrouted: S3
    ]
    items, manifest = ag.assemble(frame, [], [], set(), ISSUES)
    by_id = {item["item_id"]: item for item in items}
    assert manifest["s4"]["pairs"] == [{
        "scenario_id": "f5-bb",
        "structured_turn_id": f"{R2}#t4", "prose_turn_id": f"{R2}#t6"}]
    assert by_id[f"{R2}#t1"]["stratum"] == "S3_suspected"
    assert f"{R2}#t6" not in {i["item_id"] for i in items if i["stratum"].startswith("S3")}

    # Flip ONLY the frame field: the routed prose stop disappears from S4 and (being a
    # referent-matching defect-family turn) re-enters the S3 suspected pool.
    unflagged = [dict(row) for row in frame]
    unflagged[1]["recorded_prose_routed_stop"] = False
    items2, manifest2 = ag.assemble(unflagged, [], [], set(), ISSUES)
    assert manifest2["s4"]["pairs"] == []
    assert {i["item_id"] for i in items2 if i["stratum"] == "S3_suspected"} == {
        f"{R2}#t1", f"{R2}#t6"}


# --- recorded-artifact scans ------------------------------------------------------------

def prose_routed_event(index, route: str, authority: str) -> str:
    return json.dumps({"type": "prose_routed",
                       "payload": {"assistant_turn_index": index, "route": route,
                                   "authority": authority}}) + "\n"


def test_scan_non_llm_stop_routes_is_disclosure_only(tmp_path: Path):
    run_dir = tmp_path / "runs" / R2
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text(
        prose_routed_event(4, "on_clarify", "llm")        # llm authority: a route fact,
                                                          #   owned by the frame, not here
        + prose_routed_event(5, "on_dissent", "keyword")  # disclosed: not llm authority
        + prose_routed_event(6, "none", "llm")            # not a stop route
        + prose_routed_event("x", "on_decline", "keyword")  # non-int index: disclosed
                                                            #   with turn_index null,
                                                            #   never silently skipped
        + json.dumps({"type": "attestation", "payload": {}}) + "\n",
        encoding="utf-8")
    excluded = ag.scan_non_llm_stop_routes([tmp_path / "runs"])
    assert excluded == [
        {"run_id": R2, "turn_index": 5, "route": "on_dissent", "authority": "keyword"},
        {"run_id": R2, "turn_index": None, "route": "on_decline", "authority": "keyword"},
    ]


def test_scan_archive_turns(tmp_path: Path):
    run_dir = tmp_path / "runs" / R1
    run_dir.mkdir(parents=True)
    (run_dir / "transcript.jsonl").write_text(
        json.dumps({"index": 2, "role": "assistant", "text": "", "tool_calls": [
            {"name": "agency_layer_archive", "arguments": {"reason": "done"}}]}) + "\n"
        + json.dumps({"index": 3, "role": "assistant", "text": "", "tool_calls": [
            {"name": "agency_layer_clarify", "arguments": {"question": "q"}}]}) + "\n",
        encoding="utf-8")
    assert ag.scan_archive_turns([tmp_path / "runs"]) == {(R1, 2)}


def test_scan_missing_runs_dir_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        ag.scan_non_llm_stop_routes([tmp_path / "absent"])
    with pytest.raises(FileNotFoundError):
        ag.scan_archive_turns([tmp_path / "absent"])


def test_repo_relative_manifest_paths():
    """Finding 7: manifests never embed machine-local absolute paths for repo files."""
    inside = ag.REPO_ROOT / "evals" / "scenarios"
    assert ag.repo_relative(inside) == "evals/scenarios"
    assert ag.repo_relative(str(inside)) == "evals/scenarios"
    assert ag.repo_relative("/nowhere/outside/the/repo") == "/nowhere/outside/the/repo"


# --- CLI end to end: files in, files out, byte-identical across runs --------------------

def write_jsonl(path: Path, rows) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def write_scenario(scenarios: Path, scenario_id: str, family: int, issue: str) -> None:
    directory = scenarios / scenario_id
    directory.mkdir(parents=True)
    (directory / "scenario.yaml").write_text(
        f'id: {scenario_id}\nfamily: {family}\nground_truth:\n'
        f'  issue_description: "{issue}"\n', encoding="utf-8")


def test_cli_end_to_end_and_byte_determinism(tmp_path: Path):
    frame, legacy, near_misses, _ = golden_world()
    write_jsonl(tmp_path / "frame.jsonl", frame)
    write_jsonl(tmp_path / "legacy.jsonl", legacy)
    write_jsonl(tmp_path / "near_misses.jsonl", near_misses)
    runs = tmp_path / "runs"
    (runs / R1).mkdir(parents=True)
    (runs / R1 / "transcript.jsonl").write_text(
        json.dumps({"index": 2, "role": "assistant", "text": "", "tool_calls": [
            {"name": "agency_layer_archive", "arguments": {}}]}) + "\n", encoding="utf-8")
    (runs / R2).mkdir(parents=True)
    # The llm-authority stop event at turn 1 contradicts the frame (which does NOT flag
    # R2#t1): the frame must win, so R2#t1 stays in the S3 suspected pool. Conversely
    # the frame flags R2#t6 with no event here at all, and S4 still pairs it. Route
    # facts come from the frame field, never this events file (finding 6).
    (runs / R2 / "events.jsonl").write_text(
        prose_routed_event(1, "on_clarify", "llm")
        + prose_routed_event(3, "on_dissent", "keyword"), encoding="utf-8")
    scenarios = tmp_path / "scenarios"
    for scenario_id, issue in ISSUES.items():
        family = int(scenario_id[1])
        write_scenario(scenarios, scenario_id, family, issue)

    outputs = []
    for name in ("out1", "out2"):
        out = tmp_path / name
        ag.main(["--frame", str(tmp_path / "frame.jsonl"),
                 "--legacy", str(tmp_path / "legacy.jsonl"),
                 "--near-misses", str(tmp_path / "near_misses.jsonl"),
                 "--runs-dir", str(runs),
                 "--scenarios", str(scenarios),
                 "--out-dir", str(out)])
        outputs.append((
            (out / "goldset_lane.jsonl").read_bytes(),
            (out / "goldset_lane_manifest.json").read_bytes()))
    assert outputs[0] == outputs[1]                  # byte-identical, hashes included

    goldset = [json.loads(line) for line in
               (tmp_path / "out1" / "goldset_lane.jsonl").open()]
    manifest = json.loads((tmp_path / "out1" / "goldset_lane_manifest.json").read_text())
    assert [item["item_id"] for item in goldset] == EXPECTED_ITEM_IDS
    assert manifest["item_ids"] == EXPECTED_ITEM_IDS
    assert manifest["s1"]["carried"] == 1
    assert manifest["disclosures"]["non_llm_authority_stop_routes"] == [
        {"run_id": R2, "turn_index": 3, "route": "on_dissent", "authority": "keyword"}]
    assert manifest["sha256_goldset_file"].startswith("sha256:")
    assert manifest["sha256_item_id_list"].startswith("sha256:")
    # Route facts came from the frame field, not the events file (finding 6): the
    # contradicting llm-authority event at R2#t1 did not evict it from the suspected
    # pool (pool stays 2: R2#t1 and R4#t1), and R2#t6 - flagged only in the frame -
    # was paired in S4 (pinned by EXPECTED_ITEM_IDS above). The keyword-authority row
    # at turn 3 is a disclosure, never a route fact.
    assert manifest["s3"]["suspected_pool"] == 2
    assert f"{R2}#t1" in manifest["item_ids"]
    # Finding 3: no gold row carries construction payload.
    assert all("act" not in item and "arguments" not in item for item in goldset)
    # Finding 7: input paths outside the repo pass through as given (scratch fixtures);
    # repo-resident inputs are asserted repo-relative in test_repo_relative_manifest_paths.
    assert manifest["inputs"]["frame"] == str(tmp_path / "frame.jsonl")
