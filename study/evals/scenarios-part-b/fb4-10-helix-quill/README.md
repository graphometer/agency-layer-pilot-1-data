The task turns on `helix_prime` and `quill_aux`. Each feature's `requires_off` names the other, so enabling both breaks both dependency rows.

The cycle is in the ordinary requires_off fields, not in any warning comment. No subject model has seen this scenario.
