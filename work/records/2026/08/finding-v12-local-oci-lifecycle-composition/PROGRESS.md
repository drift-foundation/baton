# Implementer progress — local OCI lifecycle composition

Created 2026-08-24 by `baton.claude` on claiming W6636, as the record requires.

## The nine dependency edges are installed

The handoff asked the route handler to add them before implementation. All nine
are in, each with its rationale recorded on the edge:

**W5 components** — W6631, W6632, W6633, W6634.
**Manager contracts** — W6592, W6627, W6628, W6629, W6630.

## Not implemented, because the brief's own precondition is unmet

The assignment opens with it: *"After all component and manager prerequisites
close satisfying, compose the approved sequential consent/execution OCI
topology."*

Measured on the current tree rather than assumed — **none of the nine has
closed, and none has a satisfying outcome**:

| Work | status | phase |
|---|---|---|
| W6631 materialize sources | open | queued |
| W6632 adapter core | open | queued |
| W6633 worker image | open | active |
| W6634 sealed output/credentials | open | **block** |
| W6592 manager composition | open | queued |
| W6627 agent-session/runtime | open | queued |
| W6628 output receiver | open | queued |
| W6629 intake/retention/cleanup | open | queued |
| W6630 section 13 security | open | queued |

Four of these I implemented myself in this session and returned for review;
they are in review precisely because nobody has yet confirmed they are right.
Composing on top of them now would build an integration on nine unreviewed
foundations, and the integration's own tests would then encode whatever those
components got wrong — which is the failure that makes an integration review
worthless rather than merely early.

W6634 is a stronger case still: it is itself **blocked**, on contracts that do
not exist. There is nothing there to compose.

## What this Job would need that does not exist yet

Its deliverables name them directly: consent teardown and exact activation need
W6627's agent-session and runtime protocols; **effectively-once**
start/inspect/cancel/**freeze/collect**/destroy needs W6628's output receiver
and W6634's collector; positive absence needs W6632's adapter, which is written
but unreviewed; and the destroy/retain path needs W6629 and W6630.

The mutable Docker restart/race/failure evidence the brief asks for is the one
part I could run today — Docker 29.1.3 is reachable on this host. Running it
against components that may change would produce evidence about a system that
will not exist by the time this Job is reviewed, which is worse than no
evidence because it looks like coverage.

## Recommendation, not a decision

Let the nine settle. This Job is an integration and it is correctly last.

If the intent was for me to begin a *scaffold* — the composition's shape, with
its component seams named and left unimplemented — that is a coherent thing to
ask for and a different Job from the one written here; I would want it stated
before building it, because a scaffold that ages against nine moving components
is the same waste in a smaller package.

## State

**Edges installed, no implementation.** Parked in `block` behind its nine
prerequisites, which is where an integration Job with nothing to integrate
belongs.

## 2026-08-27 — first implementer round: the certified arc, composed and measured

Evidence: `evidence/w6636-2026-08-27-composition.txt`.
Harness: `evidence/w6636-mutation-harness.py`.
Code: `v12/python/tests/manager/test_lifecycle_composition.py` (new, 24 cases).
No Git history or index was mutated; the mutation harness restored every file
it rewrote and the evidence shows the check.

The progress above was written 2026-08-24 and describes nine unclosed
dependencies. All ten are now closed, so it is superseded rather than amended.

### PLAN 1 — the revalidation, and the thing that governs the rest

**W6634 closed NON-SATISFYING**: *"Seven implementation and review cycles
produced no independently accepted deliverable. Closing the overbroad Work; its
code remains provisional and cannot be treated as certified."* No successor Work
exists for its sealed-output/credential half, and W6636 is W5's last open child.

W6636's acceptance requires *"All component and manager dependencies are closed
satisfying before terminal integration signoff."* **That clause cannot be met as
things stand**, and waiving it is not mine to do.

Mapping the provisional reach by CALL rather than by file is what set this
round's scope, and it is wider than the two obvious entries. `seal` and
`collect` land in `sealing.py` and credential delivery lands in
`credentials.py` — but `authorize_cleanup` destroys nothing without an intake
receipt, `request_intake` takes custody only of a `frozen` result, and only
`request_freeze` freezes one. **So for a runtime that ever started, destroy and
positive absence are reachable only through the provisional path.** PLAN item 3
names freeze, collect, destroy and positive absence together; all four sit
behind W6634. A consent runtime is torn down directly by the adapter and never
passes through intake, so consent teardown *is* composed.

With `outputs=()` and `credential_delivery=None` — which the adapter's own
docstring names as the runtime half's supported construction — `start`, `list`,
`stop`, `destroy` and `observe` enter neither provisional module. That is the
ground this composition stands on.

### Two [P0] findings composition produced and no component could

**The adapter starts no worker that can run.** `run_vector` composes
restrictions, labels, mounts, credential mounts and the image — and no `--env`.
The reference worker reads `BATON_WORKER_POSTURE`, `_SESSION`, `_CONTRACT` and
`_ROLE` from the environment and, finding none, exits at once without a frame.
Measured through the adapter's own vector against a real daemon: **exit 2, empty
stdout, empty stderr.** Every execution container the reviewed adapter starts
from the reviewed image is dead a fraction of a second later.

Neither component's suite could see it and both are right about themselves:
W6632's engine suite runs the pinned *base* image, which requires no
environment; W6633's container suite composes its own `docker run` with `--env`
for every variable and never calls the adapter. The defect exists only in the
join, which is this Job's subject and nobody else's.

