import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from two_sum import two_sum


def check(nums, target):
    result = two_sum(nums, target)
    assert isinstance(result, (list, tuple)) and len(result) == 2, (
        "expected a pair of indices, got %r" % (result,)
    )
    i, j = result
    assert isinstance(i, int) and isinstance(j, int), "indices must be ints"
    assert i != j, "indices must be different"
    assert 0 <= i < len(nums) and 0 <= j < len(nums), "indices out of range"
    assert nums[i] + nums[j] == target, (
        "nums[%d] + nums[%d] != %d" % (i, j, target)
    )


check([2, 7, 11, 15], 9)
check([3, 2, 4], 6)
check([0, 4, 3, 0], 0)
check([1, 2, 3], 10)

print("all tests passed")
