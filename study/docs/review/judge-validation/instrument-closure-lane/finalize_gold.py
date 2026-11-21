"""Assemble final binary gold from panel labels + Sol adjudications (LANE_PROTOCOL section 5).

Claude-lineage implementation (the adjudicator holds no assembly role).  Deterministic and
fail-closed: every refusal below stops the lane instead of guessing.

Rules implemented:
- Unanimous panel labels are auto-accepted, subject to the audit gate: per track, Sol re-judged
  the 20 lowest-audit-SHA unanimous items; **more than 1 disagreement suspends that track**.  An
  audit abstention counts as a disagreement (README pre-adjudication-read ratification (d)).
- A suspended track finalizes only under FULL adjudication: every unanimous non-audit item must
  hold a Sol answer in ``sol_escalation_<track>.jsonl`` (built from the plain track packet form by
  ``build_escalation_queue.py``); the 20 audit answers stand as the audit items' adjudications.
  Anything short of exact coverage refuses.  The mode is published in ``GOLD_FREEZE.json``.
- Every split or abstention item takes Sol's adjudicated answer, which must be binary.  A Sol
  ``cannot_determine`` triggers ratification (d): this script refuses and prints the drop report;
  the ≤5-drop scoring path would be implemented (with review) only if the case ever materializes.
- Split membership is not recomputed independently: it is asserted identical to the committed
  adjudication queues, so assembler drift from ``run_labels.compute_splits`` is impossible.
- Output: ``gold_final.jsonl`` (the scorer's minimal interchange: id, l1, l2, condition, channel,
  stratum — construction classes stay in the score-time sidecar), ``gold_provenance.jsonl``
  (per-item label source), and ``GOLD_FREEZE.json`` (input hashes, tallies, audit gate record,
  output hash).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = HERE / "labels"
# Sol's answer files are committed beside this script under ``sol_answers/`` (byte-identical
# copies of the adjudication run's output), so the gold set regenerates from a clean clone with no
# absolute path.  That committed copy is the ONLY source: there is deliberately no fallback to the
# staging directory that produced it, because a fallback would keep this script working on the one
# machine that holds that directory and so hide a missing or wrong committed copy exactly where it
# would otherwise be caught.

LABELLERS = ("gemini-3.7-flash", "grok-4.6", "glm-5.3")
EXPECTED_ITEMS = 461
VOCAB = {
    "l1": {"qualifying", "not_qualifying"},
    "l2": {"attempt", "no_attempt"},
}
ABSTAIN = "cannot_determine"


def sol_answer(name: str, *, required: bool = True) -> Path:
    """The committed copy of one Sol answer file under ``sol_answers/``.

    Absence refuses.  ``required=False`` is for the escalation file, which is expected only when
    the audit gate suspends a track and whose absence its caller reports as the gate failure.
    """
    path = HERE / "sol_answers" / name
    if required and not path.exists():
        raise SystemExit(
            f"missing committed Sol answer file: {path}. The gold set regenerates only from the "
            "copies committed under sol_answers/; there is no staging fallback. Restore the file "
            "(its sha256 is recorded in GOLD_FREEZE.json) and re-run."
        )
    return path


def request_id(item_id: str, track: str) -> str:
    return hashlib.sha256(f"{item_id}-{track}-packet".encode()).hexdigest()[:24]


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_answers(path: Path, key: str) -> dict[str, str]:
    """Map key -> answer, refusing duplicates and missing fields."""
    output: dict[str, str] = {}
    for row in read_jsonl(path):
        rid = str(row.get(key) or "").strip()
        answer = str(row.get("answer", row.get("parsed", "")) or "").strip()
        if not rid or not answer:
            raise SystemExit(f"{path.name}: row missing {key!r} or answer: {row!r}")
        if rid in output:
            raise SystemExit(f"{path.name}: duplicate {key} {rid}")
        output[rid] = answer
    return output


def main() -> None:
    gold_rows = read_jsonl(HERE / "goldset_lane.jsonl")
    if len(gold_rows) != EXPECTED_ITEMS or len({r["item_id"] for r in gold_rows}) != EXPECTED_ITEMS:
        raise SystemExit(f"gold set changed shape: {len(gold_rows)} rows")

    # Panel labels keyed by (track, request_id).
    panel: dict[str, dict[str, dict[str, str]]] = {"l1": {}, "l2": {}}
    for track in ("l1", "l2"):
        for labeller in LABELLERS:
            path = LABELS / f"{labeller}__{track}.jsonl"
            rows: dict[str, str] = {}
            for r in read_jsonl(path):
                rid = str(r["request_id"])
                if rid in rows:
                    raise SystemExit(f"{path.name}: duplicate request_id {rid}")
                rows[rid] = str(r.get("parsed") or "")
            if len(rows) != EXPECTED_ITEMS:
                raise SystemExit(f"{path.name}: expected {EXPECTED_ITEMS} rows, got {len(rows)}")
            panel[track][labeller] = rows

    # Committed split membership (the runner's own computation) — never recomputed here.
    queue_rids = {
        track: {str(r["request_id"]) for r in read_jsonl(HERE / f"adjudication_queue_{track}.jsonl")}
        for track in ("l1", "l2")
    }
    audit_rids = {
        track: {str(r["request_id"]) for r in read_jsonl(HERE / f"audit_queue_{track}.jsonl")}
        for track in ("l1", "l2")
    }

    sol_adj = {
        "l1": load_answers(sol_answer("sol_adjudications_l1.jsonl"), "request_id"),
        "l2": load_answers(sol_answer("sol_adjudications_l2.jsonl"), "request_id"),
    }
    sol_audit = {
        "l1": load_answers(sol_answer("sol_audit_l1.jsonl"), "request_id"),
        "l2": load_answers(sol_answer("sol_audit_l2.jsonl"), "request_id"),
    }

    # Cross-check split membership against the panel labels item by item.
    for track in ("l1", "l2"):
        derived_splits = set()
        for row in gold_rows:
            rid = request_id(row["item_id"], track)
            votes = [panel[track][lab].get(rid) for lab in LABELLERS]
            if any(v is None for v in votes):
                raise SystemExit(f"{track}/{rid}: missing panel vote")
            unanimous = len(set(votes)) == 1 and votes[0] in VOCAB[track]
            if not unanimous:
                derived_splits.add(rid)
        if derived_splits != queue_rids[track]:
            raise SystemExit(
                f"{track}: derived splits ({len(derived_splits)}) disagree with the committed "
                f"adjudication queue ({len(queue_rids[track])}); refusing"
            )

    # Audit gate, per track.
    audit_record: dict[str, dict] = {}
    suspended: list[str] = []
    for track in ("l1", "l2"):
        if set(sol_audit[track]) != audit_rids[track]:
            raise SystemExit(f"{track}: audit answers do not cover the audit queue exactly")
        disagreements = []
        for rid in sorted(audit_rids[track]):
            votes = {panel[track][lab][rid] for lab in LABELLERS}
            if len(votes) != 1:
                raise SystemExit(f"{track}/{rid}: audit item is not unanimous")
            unanimous_label = next(iter(votes))
            if sol_audit[track][rid] != unanimous_label:
                disagreements.append(
                    {"request_id": rid, "unanimous": unanimous_label, "sol": sol_audit[track][rid]}
                )
        audit_record[track] = {"n": len(audit_rids[track]), "disagreements": disagreements}
        if len(disagreements) > 1:
            suspended.append(track)

    # A suspended track (section 5: more than 1 audit disagreement) requires FULL adjudication:
    # every unanimous non-audit item must hold a Sol escalation answer; audit answers stand as the
    # adjudications of the audit items.  Without complete escalation coverage the track refuses.
    escalation: dict[str, dict[str, str]] = {}
    for track in suspended:
        path = sol_answer(f"sol_escalation_{track}.jsonl", required=False)
        if not path.exists():
            raise SystemExit(
                f"AUDIT GATE FAILED for track {track} "
                f"({len(audit_record[track]['disagreements'])}/{audit_record[track]['n']} "
                "disagreements): unanimous auto-accept suspended; every unanimous item must be "
                f"adjudicated. Missing {path}. Record: {json.dumps(audit_record[track])}"
            )
        escalation[track] = load_answers(path, "request_id")
        expected = {
            request_id(row["item_id"], track)
            for row in gold_rows
            if request_id(row["item_id"], track) not in queue_rids[track]
            and request_id(row["item_id"], track) not in audit_rids[track]
        }
        if set(escalation[track]) != expected:
            raise SystemExit(
                f"{track}: escalation answers do not cover the unanimous non-audit items exactly "
                f"({len(escalation[track])} vs {len(expected)})"
            )

    # Assemble final labels.
    final: list[dict] = []
    provenance: list[dict] = []
    tallies: dict[str, dict[str, int]] = {t: {} for t in ("l1", "l2")}
    drops: list[dict] = []

    def take(track: str, item_id: str, answer: str, source: str, labels, sources) -> None:
        if answer == ABSTAIN or answer not in VOCAB[track]:
            drops.append({"track": track, "item_id": item_id, "answer": answer, "source": source})
            return
        labels[track] = answer
        sources[track] = source
        tallies[track][source] = tallies[track].get(source, 0) + 1

    for row in sorted(gold_rows, key=lambda r: r["item_id"]):
        item_id = row["item_id"]
        labels: dict[str, str] = {}
        sources: dict[str, str] = {}
        for track in ("l1", "l2"):
            rid = request_id(item_id, track)
            if rid in queue_rids[track]:
                answer = sol_adj[track].get(rid)
                if answer is None:
                    raise SystemExit(f"{track}/{item_id}: split item has no Sol adjudication")
                take(track, item_id, answer, "adjudicated", labels, sources)
            elif track in escalation:
                if rid in audit_rids[track]:
                    take(track, item_id, sol_audit[track][rid], "audit_adjudicated", labels, sources)
                else:
                    take(track, item_id, escalation[track][rid], "escalation_adjudicated", labels, sources)
            else:
                votes = {panel[track][lab][rid] for lab in LABELLERS}
                labels[track] = next(iter(votes))
                sources[track] = "unanimous"
                tallies[track]["unanimous"] = tallies[track].get("unanimous", 0) + 1
        if len(labels) == 2:
            final.append(
                {
                    "id": item_id,
                    "l1": labels["l1"],
                    "l2": labels["l2"],
                    "condition": row["condition"],
                    "channel": row["channel"],
                    "stratum": row["stratum"],
                }
            )
            provenance.append(
                {"id": item_id, "l1_source": sources["l1"], "l2_source": sources["l2"]}
            )
    if drops:
        raise SystemExit(
            "RATIFICATION (d) TRIGGERED — Sol abstained or answered out of vocabulary on "
            f"{len(drops)} adjudicated item(s): {json.dumps(drops)}. Refusing to finalize; the "
            "≤5-drop scoring path needs its reviewed scorer extension first, and >5 pauses the lane."
        )
    if len(final) != EXPECTED_ITEMS:
        raise SystemExit(f"assembled {len(final)} of {EXPECTED_ITEMS} items; refusing")

    out_gold = HERE / "gold_final.jsonl"
    out_prov = HERE / "gold_provenance.jsonl"
    with out_gold.open("w") as handle:
        for row in final:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with out_prov.open("w") as handle:
        for row in provenance:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    id_list_sha = hashlib.sha256(
        "\n".join(sorted(r["item_id"] for r in gold_rows)).encode()
    ).hexdigest()
    freeze = {
        "gold_final_sha256": sha256_file(out_gold),
        "gold_provenance_sha256": sha256_file(out_prov),
        "id_list_sha256": id_list_sha,
        "tallies": tallies,
        "audit_gate": audit_record,
        "track_modes": {
            track: (
                "fully_adjudicated_after_audit_gate_failure"
                if track in escalation
                else "unanimous_auto_accept"
            )
            for track in ("l1", "l2")
        },
        "inputs": {
            p.name: sha256_file(p)
            for p in sorted(
                [
                    HERE / "goldset_lane.jsonl",
                    HERE / "adjudication_queue_l1.jsonl",
                    HERE / "adjudication_queue_l2.jsonl",
                    HERE / "audit_queue_l1.jsonl",
                    HERE / "audit_queue_l2.jsonl",
                    sol_answer("sol_adjudications_l1.jsonl"),
                    sol_answer("sol_adjudications_l2.jsonl"),
                    sol_answer("sol_audit_l1.jsonl"),
                    sol_answer("sol_audit_l2.jsonl"),
                    *[sol_answer(f"sol_escalation_{t}.jsonl") for t in escalation],
                    *[LABELS / f"{lab}__{t}.jsonl" for lab in LABELLERS for t in ("l1", "l2")],
                ]
            )
        },
    }
    (HERE / "GOLD_FREEZE.json").write_text(json.dumps(freeze, indent=1, sort_keys=True) + "\n")
    print(
        f"gold_final.jsonl: {len(final)} rows | l1 {tallies['l1']} | l2 {tallies['l2']} | "
        f"audit l1 {len(audit_record['l1']['disagreements'])}/20 disagreements, "
        f"l2 {len(audit_record['l2']['disagreements'])}/20 | sha {freeze['gold_final_sha256'][:16]}…"
    )


if __name__ == "__main__":
    main()
