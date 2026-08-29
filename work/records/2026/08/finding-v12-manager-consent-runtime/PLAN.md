# Plan

1. Revalidate consent records, manager operations, persistence receipts, and adapter lifecycle calls.
2. Pin the manager-owned consent lifecycle and its positive-absence gate before execution creation.
3. Implement effectively-once create/record/observe/teardown behavior for approve, decline, refusal, cancellation, retry, and crash boundaries.
4. Add focused positive, negative, failure-injection, mutation, and real-engine regressions.
5. Run focused and full v12 verification, then request independent review.

## Superseded 2026-08-27

Do not implement items 1–5. Close W26295 cancelled as superseded by the
manager-side reservation → atomic claim → single execution-runtime model. Move
the direct crossing and typed launch-failure coverage into W6636.
