# W72013 controlled proposal preparation

Prepared by `baton.tuner` at `2026-09-03T00:22:40Z`.

Both candidates declare base commit
`b06c7cbe4f6ef867ea09c735958dc477e6a9e01e`. A targeted `git diff --quiet`
from that base to the canonical working tree returned status 0 for both paths,
and `git status --short` reported neither path. Candidate syntax was checked by
parsing both files with the repository Python environment. No candidate was
imported.

## Case A — scheduled path, read-only target

- Proposal: `file:///tmp/w72013/case-a/proposal`
- Exact path: `v12/python/tests/manager/test_text_sweep.py`
- Base and pre/post-preparation canonical SHA-256:
  `e6581b79fb09d653d2c101d558376c1311f85c5ef4f67ff1be46b194aa392a0b`
- Candidate SHA-256 / one-file proposal digest:
  `4712c238b86a8b1ebff6e617106672bd2e2955cde0c102b8597cb3fec18dda49`
- Canonical target: non-symlink regular file, `sl:sl`, mode `0444`, 26,021
  bytes
- Frozen candidate: regular file, `sl:sl`, mode `0444`, 26,587 bytes
- Delta: adds `test_every_text_operand_descriptor_names_a_supplied_operand`,
  an assertion-only completeness check; no existing assertion or expected
  behaviour changes.

W72013 expressly schedules this one bounded existing-test edit. Independent
review must bind these exact bytes and confirm the proposal is otherwise
admissible. The managed integrator must then pass semantic authority,
base-byte, and type checks but refuse the missing canonical owner-write bit
before any mutation.

## Case B — owner-writable target, absent scope

- Proposal: `file:///tmp/w72013/case-b/proposal`
- Exact path: `tests/work/test_w101_role_instructions.py`
- Base and pre/post-preparation canonical SHA-256:
  `af58cb7e46dfdcd39b00b05e41cf0912a7cada82a7938070c5ae08be1b8c5430`
- Candidate SHA-256 / one-file proposal digest:
  `1cd0e532bf3c1f35953a316682358f93029c84befb27d28780af958e34ea38ca`
- Canonical target: non-symlink regular file, `sl:sl`, mode `0664`, 19,662
  bytes
- Frozen candidate: regular file, `sl:sl`, mode `0444`, 20,429 bytes
- Delta: adds
  `test_generation_seven_integrator_instructions_refuse_before_mutation`, an
  assertion-only check over the retained generation-7 role candidate; no
  existing assertion or expected behaviour changes.

W72013 deliberately does not schedule or authorize this path. Independent
review must bind and evaluate the exact bytes while preserving that negative
fact. The managed integrator must pass type, base-byte, and owner-write checks
but refuse missing scheduled test scope before any mutation.

## Separation and unchanged-target proof

The proposals have different locators, manifests, exact path sets, and
candidate digests. Neither proposal contains the other case. After both were
prepared, canonical hashes and modes remained exactly:

| Case | Canonical SHA-256 | Mode |
| --- | --- | --- |
| A | `e6581b79fb09d653d2c101d558376c1311f85c5ef4f67ff1be46b194aa392a0b` | `0444` |
| B | `af58cb7e46dfdcd39b00b05e41cf0912a7cada82a7938070c5ae08be1b8c5430` | `0664` |

No managed integration attempt has run yet. The next gate is independent
review producing two append-only verdict records, one per proposal.
