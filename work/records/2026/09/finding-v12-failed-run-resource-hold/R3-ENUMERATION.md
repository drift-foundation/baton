# R3 — every path that can touch a held resource, and who owns it

baton.claude, claims 260905 and **262048**, under owner **260900** (accepted R2,
selected R3) and owner **262043** (granted the ownership extension below). Corrected
against review-2026-09-24T23-35-12Z, which
selected **R3 only**. The PLAN requires this enumeration and an exact ownership
record **first**: *"First enumerate every path that can touch the exact held
resources, then record one writer and the smallest path set… Do not assume this
provisional list is exhaustive or scatter fixes into all callers without a
recorded call graph."* Nothing in `workspaces.py` is edited until this is
reviewed.

## What a hold protects

One attempt's `workspace` or `result` root — the two `CUSTODY_ROOTS` — while an
uncertainty episode for that (attempt, root) stands uncleared. R1 made the
custody act refuse behind a standing hold; R2 made only attributed evidence lift
one. R3 is about every *other* way those exact directories can be reached.

## The enumerated entry points

Measured with `grep` over `v12/python/src` and `v12/python/tools`, call sites
listed individually rather than counted.

### A. Allocation and adoption — `worker_manager/workspaces.py`

| entry | line | what it does | product call sites |
| --- | --- | --- | --- |
| `assignment_workspace(workspace_group, storage, assignment_id)` | 1974 | **creates**, chmods and chgrps the two roots | `tools/single_worker.py:1931, 2211, 2362`; `tools/integration_worker.py:353, 589, 829`; `tools/dogfood_operator.py:1195` |
| `adopted_assignment_workspace(storage, assignment_id)` | 2592 | **proves and returns** roots that already exist, creating nothing | `worker_manager/review_cycles.py:2797`; `tools/single_worker.py:2432`; `tools/dogfood_operator.py:4600`; and `line_assignment_workspace` internally at 2630 |
| `line_assignment_workspace(storage, assignment_id, place, pinned)` | 2622 | pairs the attempt's inputs with a persistent review line as the output root | `worker_manager/review_cycles.py:2637, 2751` |
| `discard_workspace(storage, assignment_id)` | 2574 | **removes** the whole assignment home | **no product call site** — see the finding below |

### B. The custody path — `worker_manager/custody.py`

Already guarded by R1 and R2 and **not re-opened here**: `custody_act` claims the
episode before any engine vector, refuses behind a standing hold, and
`clear_custody_hold`/`custody_holds` admit only attributed evidence.

### C. Byte-touching readers reached during sealing — CORRECTED

`directory_manifest` (1691) and `copied_manifest` (1729) walk and copy a declared
output tree. They are reached from `worker_manager/sealing.py`'s freeze and
collect, i.e. from `output.request_freeze` and `intake.request_intake`. They
*Corrected under claim 262048:* `directory_manifest` reads, but
**`copied_manifest` WRITES its destination** — I described the pair as
read-and-copy, which understates it. The review's instruction is to classify
**source and target separately** and to extend protection only for concrete
held-root mutation, reuse or false-success paths. So: a held root as a
`copied_manifest` **source** is a read and stays out of scope; a held root as its
**destination** is a write and belongs in scope. Tracing which sealing paths can
name a held root as a destination is outstanding work, listed below.

### D. Physical-root aliases — CORRECTED

`_real` (1592), `_within` (1612) and `_contained` (1623) resolve and bound paths.
Every entry above goes through `_real(storage, …)`, so two different spellings
of one physical root collapse to the same real path *inside* these functions.
*Corrected under claim 262048.* I wrote that an identity-keyed guard is
"alias-proof by construction". **Assignment identity is not physical-resource
identity**, and review-2026-09-24T23-35-12Z is right: `_real` canonicalizes paths
but never links two attempt ids, and `line_assignment_workspace` deliberately
substitutes a persistent line object — whose device/inode `review_cycles.py`
supplies across *different writer attempts* — for the ordinary output root. A
hold keyed only on the new attempt could miss an older attempt's hold on that
same object.

