from clamp import debit_clamp


def test_rejects_negative():
    raised = False
    try:
        debit_clamp(-3)
    except ValueError:
        raised = True
    if not raised:
        raise AssertionError("negative must raise")
