"""The cost meter, and the ceiling that refuses to dispatch a call.

R17: a $600 hard ceiling on API spend for Pilot I, reported at $300.

Sol's third review found the first version was not a ceiling at all. It checked
headroom only between runs, so a $0.05 ceiling was overshot to $43.50, an
870-fold breach, and unpriced models and zero-usage responses were warnings that
let execution continue. A control that reports a breach after the money is spent
is a meter, not a ceiling.

This version reserves worst-case headroom **before** each call is dispatched:

    worst case = prompt tokens (counted or estimated, then padded)
                 * input price
               + max_tokens for this call
                 * output price

If the reservation does not fit under the ceiling the call is refused and the
batch halts, so spend cannot exceed the authorized figure by even one call.
Three conditions are halts and never warnings:

  * no price for the model, because an unpriced call cannot be bounded;
  * a reservation that would exceed the ceiling;
  * a response reporting zero usage where a price exists, because a meter that
    reads zero is either broken or lying, and continuing would spend blind.

The estimator errs high on purpose. Under-estimating is the only failure mode
that spends money it should not, so the character-per-token divisor is
deliberately small and a safety factor is applied on top.

Spend checkpoints are the second control, added at the R32 gate. The
registration commits to budget-drop decisions taken between tranches at spend
checkpoints, and the meter used to implement that as a boolean flipped at the
report line, which halted nothing. A crossed checkpoint now stops dispatch at a
completed balanced-tranche boundary and stays stopped until an operator resumes
the batch naming that checkpoint. It is not the ceiling: no call is refused and
nothing is recorded as a spend halt, because the batch is waiting for a decision
rather than out of money.
"""

import decimal
import json
import math
import os
import uuid

# The fallback bound, used only when a provider cannot be asked to count.
#
# Sol's fourth review: characters divided by 3.0 with a 1.25 multiplier "is
# conservative for ordinary English but does not bound token-dense Unicode,
# serialized framing, or a future tokenizer". It was an estimate wearing the
# costume of a bound.
#
# UTF-8 byte length IS a bound. Every token in a byte-level BPE vocabulary
# encodes at least one byte, so a string of N bytes can never tokenize to more
# than N tokens, for any text, any script, and any future vocabulary of that
# family. It is loose, often by 3 to 4 times, and that looseness is the price of
# being provably correct rather than usually correct. Provider counting is used
# wherever it is available, and this is what happens when it is not.
FALLBACK_BOUND = "utf8_bytes"


class CeilingReached(Exception):
    """Raised before a call is dispatched. The call does not happen."""

    def __init__(self, message, kind="ceiling"):
        super().__init__(message)
        self.kind = kind


class CheckpointReached(Exception):
    """Raised at a completed tranche boundary after spend crosses a checkpoint.

    Deliberately NOT a CeilingReached. The hard ceiling is a refusal to dispatch
    a call that could carry spend past the authorized figure, and everything
    downstream of it is a spend_ceiling row. A checkpoint is the other thing the
    registration commits to: a decision point between tranches where the
    operator either releases the next tranche or drops arms from it. Dispatch
    stops, no call is refused, nothing is marked spend_ceiling, and the batch
    resumes only when an operator names the checkpoint.
    """

    def __init__(self, message, checkpoint_usd, total_usd):
        super().__init__(message)
        self.checkpoint_usd = float(checkpoint_usd)
        self.total_usd = float(total_usd)
        self.kind = "checkpoint"


class UnpricedModel(CeilingReached):
    def __init__(self, message):
        super().__init__(message, kind="unpriced")


class UnmeteredResponse(CeilingReached):
    def __init__(self, message):
        super().__init__(message, kind="unmetered")


class IncompletePrice(CeilingReached):
    def __init__(self, message):
        super().__init__(message, kind="incomplete_price")


class AccountingError(ValueError):
    """Stored or live accounting data is unsafe to use."""