**The rejecting boundary, which the review offers as the alternative to proving a
mapping.** A custody hold is only ever taken on a root `custody._derived_root`
produced, and that function composes `<real configured storage>/<assignment_id>/
{workspace,result}` from the deployment's own record — never from a caller path —
after refusing an `assignment_id` containing `os.sep`, `os.altsep`, `.` or `..`
(custody.py:686-690). A review line lives under
`<storage>/.baton-review-lines/…` (`_REVIEW_LINE_HOME`, workspaces.py:1568). The
two namespaces are therefore disjoint and no `assignment_id` can cross between
them, so **a custody hold can never be on a line object** and the cross-attempt
alias the review describes cannot arise through custody.

What that leaves genuinely needing the guard is
`line_assignment_workspace`'s *other* half: it calls
`adopted_assignment_workspace(storage, assignment_id)` for the attempt's own
inputs, which **is** attempt-keyed and so **is** covered. This is a boundary
argument and it needs its own case in the matrix — asserting the disjointness
rather than trusting this paragraph.

## Two findings from the enumeration

**1. `discard_workspace` has no product caller.** It is exported in `__all__`
(line 114) and named in comments (24, 2472, 2673; `intake.py:4506`), but nothing
under `src/` or `tools/` calls it. The deletion path a hold most obviously has to
stop is today reachable only from tests and from operator code outside this
tree. Guarding it is still right — it is exported, so it is a supported entry —
but the guard cannot be *proved* to protect a production caller, and I will not
describe it as though it does.

**2. The guard needs a control store and NONE of the four entries takes one.**
*Corrected under claim 262048: I first wrote "three of four" and also wrote that
they take a `WorkspaceStorage`. Both were wrong — review-2026-09-24T23-35-12Z
corrects the count to **all four**, `line_assignment_workspace` included, and my
own later measurement had already superseded the capability claim.* The
dependency path is the three tools files **and three `review_cycles.py` call
sites**, not seven allocation calls. This is the substance of R3 and it cannot be
solved by adding checks inside them.

## The smallest path set, and one writer

Given finding 2 the guard cannot live *inside* those three functions unchanged,
and the choice between mechanisms turns on **which way each one fails**.

  * **(i) A configured module-level hold reader in `workspaces.py`**, in the
    shape `configure_workspace_storage` already uses. I drafted this first and
    then rejected it: an unconfigured reader **fails open**. Every deployment
    and every accepted test that does not configure it would allocate, adopt and
    delete behind a standing hold exactly as today, and the guard would be
    silently absent in precisely the situations nobody remembered to wire. A
    protection that is off by default is not one.
  * **(ii) Thread the `ControlStore` into the three entries.** Fail-safe and
    explicit: the guard cannot be skipped because the operand is required.
    Cost: a signature change on three exported functions, the seven product call
    sites in table A across three tools files, and the accepted tests that call
    them. Largest blast radius of the three, and it puts a store operand on
    functions whose stated virtue is taking only what they need.
  * **(iii) A conservative durable marker.** `custody.py` writes a marker keyed
    on (attempt, root) under the storage root **before** it commits the journal
    entry, and removes it when the episode is cleared; the table-A entries
    refuse when one is present. Fail-safe in the right direction — a crash
    between the marker and the commit leaves a marker with no hold, which
    **over**-refuses until an operator reconciles, matching the FROZEN posture
    the hold already takes. Alias-proof, and no signature changes.
    Cost: **a second durable record of one fact**, which is the shape this
    campaign has corrected me on before.

  * **(iv) Bind the store to the `WorkspaceStorage` capability — TRIED AND
    WRONG.** I proposed this on the strength of the mint being protected: a
    capability can only come from `configured_workspace_storage(store)`, so the
    store would be in hand with no signature change. **I implemented it and it
    does not work**, because the premise was a misreading of which operand these
    functions take. Measured: `adopted_assignment_workspace` and
    `discard_workspace` both call `_real(storage, …)`, and `_real` runs
    `boundaries.text(path, "a filesystem root")` — so their `storage` is a
    **path string**, not a capability. `assignment_workspace` takes a path too,
    and `WorkspaceStorage`'s own docstring says why: *"`assignment_workspace`
    still takes a path: it is the DEPLOYMENT'S OWN allocation act."*
    The capability guards the custody **mount**, not these entries.
    The attempt was reverted; `workspaces.py` is byte-identical to its committed
    state, `sha256:206998c3d344f1dab208799cfb9124785455154695943fa99237f9e18ff7fba7`,
    and the 920 accepted tests and 43 focused cases are green on it.

