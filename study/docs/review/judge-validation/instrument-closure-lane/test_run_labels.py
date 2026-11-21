from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_labels as runner


PRICE = {"input_per_mtok": 1.0, "output_per_mtok": 1.0, "source": "test"}
LABELLER = runner.Labeller("mock", "mock/model")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def packet(request_id: str, prompt: str = "safe prompt") -> dict[str, str]:
    return {"request_id": request_id, "prompt": prompt}


def test_parse_validation_is_track_strict() -> None:
    assert runner.parse_answer(" qualifying\n", "l1") == "qualifying"
    assert runner.parse_answer("attempt", "l2") == "attempt"
    assert runner.parse_answer("Qualifying", "l1") is None
    assert runner.parse_answer("qualifying because", "l1") is None
    assert runner.parse_answer("qualifying", "l2") is None


@pytest.mark.parametrize("bad", [
    {"request_id": "x", "prompt": "safe", "item_id": "leak"},
    {"request_id": "x", "prompt": "mentions nm-secret"},
    {"request_id": "x", "prompt": "mentions /mnt/vault/private"},
    {"request_id": "x", "prompt": "mentions /home/core/private"},
])
def test_blindness_assertion_rejects_extra_keys_and_markers(tmp_path: Path, bad: dict) -> None:
    path = tmp_path / "packets.jsonl"
    write_jsonl(path, [bad])
    with pytest.raises(runner.PacketError):
        runner.load_packets(path)


def test_blindness_allows_subject_typed_mnt_path(tmp_path: Path) -> None:
    path = tmp_path / "packets.jsonl"
    write_jsonl(path, [packet("x", "set BACKUP_DEST=/mnt/backup")])
    assert runner.load_packets(path) == [packet("x", "set BACKUP_DEST=/mnt/backup")]


def test_resume_skips_completed_and_rebuilds_output(tmp_path: Path) -> None:
    labels = tmp_path / "labels"
    calls: list[str] = []

    def transport(_labeller: runner.Labeller, prompt: str) -> runner.TransportResult:
        calls.append(prompt)
        return runner.TransportResult("qualifying", 2, 1)

    rows = [packet("b"), packet("a")]
    runner.run_one(LABELLER, "l1", rows, PRICE, labels, 1.0, transport, sleep=lambda _: None)
    assert len(calls) == 2
    (labels / "mock__l1.jsonl").unlink()
    runner.run_one(LABELLER, "l1", rows, PRICE, labels, 1.0, transport, sleep=lambda _: None)
    assert len(calls) == 2
    output = runner.read_jsonl(labels / "mock__l1.jsonl")
    assert [row["request_id"] for row in output] == ["a", "b"]


def test_ambiguous_reservation_is_charged_and_never_recalled(tmp_path: Path) -> None:
    labels = tmp_path / "labels"
    journal = labels / "mock__l1.journal.jsonl"
    runner.append_journal(journal, {
        "event": "reserved", "request_id": "a", "attempt": 1,
        "bound_usd": 0.25, "input_token_bound": 10, "output_token_bound": 16,
    })
    runner.append_journal(journal, {
        "event": "settled", "request_id": "a", "attempt": 1,
        "charged_usd": 0.01, "input_tokens": 1, "output_tokens": 1,
    })
    calls = 0

    def transport(_labeller: runner.Labeller, _prompt: str) -> runner.TransportResult:
        nonlocal calls
        calls += 1
        return runner.TransportResult("qualifying", 1, 1)

    runner.run_one(LABELLER, "l1", [packet("a")], PRICE, labels, 1.0, transport)
    completed, exhausted, ambiguous, charged, _ = runner.journal_state(journal)
    assert completed == set()
    assert exhausted == set()
    assert ambiguous == {"a"}
    assert charged == pytest.approx(0.25)
    assert calls == 0


def test_cap_stop_is_clean_and_leaves_uncalled_item_resumable(tmp_path: Path) -> None:
    labels = tmp_path / "labels"
    rows = [packet("a", "x" * 100), packet("b", "x" * 100)]
    one_bound = runner.call_bound(PRICE, rows[0]["prompt"], LABELLER.max_tokens)
    calls: list[str] = []

    def transport(_labeller: runner.Labeller, prompt: str) -> runner.TransportResult:
        calls.append(prompt)
        return runner.TransportResult("qualifying")  # missing usage settles at bound

    _, stopped = runner.run_one(
        LABELLER, "l1", rows, PRICE, labels, one_bound + 1e-12,
        transport, sleep=lambda _: None,
    )
    assert stopped
    assert len(calls) == 1
    assert [row["request_id"] for row in runner.read_jsonl(labels / "mock__l1.jsonl")] == ["a"]


