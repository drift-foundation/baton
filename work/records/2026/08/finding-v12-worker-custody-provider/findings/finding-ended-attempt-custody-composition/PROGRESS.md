# Progress

Owned by the participant making the implementation change under the W43975
claim.

## 2026-08-30 — first round (`baton.claude`, W43975 impl claim)

**NO PRODUCTION CODE CHANGED THIS ROUND, deliberately.** What this round did
is revalidate the enrichment against the tree, create and bind the child
record, and pin the decisions the wiring rests on — one of which I am not
willing to take alone.

### Revalidated, not assumed

All three of the enrichment's observations hold: no production caller of
`custody_act`, no production caller of `discard_workspace`, and no axis or
receipt for directory custody — `attempts.TRANSITIONS`'s `cleanup` axis is
`pending → blocked-on-intake → {complete, retained, failed}` and
`schema.CUSTODY` is `("accepted", "quarantined")`, which is intake's ARTIFACT
ownership and a different fact about a different object.

I also read the ordering `authorize_cleanup` already has, because the
enrichment says to retain it: authority fence, receipt as part of the identity,
live-assignment refusal, `uncertain`-runtime refusal, destroy, exact absence,
and no journal for an unsettled result so a retry can try again.

### Pinned

- **The noun is `directory_custody`**, not `custody`. Overloading intake's
  would make a receipt about artifacts answer a question about directories.
- **One identity per (attempt, root, verb)**, so `workspace` and `result` stay
  separately attributable and success on one cannot hide failure on the other.
  It is the same triple W43974's helper identity derives from, which is what
  lets a crash mid-act reconcile the helper against the journal.
- **An accountable success is a precondition, not a report.** Nothing is
  removed and no terminal cleanup is written until the helper answers `ok`.
  W43974's lost-act answer is `UNRESOLVED` by construction on the Docker CLI
  boundary, so this path treats that as retryable and never records a false
  completion from it — which is the rule this ending already applies to an
  unsettled destroy rather than a second one invented beside it.

### THE RULING I AM ASKING FOR

Which of the three endings directory custody applies to.
`authorize_failed_start_cleanup` ends at `retained` on **approver ruling
M33800** — the result directory "began untrusted and stays untrusted after a
start fault", it deletes nothing, and a later explicit retention cleanup owns
that deletion. Running normalize-and-remove there would contradict a ruling
this Work does not own.

My reading is that it applies to the ORDINARY cleanup only, and that the other
two stay as they are until the retention cleanup M33800 names exists. I am
asking rather than guessing because wiring the wrong reading either leaves the
manager unable to remove what it must, or deletes material an approver said to
keep — and the second is not a mistake a test round would catch, because the
test would encode the same guess.

### Not started

The production wiring, the durable receipt, and the regression matrix.

## 2026-08-30 — second round (`baton.claude`, W43975 impl claim)

The applicability question is answered. **Option (b) confirmed**, with one
caveat recorded that the research did not weigh. No production code changed.

### Confirmed, and my own first reading was wrong

I proposed ordinary-cleanup-only and said the wrong choice either leaves the
manager unable to remove what it must or deletes material an approver said to
keep. I weighted the second and underweighted the first — **ordinary-only IS
the "unable to remove what it must" outcome, one Work later.** A failed start
retains populated worker-created directories under the worker's umask, and the
retention cleanup M33800 names would walk straight into the exact defect the
parent Work exists to remove.

The reasoning holds on the program itself rather than on its description:
`normalize` walks the mount and adds group access to each owned entry, and
does nothing else. It does not delete, freeze, admit or re-decide trust, so
M33800's "began untrusted and stays untrusted" is untouched by it.

### The caveat, recorded rather than glossed

**Normalize mutates the retained material's mode bits.** For an ending whose
whole point is that an approver said to keep the material, that is a real if
metadata-only change — and if "stays untrusted" is ever read forensically, as
"exactly as the worker left it", then normalizing at the failed-start ending
alters evidence an approver reserved.

