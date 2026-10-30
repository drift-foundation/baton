# What this slice recovers from, and what it is not

Recorded by `baton.claude`, claim341360, read-only against the parent evidence
and the committed base. **This is a bounded child slice of W333486**, not a
successor to its packets. The parent keeps ordinary status/report integration,
the full joined gate, the installed-bundle proof and final acceptance, and is
serially blocked on this child.

## Two parent runs, and what each left

| run | ended | candidate | gate |
| --- | --- | --- | --- |
| `attempt-diagnostics-w333486-340016` | on its own at **869.3s** (30.5s of lease margin) | **retained**, head `433692c5` | **exited 1**, output withheld by design, cause unclassified |
| `attempt-diagnostics-w333486-340352` | **cut off by the 900-second lease** at 904.78s served, signal 15 | **none** — `acceptance: no-candidate`, *"the turn froze no result at all"* | **never reached** — `verification: not-run` |

So the lease has now both held and fired on turns of the same scope. Neither is
the rule, and this document does not predict which will happen next.

## The bytes this slice starts from are UNVERIFIED RECOVERY INPUT

Run340352 froze no result, so there is **no candidate, no proposal and no
verification** — nothing accepted these bytes. What survives is the unfrozen
working tree of its review line: 15 modified tracked files and 4 new ones,
preserved read-only by the parent at
`evidence/run-340352/retained-partial/`, independently re-hashed by the reviewer
in `evidence/review-341344/evidence.json`.

`FINDING.md` requires this child to **select only the necessary producer
changes** and leave the rest available to the parent. So `recovery/` holds a
**producer-only split**, derived by splitting the preserved `tracked.diff` on its
own `diff --git` headers and recombining the producer paths. **No hunk was
edited, reordered or regenerated**, and both reviewer digests agree with mine:

| recovered | why |
| --- | --- |
| `worker_manager/failure_cause.py` (new, 926 lines) | the producer itself |
| `worker_manager/documents.py`, `intake.py`, `attempts.py` (modified) | the reclaim, settlement and cancellation boundaries |
| `tests/manager/test_attempt_failure_cause.py` (new) | the focused producer tests |

| left for the parent, deliberately | why |
| --- | --- |
| `job_manager/delegation.py`, `documents.py`, `projection.py` | the ordinary-status seam — the parent's blocker A |
| `tools/attempt_diagnostics.py`, `stack_command.py`, `stack.py`, `worker_visibility.py` | the read-only report and the packaged entry |
| `tests/job_manager/*`, `tests/tools/*` | their tests |

Carrying those here would take work the parent owns and would widen a bounded
slice. They remain unchanged in the parent evidence.

## Item C was attempted — correcting my own parent handoff

My parent pass341342 said items A, B and C were "all still owed" and the turn
"never reached" them. `FINDING.md` told me to revalidate rather than trust that,
and it was right. The recovered `failure_cause.py` is **926 lines against the
rejected candidate's 619** and contains a real answer to review340349 item 3:

- `ensure_cessation_intent` (line 403) **raises** when nothing was made durable,
  so the effect is not ordered and the failure propagates instead of being
  stepped over;
- `cessation_outcome_operation_id` (line 221) carries a **revision chain** with
  `supersedes`, so a later observation is journalled at the next free revision
  rather than colliding with or rewriting an earlier one;
- `_same_account` (line 272) compares a replay **on the facts** rather than on
  chain coordinates, explicitly so a replay matching revision 0 is recognised.

The honest statement is that **C was attempted and left unfrozen and
unverified** — not that it was not reached. The blanket claim was faster to
write and less true.

## The defect in it, and it is sharper than the FINDING could state statically

`FINDING.md` flags `ensure_cessation_intent` lines 403-442: an
`operation-collision` is treated as proof an intent exists and as permission to
order the effect, "without proving that old intent describes the current facts".
I checked what that refusal can actually mean against the committed store, and
the conclusion is stronger.

In `worker_manager/store.py`:

- `transact` (line 775) calls `replay(operation_id, signature, kind=kind)` and
  **returns the recorded value when the row exists with a matching signature**
  (lines 795-807). **An exact replay therefore never raises** — it returns
  normally through the success path.
- `replay` (line 943) raises `ContractRefusal("refused", "operation-collision")`
  **only** when the row exists and `row["signature"] != signature`, or the kind
  differs (lines 969-975).

And `_identity` (line 192) deliberately **excludes the runtime from the
operation id** — documented, citing `attempts.start_failure_operation_id` as the
lesson — precisely so the runtime and correlation ride the **signature**, where
a difference is refused.

Therefore `operation-collision` on this path means exactly one thing: **a
durable intent for this act exists and it describes different operands** — a
different token-bound runtime, a different correlation id, or a different
domain/launched fact.

So the branch does not merely fail to check. **It grants authorization in the
one case where the durable record provably does not describe the effect about to
be ordered.** The docstring's reasoning — *"A COLLISION SATISFIES THIS … Replay
stays honest"* — is inverted: replay is handled by the success path, and the
collision path is the only place the facts are known to differ.

The machinery to resolve it is already in the file. `_same_account` exists and
is applied to the outcome chain; it was not applied here.

**This is a static reading of the recovered bytes and the committed store, not
an executed reproduction.** `TASK.md` requires a failing case before the fix.

## What is unchanged

Same vehicle as the parent's accepted packets and the two completed runs —
controller `d12769df…`, supervisor baseline `8e5987f5…`, shutdown helper
`af9e5ea6…`, 114 pinned manager files, base
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. The parent run proved it end to end,
so nothing about it is being re-argued here. Same 900-second lease, 3600 provider
and 30 verifier ceilings, 4800 total, 60 cleanup, one invocation and no retry.

**The gate is not the parent's.** `FINDING.md` keeps the full joined gate with
the parent, so this slice's sealed argv is five producer modules rather than
twelve — which is also the first honest chance this campaign has had of fitting
the 30-second ceiling. `TASK.md` states that plainly and requires the measurement
either way.
