# W39364 run 1 — retention policy

`discard-after-intake`. The manager freezes the worker's declared output,
takes custody of the collected bytes, and then discards the attempt's
execution roots; what survives is the custody copy and the operator's own
retained evidence.

The candidate is EXTERNAL OUTPUT. It is collected and inspected; it is not an
edit to the canonical checkout, and nothing in this attempt writes to the
repository the source was staged from.