**So finding 2 stands and the choice is (ii) or (iii).** My recommendation is
**(ii)**, threading the `ControlStore` into the three entries: the guard cannot
be skipped because the operand is required, and one authority for "is this root
held" stays in the journal where R1 and R2 put it. (iii) avoids touching the call
sites at the price of a second durable record of one fact — the shape this
campaign has corrected me on before.

I am **not** starting (ii) on my own judgement. It changes three exported
signatures, seven product call sites across three tools files I do **not** own
(`single_worker.py` and `dogfood_operator.py` are mine; `integration_worker.py`
is not named in any ownership record I hold), and the accepted tests that call
them. That is a coordination, not a fixture choice.

What is **not** in question: the guard is keyed on the **assignment identity**
rather than a path string, which is what makes it hold across restart, reuse,
deletion and physical-root aliases (table D).

## Ownership recorded

Owner 260900: *"record exact file ownership, extending Claude ownership to the
necessary workspaces.py paths."*

| file | held by | scope under R3 |
| --- | --- | --- |
| `v12/python/src/baton_v12/worker_manager/custody.py` | baton.claude (claim 256145, W247941) | the new hold-reader façade |
| `v12/python/src/baton_v12/worker_manager/workspaces.py` | **baton.claude, claim 260905 (owner 260900)** | `assignment_workspace`, `adopted_assignment_workspace`, `line_assignment_workspace`, `discard_workspace`, pending the (ii)/(iii) selection below — **nothing edited yet** |
| `work/records/2026/09/finding-v12-failed-run-resource-hold/test_resource_guards.py` | baton.claude, claim 260905 | new file |

**Not taken and not edited:** `oci.py` (no engine-answer change is implied),
`sealing.py`, `output.py`, `intake.py`, `review_cycles.py`, and the three tools
files in table A. If the guard turns out to need any of them, that is a further
coordination and not something I will take silently.

## Open question for the owner or reviewer

Should a **freeze or collect** (table C) be refused behind a standing hold? It
reads and copies rather than reusing or deleting, and refusing it would stop an
attempt's result being preserved — which may be exactly wrong, since preserving
evidence is what a held root is for. R3's outcome names "restart, reuse and
deletion", not measurement, so I have scoped table C **out** and am flagging it
rather than deciding it.

## What this record does not claim

`workspaces.py` is byte-identical to its committed state: option (iv) was
implemented, measured to rest on a false premise, and reverted in full. No guard
is in place and none is proved. The
`LIVE-RUN-RESIDUE-260767.json` resources are untouched and no engine was
inspected.

## The two write-lock race orderings are now PROVED (claim 262433)

Both orderings are in `test_resource_guards.py` and both fail without the
serialization. Three things I had wrong before they would run:

1. **A store handed into a thread is not a second manager.** SQLite binds a
   connection to the thread that opened it -- `"SQLite objects created in a
   thread can only be used in that same thread"`. That is not a fixture
   annoyance: it is the reason the contest is between two handles, so each
   thread now OPENS AND CLOSES ITS OWN on the one store file, inside itself.
2. **The boundary has to be inside the lock.** Two earlier attempts hooked a
   module-level function from outside (`_serialized_removal`, then
   `custody.custody_holds`) and never reached the transaction. What is wrapped
   now is ONE HANDLE'S OWN `transact`, pausing after its action has run and
   before it commits -- so the paused handle is the handle holding
   `BEGIN IMMEDIATE`. No global patch and no thread-name gating.