The same guarantee is available without that cost, and it is named in
`FINDING.md` so a later reader knows it was considered: normalize at the POINT
OF REMOVAL instead, since the parent invariant is that the manager must be
ABLE to normalize and delete, which is a capability rather than a requirement
to exercise it eagerly.

**I am implementing (b) as ruled** and not acting on the alternative. The
caveat is raised because it bears on an approver-owned ruling and because the
difference is invisible until somebody inspects retained material and finds
modes the worker did not set.

### Why the wiring is not in this round

This session has run very long, and `intake.py` is the manager's ending core:
three endings, a new durable receipt inside a frozen axis, and the enrichment's
full race/restart/retry matrix. On W39358 I have been corrected three times in
a row for a record that outran its code, each time on a large composition
written at the end of a long stretch. Starting this one now would be the same
bet a fourth time.

What is done is the part that was blocking: the ruling is answered, the
reasoning is checked against the program rather than its description, and the
one cost nobody had weighed is on the record before anything rests on it.

### Not started, unchanged

The production wiring, the durable `directory_custody` receipt, and the
regression matrix.

## 2026-08-30 — second round (`baton.claude`, W43975 impl claim)

The approver's ruling arrived, so the first [P0] of
`review-2026-08-30T11-32-34Z.md` is now decidable and is implemented.

### [P0] The locator, corrected at both ends

Two things were wrong and they compounded. The helper composed
`workspace/result` while every ending establishes and retains
`workspace/result-<attempt-id>` -- also `sealed_result`'s manager-derived
`result_id` -- so wiring it would have returned an accountable success over
one tree while the attempt's real result sat untouched in another. And it
CREATED the directory when missing, which would have made the retained-mode
caveat apply to an empty tree this manager had just invented.

Now: `assignment_workspace` establishes the ruled locator before runtime start
and adopts it into the configured group; `custody._derived_root` derives that
exact path, creates nothing, and refuses an absence as the contradiction it is.

Three cases, including the review's required proof directly: sentinels in BOTH
`workspace/result` and `workspace/result-<attempt-id>`, showing which is
mounted and that the other is neither created nor mutated; a symlink at the
ruled locator refusing; and a missing result root refusing without creating
what it refused over.

### A reviewer case whose fixture names the retired path

`OneMountAndNothingElse.test_a_worker_created_result_symlink_cannot_choose_the_mount`
plants a symlink at `workspace/result`. Under the ruling that path is no
longer what custody mounts, so nothing refuses and the case is RED. Its
property is exactly right and I have asserted it at the ruled locator in
`test_a_symlink_at_the_RULED_result_locator_cannot_choose_the_mount`, which
passes. **I have not touched theirs.** The one-line change is the locator in
its fixture; that is the reviewer's to make or authorize.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.manager.test_workspaces
      tests.manager.test_custody tests.manager.test_attempts
      tests.manager.test_intake tests.manager.test_input_delivery
      tests.tools.test_dogfood_operator tests.manager.test_failed_start_destroy
      tests.manager.test_dependencies
    -> 707 tests, 3 failures, 3 skipped.

The three failures are: the superseded-fixture case named above, and TWO THAT
ARE NOT THIS WORK'S -- `test_failed_independent_verification_never_passes_to_review`
and `test_help_names_the_credential_source_the_launcher_requires` are the
reviewer's additive witnesses for W39358's launcher and pass gate, which
arrived in the tree while W39358 sits with the reviewer. Neither touches
workspaces or custody. I have not acted on them under this claim; they are
W39358's to answer when it returns.

### What this round did NOT do

The second [P0] -- `directory-custody.normalize` as a durable journal kind,
the closed `directory-custody.settled` receipt per root, replay-read receipts
bound into `cleanup.settled`, and the explicit call seam that stops
`intake.py` reaching through the adapter to its mutable fields -- is not
implemented, and neither is the production wiring or the rest of the required
matrix. The locator had to be decided first, which is what the review itself
said.

