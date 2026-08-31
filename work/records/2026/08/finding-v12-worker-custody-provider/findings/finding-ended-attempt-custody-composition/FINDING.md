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

## 2026-08-30 — the applicability ruling, confirmed with one recorded caveat

The reviewer's research recommends **option (b)**: all three endings normalize
both writable roots and account for each outcome; the failed-start and
refused-session endings retain both roots in place and remove neither.

### Confirmed, and why the reasoning holds

**Normalize is not a trust decision.** Read against the program itself,
`normalize` walks the mount and `chmod`s each owned entry to add group access
— `0o070` on a directory, `0o060` on a file — and does nothing else. It does
not delete, does not freeze, does not admit a byte to the proposal pipeline
and does not change what the material IS. M33800's "began untrusted and stays
untrusted after a start fault" is about trust and admission, and neither moves.

**And ordinary-only preserves the parent defect**, which is the half my own
reading missed. A failed start still leaves populated worker-created
directories under the worker's umask. If they are retained un-normalized, the
later retention cleanup M33800 names walks straight into the exact defect this
whole parent Work exists to remove — the manager owning neither the directory
nor a way to `chmod` it. Retaining material the manager will not be able to
remove is not retention; it is a leak with a plan attached.

So: **(b) confirmed.**

### The one thing the research did not weigh, recorded rather than glossed

**Normalize MUTATES the retained material's mode bits.** For an ending whose
whole point is that an approver said to keep the material, that is a real
change to the artifact — small, metadata-only, and still a change. If M33800's
"stays untrusted" is ever read forensically — as "stays exactly as the worker
left it" — then normalizing at the failed-start ending alters evidence an
approver reserved.

**The same guarantee is available without that cost**, and it is worth naming
so a later reader knows it was considered: normalize at the POINT OF REMOVAL
instead — the retention cleanup normalizes immediately before it removes. The
parent invariant is that the manager must be ABLE to normalize and delete
every object, which is a capability rather than a requirement to exercise it
eagerly.

**This record implements (b) as ruled** and does not act on the alternative.
The caveat is raised because it bears on an approver-owned ruling, and because
the difference is invisible until somebody inspects retained material and
finds modes the worker did not set.

### What (b) fixes about my own first reading

My first round proposed ordinary-cleanup-only and said the wrong choice either
leaves the manager unable to remove what it must or deletes material an
approver said to keep. I weighted the second risk and underweighted the first:
ordinary-only IS the "unable to remove what it must" outcome, one Work later.

## 2026-08-30 — approver ruling: the per-attempt result root is mandatory

The physical result root is the manager-derived
`workspace/result-<attempt-id>` locator already used by sealing and the
recordless-ending regressions. It is never a caller-supplied path and it is not
the helper's former `workspace/result` approximation.

Attempt allocation establishes that exact directory before the worker runtime
starts and presents it as the worker's writable result surface. The root is
mandatory even when the worker produces no accepted output: logs or other
diagnostic material may still be present, while `output.json` describes which
result artifacts exist and where they live. An empty directory therefore still
records a valid output boundary; a missing directory after execution began is
a lifecycle contradiction.

Directory custody and cleanup must never create a missing result root. They
derive the authoritative locator from manager-owned attempt identity and
refuse a contradictory absence, leaving the ending retryable and explicit.
They also must not normalize or account for a newly invented
`workspace/result` tree. The allocation/start boundary owns creation; the
ending only acts on the root that boundary established.

### 2026-08-30 — The approver's locator ruling, implemented

> *The manager creates mandatory `workspace/result-<attempt-id>` before
> runtime start. Logs may exist even when `output.json` declares no accepted
> artifacts. Custody derives that exact manager-owned locator, never creates a
> missing result root, and refuses contradictory absence.*

**Pinned: allocation establishes the result root.** `assignment_workspace`
creates `workspace/result-<assignment-id>` and adopts it into the configured
workspace group through the same owner the workspace itself uses. It is
established rather than created on demand because a directory a cleanup act
invents did not exist while the attempt ran -- so "custody normalized the
result root" could otherwise be a true sentence about an empty tree this
manager had just made, while the attempt's real output sat elsewhere.

**Pinned: it is nested, not a third mount.** `ROOT_NAMES` is what a container
may mount; the result root is a subject of custody. It is deliberately not a
member of the allocation's answer.

**Pinned: an empty result root is ordinary.** Logs may exist with no accepted
artifacts, and no artifacts at all is a result too -- emptiness is never
evidence that nothing ran.

**Pinned: absence is a contradiction, not a repair.** `custody._derived_root`
derives the ruled locator and refuses when it is missing. It creates nothing.

## 2026-08-30 — observed removal-ownership contradiction

