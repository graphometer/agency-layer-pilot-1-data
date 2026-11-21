def debit_clamp(amount):
    if amount < 0:
        raise ValueError("negative debit")
    return amount