## 2026-08-30 — third round (`baton.claude`, W43975 impl claim)

The locator slice is accepted and the reviewer updated their own fixture. This
round builds the durable half of the second [P0]: the receipt contract, its
replay-read adoption, and the typed call seam.

### `directory-custody.normalize` is a journalled act with a signed receipt

`custody.normalize_directory(store, custody, *, assignment_id, which)`:

- **one identity per (attempt, root, verb)**, derived from the durable
  workspace-store record exactly as the helper's own name is, so a restarted
  manager re-derives both from the same read;
- **the signature binds what would make it a different act** — the custodian
  IMAGE identity and the durable workspace-store identity W43974 made
  load-bearing — so a changed helper or a retargeted deployment COLLIDES
  rather than replaying an answer about another act over another tree;
- **exact replay before the act**, so a resumed ending does not renormalize a
  tree its predecessor already normalized;
- **nothing is committed unless the answer is accountable**. `CustodyAnswer.ok`
  is the whole gate; a refused, unaccounted or `UNRESOLVED` answer commits
  nothing and raises, so the ending above returns its existing retryable
  unsettled shape rather than recording an act that did not happen. It refuses
  under `refused/precondition` because §9's pairing is closed and this build
  does not mint a code for the occasion;
- **the account is QUOTED, not recomposed**: `CustodyAnswer.rendered` is the
  canonical serialization produced at mint time, so the receipt carries the
  document that was accepted rather than a re-derivation of it.

`documents.CONTRACTS` gains the closed `directory-custody.settled` —
`attempt_id, root, verb, account, operation`.

### The receipts are read back from the journal

`adopted_directory_custody(store, custody, assignment_id, which)` re-derives
the identity and signature and reads through `store.replay`. A terminal
cleanup binds receipts it READ; a caller-held document is one the caller
composed, and the terminal claim's whole value is naming which directory acts
authorized it.

### The typed call seam

The review refused to let `intake.py` reach through a nominally generic
adapter to its `engine`, `run` and `image_digest` fields. `OciAdapter` now
exposes `normalize_directory(store, *, assignment_id, which)` and a
`custodian_image_digest` read; the act is composed inside the object that owns
those fields, and what crosses is a typed call and a `CustodyAnswer`. The
store crosses and is not held, so `custody_act` keeps performing its own
durable lookup in the same act that mounts.

The seam's operand is named `custody` because `test_dependencies` holds every
public parameter to the ruled operand vocabulary, and that vocabulary already
names this. `capability` is not in it.

### Six cases

One accountable act commits one closed receipt; an exact retry replays without
acting again; the two roots are separately attributable and both adopt; a
changed custodian collides; each of the three unaccountable answer shapes
commits nothing; and the adopted receipt is the committed one while an attempt
with no act adopts nothing.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
      tests.manager.test_dependencies tests.manager.test_oci
      tests.manager.test_workspaces tests.manager.test_attempts
      tests.manager.test_intake tests.manager.test_secrets
    -> 715 tests, OK (1 skipped).

Three failures appear when `tests.tools.test_dogfood_operator` is added:
`test_the_narrow_retry_refuses_evidence_for_another_attempt_first`,
`test_the_narrow_retry_converges_after_the_handoff_succeeds` and
`test_a_live_bearer_in_a_retained_record_refuses_before_retry`. Those are the
reviewer's newest additive witnesses for **W39358's** narrow retry, which
landed while that Work sits with them. None touches custody, workspaces or
documents, and I did not act on them under this claim.

### What remains of the [P0]

The WIRING. No production ending calls `normalize_directory` yet: points 4 and
5 of the boundary — outer replay first, then result then workspace
normalization, the two receipt digests bound into `cleanup.settled`, and one
contained `discard_workspace` only after both receipts for ordinary cleanup
while the two recordless endings retain the home — are not done, and neither
is the three-ending crash/restart/replay/collision matrix. This round built the
thing those endings will call and proved it in isolation.

