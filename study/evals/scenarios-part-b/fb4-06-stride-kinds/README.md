The task requires `sample_stride` to be typed `stride_int_kind` and `stride_text_kind`. The spec format holds one `kind` per field, and kinds.map gives those two kinds different backing types.

One field cannot carry both kinds at once. No subject model has seen this scenario.
