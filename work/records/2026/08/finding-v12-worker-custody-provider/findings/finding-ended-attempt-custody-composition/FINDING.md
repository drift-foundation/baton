# Compose custody into the ended-attempt path

Work: W43975
Parent: W36540 (`work/records/2026/08/finding-v12-worker-custody-provider/`)
Dependency: W43974, closed satisfying

## Purpose

Wire the manager-owned custody act into the actual ended-attempt lifecycle.
No ending calls it today, so the capability W36540 delivered is one nothing
reaches.

## 2026-08-30 — implementation revalidation (`baton.claude`, W43975 impl claim)

### Confirmed against the current tree

Every observation in the parent `PLAN.md`'s W43975 enrichment holds, checked
rather than assumed:

- **No production module calls `custody_act`.** Every match under `src/` is a
  docstring or a comment; the only callers are tests.
- **`discard_workspace` has no production caller.** Same: `workspaces.py`'s
  own prose, and nothing else.
- **No axis or receipt records directory custody.** `attempts.TRANSITIONS`
  carries `cleanup` as `pending → blocked-on-intake → {complete, retained,
  failed}` and nothing about a helper act; `schema.CUSTODY` is
  `("accepted", "quarantined")` and belongs to intake's ARTIFACT ownership.

### Confirmed: the ordering the ending already has

`authorize_cleanup` fences at the AUTHORITY before anything destructive, reads
the intake receipt as part of the operation identity, refuses a still-live
assignment, refuses an `uncertain` runtime, destroys, proves exact absence,
and deliberately does NOT journal an unsettled result so a retry can try
again. That order is the one the enrichment says to retain, and it is where
directory custody has to fit rather than something to rearrange.

## Decisions this round PINS, and why they are pinned before the wiring

The enrichment names a naming hazard and several ordering rules. Each is a
decision the implementation rests on, so each is written here before any
production edit — and each is offered for the reviewer's ruling rather than
settled unilaterally where it changes a frozen axis.

### Pinned: directory custody is NOT the intake `custody` noun

`schema.CUSTODY` is `("accepted", "quarantined")` and describes what the
manager did with COLLECTED ARTIFACTS. The state this Work needs describes
whether a manager-owned helper has normalized an attempt's DIRECTORY so the
manager can remove it. **They are different facts about different objects, and
one cannot be inferred from the other.**

**The noun is `directory_custody`** and its states are its own. Overloading
`custody` would make a receipt about artifacts answer a question about
directories, which is the exact confusion the enrichment warns about.

### Pinned: one identity per (attempt, root, verb)

An act over `workspace` and an act over `result` are two acts with two
outcomes, and the enrichment requires them separately attributable so success
on one cannot hide failure on the other. The operation identity therefore
derives from the attempt, the root kind and the verb — the same three the
W43974 helper identity derives from, which is what lets a crash mid-act
reconcile the helper and the journal against each other.

### Pinned: an accountable success is a PRECONDITION, not a report

No manager-side removal and no terminal cleanup write happens until the
helper's answer is `ok` for the applicable roots. An unaccounted, timed-out or
`UNRESOLVED` act leaves the ending retryable and journals nothing — which is
the rule `authorize_cleanup` already applies to an unsettled destroy, and
reusing it rather than inventing a second one is the point.

W43974's lost-act answer is `UNRESOLVED` by construction on the Docker CLI
boundary, so this path must treat that as retryable rather than as a failure,
and must never record a false completion from it.

### Open, and NOT decided here — the three endings' applicability

`authorize_cleanup`, `authorize_failed_start_cleanup` and
`authorize_refused_session_cleanup` each need an explicit applicability
decision, and one of them is not mine to take alone:

**`authorize_failed_start_cleanup` ends at `retained` on approver ruling
M33800** — the result directory "began untrusted and stays untrusted after a
start fault", it deletes nothing, and a later explicit retention cleanup owns
that deletion. Running a normalize+remove there would contradict a ruling this
Work does not own. My reading is that directory custody applies to the
ORDINARY cleanup only, and that the other two ends stay as they are until the
retention cleanup M33800 names exists.

That is a ruling I want before wiring, because getting it wrong means either
a manager that cannot remove what it must, or one that deletes material an
approver said to keep.

## 2026-08-30 — reviewer analysis of the applicability ruling

### Confirmed: ordinary-cleanup-only would preserve the parent defect

Both recordless endings can leave worker-created, mode-zero trees in the
attempt workspace and result roots. If directory custody applies only to
`authorize_cleanup`, the manager still has no unconditional way to inspect or
later remove those retained trees. That is the exact defect W36540 owns, not a
separate retention concern, so option (a) does not satisfy the parent purpose.

The parent enrichment also requires an explicit decision and regression for
all three endings; it does not say the recordless endings are outside custody.

### Proposed: normalize both roots on both recordless endings, remove neither

M33800 says the failed-start and refused-session result bytes remain untrusted,
stay in their existing per-attempt directory, are not frozen or admitted, and
are deleted only by a later explicit retention cleanup. `normalize` is
compatible with each clause: the custodian changes access metadata on objects
it owns so the manager can later act, but it does not read, freeze, admit,
delete or relabel their bytes as trusted.

The recommended applicability is therefore:

- ordinary cleanup: normalize each declared writable root, account for both
  outcomes, then perform the manager-owned removal and terminal settlement;
- failed-start and refused-session cleanup: normalize both `workspace` and
  `result`, account for each outcome, retain both roots in place, and settle
  `retained`; a later explicit retention cleanup owns their removal;
- any unaccounted, refused or `UNRESOLVED` normalize leaves the ending
  retryable and writes no false terminal cleanup.

This preserves M33800's retained bytes while making “retained” mean the manager
actually has custody of what it promises to retain. It also keeps the two root
outcomes independently attributable as the parent plan requires.

### Authority required

This is an interpretation and extension of approver ruling M33800, not a new
reviewer ruling. The reviewer recommends option (b) with the scope above and
routes the directed obligation into parent W36540 for `baton.ops` to confirm or
supersede before production wiring starts.

## 2026-08-30 — approver ruling: option (b) is accepted

The proposed applicability above is approved. Ordinary cleanup normalizes and
accounts for each declared writable root before manager-owned removal.
Failed-start and refused-session cleanup normalize and account for both the
`workspace` and `result` roots, then retain both roots in place and settle
`retained`; neither path removes, trusts, freezes or admits those bytes.

Here `normalize` means only restoring manager group access through the bounded
custody helper: add group `rwx` to worker-owned directories and group `rw` to
worker-owned files, without changing content or ownership and without
following symlinks. Any refused, unaccounted or `UNRESOLVED` normalization
keeps the ending retryable and cannot support a terminal cleanup claim.

## Acceptance (unchanged from the parent enrichment)

- Ordinary cleanup performs the directory acts over both roots after the fence
  and the absence proof, with per-root attributable outcomes.
- Exact retry replays a settled answer; a crash before settlement reconciles
  the helper identity and performs or observes the act again.
- Retained and quarantined material stays at its custody locator; this ending
  removes attempt roots and not material a retention decision keeps elsewhere.
- No path invents a worker disposition or an intake receipt to reach directory
  custody, and terminal cleanup is written only after every applicable ending
  is settled.