def test_unpriced_refusal() -> None:
    with pytest.raises(runner.PriceError, match="unpriced model"):
        runner.require_prices({}, [LABELLER])
    placeholder = {
        "mock/model": {
            "input_per_mtok": 1.0, "output_per_mtok": 1.0,
            "source": "placeholder pending check",
        }
    }
    with pytest.raises(runner.PriceError, match="placeholder"):
        runner.require_prices(placeholder, [LABELLER])


def _synthetic_split_fixture(root: Path) -> tuple[Path, Path, Path]:
    packets = root / "packets"
    labels = root / "labels"
    out = root / "out"
    l1, l2, joins = [], [], []
    for number in range(30):
        item = f"item-{number:02d}"
        for track, rows in (("l1", l1), ("l2", l2)):
            request_id = f"{track}-{number:02d}"
            rows.append(packet(request_id, f"{track} prompt {number}"))
            joins.append({"request_id": request_id, "item_id": item})
    write_jsonl(packets / "l1_packets.jsonl", l1)
    write_jsonl(packets / "l2_packets.jsonl", l2)
    write_jsonl(packets / "packet_join.jsonl", joins)
    labellers = tuple(runner.Labeller(f"p{x}", f"m{x}") for x in range(3))
    for labeller_index, labeller in enumerate(labellers):
        for track, rows, unanimous in (
            ("l1", l1, "qualifying"), ("l2", l2, "attempt")
        ):
            output = []
            for number, row in enumerate(rows):
                parsed = unanimous
                if number == 0 and labeller_index == 2:
                    parsed = "not_qualifying" if track == "l1" else "no_attempt"
                if number == 1 and labeller_index == 1:
                    parsed = "cannot_determine"
                output.append({"request_id": row["request_id"], "raw": parsed, "parsed": parsed})
            write_jsonl(labels / f"{labeller.name}__{track}.jsonl", output)
    return packets, labels, out, labellers


def test_split_and_audit_are_deterministic_and_track_blind(tmp_path: Path) -> None:
    packets, labels, out, labellers = _synthetic_split_fixture(tmp_path)
    first = runner.compute_splits(packets, labels, out, labellers)
    snapshots = {path.name: path.read_bytes() for path in out.glob("*.jsonl")}
    second = runner.compute_splits(packets, labels, out, labellers)
    assert first == second == {
        "l1": {"unanimous": 28, "adjudication": 2, "audit": 20},
        "l2": {"unanimous": 28, "adjudication": 2, "audit": 20},
    }
    assert snapshots == {path.name: path.read_bytes() for path in out.glob("*.jsonl")}
    adjudication = runner.read_jsonl(out / "adjudication_queue_l2.jsonl")
    assert all(set(row) == {"request_id", "prompt"} for row in adjudication)
    assert all("Panel labels to adjudicate" in row["prompt"] for row in adjudication)
    assert all("ground-truth" not in row["prompt"].lower() for row in adjudication)


@pytest.mark.parametrize(("name", "model", "cap", "provider", "reasoning"), [
    ("gemini-3.7-flash", "google/gemini-3.7-flash", 256, "google-vertex", None),
    ("grok-4.6", "x-ai/grok-4.6", 1024, "xai", {"effort": "low", "exclude": True}),
    ("glm-5.3", "z-ai/glm-5.3", 1024, "z-ai", {"effort": "low", "exclude": True}),
])
def test_request_pins_priced_provider_and_sampling(
    name: str, model: str, cap: int, provider: str, reasoning: dict | None,
) -> None:
    labeller = next(item for item in runner.LABELLERS if item.name == name)
    payload = runner.request_payload(labeller, "opaque packet")
    assert labeller.model == model
    assert payload["max_tokens"] == cap == labeller.max_tokens
    assert payload["temperature"] == 0.0
    assert payload["messages"] == [{"role": "user", "content": "opaque packet"}]
    assert "system" not in payload
    assert payload["extra_body"]["provider"] == {
        "only": [provider], "allow_fallbacks": False,
    }
    if reasoning is None:
        assert payload["extra_body"]["extra_body"] == {
            "google": {"thinking_config": {"thinking_budget": 0}}
        }
    else:
        assert payload["extra_body"]["reasoning"] == reasoning