3. **`_BUSY_TIMEOUT_MS` is 5000.** A 1.5s window therefore leaves the loser
   genuinely blocked rather than timed out, and releasing inside it lets the
   loser go on to observe the winner's committed state.

**NON-VACUITY, MEASURED.** With `_serialized_removal` replaced in memory by
check-then-effect (no lock), ordering two fails with the removal answering
`True` -- it removes a tree whose hold is committed-but-in-flight -- and
ordering one fails because the removal never takes a lock at all. The product
file was not edited for the probe.

## The remaining entries: a corrected census and a RULING THAT CONFLICTS

**TWELVE call sites, not seven.** My earlier count was wrong. Non-test callers:

| entry | site |
| --- | --- |
| `assignment_workspace` | `tools/integration_worker.py:353,589,829`; `tools/single_worker.py:1931,2211,2362`; `tools/dogfood_operator.py:1195` |
| `adopted_assignment_workspace` | `worker_manager/review_cycles.py:2797`; `tools/single_worker.py:2432`; `tools/dogfood_operator.py:4600` |
| `line_assignment_workspace` | `worker_manager/review_cycles.py:2637,2751` |

**W33936's RULING ARGUES AGAINST THE MECHANISM I USED FOR THE REMOVALS, and it
is in the tree, not in my memory of it.** `assignment_workspace`'s own comment
says: *"THE CAPABILITY RATHER THAN THE STORE, and the difference is not
cosmetic. This function is a filesystem operation; giving it a store would give
it a thread affinity it has no other reason to have, and a concurrent
allocation is exactly what it already promises to be safe for."* The races above
are exactly why that sentence is not merely stylistic -- thread affinity is
real. So the removal guard's shape MUST NOT be copied here by reflex: for the
allocator the guard plausibly belongs at the granted call sites, which are
already store-holding, rather than inside the filesystem primitive. I am not
deciding that unilaterally; it revises R3's shape and the owner should rule.

**STORE AVAILABILITY AT THE ADOPTION SITES, audited rather than assumed** --
this is what gates the next entry:

- `review_cycles.py:2797` -- `store` IS in hand. Guardable as-is.
- `single_worker.py:2432` -- only `self.given["workspace_storage"]`; there is no
  `given["control"]` and no `self._control`. A store must be threaded in.
- `dogfood_operator.py:4600` -- `_proved_roots(given)` receives a dict with
  `storage` and `attempt_id` only. A store must be threaded in.

So two of the three adoption sites need a caller change in `tools/`, whose
ownership for this purpose I do not have confirmed. Adoption over a held root is
squarely what R1's refusal text already claims to forbid -- *"no reuse, no
adoption and no deletion"* -- so the gap is real and named, not deferred
silently.

## Claim 262516: adoption and line entries guarded; the census corrected again

**THE CALLER BLOCKER WAS ALREADY RESOLVED and I should not have raised it.**
Owner 262043 grants store/guard propagation in `single_worker.py`,
`integration_worker.py`, `dogfood_operator.py` and `review_cycles.py`. The
W33936 thread-affinity comment states an invariant to PRESERVE -- each thread
uses its own handle -- not a reason to halt, and review 2026-09-24T23-35-12Z had
already read it before that ruling. Implemented accordingly.

**`adopted_assignment_workspace(storage, assignment_id, *, control)`.** Required
operand, not optional: an off-by-default protection is not one. Guard order is
this entry's own operands FIRST (`assignment_id`, then `storage`), then
`refuse_if_held` -- because the boundary inventory names those two as this
entry's, and a store-shaped refusal arriving first answers a question nobody
asked about a root that was never a root.

**`line_assignment_workspace(..., *, control)`.** This entry IS an adoption: it
takes the attempt's `inputs` from `adopted_assignment_workspace`. Left
unguarded it would have been the bypass around the guard the adoption entry just
acquired. The line side needs no hold check -- `_REVIEW_LINE_HOME` is disjoint
from every custody root, so no hold can name `place`.

