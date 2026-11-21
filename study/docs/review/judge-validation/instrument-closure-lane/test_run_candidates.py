"""Tests for run_candidates.py's Grok post-label fixes (findings 1-7)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_candidates as rc
from run_labels import RunnerError, journal_state


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(rc.time, "sleep", lambda seconds: None)


PRICE = {"input_per_mtok": 1.0, "output_per_mtok": 1.0, "source": "test"}
ENDPOINT = rc.Endpoint(
    name="test-endpoint", model="test-model", base_url="http://x", api_key_env="X",
    max_tokens=8, price_key="test-model",
)


def setup_dirs(tmp_path, monkeypatch):
    labels = tmp_path / "labels"
    out = tmp_path / "candidates"
    labels.mkdir()
    out.mkdir()
    monkeypatch.setattr(rc, "LABELS", labels)
    monkeypatch.setattr(rc, "OUT", out)
    monkeypatch.setattr(rc, "HERE", tmp_path)
    return labels, out


class StubClient:
    """Sequence of behaviors: 'ok:<word>', 'ok-no-usage:<word>', 'raise'."""

    def __init__(self, behaviors):
        self.behaviors = list(behaviors)
        self.calls = 0

        stub = self

        class _Completions:
            @staticmethod
            def create(**kwargs):
                stub.calls += 1
                behavior = stub.behaviors.pop(0)
                if behavior == "raise":
                    raise RuntimeError("boom")

                class Usage:
                    prompt_tokens = 10
                    completion_tokens = 2

                class Message:
                    content = behavior.split(":", 1)[1]

                class Choice:
                    message = Message()

                class Response:
                    choices = [Choice()]
                    usage = None if behavior.startswith("ok-no-usage") else Usage()

                return Response()

        class _Chat:
            completions = _Completions()

        self.chat = _Chat()


def run(tmp_path, monkeypatch, behaviors, *, retry_exhausted=False, queue=None):
    _, out = setup_dirs(tmp_path, monkeypatch)
    client = StubClient(behaviors)
    monkeypatch.setattr(rc, "make_client", lambda endpoint: client)
    journal = out / "test.journal.jsonl"
    output = out / "test.jsonl"
    rc.run_queue(
        label="test", endpoint=ENDPOINT, journal=journal, output=output,
        queue=queue or [("req-1", None, "hello")],
        prices={"test-model": PRICE}, parse=lambda raw: raw if raw == "yes" else None,
        retry_exhausted=retry_exhausted, log=lambda m: None,
    )
    return journal, output, client


def test_success_settles_at_actual_usage(tmp_path, monkeypatch):
    journal, output, _ = run(tmp_path, monkeypatch, ["ok:yes"])
    rows = [json.loads(l) for l in journal.open()]
    settled = [r for r in rows if r["event"] == "settled"]
    assert settled[0]["charged_usd"] == pytest.approx(12 / 1_000_000)
    assert [json.loads(l)["parsed"] for l in output.open()] == ["yes"]


def test_exception_settles_at_bound_not_zero(tmp_path, monkeypatch):
    journal, _, _ = run(tmp_path, monkeypatch, ["raise", "ok:yes"])
    rows = [json.loads(l) for l in journal.open()]
    reserved = {r["attempt"]: r for r in rows if r["event"] == "reserved"}
    settled = {r["attempt"]: r for r in rows if r["event"] == "settled"}
    assert settled[1]["charged_usd"] == pytest.approx(reserved[1]["bound_usd"])
    assert settled[1]["charged_usd"] > 0
    assert settled[2]["charged_usd"] == pytest.approx(12 / 1_000_000)


def test_missing_usage_settles_at_bound(tmp_path, monkeypatch):
    journal, output, _ = run(tmp_path, monkeypatch, ["ok-no-usage:yes"])
    rows = [json.loads(l) for l in journal.open()]
    reserved = [r for r in rows if r["event"] == "reserved"][0]
    settled = [r for r in rows if r["event"] == "settled"][0]
    assert settled["charged_usd"] == pytest.approx(reserved["bound_usd"])
    assert [json.loads(l)["parsed"] for l in output.open()] == ["yes"]


def test_retry_exhausted_continues_attempt_numbering(tmp_path, monkeypatch):
    journal, _, client = run(tmp_path, monkeypatch, ["ok:no"] * rc.MAX_ATTEMPTS)
    completed, exhausted, _, _, _ = journal_state(journal)
    assert exhausted == {"req-1"} and not completed
    # Re-run with the flag; the same journal must accept the new settlements.
    client2 = StubClient(["ok:yes"])
    monkeypatch.setattr(rc, "make_client", lambda endpoint: client2)
    rc.run_queue(
        label="test", endpoint=ENDPOINT, journal=journal,
        output=journal.parent / "test.jsonl",
        queue=[("req-1", None, "hello")], prices={"test-model": PRICE},
        parse=lambda raw: raw if raw == "yes" else None,
        retry_exhausted=True, log=lambda m: None,
    )
    completed, exhausted, _, _, _ = journal_state(journal)
    assert completed == {"req-1"} and not exhausted
    attempts = [json.loads(l)["attempt"] for l in journal.open()
                if json.loads(l).get("event") == "reserved"]
    assert attempts == [1, 2, 3, 4, 5]


def test_without_flag_exhausted_not_redispatched(tmp_path, monkeypatch):
    journal, _, client = run(tmp_path, monkeypatch, ["ok:no"] * rc.MAX_ATTEMPTS)
    calls_before = client.calls
    client2 = StubClient(["ok:yes"])
    monkeypatch.setattr(rc, "make_client", lambda endpoint: client2)
    rc.run_queue(
        label="test", endpoint=ENDPOINT, journal=journal,
        output=journal.parent / "test.jsonl",
        queue=[("req-1", None, "hello")], prices={"test-model": PRICE},
        parse=lambda raw: raw, retry_exhausted=False, log=lambda m: None,
    )
    assert client2.calls == 0 and calls_before == rc.MAX_ATTEMPTS


def test_validate_prices_refuses_placeholder_and_missing(tmp_path, monkeypatch):
    good = {e.price_id(): dict(PRICE) for e in (*rc.CANDIDATES, rc.ROUTER)}
    rc.validate_prices(good)
    bad = {k: dict(v) for k, v in good.items()}
    bad[rc.CANDIDATES[0].price_id()]["source"] = "PLACEHOLDER pending"
    with pytest.raises(Exception, match="verified source"):
        rc.validate_prices(bad)
    with pytest.raises(Exception, match="no committed price row"):
        rc.validate_prices({})


def test_require_freeze_refuses_without_files(tmp_path, monkeypatch):
    setup_dirs(tmp_path, monkeypatch)
    with pytest.raises(RunnerError, match="gold has not frozen"):
        rc.require_freeze()


def test_require_freeze_refuses_hash_mismatch(tmp_path, monkeypatch):
    setup_dirs(tmp_path, monkeypatch)
    (tmp_path / "gold_final.jsonl").write_text('{"id": "x"}\n')
    (tmp_path / "GOLD_FREEZE.json").write_text(json.dumps({"gold_final_sha256": "0" * 64}))
    with pytest.raises(RunnerError, match="does not match"):
        rc.require_freeze()


def test_assemble_timing_refuses_unfinished_router(tmp_path, monkeypatch):
    setup_dirs(tmp_path, monkeypatch)
    gold = [
        {"item_id": "it-tool", "channel": "tool"},
        {"item_id": "it-prose", "channel": "prose"},
    ]
    with pytest.raises(SystemExit, match="INCOMPLETE"):
        rc.assemble_timing(gold, {"it-prose": "some prose"}, 1)


def test_assemble_timing_exhausted_becomes_cannot_determine(tmp_path, monkeypatch):
    _, out = setup_dirs(tmp_path, monkeypatch)
    gold = [
        {"item_id": "it-tool", "channel": "tool"},
        {"item_id": "it-prose", "channel": "prose"},
        {"item_id": "it-empty", "channel": "prose"},
    ]
    rid = rc.router_request_id("it-prose")
    journal = out / "router_pass1.journal.jsonl"
    with journal.open("w") as handle:
        handle.write(json.dumps({"event": "reserved", "request_id": rid, "attempt": 1,
                                 "bound_usd": 0.001}) + "\n")
        handle.write(json.dumps({"event": "settled", "request_id": rid, "attempt": 1,
                                 "charged_usd": 0.001}) + "\n")
        handle.write(json.dumps({"event": "exhausted", "request_id": rid,
                                 "output": {"request_id": rid, "raw": "", "parsed": None}}) + "\n")
    rc.assemble_timing(gold, {"it-prose": "some prose", "it-empty": "  "}, 1)
    rows = {json.loads(l)["id"]: json.loads(l)["parsed"]
            for l in (tmp_path / "timing_pass1.jsonl").open()}
    assert rows == {"it-tool": "attempt", "it-prose": "cannot_determine",
                    "it-empty": "no_attempt"}
