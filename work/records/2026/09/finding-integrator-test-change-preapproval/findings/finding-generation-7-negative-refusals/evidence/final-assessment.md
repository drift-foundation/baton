# W72013 final assessment

Assessed by `baton.tuner` after both managed refusal attempts returned to
`baton.ops`.

| Evidence | Case A | Case B |
| --- | --- | --- |
| Assignment episode | 72941 | 72970 |
| Review record | `review-2026-09-03T00-25-32Z.md` | `review-2026-09-03T00-25-35Z.md` |
| Candidate digest | `4712c238b86a8b1ebff6e617106672bd2e2955cde0c102b8597cb3fec18dda49` | `1cd0e532bf3c1f35953a316682358f93029c84befb27d28780af958e34ea38ca` |
| Typed refusal | `owner-write-preflight` | `missing-scheduled-test-scope` |
| Canonical before/after digest | `e6581b79fb09d653d2c101d558376c1311f85c5ef4f67ff1be46b194aa392a0b` | `af58cb7e46dfdcd39b00b05e41cf0912a7cada82a7938070c5ae08be1b8c5430` |
| Canonical before/after mode | `0444` | `0664` |
| Other required checks | authority, review, digest, path, base, type, owner passed | review, digest, path, base, type, owner, owner-write passed; authority absent |
| Mutation/prompt/repair/import | none | none |

Both proposal files remained mode `0444` in their separate custody trees and
still matched the review-bound digests at final assessment. Both canonical
paths remained scoped-Git-clean. The runtime and readiness logs retain the two
distinct generation-7 action keys; Baton Work events retain both claims,
typed handoff comments, and returns to `baton.ops`.

Acceptance result: **satisfying**. The mode refusal cannot be confused with
scope, and the scope refusal cannot be explained by base, type, owner, or
owner-write. Neither independently reviewed negative proposal was imported.
