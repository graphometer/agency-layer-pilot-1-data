def two_sum(nums, target):
    """Return the indices of two different elements that add up to target."""
    for i in range(len(nums)):
        for j in range(len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return None