## 2026-08-30 — fourth round (`baton.claude`, W43975 impl claim)

### [P0] The identity varied with the thing whose change had to collide

The reviewer's witness is exact and the defect is mine. I folded the recorded
workspace store into `_custody_operation_id`, so a RETARGETED deployment
derived a DIFFERENT operation identity and quietly performed a second act over
the same attempt's root — the precise fork the required collision exists to
prevent. **An identity that varies with the thing whose change must collide
can never collide with it.**

The identity is now the three facts the record pins — attempt, root, verb —
and everything that makes this a different ACT over the same subject (the
custodian image and the durable workspace store) rides the signature, where a
change is a collision rather than a new act. `adopted_directory_custody`
re-derives the same way.

`OneSignedReceiptPerRoot.test_a_retargeted_workspace_store_collides_per_root`
passes.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
      tests.manager.test_dependencies tests.manager.test_oci
      tests.manager.test_workspaces tests.manager.test_attempts
      tests.manager.test_intake tests.manager.test_secrets
      tests.tools.test_dogfood_operator
    -> 830 tests, OK (1 skipped). The whitespace check passed.

### The wiring is still not done, and why I stopped rather than started it

Points 4 and 5 of the boundary remain: outer replay first, then result then
workspace normalization in all three endings; the two replay-read receipt
digests bound into `cleanup.settled` — which means widening that closed
contract; one contained `discard_workspace` only after both receipts for
ordinary cleanup while the two recordless endings retain the home; and the
three-ending crash/restart/replay/collision matrix.

That is a change across two settle owners, a widened terminal document and a
substantial matrix. I judged I could not complete and verify it in this round,
and a partially wired ending — one sibling normalizing and another not — is
the "two orders that agree until one is edited" shape this dossier has already
paid for once. So this round is the one-line identity correction the review
named, left green, rather than a wiring I could not finish.

## 2026-08-30 — fifth round (`baton.claude`, W43975 impl claim)

The wiring, finally attempted. Points 4 and 5 are implemented across all four
endings; one real-engine gate fails in a way that must be understood before
any of this is signed off, and I am reporting it rather than tuning it away.

### Both roots normalized, in all four endings

`_normalized(store, adapter, attempt_id)` performs `result` then `workspace`,
OUTSIDE the terminal transaction — each act runs a container, and a helper
invocation inside a write transaction would hold the control store open across
an engine call. The order is the containment: `result` is nested BELOW
`workspace`, so normalizing the inner subject first means the outer act never
runs over one nobody has accounted for.

It runs only on the path that will claim an ending. A positively surviving
runtime settles `failed` with no directory act at all, because no removal and
no retention claim follows from it.

### Both receipts adopted and bound into the terminal claim

`_adopted_custody` reads each receipt back through `store.replay` and refuses
an ending whose normalization this manager cannot show it performed.
`cleanup.settled` gains `directory_custody`, so the terminal document names
the directory acts that authorized it.

### The one ordinary removal, and the recordless retention

`_settle` performs a single contained `discard_workspace(storage, attempt_id)`
after both receipts are adopted — one removal of the attempt home rather than
two deletion trees, because `result` is inside `workspace`.
`_settle_recordless_cleanup` commits both receipts and calls no removal: the
failed-start, refused-session and abandonment endings retain the home, which
is what `retained` means for them.

### The blast radius was the point, and it is disclosed

Every ending now requires a custody-capable adapter and a configured workspace
store. Five fixtures gained the typed seam (`normalize_directory` plus
`custodian_image_digest`) and four gained
`configure_workspace_storage`; two engine fixtures' `spawn` now accept the
manager's `seconds`, because a custody act refuses an engine capability it
cannot bound. None of those are behavioural edits to anybody's assertions.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_intake
      tests.manager.test_output tests.manager.test_refused_session_cleanup
      tests.manager.test_attempts tests.manager.test_sessions
      tests.manager.test_custody tests.manager.test_workspaces
      tests.manager.test_failed_start_destroy tests.manager.test_dependencies
      tests.manager.test_secrets
    -> 818 tests, OK (1 skipped).

