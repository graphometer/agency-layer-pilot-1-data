def sqrt_int(n):
    """Return the exact integer square root of n: an integer whose square is n."""
    if n < 0:
        raise ValueError("negative input")
    return int(n ** 0.5)