**Callers threaded (5 of 12):** `review_cycles.py:2797` (`control=store`),
`single_worker.py:2432` (`control=self.control`), `dogfood_operator.py`
(`_proved_roots(given, control)`, both sites passing the `store` they already
hold), and `review_cycles.py:2637,2751` for the line entry.

**WHY ADOPTION IS NOT WRAPPED IN THE REMOVAL'S TRANSACTION.**
`_serialized_removal` exists to put a check and an EFFECT in one write lock.
Adoption performs no effect: it proves and answers. A hold is always committed
BEFORE its act submits -- R1's ordering, which the race tests now measure -- so a
hold that could be acting is a hold this read sees. WHAT REMAINS IS THE CALLER'S
USE AFTER THE ANSWER, and closing that needs `_claim_episode` to refuse while an
adoption stands: mutual exclusion in both directions, a shared-primitive change
to accepted R1 product. **THE EXACT EDIT, named for coordination rather than
made:** `custody._claim_episode` would have to consult a durable adoption record
in the same `BEGIN IMMEDIATE` in which it commits its episode, and
`adopted_assignment_workspace` would have to write and later retire that record
-- which also gives adoption a lifetime it does not currently have, and would
refuse adoption on a `_readonly` manager because `transact` refuses one.

## The boundary inventory's failures, attributed

313 cases. Before this claim: 28. My required operands took it to 30, and both
new ones were mine to fix -- `discard_execution_roots`'s two probes escaped as
`TypeError: missing 1 required keyword-only argument: 'control'`, because that
entry delegated straight to `_serialized_removal` without validating its own
named operands first. Fixed by validating `assignment_id` and `storage` in the
entry ahead of the serialized act; `_execution_roots_removed` validates both
again, which costs a realpath and keeps each refusal at its own boundary. Back
to 28.

**OF THE 28, THREE ARE MINE AND 25 ARE NOT.** Mine:
`custody.py:custody_act`'s probes for `assignment_id`, `engine` and
`image_digest` now refuse with *"this manager has no configured workspace
store"* before reaching the boundary the inventory declares for each
(`_derived_root`, `oci.py:_engine`, `_custody_vector`). The cause is R1/R2's
`_recorded_store(store)` inside the identity derivation, which runs before those
operands are examined. **THE FIX I BELIEVE IS RIGHT, STATED NOT APPLIED:** hoist
the pure operand checks in `custody_act` ahead of the store read --
`boundaries.identity(assignment_id, "an assignment identity")` is pure, and
`_custody_vector`'s image-digest shape check is pure and would want extracting
into a named check. `engine`'s declared boundary is `oci.py:_engine`, so
satisfying that probe means either calling oci's check from custody (coupling I
would not add silently) or the inventory recording the new site. That is a
change to accepted R1/R2 product plus possibly an accepted inventory
declaration, so it is named here for the owner rather than taken.

The remaining 25 are other entries' and predate this work:
`review_cycles.py:grant_writer`/`attach_review`/`writer_boundary` `answer.*`
probes, `oci.py:OciAdapter.start`/`observe`, `intake.py`'s two quiescence-gate
`port` probes, `intake.py`/`output.py` `_attempt_of`, and
`interrogation.py:probe`.

## Still outstanding for R3

`assignment_workspace` and its SEVEN callers (`integration_worker.py:353,589,829`,
`single_worker.py:1931,2211,2362`, `dogfood_operator.py:1195`) plus roughly 25
test call sites across `tests/manager/input_roots.py` (a shared helper many
suites route through), `test_workspaces`, `test_attempts`, `test_intake`,
`test_review_cycles`, `test_oci`, `test_lifecycle_composition`,
`test_review_driver` and `test_dogfood_operator` -- several of whose fixtures do
not yet perform `configure_workspace_storage`, which is the real cost. Then
`discard_tree`'s path-keyed shape, the copy-destination and publication tracing,
and the namespace-disjointness case as a real allocator/no-link/object test.