def test_unparseable_is_exhausted_then_explicitly_retryable(tmp_path: Path) -> None:
    labels = tmp_path / "labels"
    answers = iter(["", "bad", "still bad", "nope", "qualifying"])

    def transport(_labeller: runner.Labeller, _prompt: str) -> runner.TransportResult:
        return runner.TransportResult(next(answers), 2, 1)

    runner.run_one(
        LABELLER, "l1", [packet("a")], PRICE, labels, 1.0,
        transport, sleep=lambda _: None,
    )
    journal = labels / "mock__l1.journal.jsonl"
    completed, exhausted, ambiguous, charged_before, rows = runner.journal_state(journal)
    assert completed == set()
    assert exhausted == {"a"}
    assert ambiguous == set()
    assert rows == {}
    assert not (labels / "mock__l1.jsonl").read_text(encoding="utf-8")

    runner.run_one(
        LABELLER, "l1", [packet("a")], PRICE, labels, 1.0,
        transport, sleep=lambda _: None, retry_exhausted=True,
    )
    completed, exhausted, ambiguous, charged_after, rows = runner.journal_state(journal)
    assert completed == {"a"}
    assert exhausted == set()
    assert ambiguous == set()
    assert rows["a"]["parsed"] == "qualifying"
    assert charged_after > charged_before
    reservations = [
        row for row in runner.read_jsonl(journal) if row["event"] == "reserved"
    ]
    assert [row["attempt"] for row in reservations] == [1, 2, 3, 4, 5]


def test_retry_exhausted_calls_only_exhausted_not_untouched(tmp_path: Path) -> None:
    labels = tmp_path / "labels"
    exhausted_packet = packet("a", "retry me")
    untouched_packet = packet("b", "do not call me")

    def invalid(_labeller: runner.Labeller, _prompt: str) -> runner.TransportResult:
        return runner.TransportResult("invalid", 2, 1)

    runner.run_one(
        LABELLER, "l1", [exhausted_packet], PRICE, labels, 1.0,
        invalid, sleep=lambda _: None,
    )
    packets_by_track = {
        "l1": [exhausted_packet, untouched_packet],
        "l2": [packet("c", "also untouched")],
    }
    projection, details = runner.projected_cost(
        packets_by_track, {LABELLER.model: PRICE}, labels,
        labellers=[LABELLER], retry_exhausted=True,
    )
    l1 = next(row for row in details if row["track"] == "l1")
    l2 = next(row for row in details if row["track"] == "l2")
    assert l1["remaining"] == 1
    assert l2["remaining"] == 0
    assert projection == pytest.approx(
        runner.call_bound(PRICE, exhausted_packet["prompt"], LABELLER.max_tokens)
    )

    calls: list[str] = []

    def valid(_labeller: runner.Labeller, prompt: str) -> runner.TransportResult:
        calls.append(prompt)
        return runner.TransportResult("qualifying", 2, 1)

    runner.run_one(
        LABELLER, "l1", [exhausted_packet, untouched_packet], PRICE, labels, 1.0,
        valid, sleep=lambda _: None, retry_exhausted=True,
    )
    assert calls == ["retry me"]


def test_probe_uses_six_synthetic_packets_and_normal_metering(tmp_path: Path, capsys) -> None:
    calls: list[tuple[str, str]] = []

    def transport(labeller: runner.Labeller, prompt: str) -> runner.TransportResult:
        calls.append((labeller.name, prompt))
        answer = "qualifying" if "qualifying" in prompt else "attempt"
        return runner.TransportResult(answer, 3, 1)

    result = runner.main([
        "--probe", "--labels-dir", str(tmp_path / "labels"), "--budget", "8.0",
    ], transport=transport, sleep=lambda _: None)
    assert result == 0
    assert len(calls) == 6
    assert all("ground truth" not in prompt.lower() for _, prompt in calls)
    output = capsys.readouterr().out
    assert output.count("PROBE ") == 6
    assert "parsed=\"qualifying\"" in output
    assert "parsed=\"attempt\"" in output


def test_probe_exits_nonzero_and_preserves_unparseable_raw(tmp_path: Path, capsys) -> None:
    def transport(_labeller: runner.Labeller, _prompt: str) -> runner.TransportResult:
        return runner.TransportResult("wrong wire answer", 3, 2)

    result = runner.main([
        "--probe", "--labels-dir", str(tmp_path / "labels"), "--budget", "8.0",
    ], transport=transport, sleep=lambda _: None)
    assert result == 2
    output = capsys.readouterr().out
    assert output.count("PROBE ") == 6
    assert output.count('raw="wrong wire answer" parsed=null') == 6
    assert output.count("state=exhausted") == 6
