
## 2026-10-22 — baton.claude, claim354165 — COMPOSITION DONE ON THE CURRENT BASELINE; NATIVE SEAM MAPPED, NOT PROVED

Successful canonical claim354165 after reading current state (queued,
unclaimed, routed `baton.impl`, `last_change_seq 354162`, **zero open
blockers** — W333485, W333486 and W338305 all closed satisfying), the complete
handoff through `work-events` (58 events, `next_after` null) and thread T325959
in full (5 messages, `last_seq 329708`). Read
`review-2026-10-22T18-44-40Z.md`, the current `PLAN.md` and
`INPUTS-354131.json`.

### Base revalidated before anything was composed

The review said to revalidate its observed baseline rather than trust it.
`HEAD` is **`d6881d8adbd567b6e92a4a2a1d0cb68ee781f70a`** — the same commit,
*"Fix managed confinement descriptor cleanup and source-line verification"*,
which is the human's integration of W339626's confinement work. The isolated
baseline was materialized from the **committed** tree and
`worker_manager/workspaces.py` was re-hashed against HEAD's own object to
prove it is not the dirty shared working tree.

### The composition, and the one mismatch

Of the 24 accepted W333486 paths (`evidence/review-354068/CANDIDATE.json`,
base `bc925cf5`):

- **19** have `bc925cf5 == d6881d8a`, so the accepted bytes apply unchanged.
- **4** are new files the candidate adds (`failure_cause.py`,
  `test_attempt_failure_cause.py`, `attempt_diagnostics.py`,
  `test_attempt_diagnostics.py`).
- **1 real base mismatch**: `worker_manager/attempts.py`. `d3a7a41c` — the
  human's integration of W339626's candidate345109 — added
  `runtime_recovery_inventory` to it after the diagnostics candidate was
  based. **This is exactly the overlap M345516 declared.**

**Resolved by a refusing three-way merge, not an overwrite.** `threeway.py`
applies each side's edit regions against the common base and **raises if the
two sides touch overlapping base lines**, because a silent pick is precisely
the overwrite the review forbids. The regions are disjoint — the baseline
inserts a function after `attempt_runtime_of`, the candidate rewrites
`_order_quiescence` branches — so both were applied, and both were then
verified present: `runtime_recovery_inventory` once, and all **6** of the
candidate's `carry_degradation` carriers, equal to the candidate's own count.
`git merge-file` is unavailable here, so the merge is a small explicit program
whose bytes are retained for review rather than a hand-placed insertion.

Composed result: **23 paths byte-identical to the accepted candidate, 1
merged** at `e929d730…`.

**Joined 12-module gate on the composed current baseline: 1260 tests,
14.213s, OK, exit 0, zero skips** — against 1259 for the accepted candidate on
the old base. The composition does not regress the accepted suppliers on the
newer tree, which is what this gate is for. W333485's 171+37+46 and W333486's
42-focused/packaged proofs are **reused** as accepted records attributed to
their own Work; no supplier research was repeated.

### The native seam, located exactly — and not proved

`NATIVE-SEAM.json` is item (1) of the PLAN carried out with citations:
`stage_execution:factory` → `operations_from` →
`single_worker:2233 request_runtime_start(govern=prepared_workspace_governance(...))`
→ `workspaces.py:3968 PreparedGovernance.reserve`.

**The gap is one missing argument.** `reserve` calls `tokens.acquire(...)`
with **no `seconds=`**, so it takes the default `LIFETIME_SECONDS = 900`
(`tokens.py:37`) and the Job's admitted per-invocation provider ceiling never
reaches the token. Nothing in `tokens.py` or `workspaces.py` references
`provider_turn` or `execution_limits` at all. That is the mechanism behind the
owner's recorded failure: the pilot's implementation token expired at 900s
with zero renewals while the Job allowed 3600s.

**What is already available and unused:** `stage_execution.limits()` already
resolves a Job's effective boundaries through
`single_worker.job_execution_reader` — in the same module as the acquisition
call site — and uses them for the integration worker request, not for token
acquisition. And `tokens.renew` with `RENEWAL_LIMIT = 4` is the accepted
W333485 supplier.

**The fork the next claim must settle first, recorded rather than guessed.**
A bounded initial permission needs one number per attempt, and 3600 + 900 is
only right if an attempt makes one provider turn and one verification — a
count `revision-4/inputs/policy.json` states verbatim is an **assumption**:
*"No product cumulative ceiling. Operator observes a proposed 9900s window;
9000s assumes one provider and one verification invocation per stage."* So
route A appears to need an invocation-count policy nobody has pinned. Route B,
timely eligible renewal, declares no total and assumes no count — its bound is
the existing renewal limit — and the PLAN already permits either. **My reading
is that route B is the one that needs no new owner policy, and I am explicitly
not asserting that as established**: it turns on whether the native serving
loop can renew a live attempt's token, which I mapped but did not verify.

### What I did not do

No deterministic native two-stage seam test was written, so the 900 ceiling is
located by **reading** the pinned baseline and corroborated by the owner's
failure evidence, **not** by an executed reproduction at the seam. No
permission policy was pinned and no connection implemented — therefore no
proof of authorized work beyond 900, no expiry/cancellation/cleanup proof, no
replay/restart/no-revival proof, and no new owner-produced expiry joined
through durable capture, `/7` status and the packaged report. No
installation/recovery operands were prepared; the review forbids building that
on an unaccepted composition.

### Boundaries and cost

No live instance, engine, provider or credential; no deployment, recovery,
start or migration; **no Git mutation** — the only version-control operations
were reads (`rev-parse`, `log`, `show`, `ls-tree`, `archive`, `diff`). No
shared-tree import or edit: the composition exists only under
`/tmp/w325959-354165`. Nothing was implemented, so no expired-token revival,
deadline reset or invented whole-Job cap was possible. The failed native
episode and the `quickstart-a` / `sub-w321608-quickstart-1` identities are
untouched.

Measured this claim: joined gate 14.213s once, the three-way merge and
composition verification well under a second, plus unmeasured reading and
hashing. Product tests executed: one joined gate run, in the isolated root
under M353196 direct development. Jobs 0; attempts 0; runtimes 0; provider
calls 0; engine calls 0; credential reads 0; live invocations 0. Prior
attributions stay with their own Work: W333486's parent ≈2253s and child
≈5726.14s plus unknowns, and the supplier proofs' own costs.