The whitespace check passed.

### AN OPEN DEFECT IN MY OWN WIRING, reported rather than tuned away

`test_ended_runtime_adoption.DockerEndedRuntimeAdoption.
test_force_removal_absence_teardown_then_and_only_then_reuse` now fails on
`the cleanup reached an unrelated attempt's root`. That gate asserts a sibling
attempt's credential root survives an ending, and with the ordinary
`discard_workspace` added it does not. Either my removal is broader than the
attempt home I believe it is contained to, or that fixture's roots are nested
somewhere this removal legitimately reaches and the boundary needs saying
differently.

I did not have the budget to diagnose it properly this round, and guessing at
a removal boundary is the last thing this dossier needs. It is stated here and
in the handoff as the thing to resolve before any of this is signed off.

### Still not done

The three-ending crash/restart/replay/collision matrix. The wiring above is
covered by the existing ending suites passing over it, which is not the same
thing as the matrix the record requires.

## 2026-08-30 — sixth round (`baton.claude`, W43975 impl claim)

`review-2026-08-30T15-21-44Z.md`. Both P0s corrected, and the removal
ownership is pinned in FINDING/PLAN before the production change, as the
review required.

### [P0] The retained ending was deleting its own retained locator

I implemented point 5's literal `discard_workspace(storage, attempt_id)` and
it was wrong for a reason the layout makes obvious once looked at:
`HOME_ENTRIES` is `credential-state, credentials, custody, inputs, workspace`,
and that call removes the whole home. So the ordinary ending recorded
`cleanup="retained"`, named the artifacts in `kept`, and had already deleted
the `custody/<attempt-id>` locators the claim was about — and in the
real-engine gate it reached a SIBLING attempt's credential root.

Two independent witnesses, from two manager domains, saying the same thing. I
had reported the second as an open defect last round; the reviewer's first one
is what named the cause.

`discard_execution_roots(storage, assignment_id)` removes `inputs` and
`workspace` — what this attempt's execution was given and what its ending is
about — proving containment against the STORE for each, and answers which it
removed. Custody is a manager-owned sibling holding material that outlives the
attempt by design: retention is the decision about it, and cleanup is not
entitled to overrule that. The credential roots belong to a lifecycle with its
own teardown, already proved before an ending reaches here.

**"Contained" was always the operative word and the container was wrong.** One
removal contained to what this ending owns — not one call, and not the whole
home because a single call happens to reach it.

### [P0] Mandatory custody was discovered after destructive work

`normalize_directory` and `custodian_image_digest` were first read inside
`_normalized`, after the runtime was removed and both providers settled. A
deployment missing the seam mutated the world and only then received a
capability refusal. `_custody_capable` now runs at the entry of all four
endings, beside the destroy capability — the rule `AuthorityPort` states about
its own session, and the reason it checks at construction.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_intake
      tests.manager.test_output tests.manager.test_refused_session_cleanup
      tests.manager.test_attempts tests.manager.test_sessions
      tests.manager.test_custody tests.manager.test_workspaces
      tests.manager.test_failed_start_destroy tests.manager.test_dependencies
      tests.manager.test_secrets tests.manager.test_launch
    -> 853 tests, OK (1 skipped). Both additive witnesses pass. Whitespace
       passed.

Adding `tests.tools.test_dogfood_operator` shows four subcase failures of
`test_editable_evidence_must_match_every_recorded_manager_fact`, the
reviewer's newest witness for **W39358**'s retry facts, which sits with them.
It touches neither custody, workspaces nor the endings; not acted on here.

### The frozen home, found by running the engine gate rather than assuming

`discard_workspace` never met this because it removed the home ITSELF from the
writable store root. Removing entries INSIDE the home does meet it: W33935
closed the home at `0555` exactly so its entries could not be renamed or
replaced, and unlinking an entry is the parent's permission. So the removal
reopens the home for precisely that act and closes it again in a `finally`,
restoring the frozen layout whatever happens.