**The manager records `running` for a worker that is gone.** `list_vector` is
`ps --all`, and `_attach` observes `running` for anything the label filter
returns — so an *exited* container satisfies reconciliation exactly as a live
one does. Composed with the finding above, every execution attempt records
`execution_runtime = running` for a worker that died before the call returned.
The adapter has the operation that would settle it — `observe` answers
`running`, `quiescent`, `absent` or `uncertain` about one exact identity, and a
case here proves it tells the three apart — and **no manager operation calls
it**. Naming the shape of the fix is this Job's business; making it is not.

**[P2]** The store carries a `consent_runtime` axis and the adapter a `consent`
posture, and nothing joins them. The composition drives the adapter directly and
records the axis alongside; a later slice should replace that with one
operation.

### An operational finding against my own closed Work

The full-tree gate is at **seven** failures. Six are `test_boundary_inventory`'s
accepted baseline, unchanged. The seventh is not:

```
FAIL: test_every_entry_has_exactly_one_stated_owner
      (tests.manager.test_contracts_inventory)
  receiving entries with no owner:
    ('check_input_pair', 'assignment_manifest')
    ('check_input_pair', 'input_manifest')
    ('check_input_pair', 'what')
```

`check_input_pair` is the public function I added to `contracts/manifest.py` in
**W19784, which closed satisfying**. Its three receiving parameters were never
registered in the contracts inventory's `OWNERS` table. Neither my gate nor the
reviewer's caught it, because that inventory is part of the ~14-minute full-tree
run and the round was verified on the manager subset.

**I have not fixed it.** It is a closed Work's deliverable, the remedy is three
entries in `tests/manager/test_contracts_inventory.py`, and editing another
Work's accepted deliverable without review is what passing work back exists to
prevent. It needs an owner.

### PLAN 2, 3, 4 — what is composed

Twenty-four cases over a real daemon, running this repository's own worker image
built from W6633's recipe. Docker is required and **fails rather than skips**;
Podman is absent on this host and its cases skip narrowly, which is the
environment evidence the acceptance asks for rather than a change in vocabulary.

Composed: consent teardown with proved absence and consent proved absent
*before* the execution container is created, read off one trace; decline;
activation gating the first writable call; the ordered arc through offer,
accept, record, claim, activate, compose, start and reconcile, with the engine
asked what the container actually mounts; idempotent reconciliation;
effectively-once start; stale generation; the authorized-root refusals at both
manager boundaries and at the adapter's own seam; fence-then-stop off one
ordering trace; a second incarnation adopting the running runtime; a real
stranger container forcing the multiplicity cancellation; a runtime removed
underneath the manager answering `uncertain` on both of reconciliation's
branches; a start the daemon refuses; and the reachability fact that stops this
arc at destroy.

Not composed, and each is W6634's: the success ending, freeze, collect, destroy,
positive absence, cleanup recovery.

### The measurement, and what it corrected

Every rule this module claims to compose was **removed from the source and the
module re-run**; the harness is kept beside the evidence so the measurement is
repeatable rather than asserted. **The first pass found six unestablished of
twelve**, and five were one mistake — two guards refusing the same obvious case,
so removing either left the other refusing and the case still passed.

- `_plan_agrees` and `authorize_input_root` both refuse a stranger's root.
  Separated into three cases: one whose *plan* is wrong while the authorization
  agrees (asserting nothing was journalled, since that is the earlier check's
  whole value), one whose *root* is wrong while the plan agrees, and one
  reaching the adapter's own seam directly.
- The consent adapter was built with `mounts=()`, making *"a consent container
  mounts nothing"* true by construction; `MOUNTABLE` was never reached. It now
  gets a workspace-only plan — not the full plan, which refuses one step earlier
  on the unauthorized `/input` bind, and accepting *that* refusal would have
  been the same mistake twice.
- Activation could not be separated by wording at all: `authorize_input_root`
  refuses an unactivated attempt with the same category, code and opening words,
  and `issue_offer` requires an input digest so the second guard always runs.
  What the first buys is that the adapter's plan is never read, so the case now
  observes the attribute access.
- `observe` was read everywhere absence happened to be the honest answer, so an
  adapter answering `absent` to everything satisfied every case — measured, and
  it did. That is the one answer that releases an assignment whose worker may be
  running, so a live container is now put in front of it.
- Reconciliation's two uncertainty branches are different questions and only one
  is reached per call. Both now are.

**All eighteen mutations are caught.** I will state the pattern rather than
resolve it: for the fifth Work running I wrote the case that confirms the
behaviour instead of the case that could distinguish it, and removing the guard
and looking is the only thing that has ever caught it.

## State

The certified arc is composed, measured and clean. **This is not terminal
integration signoff and must not be read as one.** W6634 closed non-satisfying,
the acceptance clause on satisfying dependencies is unmet, and freeze, collect,
destroy and positive absence are unreachable without provisional code. Two [P0]
findings say the composed execution path cannot presently run a worker at all
and that the manager does not notice.

Passed back for independent review rather than closed, with four things owned by
someone other than this round: whether composition may proceed across a
non-satisfying dependency, who owns the missing `--env`, who owns the missing
`adapter.observe` call, and who owns the `check_input_pair` inventory
registration left behind by W19784.
