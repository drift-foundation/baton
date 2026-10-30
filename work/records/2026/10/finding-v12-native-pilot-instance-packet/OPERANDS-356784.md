# Retained-native installation/recovery operands — parent finalization, claim356784

Parent W325959 joining of the seven finite pins that
`findings/finding-native-installation-prerequisites/PREPARATION-354410.md` left
explicitly unresolved, accepted by its `review-2026-10-22T19-23-38Z.md`.

`review-2026-10-22T20-41-13Z.md` gates this work on *"after reviewed
integration and observed human checkpoint"*. **Both are now observed complete**
and verified byte-for-byte at claim356784 —
`evidence/integration-356784/INDEX.json`. That is what makes group 1
resolvable; it does not make the operational groups resolvable, and this
document does not pretend otherwise.

**`PENDING(...)` remains notation, not shell syntax.** The preparation's rule
is kept exactly: an unresolved operand is never dressed up as a runnable line,
and nothing below is pasteable unless it is marked RESOLVED and its bytes are
named. No new script or executable helper is created here.

---

## Group 1 — RESOLVED IN FULL

*"Final combined manifest/diff/base and independent verdict, including actual
native permission policy and both implementation/review proof; resulting human
integration commit."*

| Operand | Resolved value |
|---|---|
| Base | `d6881d8adbd567b6e92a4a2a1d0cb68ee781f70a` |
| Combined manifest (all 1778 files) | `080ab4f454d65583f689b476302b2ce118f8bc23a217eee3880252c80f5f735d` |
| Attributed delta (34 paths, 7 added) | `cf84e58a11a687db33a49b2cce8e6c3229e65d9bd2a11e37a7af0c074e4b71b8` |
| Durable 34-file archive | `e497831c865f1aa3cb771706a7403370fb50f685815a440109c0ac80cff46382` |
| Independent verdict | `review-2026-10-22T20-41-13Z.md`, reviewer `baton.rvpc` claim355071 |
| Working-tree import | performed by `baton.prompt` 00:52:57Z under owner authority M356736, receipt `evidence/integration-356736.json` — 34 files, path set identical to the delta, every digest matching |
| Human integration commit | `302453869d07eb5579e79a6572586d3c3cf62a5c`, parent `d6881d8a`, authored by Slawomir 2026-10-23T00:57:38Z, subject `fix(v12): compose native token lifetimes and actionable failure reports` — the only version-control act |

Native permission policy, as actually composed rather than as intended:
`stage_execution.native_lifetime_policy` resolving through
`execution_limits.task_token_seconds`, giving **7320s** for the pilot's
admitted **3600/900** — `CHECKOUT_STEPS × CHECKOUT_SECONDS + provider_turn +
ordinary_verification + CLEANUP_RESERVE_SECONDS`. **Per-invocation ceilings are
unchanged and 7320 is not a cumulative cap**; it is one token's lifetime, per
attempt.

Both proofs, and both are in the integration commit:

- **Implementation stage** reaches an actual acquired token at 7320, above 900,
  no envelope, bound to the engine's runtime.
- **Review stage** reaches its **own** token, own generation, own workspace
  resource — through the real `route_fenced` ending, with a no-policy negative
  arm falling back to 900.
- **Stop/cancel, cleanup/unknown holds, persisted restart** and
  **revoked-token refusal after clock rollback** from the accepted child
  W354630 test `f05726cf…`.
- **Owner expiry cause** through durable capture → ordinary `/7` status →
  packaged report.

Verified in the integrated tree at claim356784: joined **26 OK**, and all 15
delta test modules **1328 tests / 1300 passing**, the 28 failures being the
disclosed pre-existing `test_boundary_inventory` set and nothing new.

## Group 3 — HALF RESOLVED; schema compatibility stays pending

*"Exact publisher/reader `/7` pair and control/Job/authority schema
compatibility with retained stores."*

**RESOLVED, at source level, in the integration commit** — the pair is pinned
to one constant rather than to two agreeing strings:

- **Publisher**: `documents.STATUS_SCHEMA = "baton.v12.job-status/7"`
  (`v12/python/src/baton_v12/job_manager/documents.py:133`).