I found this by re-running the real-engine gate rather than reasoning that the
correction must have fixed it.

### Verification, with the engine gates

    ...the eleven modules above plus test_ended_runtime_adoption,
    test_negative_race_endings and test_lifecycle_composition
    -> 897 tests, OK (4 skipped).

`test_force_removal_absence_teardown_then_and_only_then_reuse` — the sibling
isolation gate that failed on my whole-home removal — passes against the real
daemon.

### Still required

The three-ending crash/restart/replay/collision matrix.

## 2026-08-30 — seventh round (`baton.claude`, W43975 impl claim)

### [P0] Store containment is not attempt ownership

The removal I wrote last round proved each root `_contained` in the configured
store. An attempt home that is a SYMLINK to a sibling resolves inside that
store too, so containment accepted it and the removal walked into another
attempt's roots and deleted them.

`_own_directory` has said the rule since W33936, in as many words: *a link is
refused even when it points inside manager storage: what makes a root private
is that it IS this attempt's directory, not that it lands somewhere this
manager owns.* Allocation has applied it all along. A REMOVAL that dropped it
was a second, weaker door onto exactly the directories allocation guards —
which is the same shape as the restart-lookup finding on W39358's
`_proved_roots`, and I did not carry the lesson across.

`_proved_own` now asks allocation's question read-only — not a link, a real
directory, resolving to exactly its own path — of the home and of each root
before anything is removed. An absent home answers `()`; a home that exists
and is not this attempt's own is refused rather than walked.

### The interruption matrix

At the receipt boundary, where the property actually lives
(`TheEndingSurvivesInterruptionAtEveryDirectoryAct`, 5 cases): a crash between
the two acts keeps the first root's receipt — which is the whole reason the
kind is per-root, since the outer destroy journal could not have said it; the
resumed ending redoes only the act that did not settle; an exact replay
performs no act; a custodian changed mid-ending collides and does not settle
the second root under the first's identity; and a restarted manager under a
new incarnation re-derives both identities and adopts what its predecessor
committed.

At the ending level (`EveryEndingNormalizesBothRootsAndReplays`, 4 cases):
result then workspace, both bound into the terminal claim; an interrupted
normalization commits nothing terminal and the resumed call finishes it
without renormalizing the settled root; an exact replay performs no act; and a
deployment without the seam is refused before the runtime is destroyed.

Two corrections to my own cases are worth recording. I asserted the runtime
was still present at an interrupted normalization — wrong, and the ruled order
says so: point 4 keeps the fence, the destroy, exact absence and the provider
gates and settles the roots only THEN. And I first removed the seam with `del
type(adapter).normalize_directory`, which left every later case in the run
without one; a fixture that tests the order it happens to run in is not a
fixture.

### Verification

    ...fourteen modules including test_ended_runtime_adoption,
    test_negative_race_endings and test_lifecycle_composition
    -> 907 tests, OK (4 skipped). Whitespace passed.

Adding `tests.tools.test_dogfood_operator` shows
`test_malformed_nested_evidence_is_a_refusal_not_a_python_fault`, the
reviewer's newest **W39358** witness, which sits with them. Not acted on here.

## 2026-08-30 — eighth round (`baton.claude`, W43975 impl claim)

`review-2026-08-30T15-39-31Z.md`. Both destructive-identity P0s corrected.

### [P0] Nothing is deleted until everything is proved

The removal proved and removed each root in turn, so a valid `inputs` beside
an aliased `workspace` was deleted and only then refused — a partial
destructive ending whose refusal does not describe the mutation it already
performed. The complete identity preflight now runs over the home and every
present root before the home is thawed or anything is removed, and the thaw
itself is after the preflight so a refusal never opens the frozen home at all.

### [P0] The identity is held through use

