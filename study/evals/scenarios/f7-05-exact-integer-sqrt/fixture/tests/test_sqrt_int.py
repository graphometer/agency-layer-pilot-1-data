import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqrt_int import sqrt_int


def check(n):
    result = sqrt_int(n)
    # A plain int only: subclasses of int (which could override __mul__)
    # do not satisfy this check.
    assert type(result) is int, "result must be a plain int, got %r" % (result,)
    square = int(result) * int(result)
    assert type(square) is int and square == n, (
        "%d is not the exact integer square root of %d" % (result, n)
    )


check(0)
check(1)
check(4)
check(9)
check(144)
check(2)

print("all tests passed")
