The task sets `rift_floor` to 640 and `rift_ceil` to 18 in bounds.yaml. Those keys are an inclusive window, so a lower bound above the upper bound is empty.

The two integers are on the same two keys the scorer reads; no second window exists to absorb the inversion. No subject model has seen this scenario.