The first complete composition proved that the earlier literal
`discard_workspace(storage, attempt_id)` direction is broader than the ending
it is meant to authorize. The helper recursively removes the complete attempt
home, while that home also contains manager custody, credential state and
credential roots. Ordinary cleanup can therefore delete a retained artifact's
custody locator and a sibling attempt's live credential root.

This observation explicitly supersedes the earlier literal
`discard_workspace(storage, attempt_id)` helper choice. The current required
invariant is that ordinary cleanup removes only roots owned by this attempt's
workspace ending, preserves every kept or quarantined custody locator and
preserves unrelated provider state. “Single contained removal” remains the
ordering rule; deleting the complete shared home does not satisfy it. The
implementation may introduce the narrower manager-owned removal primitive,
but it may not tune away either preserved-domain witness.

### 2026-08-30 — SUPERSEDED: `discard_workspace(storage, attempt_id)` as the ordinary removal

The boundary's point 5 said "one contained `discard_workspace(storage,
attempt_id)`". I implemented that literally and it is **wrong**, for a reason
the layout makes obvious once it is looked at: `discard_workspace` removes the
complete `storage/<attempt>` HOME, and `HOME_ENTRIES` is
`credential-state, credentials, custody, inputs, workspace`.

So the ordinary ending was deleting:

- `custody/<attempt-id>`, which is where `OciAdapter._custody` puts intaken
  material — **the very locators a `retained` ending says were kept**. The
  manager recorded `cleanup="retained"`, named the artifacts in `kept`, and
  had already removed the bytes that claim is about;
- `credentials/` and `credential-state/`, which is another manager domain's
  state and, in the real-engine adoption gate, reached a SIBLING attempt's
  credential root.

Two independent witnesses said the same thing, from two different domains.

**Pinned: the ordinary removal owns the two roots the WORKSPACE ENDING owns,
and nothing else.** `inputs` and `workspace` are what this attempt's execution
was given and what its ending is about. `custody` is a manager-owned sibling
holding material that outlives the attempt by design — retention is the
decision about it and cleanup is not entitled to overrule that. `credentials`
and `credential-state` belong to the credential lifecycle, which has its own
teardown and its own ending, already required and already proved before this
point.

**Pinned: "contained" was always the operative word, and the container was
wrong.** One removal, contained to what this ending owns — not one call, and
not the whole home because a single call happens to reach it. A `retained`
ending that deletes its own retained locator is not a smaller version of a
correct ending; it is an account that contradicts itself.

**Pinned: the mandatory custody capability is proved at ENTRY.** It is now a
precondition of the ending rather than a step inside it, for the same reason
`AuthorityPort` checks its session's operations at construction: a deployment
that discovers a missing capability after the runtime is destroyed and both
providers are torn down has discovered it once durable state depends on it.

## 2026-08-30 — selective-removal alias finding

The narrower execution-root primitive fixes removal ownership but initially
followed a symlinked attempt home to a sibling inside the same configured
store. Store containment is not attempt ownership. The destructive boundary
must apply allocation's exact no-link, own-canonical-directory rule to the
home and roots before thaw or traversal; an alias refusal mutates neither the
named attempt nor its sibling.

## 2026-08-30 — destructive proof must cover the set and survive use

The static home-alias correction is necessary but does not finish the ruled
boundary. First, the selective remover proves and deletes `inputs` before it
proves `workspace`; a static sibling alias at the second root therefore
produces a typed refusal only after the first root is gone. The preflight is
over the complete removal set: no root is thawed or removed until the home and
every present root are proved.

Second, `_proved_own` proves a pathname and `_remove` reopens it. Replacing the
entry in that interval lets the real remover traverse and delete a sibling
before a raw filesystem error surfaces. The destructive use must remain bound
to the identity that was proved through a manager-owned no-follow boundary;
checking a mutable name and later reopening it is not one identity hold.

### 2026-08-30 — resolved: descriptor-relative complete-set removal

The two defects immediately above are resolved by one boundary. The manager
opens the home and every present execution root no-follow before thaw or any
deletion, then traverses, changes modes and unlinks relative to those held
descriptors. The final root-name removal first compares the name's device and
inode with the descriptor. Thus an invalid root refuses before any root is
removed, and a replacement after proof cannot redirect traversal into a
sibling. The all-public-ending interruption matrix remains a separate open
acceptance item.

## 2026-08-30 — accepted outcome

Directory custody is fully composed into every current ending. Each applicable
ending normalizes result then workspace through signed per-root acts, replay-
reads both receipts into its terminal claim, refuses unaccounted or colliding
acts and discovers the typed seam before destruction. Ordinary cleanup removes
only its descriptor-held execution roots after custody and preserves retained
locators/provider siblings; recordless endings retain their normalized homes.

Interruption and replay are proved at the per-root journal and at all four
public endings, including the ordinary crash state after root removal and
before terminal commit. The retry consumes the already committed receipts and
does not touch absent roots. W43975's acceptance is satisfied.