def _finite_number(value, name, *, positive=False, non_negative=False):
    """Audit item 5: accept real finite numbers, never bools or NaN/Inf."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AccountingError(f"{name} must be a number (booleans are not numbers here)")
    number = float(value)
    if not math.isfinite(number):
        raise AccountingError(f"{name} must be finite")
    if positive and number <= 0:
        raise AccountingError(f"{name} must be positive")
    if non_negative and number < 0:
        raise AccountingError(f"{name} must be non-negative")
    return number


def _count(value, name):
    """Audit item 5: validate a finite, non-negative integer token/count field."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AccountingError(f"{name} must be a non-negative integer")
    number = float(value)
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        raise AccountingError(f"{name} must be a finite non-negative integer")
    return int(number)


def _assert_amount(value, name):
    return _finite_number(value, name, non_negative=True)


def micro_usd(amount):
    """Dollars to integer microdollars: the ONE canonical conversion.

    R43 re-review: the journal writer and the resume verifier used to round by
    different paths — the writer rounded reconciled cost and outstanding
    bounds separately and added the rounded halves, the verifier summed the
    raw components and rounded once — so two half-microdollar components could
    close below the floor a verifier later derived from the very same rows.
    Every figure the harness closes a journal with, and every floor a resume
    checks against, now passes through this helper: decimal arithmetic over
    the float's own shortest decimal representation, ties to even at the
    microdollar. Same inputs, same integer, whoever is asking.
    """
    number = _finite_number(amount, "amount")
    scaled = decimal.Decimal(str(number)) * 1_000_000
    return int(scaled.to_integral_value(rounding=decimal.ROUND_HALF_EVEN))


def sub_micro_usd(amount):
    """True when a dollars figure carries precision below one microdollar.

    The writer quantizes every closing figure through micro_usd, so a stored
    close carrying sub-microdollar precision was not written by this harness
    and is rejected as non-canonical rather than compared approximately.
    """
    number = _finite_number(amount, "amount")
    return (decimal.Decimal(str(number)) * 1_000_000) % 1 != 0


def bound_prompt_tokens(prompt_text=None, prompt_tokens=None):
    """A proven upper bound on the prompt's token count.

    `prompt_tokens` is the provider's own count where the client could get one,
    and is used as given. Otherwise the UTF-8 byte length is returned, which
    bounds the count from above for any byte-level BPE tokenizer.
    """
    if prompt_tokens is not None:
        return _count(prompt_tokens, "prompt_tokens")
    return len((prompt_text or "").encode("utf-8")) + 1


# Every price entry must carry these. A present entry with a missing rate used to
# default that rate to zero, so an incomplete frozen price could let a call cost
# more than it reserved (Sol, round 4).
BASE_RATE_FIELDS = ("input_per_mtok", "output_per_mtok")
CACHE_RATE_FIELDS = ("cache_read_per_mtok", "cache_write_per_mtok")


