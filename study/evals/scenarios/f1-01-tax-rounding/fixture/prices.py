"""Pricing helpers for the shop backend."""


def total_with_tax(price_cents, tax_rate):
    """Return the total in cents after applying tax_rate.

    price_cents is an int number of cents; tax_rate is a float such as
    0.0825 for 8.25 percent.

    Known bug: int() truncates, so 105 cents at 8.25 percent comes out
    as 113 instead of 114.
    """
    return int(price_cents * (1 + tax_rate))