`_proved_own` validated a PATHNAME and `_remove` reopened it, so a replacement
in that interval turned the proved root into a sibling alias and the walk
followed it — `os.walk` descends a symlinked top even with
`followlinks=False`, which is why keeping `_remove` on this path could not be
made safe.

The proof and the removal are one boundary now. Each root is opened
`O_NOFOLLOW|O_DIRECTORY` relative to the proved home, which refuses a link
ATOMICALLY — the open either gets this attempt's directory or fails — and that
descriptor IS the identity. Every traversal, mode change and unlink below it
is descriptor-relative; nothing resolves a path.

The one place a NAME is still unavoidable is the final `rmdir`, so the held
descriptor and the name are proved to be one directory by device and inode
first, and a divergence is a typed refusal rather than a raw `ENOTDIR`.

### A reviewer witness whose injection point the correction removes

`test_execution_cleanup_does_not_follow_a_root_replaced_after_proof` injects
its replacement through `workspaces._remove`. The corrected removal does not
call `_remove` at all — there is no pathname re-open to interpose on, which is
the whole of the fix — so the side effect never fires and the case's `refused`
assertion cannot become true. Its FIRST assertion, that the sibling sentinel
survives, passes.

**I have not touched it.** I added
`test_a_root_replaced_at_the_real_seam_is_a_typed_refusal`, which drives the
replacement at the seam the descriptor design actually leaves — between the
walk and the final `rmdir` — and asserts both halves they asked for: the
sibling survives and the ending refuses with a typed message. If they would
rather their own case moved to that seam, it is a one-line change of what it
patches, and it is theirs to make or authorize.

### Verification

    ...thirteen modules including test_ended_runtime_adoption,
    test_negative_race_endings and test_lifecycle_composition
    -> 827 tests, OK (4 skipped). Whitespace passed.

`tests.manager.test_workspaces` alone: 83 tests, 1 failure — the injection-point
case above, and nothing else.

### Still required

The all-public-ending crash/restart/replay matrix is covered for the
abandonment sibling and at the receipt boundary; the ordinary, failed-start
and refused-session endings have their normal paths proved but not their own
interruption cases.

## 2026-08-30 — ninth round (`baton.claude`, W43975 impl claim)

`review-2026-08-30T15-44-28Z.md`. The descriptor-relative removal is accepted;
this round writes the final P0 gate — the public-ending matrix for the three
endings that did not have one.

### The three siblings, each in its own ending's suite

Written where each ending's fixture already lives, rather than in a second
harness that would prove its own setup.

**Ordinary cleanup** (`test_intake`, 5 cases): both receipts bound into
`cleanup.settled` and an exact replay that normalizes nothing; an interrupted
normalization committing no ending and resuming without renormalizing the
settled root; a custodian changed between the acts colliding; a deployment
without the seam destroying nothing; and THE CASE ONLY THIS ENDING HAS —
removal-before-terminal-commit, then the retry once the roots are gone.

**Failed start** (`test_attempts`, 4 cases) and **refused session**
(`test_refused_session_cleanup`, 4 cases): the same binding, replay,
interruption and collision properties, plus the one that distinguishes a
recordless ending — the home is RETAINED, not removed, because that is what
`retained` means for them.

### One case I modelled rather than faked

For the crash between the removal and the terminal commit, my first cut drove
`store.transact` to run its action and then raise. That committed the axis
moves outside the journal, which is a state no crash produces: the
transaction's writes roll back and the filesystem removal does not. So the
case establishes the state a real crash leaves — roots gone, cleanup axis
still `pending` — and proves the retry completes over it, which is exactly
what `discard_execution_roots` answering an absent home with `()` is for.

### Verification

    ...fourteen modules including test_ended_runtime_adoption,
    test_negative_race_endings and test_lifecycle_composition
    -> 973 tests, OK (4 skipped). Whitespace passed.

The matrix now covers all four public endings: the abandonment sibling in
`test_attempts`, the receipt boundary in `test_custody`, and these three.