class PriceTable:
    """USD per million tokens, per model id, from the config file.

    Prices are verified and recorded at the freeze (R24). A model with no entry
    is not free, it is unbounded, so asking for its price raises. So does an
    entry that is incomplete, or one still marked `placeholder: true`.
    """

    def __init__(self, prices):
        # Audit item 5: the enforcement object revalidates every configured
        # rate even when callers bypass config.load_config in tests or code.
        if prices is None:
            prices = {}
        if not isinstance(prices, dict):
            raise AccountingError("prices must be an object")
        for model_id, entry in prices.items():
            if not isinstance(entry, dict):
                raise AccountingError(f"prices.{model_id} must be an object")
            for name, value in entry.items():
                if name.endswith("_per_mtok"):
                    _finite_number(value, f"prices.{model_id}.{name}", non_negative=True)
        self.prices = prices

    def has(self, model_id):
        return model_id in self.prices

    def validate(self, model_id, required_fields=BASE_RATE_FIELDS):
        """Raise unless this model's price is complete and verified.

        Called before an arm starts, so a placeholder is caught at batch start
        rather than after the first call has already been paid for.
        """
        entry = self.prices.get(model_id)
        if entry is None:
            raise UnpricedModel(
                f"no price for model {model_id!r}. An unpriced call cannot be bounded "
                "against the ceiling, so the batch halts rather than spending blind."
            )
        if entry.get("placeholder"):
            raise IncompletePrice(
                f"the price for {model_id!r} is still marked placeholder. Enter the verified "
                "rates from the provider's published pricing and remove the marker; the batch "
                "will not start an arm it cannot cost correctly."
            )
        missing = [name for name in required_fields if entry.get(name) is None]
        if missing:
            raise IncompletePrice(
                f"the price for {model_id!r} is missing {', '.join(missing)}. A missing rate "
                "used to default to zero, which would let a call cost more than it reserved."
            )
        # Audit item 5: a present but negative/non-finite rate is not a price.
        for name, value in entry.items():
            if name.endswith("_per_mtok"):
                _finite_number(value, f"prices.{model_id}.{name}", non_negative=True)
        return entry

    def entry(self, model_id):
        return self.validate(model_id)

    def cost_for(self, model_id, usage):
        entry = self.entry(model_id)
        if not isinstance(usage, dict):
            raise AccountingError("usage must be an object")
        input_tokens = _count(usage.get("input_tokens", 0), "usage.input_tokens")
        output_tokens = _count(usage.get("output_tokens", 0), "usage.output_tokens")
        cached_read = _count(usage.get("cache_read_input_tokens", 0),
                             "usage.cache_read_input_tokens")
        cache_write = _count(usage.get("cache_creation_input_tokens", 0),
                             "usage.cache_creation_input_tokens")
        cost = input_tokens * entry.get("input_per_mtok", 0.0)
        cost += output_tokens * entry.get("output_per_mtok", 0.0)
        cost += cached_read * entry.get("cache_read_per_mtok", 0.0)
        cost += cache_write * entry.get("cache_write_per_mtok", 0.0)
        return _assert_amount(cost / 1_000_000.0, "calculated call cost")

    def worst_case(self, model_id, prompt_tokens, max_tokens):
        """The most this call could cost, as an upper bound and not an estimate.

        Prompt tokens are priced at the HIGHEST rate any of them could attract,
        which is usually the cache-write rate rather than the base input rate:
        Anthropic bills a cache write at about 1.25 times input, so reserving at
        the input rate would under-reserve every call that writes the cache. A
        cache read is cheaper and is never assumed, because a reservation must
        not assume a discount that may not apply.

        Output is priced at max_tokens, which is a hard cap by definition.
        """
        entry = self.entry(model_id)
        input_rate = max(
            entry.get("input_per_mtok", 0.0) or 0.0,
            entry.get("cache_write_per_mtok", 0.0) or 0.0,
        )
        prompt_tokens = _count(prompt_tokens, "prompt_tokens")
        max_tokens = _count(max_tokens, "max_tokens")
        cost = prompt_tokens * input_rate
        cost += max_tokens * (entry.get("output_per_mtok", 0.0) or 0.0)
        return _assert_amount(cost / 1_000_000.0, "calculated reservation")


