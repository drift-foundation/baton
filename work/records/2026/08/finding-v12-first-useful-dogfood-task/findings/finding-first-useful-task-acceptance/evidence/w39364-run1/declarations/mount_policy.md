# W39364 run 1 — mount policy

Exactly two roots reach the container and the adapter proves both:

- the assignment's input root, read-only at `/input`, carrying the two manager
  protocol documents, the operator's `task.json` and the four-file staged
  source subset;
- the assignment's workspace root, writable at `/output`.

The credential is not a third mountable root. It is delivered at the fixed
credential path by its own owner, and the launch document likewise. No host
path outside the attempt's own home is offered to any container.