- **Reader**: `tools/job_viewer.py:200` refuses anything whose schema is not
  **that same constant**, so a mismatched document is declined rather than
  half-read.
- **Served as**: `tools/stack_command.py:266`,
  `COMMANDS["attempt-diagnostics"]` → `tools/attempt_diagnostics.report`,
  emitting `baton.v12.attempt-diagnostics/1` and reading
  `baton.v12.attempt-failure-cause/1`.

**STILL PENDING** — `PENDING(control/Job/authority schema compatibility against
the retained pilot stores)`. This needs a readback of the retained instance's
actual store schemas, which is group 4's readback and is not authorized here.
Any migration remains a separate selection and is **not** implied.

**A deployment fact the source states about itself, not a defect**:
`stack_command`'s own docstring says a source-level entry is **not** a deployed
one. The retained pilot bundle was built before `attempt-diagnostics` existed,
so an operator reading from that bundle will not find the subcommand until a
rebuilt bundle is installed. That is group 2, below.

## Groups 2, 4, 5, 6, 7 — PENDING, each with its exact blocking condition

These are **not** deferred for convenience. Each needs an action this Work has
no authority to take: *"no install, build/deployment selection, recovery, new
live run, migration or W339626 cleanup is implied"*, and W321608's gate remains.

**Group 2 — build identity.**
`PENDING(build source/environment/platform)`,
`PENDING(selected build action or accepted existing build)`,
`PENDING(embedded identity, executable and complete bundle digests)`.
Blocked on: an owner-selected build. The reviewed source is now pinned
(`30245386`), so the build's **input** is resolved and only the build act and
its output digests are missing. The preparation's own allowance holds — an
already accepted matching build may be used and no redundant rebuild is
required — but **no such build exists for this commit yet**, and a bundle
predating `attempt_diagnostics` is not a matching build.

**Group 4 — current instance readback and changed installation paths.**
`PENDING(supported read-only command)`,
`PENDING(current public instance/state/guard/config readback)`,
`PENDING(changed installation paths with before/after hashes and modes)`,
`PENDING(exact supported update operation)`.
Blocked on: a read-only readback of the retained instance
`native-coordination-pilot-w321608-1`, which is an operational step. **The
preparation's standing instruction applies and is restated rather than
answered**: if no supported retained-instance update operation exists after
combined acceptance, the exact missing operation is to be reported then. It is
not reported as missing here, because establishing that requires the readback.

**Group 5 — failed-episode recovery disposition.**
`PENDING(exact current failed-episode recovery disposition)`,
`PENDING(supported operation operands)`,
`PENDING(proof of runtime/launch exclusion)`.
Blocked on: a concrete current hold, which the preparation already warned may
make this impossible until resolved. Invariants that hold regardless and are
**not** weakened: preserved old evidence and workspace, and **no revival and no
resubmission** of the expired-token episode.

**Group 6 — owner operational selections.**
`PENDING(separate owner installation selection)`,
`PENDING(recovery selection)`, `PENDING(live-serving selection)`.
Blocked on: the owner. Message356736 authorized integration **only** and said
in terms that no deployment, recovery or live execution is authorized. The
limits those commands will carry are already pinned by group 1's reviewed
policy — **per-invocation, never converted into a cumulative cap**.

**Group 7 — post-execution receipts.**
`PENDING(actual candidate/verification/independent semantic review and human
native receipts)`.
Blocked on: execution that has not happened. These are **future results and
never prepared fixture substitutes** — that rule is the preparation's and it is
kept.

---

## What this finalization claims, and what it does not

**Claims**: group 1 is fully pinned to reviewed, independently accepted and
now-committed bytes; group 3's publisher/reader pair is pinned to one constant
in those committed bytes; and the remaining five groups each carry their exact
blocking condition rather than a guess.

**Does not claim**: installed readiness, a usable native delivery, a matching
build, any readback of the retained instance, or any operational selection.
Nothing here was executed against the retained pilot. The deterministic proofs
behind group 1 remain deterministic — fake engine, provider and clock at their
boundaries with real owners — and certify no live behaviour.

**Minimality, as the review asked for "minimal retained-native operands"**:
this resolves only what the integration and checkpoint actually settle, and
deliberately leaves every operand that would need a build, a readback, an owner
selection or a future receipt unresolved and named.