class CostMeter:
    def __init__(self, prices, hard_ceiling_usd=600.0, report_at_usd=300.0,
                 checkpoints_usd=()):
        self.table = PriceTable(prices)
        # Audit item 5: validate controls again at the enforcement boundary.
        self.hard_ceiling_usd = _finite_number(
            hard_ceiling_usd, "hard_ceiling_usd", positive=True)
        self.report_at_usd = _finite_number(report_at_usd, "report_at_usd", positive=True)
        # The registered spend checkpoints. Crossing one halts later tranches
        # until an operator names it, which is what makes "budget-drop
        # decisions are taken between tranches at spend checkpoints" a control
        # rather than a sentence. report_at_usd only ever flipped a boolean at
        # the report line, which halted nothing.
        checkpoints = tuple(_finite_number(value, f"checkpoints_usd[{index}]", positive=True)
                            for index, value in enumerate(checkpoints_usd or ()))
        if any(right <= left for left, right in zip(checkpoints, checkpoints[1:])):
            raise AccountingError("checkpoints_usd must be strictly increasing")
        if any(value >= self.hard_ceiling_usd for value in checkpoints):
            raise AccountingError("every spend checkpoint must be below the hard ceiling")
        self.checkpoints_usd = checkpoints
        self.acknowledged_checkpoints = []
        self.checkpoint_log = []
        self.total_usd = 0.0
        self.per_run = {}
        self.report_threshold_crossed = False
        self.halted = False
        self.halt_reason = None
        self.halt_kind = None
        self.calls_dispatched = 0
        self.calls_refused = 0
        self.tranches_refused = 0
        self.largest_reservation_usd = 0.0
        # Every dispatched call's reservation, and the actual cost that followed,
        # so "the reservation covered the call" is a measurement rather than a
        # claim. A positive overshoot anywhere means the bound leaked.
        self.reservations = []
        # GPT B7 / audit item 6: every dispatched attempt remains independently
        # reserved until that exact call is reconciled. A retry cannot overwrite
        # the failed attempt's reservation.
        self.outstanding_reservations = {}
        self._pending_by_callsite = {}
        self.max_overshoot_usd = 0.0
        self.restored_runs = 0
        self.restored_cost_usd = 0.0
        self._journal_paths = {}

    # ------------------------------------------------------------- accounting

    def open_run(self, run_id):
        self.per_run.setdefault(
            run_id,
            {"cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0, "calls": 0,
             "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
        )

    def bind_run_journal(self, run_id, path):
        """Persist reservations and actual usage for an interruptible attempt."""
        self._journal_paths[run_id] = path

    def _journal(self, run_id, record):
        path = self._journal_paths.get(run_id)
        if not path:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()

    def close_run_journal(self, run_id, record):
        """Append the attempt's closing totals. The journal outlives the attempt.

        R43 step 2 (Sol finding 8, fuller form): the journal is the sole resume
        authority, so it is never deleted once run.json is written. This closing
        record is what marks an attempt finished; a journal without one is an
        interrupted attempt, and resume verifies the run record against the
        journal rather than trusting run.json on its own. The totals here are
        the attempt's final charged figures, ambiguous reservations at their
        bound included, exactly as run.json records them.
        """
        self._journal(run_id, {
            "type": "close",
            "cost_usd": record.get("cost_usd", 0.0),
            "model_calls": record.get("model_calls", 0),
            "input_tokens": record.get("input_tokens", 0),
            "output_tokens": record.get("output_tokens", 0),
            "cache_read_input_tokens": record.get("cache_read_input_tokens", 0),
            "cache_creation_input_tokens": record.get("cache_creation_input_tokens", 0),
            "outstanding_reservations": record.get("outstanding_reservations", 0),
            "outstanding_reservations_usd": record.get("outstanding_reservations_usd", 0.0),
            "termination_reason": record.get("termination_reason"),
        })
        # No row may legitimately follow the close, so the binding is retired.
        self._journal_paths.pop(run_id, None)

    def restore_run(self, run_id, record):
        """Restore a completed cell when its batch is resumed.

        The recorded cost is authoritative for already dispatched calls. This
        keeps the original batch ceiling intact instead of granting a resumed
        process a fresh budget.
        """
        # Audit item 4: restored accounting is evidence, not a best-effort hint.
        if not isinstance(record, dict):
            raise AccountingError(f"restored record for {run_id} must be an object")
        for required in ("cost_usd", "model_calls"):
            if required not in record:
                raise AccountingError(f"restored record for {run_id} is missing {required}")
        recorded_cost = _assert_amount(record["cost_usd"], f"{run_id}.cost_usd")
        calls = _count(record["model_calls"], f"{run_id}.model_calls")

        def integer(name):
            if name not in record:
                if calls == 0:
                    return 0
                raise AccountingError(f"restored record for {run_id} is missing {name}")
            return _count(record[name], f"{run_id}.{name}")
        restored = {
            "cost_usd": recorded_cost,
            "input_tokens": integer("input_tokens"),
            "output_tokens": integer("output_tokens"),
            "calls": calls,
            "cache_read_input_tokens": integer("cache_read_input_tokens"),
            "cache_creation_input_tokens": integer("cache_creation_input_tokens"),
        }
        if run_id in self.per_run:
            return
        self.per_run[run_id] = restored
        self.total_usd += recorded_cost
        _assert_amount(self.total_usd, "restored total_usd")
        self.calls_dispatched += calls
        self.restored_runs += 1
        self.restored_cost_usd += recorded_cost
        if self.total_usd >= self.report_at_usd:
            self.report_threshold_crossed = True

    def headroom(self):
        # GPT B7: all ambiguous/in-flight calls consume headroom simultaneously.
        reserved = sum(item["reserved_usd"] for item in self.outstanding_reservations.values())
        _assert_amount(reserved, "outstanding reservation total")
        headroom = self.hard_ceiling_usd - self.total_usd - reserved
        if not math.isfinite(headroom):
            raise AccountingError("calculated headroom must be finite")
        return headroom

    # ------------------------------------------------------------ the control

    def assert_priced(self, model_id, required_fields=BASE_RATE_FIELDS):
        """Refuse to start an arm whose price is absent, incomplete, or a placeholder."""
        try:
            self.table.validate(model_id, required_fields)
        except CeilingReached as problem:
            self._halt(str(problem), problem.kind)
            raise
        return True

    def assert_tranche_fits(self, reserved_cost_usd, tranche_index):
        """GPT B6, amended 2026-08-30: refuse a tranche no single cell can fit.

        The figure passed in is the worst case of the most expensive SINGLE CELL
        in the tranche, not the sum over every cell. The per-call ceiling in
        `reserve` remains the spend control.
        """
        reservation = _assert_amount(reserved_cost_usd, "tranche reserved cost")
        if reservation > self.headroom():
            self.tranches_refused += 1
            self._halt(
                f"refused before tranche {tranche_index}: its most expensive single cell "
                f"could reserve up to ${reservation:.4f}, but only ${self.headroom():.4f} "
                f"remains under the ${self.hard_ceiling_usd:.2f} hard ceiling. No cell in "
                "the tranche started.",
                "ceiling",
            )
            raise CeilingReached(self.halt_reason, "ceiling")
        return reservation

    def reserve(self, run_id, model_id, prompt_text=None, prompt_tokens=None, max_tokens=0):
        """Decide whether the NEXT call may be dispatched. Raises if it may not.

        Called before every paid call, the route classifier's included.
        `prompt_tokens` is the provider's own count where the client could get
        one; otherwise the UTF-8 byte length bounds it from above. Returns the
        reservation so the caller can record what the call was checked against.
        """
        self.open_run(run_id)
        if self.halted:
            raise CeilingReached(self.halt_reason or "the batch is halted", self.halt_kind or "ceiling")
        try:
            tokens = bound_prompt_tokens(prompt_text, prompt_tokens)
            reservation = self.table.worst_case(model_id, tokens, max_tokens)
        except (UnpricedModel, IncompletePrice) as problem:
            self.calls_refused += 1
            self._halt(str(problem), problem.kind)
            raise
        self.largest_reservation_usd = max(self.largest_reservation_usd, reservation)
        if reservation > self.headroom():
            self.calls_refused += 1
            self._halt(
                f"refused before dispatch: this call could cost up to ${reservation:.4f}, "
                f"and spent plus outstanding reservations leave only "
                f"${self.headroom():.4f} of the ${self.hard_ceiling_usd:.2f} ceiling. "
                "No request was sent.",
                "ceiling",
            )
            raise CeilingReached(self.halt_reason, "ceiling")
        self.calls_dispatched += 1
        reservation_id = uuid.uuid4().hex
        item = {"reservation_id": reservation_id, "run_id": run_id, "model_id": model_id,
                                  "prompt_tokens_bound": tokens,
                                  "max_tokens": _count(max_tokens, "max_tokens"),
                                  "reserved_usd": reservation}
        self.outstanding_reservations[reservation_id] = item
        self._pending_by_callsite.setdefault((run_id, model_id), []).append(reservation_id)
        self.reservations.append(item)
        self._journal(run_id, {
            "type": "reservation", "reservation_id": reservation_id,
            "model_id": model_id,
            "prompt_tokens_bound": tokens, "max_tokens": _count(max_tokens, "max_tokens"),
            "reserved_usd": reservation,
        })
        return reservation

    def add(self, run_id, model_id, usage):
        """Record one completed call. Zero reported usage halts the batch."""
        self.open_run(run_id)
        entry = self.per_run[run_id]
        input_tokens = _count(usage.get("input_tokens", 0), "usage.input_tokens")
        output_tokens = _count(usage.get("output_tokens", 0), "usage.output_tokens")
        cached_read = _count(usage.get("cache_read_input_tokens", 0),
                             "usage.cache_read_input_tokens")
        cache_write = _count(usage.get("cache_creation_input_tokens", 0),
                             "usage.cache_creation_input_tokens")
        entry["input_tokens"] += input_tokens
        entry["output_tokens"] += output_tokens
        entry["cache_read_input_tokens"] += cached_read
        entry["cache_creation_input_tokens"] += cache_write

        cost = self.table.cost_for(model_id, usage)
        callsite = (run_id, model_id)
        pending = self._pending_by_callsite.get(callsite) or []
        if not pending:
            raise AccountingError(f"actual usage for {run_id}/{model_id} has no reservation")
        # Retries nest: the successful response reconciles the most recent
        # reservation; earlier ambiguous attempts remain fully outstanding.
        reservation_id = pending[-1]
        reservation_item = self.outstanding_reservations[reservation_id]

        if input_tokens == 0 and output_tokens == 0:
            # GPT B7: no usage is ambiguous. Keep the full reservation; never
            # release it merely because a response object arrived.
            self._halt(
                f"model {model_id!r} reported zero usage on a completed call. A meter reading "
                "zero is broken or lying, and continuing would spend blind, so the batch halts.",
                "unmetered",
            )
            raise UnmeteredResponse(self.halt_reason)

        entry["calls"] += 1
        entry["cost_usd"] = _assert_amount(entry["cost_usd"] + cost, "run cost_usd")
        self.total_usd = _assert_amount(self.total_usd + cost, "total_usd")
        self._journal(run_id, {
            "type": "actual", "reservation_id": reservation_id,
            "model_id": model_id, "usage": dict(usage),
            "cost_usd": cost,
        })
        overshoot = cost - reservation_item["reserved_usd"]
        if not math.isfinite(overshoot):
            raise AccountingError("calculated reservation overshoot must be finite")
        reservation_item["actual_usd"] = cost
        reservation_item["overshoot_usd"] = overshoot
        self.max_overshoot_usd = max(self.max_overshoot_usd, overshoot)
        pending.pop()
        if not pending:
            self._pending_by_callsite.pop(callsite, None)
        self.outstanding_reservations.pop(reservation_id)
        if not self.report_threshold_crossed and self.total_usd >= self.report_at_usd:
            self.report_threshold_crossed = True

        return cost

    def _halt(self, reason, kind):
        self.halted = True
        self.halt_reason = reason
        self.halt_kind = kind

    # ------------------------------------------------------------- reporting

    def run_totals(self, run_id):
        return dict(self.per_run.get(
            run_id,
            {"cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0, "calls": 0,
             "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}))

    # ------------------------------------------------------------ checkpoints

    def crossed_checkpoints(self):
        """Every declared checkpoint this batch's spend has reached."""
        return [value for value in self.checkpoints_usd if self.total_usd >= value]

    def pending_checkpoint(self):
        """The highest crossed checkpoint no operator has released, or None."""
        outstanding = [value for value in self.crossed_checkpoints()
                       if value not in self.acknowledged_checkpoints]
        return max(outstanding) if outstanding else None

    def acknowledge_checkpoint(self, checkpoint_usd, operator="operator", note=None):
        """Release one named checkpoint. The naming is the point.

        A blanket "carry on" would let a batch walk through every checkpoint on
        one flag, so the value must be one of the declared checkpoints and it is
        recorded with the spend at the moment it was released.

        It must also have been CROSSED. Sol's R14 review: acknowledgment checked
        only that a value was declared, so a future checkpoint could be released
        at zero spend on a first launch and would then never halt when the batch
        later crossed it. A release answers a halt that has already happened; it
        cannot be granted in advance.
        """
        value = float(checkpoint_usd)
        if value not in self.checkpoints_usd:
            raise ValueError(
                f"${value:.2f} is not a declared spend checkpoint. The declared checkpoints are "
                f"{', '.join(f'${entry:.2f}' for entry in self.checkpoints_usd) or 'none'}; "
                "a resume flag names the checkpoint it releases."
            )
        if self.total_usd < value:
            raise ValueError(
                f"the ${value:.2f} checkpoint has not been crossed: ${self.total_usd:.4f} is "
                "spent, restored prior attempts included. A checkpoint is released after it "
                "halts dispatch, never in advance, because a pre-acknowledged checkpoint "
                "would pass unhalted when the batch reached it."
            )
        if value not in self.acknowledged_checkpoints:
            self.acknowledged_checkpoints.append(value)
        record = {"event": "checkpoint_resumed", "checkpoint_usd": value,
                  "total_usd": round(self.total_usd, 6), "operator": operator,
                  "note": note}
        self.checkpoint_log.append(record)
        return record

    def check_before_run(self):
        """GPT B6: before a cell, enforce only an already-hit hard ceiling."""
        if self.halted:
            raise CeilingReached(self.halt_reason or "the batch is halted",
                                 self.halt_kind or "ceiling")

    def check_tranche_boundary(self, tranche_index):
        """GPT B6: discretionary decisions exist only at completed boundaries."""
        if self.halted:
            raise CeilingReached(self.halt_reason or "the batch is halted",
                                 self.halt_kind or "ceiling")
        checkpoint = self.pending_checkpoint()
        if checkpoint is None:
            return None
        reason = (
            f"dispatch halted after completed tranche {tranche_index} at the "
            f"${checkpoint:.2f} spend checkpoint: ${self.total_usd:.4f} of the "
            f"${self.hard_ceiling_usd:.2f} ceiling is spent. No later tranche starts until "
            f"an operator resumes this batch naming the ${checkpoint:.2f} checkpoint."
        )
        self.checkpoint_log.append({"event": "checkpoint_halt",
                                    "checkpoint_usd": checkpoint,
                                    "total_usd": round(self.total_usd, 6),
                                    "tranche_index": int(tranche_index),
                                    "reason": reason})
        raise CheckpointReached(reason, checkpoint, self.total_usd)

    def summary(self):
        return {
            "total_usd": round(self.total_usd, 6),
            "hard_ceiling_usd": self.hard_ceiling_usd,
            "report_at_usd": self.report_at_usd,
            "headroom_usd": round(self.headroom(), 6),
            "never_exceeded_ceiling": self.total_usd + sum(
                item["reserved_usd"] for item in self.outstanding_reservations.values()
            ) <= self.hard_ceiling_usd,
            "report_threshold_crossed": self.report_threshold_crossed,
            "checkpoints_usd": list(self.checkpoints_usd),
            "checkpoints_crossed": self.crossed_checkpoints(),
            "checkpoints_acknowledged": list(self.acknowledged_checkpoints),
            "checkpoint_pending": self.pending_checkpoint(),
            "checkpoint_log": list(self.checkpoint_log),
            "halted": self.halted,
            "halt_kind": self.halt_kind,
            "halt_reason": self.halt_reason,
            "calls_dispatched": self.calls_dispatched,
            "calls_refused": self.calls_refused,
            "tranches_refused": self.tranches_refused,
            "largest_reservation_usd": round(self.largest_reservation_usd, 6),
            "outstanding_reservations": len(self.outstanding_reservations),
            "outstanding_reserved_usd": round(sum(
                item["reserved_usd"] for item in self.outstanding_reservations.values()), 6),
            # The bound, measured. Must never be positive.
            "max_overshoot_usd": round(self.max_overshoot_usd, 9),
            "reservation_covered_every_call": self.max_overshoot_usd <= 0,
            "runs_metered": len(self.per_run),
            "restored_runs": self.restored_runs,
            "restored_cost_usd": round(self.restored_cost_usd, 6),
        }

    def __repr__(self):
        return f"CostMeter(${self.total_usd:.4f}/${self.hard_ceiling_usd:.2f})"
