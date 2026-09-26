# Implementer progress — W270664

## 2026-09-26 claim 272502 — dossier created and bound; F2 re-anchored; NO source change

FIRST CLAIM ON THIS WORK. It had no binding at all (`binding: null`) and no prior handoff,
and owner 270664 requires a dedicated dossier bound BEFORE implementation. This claim
delivers that dossier and the groundwork a correction cannot be written safely without. It
changes NO product source and NO test.

**WHAT WAS DONE, exactly.**

* Read the canonical state, claimed W270664 (seq 272502), read its complete event history
  (three events: create 270664, reroute 272500, this claim) and its one thread message,
  which is the owner's selection and the authority for this work.
* Read F2 in the audit and the owner disposition note beside it.
* Re-verified every F2 site against the CURRENT bytes and recorded the file hashes.
* Created and bound this dossier; wrote FINDING.md and PLAN.md.

**THE FINDING THIS CLAIM CONTRIBUTES: the audit's line numbers no longer match the file.**
W257624's accepted restoration-lock additions shifted `workspaces.py`, so all eight cited
line numbers for F2 are stale. FINDING.md records the current locations by name. A patch
driven by the audit's numbers would land in the wrong place, and that is worth knowing
before anybody writes one rather than after.

**OWNERSHIP COORDINATION, as the owner required before routing implementation.** W257624's
narrow region in `workspaces.py` is its five restoration-lock functions; W270664's region is
the seven removal functions plus `intake._settle`'s call site. The two sets are disjoint and
neither calls the other. `intake.py` was a pending item W257624 named but never claimed or
edited; it is owned here now. FINDING.md carries the exact lists.

**WHAT IS NOT DONE: the correction itself, and no part of it was started.** No product file
was opened for writing. The reason is honest rather than procedural: F2 needs an ownership
transition, both entry paths reworked, the nested `in_transaction` branch removed, and nine
deterministic cases including two real entry paths and a paused-filesystem schedule. That is
several claims of work in the shape W257624 took, and starting it without room to finish and
prove it would leave the tree in a state neither accepted nor reverted. The dossier is
therefore delivered complete and the Work is returned with exact remaining scope rather than
held open.

**VERIFICATION SPENDING THIS CLAIM: none executed.** No selector, no suite, no mutation
probe — there was no code change to verify. The bounded command this Work will use is
recorded in VERIFICATION-SELECTORS.md so the next claim starts from a named selector rather
than inventing one.

## 2026-09-26 claim 272559 — baseline measured; the STANDALONE entry corrected and proved

Review 272555's next milestone was "baseline focused regressions, pin the minimal reciprocal
custody-hold/reuse/adoption admission hooks ..., then implement and verify". The baseline is
measured, the reciprocal custody hook is implemented rather than only pinned, and the
STANDALONE removal entry is corrected and proved. The INTAKE entry is not done.

**BASELINE, BEFORE ANY EDIT, so a pre-existing failure can never be reported as a
regression and a regression can never be excused as pre-existing:**
`tests.manager.test_workspaces` 136 OK, `tests.manager.test_custody` 121 OK,
`tests.manager.test_intake` 204 OK. All three still pass after the change, at the same
counts.

**THE TEST ROOT IS `/tmp/baton-w270664-claude`**, recorded because review 272555 says
`/var/tmp/baton-w270664` is not writable in the reviewer's environment. It is not W257624's
root and shares no residue with it.

**WHAT THE CORRECTION DOES.** `_serialized_removal`'s standalone path is now
prepare-outside / admit-in-the-database / remove-outside / complete-in-the-database:

* `refuse_if_held` runs first and OUTSIDE every transaction, because it reaches `realpath`.
  Its typed refusal and message are unchanged; only where it runs changed.
* `_admitted_removal` takes ONE short raw `BEGIN IMMEDIATE` doing only database work: both
  roots' custody holds re-read from the journal, any standing removal ownership refused, and
  this act's ownership committed. `create_line` and `review_cycles._admitted_execution` are
  the precedent for the raw short transaction.
* the removal itself runs with NO transaction open;
* `_completed_removal` records what was removed in a second short transaction, revalidating
  in pure SQL that the ownership is still this act's and that no hold arrived while the tree
  came off the disk.

**THE RECIPROCAL HALF IS IMPLEMENTED, which review 272555 said the ownership record alone
could not give.** `custody._claim_episode`'s claiming callback now reads
`workspaces.standing_removal` under its OWN `BEGIN IMMEDIATE` and refuses while a removal
ownership stands with no completion. Whichever act is admitted first excludes the other;
neither side checks only its own side.

**AN INTERRUPTED REMOVAL IS HELD.** Ownership with no completion behind it refuses the next
removal by ordinal and refuses a custody claim. The accepted asymmetry is preserved: an
absent home is still `False` rather than a refusal.

**8 CASES OK, 0.047s, three consecutive runs**, in
`test_removal_outside_the_lock.py` under this dossier. THREE MUTATIONS, ALL THREE
LOAD-BEARING: the reciprocal custody hook removed, the standing-removal hold removed, and
the admission's own hold re-read removed — the third only after I added the case for the
interval it protects, because the outer `refuse_if_held` had been covering it.

**TWO FIXTURE DEFECTS I FOUND BY RUNNING, both reported rather than quietly fixed.** The
unrelated-progress case opened its second sqlite connection in the main thread and used it
in a worker, so `sqlite3.ProgrammingError` looked exactly like "the write was blocked" —
a fixture that can fail silently into the answer it is looking for. It now opens the
connection in the thread that uses it and asserts the worker raised nothing. And that same
case cost a 90-second red run through its own timeouts, which is in the spending.

**WHAT IS NOT DONE: THE INTAKE ENTRY.** `intake._settle` still calls
`discard_execution_roots` from inside the cleanup transaction, and `_serialized_removal`'s
nested `in_transaction` branch still serves it, unchanged. It is reached BEFORE the new
shape, so intake's behaviour is byte-for-byte what it was — which is why `test_intake` still
passes at 204. Removing that branch without correcting intake would break the cleanup, so
the two must move together. The retired pre-correction body is kept for one claim as
`_superseded_serialized_removal`, with no callers, so a reviewer can compare shapes; the
next claim deletes it.

## 2026-09-26 claim 272653 — the cleared-history false refusal fixed

Review 272635's probe caught a defect I introduced, and it was worse than the one this
correction is about: `_journal_holds` returned EVERY recorded custody episode, so a root whose
uncertainty an operator had already reconciled could NEVER be removed. A permanent false
refusal on a cleared history is not conservatism, it is a new bug.

**THE PREDICATE IS NOW THE ACCEPTED ONE.** `custody._standing_overlap` -- the reader
`_claim_episode` itself uses -- walks both roots and answers the oldest UNCLEARED episode.
Borrowing it rather than writing a second reader is deliberate: two readers of one fact are
two chances to disagree about it.

**NEW CASE, three histories through one predicate:** no history removes; a cleared-only
history removes; a MIXED history with one cleared and one live episode refuses and the live
one is what refuses. Measured while writing it: the mixed case is answered by the OUTER
`refuse_if_held` with its own accepted `policy/denied` refusal, before the admission is
reached -- so the case asserts that rather than the admission's refusal I had expected, and
the admission's own re-read keeps its own case (the hold that arrives in the interval).

**9 cases OK, 0.054s, three consecutive runs.** Reviewer probe `review_cleared_hold_20260926`
OK. Regressions unchanged: 136 / 121 / 204 OK. MUTATION: restoring the every-episode reader
fails the new case.

**STILL NOT DONE, unchanged from the previous claim:** the intake entry and its ordering, the
nested shortcut and the retired `_superseded_serialized_removal`, the reuse/adoption
reciprocal hooks, and the concurrent-removal, both-root/alias and stale-completion
obligations.

## 2026-09-26 claim 272688 — the two labelling corrections review 272675 asked for

Small claim, and deliberately only what was asked: the result-root diagnostic attribution and
the simulated-clearance label. No new scope.

**THE DIAGNOSTIC NO LONGER NAMES THE WRONG ROOT.** `_journal_holds` defaulted the reported
root to "workspace" whenever the episode document carried no `root` field, so a RESULT-root
hold could have been diagnosed as a workspace one -- a refusal that names the wrong resource
is a refusal an operator cannot act on.

**AND MY FIRST FIX FOR IT WAS WRONG, measured rather than reasoned.** I assumed every episode
`custody_holds` returns carries `("root", which)` and made a missing one an integrity refusal;
the standing episode from `_record_hold` does NOT carry it, so a correct refusal became an
integrity error and my own interval case failed. The reader now reports an unlabelled episode
as covering the overlapping PAIR rather than defaulting to either name, which is what the
review actually asked for.

**THE SIMULATED CLEARANCE IS LABELLED AS ONE.** The cleared/mixed case mocks the READER's
validated output, not an operator's reconciliation: a real clearance goes through
`custody.clear_custody_hold`, which requires the operator's account AND the engine's own
settlement. Measured while looking for a real one: `clear_custody_hold` has NO exercise
anywhere in this build -- no test in `tests/` calls it -- so a real-clearance case has to
construct that settlement from the contract rather than copy a precedent. It is remaining
scope and is now named as such in the case's own docstring.

**9 cases OK, 0.053s, three consecutive runs.** Reviewer probe OK. Regressions unchanged:
136 / 121 / 204 OK.

**STILL NOT DONE, unchanged:** a real journal clearance through `clear_custody_hold`; the
intake entry and its ordering; the nested shortcut and the retired body; the reuse/adoption
reciprocal hooks; actual-object pinning and alias safety; absent-but-unresolved versus ordinary
absent-home; and the concurrent-removal, both-root and stale-completion obligations.

## 2026-09-26 claim 272727 — absent-but-unresolved implemented; the root field finally right

**ABSENT IS NOT THE SAME AS RESOLVED, and that gap is now closed.** A home can be gone
BECAUSE an admitted removal was part way through when it stopped, so answering `False` there
reported the caller's desired state while the act that produced it was unaccounted for.
`discard_workspace` now refuses before the absence shortcut when a removal ownership stands
with no completion; a home that is absent with nothing outstanding still answers `False`, and
that case is untouched beside the new one.

**THE ROOT FIELD IS `standing["held"]["root"]`, which review 272713 had to tell me after two
wrong guesses of my own.** `_standing_overlap` answers `{"held": <episode>, "episode": n}`, so
the top-level document has no `root` at all: my first cut defaulted the NAME to "workspace",
which could diagnose a result-root hold as a workspace one, and my second refused the missing
top-level field as malformed, which turned a correct refusal into an integrity error. Reading
the field that actually carries it fixes both. Two wrong attempts at one three-line read is
worth recording as a pattern, not just as an outcome.

**MEASURED WHILE WRITING THE NEW CASE:** with the home only partly removed, the ADMISSION's
standing-removal refusal arrives before the absence path -- also a hold, but a different
sentence -- so the case removes what the interrupted act left and asserts the absence
refusal it is actually about, rather than whichever guard happened to answer.

**10 cases OK, 0.058s, three consecutive runs.** Reviewer probe OK. Regressions unchanged:
136 / 121 / 204 OK. MUTATION: letting an absent home answer `False` regardless of an
unresolved removal fails the new case.

**THE REAL-CLEARANCE CASE IS STILL OPEN, and now for a stated reason rather than for want of a
precedent.** Review 272713 supplied it: W257624's `test_hold_clearance.py` composes the
settlement from an ENGINE DOUBLE's own submission (`self.engines`, `answered()`, `clearing()`
at lines 102/129/145). Adapting that needs the engine double stood up in this dossier's
fixture, which is a case-construction task of its own rather than a copy; I read the
precedent without editing it, as instructed.

**STILL NOT DONE:** the real journal clearance above; the intake entry and its ordering; the
nested shortcut and the retired body; the reuse/adoption reciprocal hooks; actual-object
pinning and alias safety; and the concurrent-removal, both-root and stale-completion
obligations.

## 2026-09-26 claim 272758 — the actual object pinned across the admission

**A REMOVAL IS NOW BOUND TO AN OBJECT, NOT TO A NAME.** The effect runs outside every lock,
so a home replaced between the admission and the removal would have been deleted under an
authority granted for a different inode. `_pinned_home` records the home's device and inode
BEFORE admission -- outside every transaction, where filesystem reads belong -- the ownership
document carries it, and `_still_the_pinned_home` compares it immediately before the effect.
`_real` already refuses a symlinked home at entry; this closes the interval AFTER that proof,
for the same reason `discard_execution_roots` opens a directory descriptor rather than
trusting a pathname.

ABSENCE IS PINNED AS ABSENCE rather than refused, because an absent home has its own accepted
answer at the caller and its own case beside this one.

**NEW CASE, staged deterministically:** the home is swapped for a different real directory
from inside the admission itself, so the replacement provably falls in the interval, and the
refusal is `runtime-observation/identity-mismatch`. The substitute survives -- nothing is
deleted under the wrong authority -- and it is this fixture's own temporary directory.

**11 cases OK, 0.062s, three consecutive runs.** Reviewer probe OK. Regressions unchanged:
136 / 121 / 204 OK. MUTATION: dropping the comparison fails the new case.

**STILL NOT DONE:** the reciprocal reuse and adoption admission hooks and their race proofs;
the intake entry -- eligibility before delete, completion before lane release, no external
I/O under any transaction -- and the nested shortcut and retired body deleted with it; the
actual journal clearance through `clear_custody_hold`, whose precedent needs this dossier's
fixture to stand up an engine double; and the concurrent-removal, both-root and
stale-completion obligations.

## 2026-09-26 claim 272806 — my object-pinning claim is WITHDRAWN in the code's own prose

Review 272784 swapped the home AFTER my identity check answered and the production removal
deleted the substitute's marker. The finding is right and my previous handoff was wrong: I
said the removal was "bound to an object, not to a name", and a stat comparison cannot bind
anything, because the deletion that follows still resolves a PATHNAME. What I built is a
TIME-OF-CHECK comparison that closes the admission-to-effect interval and nothing after it.

**THE OVERSTATEMENT IS CORRECTED WHERE IT WILL BE READ**, not only here: both
`_still_the_pinned_home`'s docstring and the call site now state what the comparison does and
does not establish, name review 272784 as what proved the gap, and record that the object
binding is still owed. The comparison is KEPT because the interval before the effect is real
and has its own passing case; it is no longer described as more than that.

**WHAT THE REAL FIX NEEDS, and why it is not in this claim.** The deletion, the traversal and
the final removal have to run RELATIVE TO A DIRECTORY DESCRIPTOR opened once with
`O_NOFOLLOW|O_DIRECTORY` and `fstat`-verified against the pin -- which is exactly what
`discard_execution_roots` already does for the execution roots and what `_remove` does not do
for the home. `_remove` is a two-pass, mount-table-aware, top-down walk over PATHNAMES whose
current shape is the product of at least three prior reviews (the superseded bottom-up
reasoning is recorded in its own docstring). Converting it to descriptor-relative traversal
is a rewrite of heavily-reviewed accepted code, and it must preserve the mount refusal, the
admit-then-remove two-pass order and the same-device bind detection. I am not starting that
without room to finish and prove it; starting it would leave the most destructive function in
this module half-converted.

**11 cases OK, 0.065s.** No product behaviour changed this claim -- prose only, and I am not
calling that a milestone. The reviewer's after-pin-swap probe still fails, as it should until
the descriptor work lands.

**STILL NOT DONE:** the descriptor-relative binding above, which is now the head of the queue;
non-absence stat errors preserved as uncertainty; the reciprocal reuse and adoption hooks; the
intake entry with the nested shortcut and retired body; the actual journal clearance; and the
concurrent-removal, both-root and stale-completion obligations.

## 2026-09-26 claim 272826 — the descriptor binding ATTEMPTED and reverted; exact obstacle measured

I implemented the object binding review 272784/272813 asked for, ran it, and reverted it. This
is a measured blocker rather than a voluntary early return, and the measurement is the useful
part.

**WHAT I BUILT.** `_removed_pinned_home`: open the storage root `O_DIRECTORY|O_NOFOLLOW`,
`fstatat` the attempt's name to get the child object, open THAT `O_NOFOLLOW` relative to the
parent, compare `fstat` against the entry, remove the CONTENTS through `/proc/self/fd/<fd>` --
which resolves to the open object, so no rename of the home, its name or any ancestor can
redirect the walk -- and then `rmdir` the name relative to the PARENT's descriptor after
re-proving the child still resolves to the same object. That last part is review 272813's own
point: an fd on the home is not exact-child authority, so the parent fd plus a verified child
stat is what authorizes the final `rmdir`. Non-`ENOENT` stat errors refuse instead of reading
as absence.

**WHY IT DOES NOT WORK AS WRITTEN, measured:** six cases failed with
`'/proc/self/fd/7/workspace' is on another filesystem than the tree '/proc/self/fd/7'`.
`_remove`'s mount detection begins with `os.lstat` of the tree ROOT, and lstat of a
`/proc/self/fd/N` magic symlink answers PROCFS -- so every real child looks cross-device and
the mount refusal fires on the manager's own workspace. The device comparison that the
W71917 run7 [P0] review put there is exactly what rejects the fd path.

**SO THE OBSTACLE IS NAMED PRECISELY: `_remove` must take a `dir_fd` and do its own stats
with `dir_fd=`/`follow_symlinks=False` internally, rather than being handed a path that
stands for a descriptor.** That is the rewrite of its two passes I flagged last claim, now
with the reason stated as a measurement rather than a prediction: the magic-symlink shortcut
is not available, so the descriptor has to be threaded through both passes and through the
mount-table check, preserving the top-down admit-then-remove order and the same-device bind
detection. `discard_execution_roots` already does descriptor-relative work and is the shape
to follow.

**THE TREE IS BACK AT THE LAST GREEN STATE**, `workspaces.py`
ec97b94268fb16881457dd340f76f09cd2e611826521ad530ee84be71140684b -- byte-identical to the
hash I handed over last claim. 11 cases OK 0.063s twice; regressions 136 / 121 / 204 OK. The
reviewer's after-pin-swap probe still fails, and the code still says so in its own prose.

**STILL NOT DONE:** the dir_fd rewrite of `_remove` above, which is the head of the queue and
now has its design and its obstacle both recorded; non-absence stat errors as uncertainty
(written and reverted with the rest, easy to restore inside that rewrite); the reciprocal
reuse and adoption hooks; the intake entry with the nested shortcut and retired body; the
actual journal clearance; and the concurrent-removal, both-root and stale-completion
obligations.

## 2026-09-26 claim 272864 — THE DESTRUCTIVE EFFECT IS BOUND TO THE ADMITTED OBJECT

Review 272850's P1 is closed: the reviewer's own after-pin-swap probe now PASSES, and the
selector and all three focused suites are green with it.

**WHAT THE BINDING IS.** `_removed_pinned_home` opens the attempt's home
`O_NOFOLLOW|O_DIRECTORY` relative to its PARENT's descriptor, compares the opened object
against the entry the parent gave AND against the object recorded before admission, and then
removes the CONTENTS through `/proc/self/fd/<descriptor>` -- a path that resolves to the open
inode, so no rename of the home, its name or any ancestor can redirect the walk. The reviewed
two-pass mount-aware walk runs unchanged beneath it.

**THREE MEASURED OBSTACLES, each one fixed only after it actually happened:**

1. `_remove`'s root measurement used `os.lstat`, and `lstat` of a `/proc/self/fd/N` magic
   symlink answers PROCFS -- so every real child looked cross-device and the mount refusal
   rejected the manager's own workspace. The root is now measured with `stat`, which follows
   the one link the caller supplied deliberately and is identical to `lstat` for the ordinary
   real path every other caller passes.
2. The per-entry check then refused the ROOT against itself, for the same reason. The root is
   no longer re-measured by its name -- `base` above IS its device -- while every DESCENDANT
   is still measured with `lstat`, which is where a mount can actually appear.
3. AND THE COMPARISON THAT MATTERED WAS THE ONE I HAD NOT MADE: comparing the opened object
   only against the parent's CURRENT entry is self-consistent and therefore proves nothing --
   a replacement swapped in before the call is opened, matches itself, and is deleted. That is
   exactly what review 272850's probe did, and it kept failing until the opened object was
   compared against the object recorded BEFORE admission.

**THE ONE WINDOW THAT REMAINS IS STATED, NOT CLAIMED CLOSED.** Review 07:01:39Z is right that
parent-fd plus stat plus `rmdir` is not exact-child authority: between the final stat and the
`rmdir` the name can be replaced again, and this build has no `renameat2` exchange or
by-handle unlink. What that window can cost is bounded and the docstring says so: the contents
are already gone from the pinned object, and the only path that ever reaches contents is the
descriptor's, so a late swap could lose one EMPTY directory and nothing with material in it.

**11 cases OK, 0.063s, three consecutive runs.** Reviewer probes: after_pin_swap OK (was
failing), cleared_hold OK. Regressions 136 / 121 / 234 -- correction: 136 / 121 / 204 OK.
MUTATION: dropping the admitted-object comparison makes the after-pin-swap probe fail again.

**STILL NOT DONE:** the remaining `rmdir` window above if the reviewer wants it closed (it
needs a syscall this build does not use); the reciprocal reuse and adoption hooks; the intake
entry with the nested shortcut and retired body; the actual journal clearance; and the
concurrent-removal, both-root and stale-completion obligations.

## 2026-09-26 claim 272924 — descendant re-proof ATTEMPTED, measured, reverted

Review 272890's descendant-swap probe is a real escape and my attempt at it did not work. The
tree is back at 53e5a03b, the state you verified, and everything that passed then passes now.

**THE DEFECT, RESTATED SO IT IS NOT LOST.** `_remove`'s preflight admits DIRECTORIES AS
STRINGS. The second pass then walks those strings, so a descendant replaced by a symlink
between the passes is resolved through: the preflight cleared the real directory and the
deletion reaches whatever the name points at afterwards, including material outside the tree.
The root descriptor does not help, because these names are resolved later and separately.

**WHAT I IMPLEMENTED:** record each admitted directory as `(path, lstat)` in pass one and
re-prove `(st_dev, st_ino)` immediately before touching it in pass two, refusing a mismatch as
`runtime-observation/identity-mismatch` and refusing an unreadable member as uncertain rather
than absent.

**WHY IT DOES NOT WORK YET, measured twice:** the ROOT of the walk is the magic symlink
`/proc/self/fd/N` when the removal is bound to the open object, and it needs different
treatment from every descendant in BOTH passes -- `lstat` answers procfs for it. I special-cased
the root with `stat` in both places and still got six errors in my selector and two in
`tests.manager.test_workspaces`; the remaining cause is not yet identified, and I stopped
rather than guess at the most destructive function in this module with no room to verify.

**THE DESIGN THAT FOLLOWS FROM THIS.** Special-casing the root is the wrong shape -- it needs
the case distinction in four places and I got it wrong twice. The right shape is for `_remove`
to take the DESCRIPTOR rather than a path standing for one, and to do its own `scandir`/`stat`
with `dir_fd=` so that root and descendants are measured the same way and no name is resolved
twice. That is the rewrite I named two claims ago; this attempt is evidence for it rather than
against it.

**CURRENT STATE, verified after the revert:** 11 cases OK 0.064s; after_pin_swap OK;
cleared_hold OK; 136 / 121 / 204 OK. The descendant-swap probe FAILS and the defect above is
recorded rather than papered over.

**STILL NOT DONE:** the descendant binding above, now with two measured failures behind it;
the final-rmdir window; the reciprocal reuse and adoption hooks; the intake entry with the
nested shortcut and retired body; the actual journal clearance; and the concurrent-removal,
both-root and stale-completion obligations.

## 2026-09-26 claim 272962 — THE HANDLE-RETAINING WALK, implemented and proved

Review 272949's sequence, followed step by step. 12 cases OK, 0.068s; regressions
136 / 121 / 204 OK.

**PASS ONE RETAINS WHAT IT PROVED.** `_removed_through_handles` descends with `scandir` over an
open directory handle, opens each child directory `O_NOFOLLOW|O_DIRECTORY` RELATIVE to its
parent's handle, and KEEPS that handle. Every directory is device-compared by `fstat` on the
handle and checked against the mount table through the handle's own `/proc/self/fd` link -- the
kernel's answer about the open object, not a path a caller could swap. `scandir` consumes the
fd, as the review noted, and the names it yields are used as RELATIVE operands.

**PASS TWO USES THE SAME OBJECTS.** `_thaw_handle` does `fchmod` on the handle;
`unlink`/`rmdir` are by name relative to it; the final directory is removed by name relative to
its PARENT's handle. No name is resolved from the root twice and no absolute path is rebuilt.
The admit-everything-then-remove-deepest-first order is preserved, so a refusal still precedes
every unlink, and the worker-owned refusal is kept. All handles are closed on success, refusal
and failure.

**THE REVIEWER'S PROBE NO LONGER TRIGGERS AND I AM NOT COUNTING THAT AS PROOF.**
`review_descendant_swap_20260926.py` interposes on `_thaw(path)`; the handle walk calls
`_thaw_handle(handle)` and never hands a descendant path to `_thaw`, so its swap never fires and
its first assertion fails. Review 272949 anticipated exactly this -- "adapt a new schedule if a
legitimate internal refactor retires the old interception point; never count a non-triggered
probe as proof" -- so my new case runs the SAME schedule at the new interception point: the
descendant's name is replaced by a symlink to material outside the tree at the first thaw of the
removal pass, and the outside marker SURVIVES.

**MUTATION: putting the path-based `_remove` back in place of the handle walk fails that case**,
so the handles are what carry the property.

**STILL NOT DONE:** the final-entry identity through the selected reciprocal exclusion rather
than a stat claim; the reciprocal reuse and adoption hooks; the intake entry with the nested
shortcut and retired body; the actual journal clearance; non-absence uncertainty inside the new
walk; and the concurrent-removal, both-root and stale-completion proofs.

## 2026-09-26 claim 273016 — the reciprocal exclusion at the chokepoint; final entry covered

Review 273000's next item. 13 cases OK, 0.072s twice; regressions 136 / 121 / 204 OK; both
compatible reviewer probes OK.

**ONE READING, AT THE POINT EVERY ENTRY ALREADY PASSES THROUGH.** `refuse_if_held` is where
allocation, adoption and removal all go, so the standing-removal reading lives there rather
than bolted onto each of them: an unresolved removal now refuses reuse, adoption AND a second
removal with one message, and it is the same reading `custody._claim_episode` makes under its
own lock, so neither side trusts only its own.

**AND THIS IS WHAT COVERS THE FINAL ENTRY.** Review 07:01:39Z was right that parent-fd plus
stat plus `rmdir` is not exact-child authority. What makes the last `rmdir` safe is not a better
stat but that nothing else may create, adopt or remove at that name while the ownership stands.
That is an exclusion, not an inference, and it is now recorded as the answer to that item.

**A MESSAGE MOVED AND I FOLLOWED IT RATHER THAN PINNING THE OLD ONE.** With the check at the
chokepoint, the interrupted-removal case now meets the broader true sentence -- these roots are
not reused, adopted or removed again until reconciled -- instead of the admission's older
wording. The assertion follows the behaviour to where the review asked it to be.

**NEW CASE:** with an unresolved removal standing, `adopted_assignment_workspace` is refused
AND a custody claim is refused, from the other side of the same fact. MUTATION: removing the
chokepoint reading fails it.

**STILL NOT DONE:** the intake entry -- eligibility before delete, completion before lane
release, no external I/O under any transaction -- with the nested `in_transaction` shortcut and
the retired `_superseded_serialized_removal` deleted alongside; the actual journal clearance;
non-absence stat uncertainty inside the handle walk; and the both-root/alias, concurrent-removal
and stale-completion proofs.

## 2026-09-26 claim 273053 — reciprocal READ is not mutual exclusion; design named, nothing started

Review 273030 is right and the distinction matters: what I put at the chokepoint is a READ of the
ownership record before the act. The adoption-admission probe walks straight through it --
adoption reads "no standing removal", a removal is admitted after that read, and adoption then
proceeds. A guard that answers before the competing act commits excludes nothing.

**WHAT MUTUAL EXCLUSION ACTUALLY REQUIRES HERE, named precisely so the next claim starts from
it:** adoption and allocation need their own DURABLE IN-FLIGHT RECORD taken in the same
`BEGIN IMMEDIATE` discipline the removal admission uses, so the two decisions serialize against
each other in the journal rather than each reading the other's absence. Symmetrically:
`_admitted_removal` must refuse while an adoption or allocation record stands unresolved, and
the adoption/allocation admission must refuse while a removal ownership stands. Both orders then
have a winner decided by the store, and an actor already past its early read is refused at its
own admission rather than after it.

**AND ONE OF THE TWO ENTRIES CANNOT BE HOOKED WITHOUT AN INTERFACE CHANGE:**
`assignment_workspace` (workspaces.py:2647) takes no `control` operand at all, so it cannot read
or write any admission record. Review 273030 says to audit its callers, and that audit plus the
operand is part of this item rather than a side quest.

**NOTHING WAS STARTED THIS CLAIM, and the reason is my own limit rather than the code's.** I am
at the end of the context available to me in this session, and a symmetric lifetime record across
three entries plus a caller audit is not work I can land and verify in what remains. Starting it
would leave a half-built exclusion in the most destructive path in this module, which is worse
than leaving the read that is there now -- the read is disclosed, a half-exclusion would not be.

**STATE VERIFIED THIS CLAIM:** workspaces.py 0482352243b1022f5f41aed078cc1d870856ec82c3d6cb9d1c6fdc4dc708a09a,
unchanged; 13 cases OK. Everything previously accepted stands: the handle-retaining traversal,
the admitted-object binding, the cleared-history predicate, the absent-but-unresolved refusal and
the chokepoint read -- which is useful but is now correctly described as a read.

**STILL NOT DONE:** the symmetric admission above and the `assignment_workspace` operand with its
caller audit; the final-entry identity, which depends on that exclusion; the intake entry with the
nested shortcut and retired body; the actual journal clearance; non-absence uncertainty in the
handle walk; and the both-root/alias, concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273092 — SYMMETRIC ADMISSION: both orders excluded, both proved

Review 273030/273077's item is implemented. The reviewer's adoption-admission probe PASSES --
it failed on the previous bytes -- and both orders have a case.

**ADOPTION IS ADMITTED, NOT MERELY CHECKED.** `_admitted_adoption` takes its own short
`BEGIN IMMEDIATE`: it refuses while a removal ownership stands and records an adoption in-flight
row. `_admitted_removal` now reads THAT record inside its own transaction and refuses while it
stands. Whichever transaction commits first wins and the other sees it, so an actor already past
its early read is refused at its OWN admission rather than after it. Neither side is trusted to
check only the other's absence -- which is exactly what my previous read-before-use did wrong.

**THE ADOPTION WINDOW IS A WINDOW, NOT A HOLD.** Adoption only proves roots it does not create,
so its record is settled on success AND on failure, in a `finally`. A window the product opened
and never closed would block that attempt's removal forever -- the failure mode an exclusion
turns into when it is mistaken for a hold -- so the case asserts that a SUCCESSFUL adoption
leaves nothing standing and the removal afterwards still works.

**14 cases OK, 0.086s.** Regressions 136 / 121 / 204 OK. Reviewer probes: adoption_admission OK,
after_pin_swap OK, cleared_hold OK.

**THREE MUTATIONS AND AN HONEST SPLIT OF WHAT COVERS WHAT.** Removing the removal's
standing-adoption read fails MY case. Removing adoption's admission entirely fails the
REVIEWER's probe and not mine, because my case admits the window directly to stage the reverse
order -- their probe is what covers that direction and I am saying so rather than implying my
selector covers both. Never settling the window failed nothing until I added the successful-
adoption assertion; it fails now.

**STILL NOT DONE:** `assignment_workspace` (workspaces.py:2647) still takes no `control`
operand, so the allocation entry cannot participate in this exclusion -- the operand plus its
caller audit is the next piece; the final-entry identity, which rests on this exclusion and can
now be argued from it; the intake entry with the nested shortcut and retired body; the actual
journal clearance; non-absence uncertainty in the handle walk; and the both-root/alias,
concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273131 — the adoption lifetime hits an OWNERSHIP boundary, not a context one

Review 273108 is right: my `finally` settles the adoption window before the caller receives the
roots, so a removal admitted in that gap can delete what the caller is about to use. The
exclusion I built covers the ADMISSION race and not USE, and this claim is the audit of what
extending it to use would actually take.

**THE CALLER AUDIT, measured rather than assumed.** `adopted_assignment_workspace` has exactly
three product callers and one accepted suite:

    workspaces.py:3482          line_assignment_workspace -- MINE, inside this Work's region
    review_cycles.py:3955       W257624's file, inside the region that Work owns
    source_boundary.py / oci.py references are prose, not calls
    tests/manager/test_source_boundary.py -- SIX call sites in an accepted suite I do not own

**SO BOTH SHAPES THE REVIEW OFFERS CROSS AN OWNERSHIP LINE, and that is the blocker.**

* AN ACTUAL-USE LIFETIME means adoption returns something the caller releases -- a context
  manager or an explicit release entry. That changes the call shape at `review_cycles.py:3955`,
  which is W257624's region, and at six sites in an accepted suite that is not mine. Owner 270664
  told me to "coordinate exact ownership with active W257624 before routing implementation; do
  not interrupt or overlap its correction", so making that edit unilaterally is exactly what I
  was told not to do.
* A GAP-FREE TRANSFER TO AN EXISTING ADMITTED AUTHORITY needs a target that already protects
  those roots through use. For the review path the candidate is the grant that immediately
  follows (`_granted_roots`/`_review_grant` at review_cycles.py:3957) -- also W257624's region --
  and for `line_assignment_workspace` there is none: its docstring says plainly that the review
  line home is a namespace NO custody hold can name.

**WHAT I DID NOT DO, and why that is a decision rather than an omission.** I did not change
adoption's signature, did not edit `review_cycles.py`, and did not touch the accepted suite. The
admission race the previous claim closed stays closed; the use gap stays open and is now
documented with its cause, its two candidate shapes and the exact files each one requires.

**STATE THIS CLAIM: unchanged product bytes** -- workspaces.py
ce7d5c596f7e7d7b07f343ba4bed59719ae389dc76f58d759a5c47635fd9ba62 -- 14 cases OK 0.086s.

**WHAT I AM ASKING FOR, precisely:** a ruling on which shape to take, or authority to edit
`review_cycles.py:3955` and the six `test_source_boundary.py` call sites as part of W270664. I
can implement either within one claim once the boundary is settled; what I cannot do is choose to
cross it myself.

## 2026-09-26 claim 273158 — A REGRESSION I INTRODUCED, found by widening the regression boundary

This claim's most important output is not the lifetime work. It is that **I weakened the
foreign-mount protection two claims ago and neither of us caught it**, because my named
regression boundary did not include the suite that owns that case.

**THE REGRESSION.** `tests.manager.test_source_boundary`'s
`CleanupNeverRemovesMaterialThisManagerDidNotCreate.test_a_foreign_mount_under_a_root_refuses_before_anything_is_removed`
expects a ContractRefusal and gets none. Bisected across my own candidates, on a disk-backed
root:

    ec97b942  (before the descriptor binding)      OK
    53e5a03b  (descriptor-bound `_remove`)         FAILED
    ce7d5c59  (current)                            FAILED

So it broke at 53e5a03b, where I measured the walk's ROOT with `stat` instead of `lstat` and
stopped re-measuring the root in the per-directory check -- both to make a `/proc/self/fd` path
usable. "Cleanup removes only what this manager made" is the protection at stake, and the case
asserting it has been failing since then.

**AND IT ONLY SURFACED BECAUSE THE SUITE LIST WAS TOO NARROW.** My dossier named
test_workspaces, test_custody and test_intake as this Work's regression boundary; the mount case
lives in test_source_boundary, which I never ran. That is my error in scoping the evidence, not
an accident of the code.

**A SECOND ENVIRONMENT FACT, measured while finding it.** Those two suites refuse a tmpfs
`BATON_V12_DISK_ROOT` outright -- "W71917 refuses a workspace on memory" -- so on `/tmp` they
report 162/162 and 62 failures that mean nothing. They must be run with a DISK-BACKED root;
`/var/tmp/baton-w270664-claude` works. Baseline there, on current bytes: test_source_boundary
75 ran / 2 failures (the mount case above, plus a scratch-mount list difference that predates
my work and is environmental), test_review_cycles 162 ran / 36 errors (W257624's known
intake.py setUp condition, unrelated to this Work).

**THE LIFETIME ATTEMPT, and why it is not in the tree.** I implemented the handed-out adoption
window -- `_adoption` carried on `AllocatedRoots`, `release_adopted_workspace`, gap-free transfer
through `_granted_roots` -- and reverted it. With no caller releasing, every existing adoption
leaves a window standing and the chokepoint then refuses that attempt's later acts. The wiring
has to land in the same claim as the shape, and I would not start that while a live regression
of mine was unreported.

**STATE: workspaces.py ce7d5c596f7e7d7b07f343ba4bed59719ae389dc76f58d759a5c47635fd9ba62,
unchanged this claim.** 14 cases OK; test_workspaces 136 OK.

**FIRST THING NEXT CLAIM: fix the mount regression**, restore the root's own mount-table and
device check under the handle walk (`fstat` on the handle for the device, the handle's own
`/proc/self/fd` link for table membership -- including for the ROOT, which is what I dropped),
and add test_source_boundary to this dossier's regression boundary permanently.

## 2026-09-26 claim 273206 — my "regression" was the TEST's injection, and I withdraw the claim

Review 273184 is right and my previous claim's headline was wrong. The walker already checks
`fstat` on the handle AND the mount table including the root; the protection did not weaken.
What broke was the legacy case's INJECTION: it faked a foreign device by patching `os.lstat`
BY PATHNAME, and the handle walk compares devices with `os.fstat` on the retained handle, so
the simulation stopped reaching the comparison. The refusal stopped arriving because the test
stopped testing, not because cleanup stopped protecting. I called that a regression in my own
code and it was not one; the correction is recorded here because a wrong diagnosis in the
dossier is worse than the bug would have been.

**THE CASE IS ADAPTED, UNDER STANDING TEST AUTHORITY, and it now proves its own injection.**
`test_a_foreign_mount_under_a_root_refuses_before_anything_is_removed` applies the same
foreign-device simulation at BOTH observations -- `os.lstat` by pathname, for the path-based
walk that `discard_execution_roots` still uses, and `os.fstat` by (device, inode) identity, for
the retained-handle walk -- and asserts `fired` is non-empty before asserting the refusal. Every
original safety assertion is kept: the `policy` category and the survival of the file behind the
mountpoint. A case that can silently stop firing is the failure mode that produced my wrong
diagnosis, so it no longer can.

**MEASURED, disk-backed root:** test_source_boundary 75 ran / 1 failure, down from 2.
test_review_cycles 162 ran / 36 errors -- W257624's known intake.py setUp condition.
test_workspaces 136 OK, test_custody 121 OK, test_intake 204 OK, focused selector 14 OK.

**THE REMAINING test_source_boundary FAILURE IS NOT MINE, and I checked rather than asserting
it.** `test_the_runtime_gets_exactly_the_declared_bounded_scratch` expects one mount list and
sees an extra `/run/baton/logs` entry. Run against ec97b942 -- the bytes from before any of this
Work's handle changes -- it fails identically, so it predates W270664 and is environmental or
belongs to another Work.

**STATE: workspaces.py ce7d5c59 unchanged; tests/manager/test_source_boundary.py
28776c75e08c81d4024e790088fcb07b22ab042df96f5ceebd1e07df50664a56 (the adapted case).**

**STILL NOT DONE:** the adoption use lifetime with its caller wiring, which is the next item and
whose shape and failure mode are recorded two entries above; allocation's participation;
the intake entry with the nested shortcut and retired body; the actual journal clearance;
non-absence uncertainty in the handle walk; and the both-root/alias, concurrent-removal and
stale-completion proofs.

## 2026-09-26 claim 273250 — the actual-use lifetime, with the caller wiring

Review 273108/273234's item is implemented: the adoption window now reaches the caller and ends
at a DEFINED HANDOVER instead of in a `finally` before the roots were returned.

**THE SHAPE.** `adopted_assignment_workspace` admits the window, hands it out on the roots
(`_adoption`, a new `AllocatedRoots` slot), and settles it only if the proving FAILS -- nothing
was handed out then. Two exits end it afterwards:

* **THE GRANT HANDOVER, gap-free.** `_granted_roots` settles the window AFTER binding, because
  from that point the grant is what says the roots are in use -- and a grant is a predicate over
  durable state (`_review_grant`: attachment active, line reviewing, checkpoint matching;
  `_writer_grant`: writer active, line writing). That is the "existing admitted authority" review
  273108 pointed at, and the settle happens after the binding, never before.
* **`release_adopted_workspace(roots)`** for a caller that takes roots and binds no grant.
  Idempotent, and harmless on roots that carry no admission.

**THE CALLER WIRING, and the one it exposed.** `line_assignment_workspace` adopts only to prove
the attempt's inputs and then builds its OWN roots for the line home, discarding the adopted
object -- so the window it carried would have stood forever with nobody holding it. Measured:
three review-mount cases in `tests.manager.test_review_cycles` failed exactly that way
(36 errors became 39). It now releases as soon as it has finished with what it adopted, and the
count is back to the baseline 36.

**14 cases OK.** My both-orders case now asserts the corrected behaviour end to end: a bare
adoption keeps its window, a removal is REFUSED while the caller holds the roots, the roots are
still there, an explicit release ends it, and the removal then succeeds -- plus binding a grant
settles the window at the binding.

**REGRESSION, disk-backed:** test_workspaces 136 OK, test_custody 121 OK, test_intake 204 OK,
test_source_boundary 75 ran / 1 known environmental failure, test_review_cycles 162 ran / 36
errors = the W257624 baseline. Reviewer probes adoption_admission, after_pin_swap and
cleared_hold all OK.

**AND THE LIFETIME PROBE NO LONGER TRIGGERS, which I am not counting as a pass.**
`review_adoption_lifetime_20260926` hooks `_settled_adoption` and expects it to be called DURING
adoption -- that was the defect. On the corrected path it is not called there at all, so the
probe fails at `0 != 1`: its injection never fires. Review 272949's rule applies ("adapt a new
schedule if a legitimate internal refactor retires the old interception point; never count a
non-triggered probe as proof"), and my case above is that adapted schedule, asserting the same
property the probe was after: a removal cannot win before the caller has done with the roots.

**STILL NOT DONE:** allocation's participation via a `control` operand on `assignment_workspace`
plus its caller audit; the intake entry with the nested shortcut and the retired body; the actual
journal clearance; non-absence uncertainty in the handle walk; and the both-root/alias,
concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273300 — two of the three lifetime defects fixed; the third measured precisely

Review 273282 named three. Two are corrected in the code; the third is now a measurement rather
than a guess, and it says the fix needs something the removal does not yet have.

**FIXED: the release cleared its token before the settlement committed.** Clearing first meant a
failed settle left the window standing with nobody holding a way to end it -- an orphan by
construction. `release_adopted_workspace` now settles FIRST and clears the carried token only
after the commit, so a failed release leaves the roots still holding their admission and the
caller can retry.

**FIXED: `line_assignment_workspace` released while still handing out the attempt's inputs.** It
returns the attempt's own `inputs` beside the line home, so releasing there ended the exclusion
over material it was about to give away. The admission is now CARRIED onto the roots that entry
returns and ends where every other adopted set's does.

**MEASURED, NOT FIXED: the grant binding is not a handover, because the removal reads no grant.**
I settled the window at `_granted_roots` and called that a gap-free transfer. It is not one:
nothing the removal consults changes when a grant is bound, so the settle simply ended the
exclusion while the roots were in use -- exactly as review 273282 says.

I tried the obvious alternative and it does not work either: carrying the window PAST the binding,
so the adoption record itself stays the exclusion, breaks three review-mount flows in
`tests.manager.test_review_cycles` (36 errors become 39) because those flows bind a grant and then
remove without releasing. So neither settling at the binding nor carrying past it is correct, and
that is the finding: **the removal needs a durable target for "an active writer or review
attachment holds this attempt"** -- the same predicates the grants themselves test
(`_writer_grant`: writer active and line writing; `_review_grant`: attachment active, line
reviewing, checkpoint matching). With that target the binding becomes a real handover and the
window can settle at it; without it, no placement of the settle is sound. Finding that reader,
which `discard_workspace` currently has no operand for -- it knows only the attempt id -- is the
next piece.

**STATE: workspaces.py 73679b1bbbe2018776eb52a896845e84db64d1e10120fdd10b2c0068f8a99802.**
14 cases OK; test_review_cycles 162 ran / 36 errors = baseline; test_source_boundary 75 ran / 1
known environmental failure; test_workspaces 136 OK; test_intake 204 OK.

**STILL NOT DONE:** the durable in-use target above; allocation's participation via a `control`
operand on `assignment_workspace`; the intake entry with the nested shortcut and retired body;
the actual journal clearance; non-absence uncertainty in the handle walk; and the
both-root/alias, concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273330 — the durable in-use target, and the orphan on a rejected composition

Review 273314's two failures are addressed.

**THE GRANT BINDING IS A HANDOVER NOW, because the removal finally reads something that changes
at it.** `_durably_in_use` asks, in PURE SQL inside the admission transaction, exactly what the
grants themselves test: is a writer ACTIVE for this attempt (`line_writers`), or a review
attachment ACTIVE for it (`review_attachments`). While either holds, the roots are in use and no
removal is admitted -- which is precisely as long as a grant could be live. The reviewer was
right that nothing new was needed to reach those rows: the removal already has the store.

**AND A REJECTED COMPOSITION NO LONGER ORPHANS THE WINDOW.** Everything below the adoption in
`line_assignment_workspace` can refuse -- an unreserved namespace, a moved line object -- and the
caller then gets an exception rather than roots, so nothing it holds could ever release. The
composition is now wrapped and the window is ended on every failure path.

**15 cases OK.** MUTATION: dropping the durable-use read fails the new case.

**WHAT THE NEW CASE COVERS AND WHAT IT DOES NOT, recorded rather than implied.** It covers the
removal's CONSUMPTION of the answer -- refused while use is reported, no ownership taken, and it
proceeds when use stops. It does NOT cover the SQL: inserting a writer row needs a real line and
attachment to satisfy the foreign keys, which this fixture has no machinery for, so
`_durably_in_use` is replaced by a labelled answer. **The reader's own query is unproved.** The
honest way to close that is a case built on the accepted line/writer machinery, which lives in
`tests.manager.test_review_cycles`' fixtures rather than mine.

**REGRESSION, disk-backed:** test_review_cycles 162 ran / 36 errors = baseline;
test_source_boundary 75 ran / 1 known environmental failure; test_workspaces 136 OK;
test_custody 121 OK; test_intake 204 OK. Reviewer probes adoption_admission, after_pin_swap and
cleared_hold all OK.

**STILL NOT DONE:** the `_durably_in_use` query itself under real rows; allocation's
participation via a `control` operand on `assignment_workspace`; the intake entry with the nested
shortcut and retired body; the actual journal clearance; non-absence uncertainty in the handle
walk; and the both-root/alias, concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273391 — reciprocal grant admission, and the handover made conditional

Review 273367's two failures are addressed, and the second one corrected a mistake I had made
twice in a row.

**A REMOVAL ADMITTED FIRST NOW BLOCKS A REAL GRANT.** `grant_writer` and `attach_review` read
`standing_removal` inside their OWN admission transactions -- the very locks that admit them --
and refuse while a removal of that attempt's roots stands with no completion. Whichever act
commits its admission first excludes the other. This is the reciprocal half of the durable-use
read the removal already performs, and it lives in `review_cycles.py` under the caller ownership
review 07:39:12 granted; the restoration regions are untouched.

**AND THE GRANT BINDING ONLY HANDS OVER WHEN THERE IS SOMETHING TO HAND OVER TO.** I settled the
adoption window at EVERY binding -- twice -- and review 273367 caught what that misses:
`_granted_roots` is generic, so a grant can be bound while the durable state says nothing (no
active writer, no active attachment), and the settle then dropped the exclusion with nothing
behind it. The window is now released at the binding exactly when `_durably_in_use` answers for
that attempt -- the same condition that makes the removal refuse -- and otherwise travels on with
the granted roots until an explicit release.

**15 cases OK, 0.099s twice.** My both-orders case now asserts both branches of that condition.
MUTATION: dropping the grant-side standing-removal read fails a case.

**REGRESSION, disk-backed:** test_review_cycles 162 ran / 36 errors = baseline -- and this is the
first claim that edited `review_cycles.py`, so the count staying at the baseline is the evidence
that the two hooks changed nothing else; test_source_boundary 75 ran / 1 known environmental
failure; test_workspaces 136 OK; test_custody 121 OK; test_intake 204 OK.

**STILL NOT DONE:** the `_durably_in_use` query under real rows -- still a labelled answer in my
case, and review 273367's ReviewCycles-based probe is the better vehicle; the lifecycle/tool
release proofs; allocation's participation via a `control` operand on `assignment_workspace`; the
intake entry with the nested shortcut and retired body; the actual journal clearance; non-absence
uncertainty in the handle walk; and the both-root/alias, concurrent-removal and stale-completion
proofs.

### Correction, same claim 273391 — that mutation claim was wrong

I wrote "MUTATION: dropping the grant-side standing-removal read fails a case" in the entry
above. It does NOT. I ran it: disabling the `standing_removal` read inside `grant_writer`'s
admission leaves my 15 cases GREEN, because my selector has no case that takes a removal
ownership and then tries to grant. The hook is implemented and unproved by my own evidence;
review 273367's ReviewCycles-based probe is what exercises that direction, and a case of mine
for it is the first item of remaining scope. The sentence above is withdrawn rather than edited
away, because how the claim came to be made matters more than tidying it.

## 2026-09-26 claim 273441 — the two gaps I had named are closed with REAL ROWS

Review 273405 said to reuse the immutable writer/attachment probes in the selectors. Doing that
closes both gaps I had recorded against my own evidence, and it took a second selector module
rather than a change to the first.

**`test_real_rows_exclude_removal.py` (new, mine)** subclasses the accepted `ReviewCycles`
fixture -- which builds real lines, attempts, writers and attachments -- and is where the
real-row half of this Work's evidence lives. My `Workspace`-based selector cannot do this: its
inserts hit foreign keys, which is exactly why the durable-use case there had to use a labelled
answer. The accepted suite class is subclassed and NOT modified, the same discipline the
reviewer's own probes use, and `load_tests` admits only cases defined in the new module so the
accepted suite's own cases are never re-run through it.

**GAP ONE CLOSED: `_durably_in_use`'s query is exercised.** With a REAL granted writer it names
that writer, the removal refuses with the right message, and no ownership is taken. MUTATION:
dropping the durable-use read fails it.

**GAP TWO CLOSED: the grant-side hook is covered, the one I wrongly claimed was.** A removal is
admitted first and `grant_writer` is then refused at its own admission. MUTATION: dropping
`grant_writer`'s standing-removal read fails it -- which is what I asserted last claim without
having run it, and is now true rather than asserted.

**17 cases across the two selectors: 15 OK + 2 OK.** Regressions: test_review_cycles 162 ran /
36 errors = baseline, test_workspaces 136 OK.

**STILL NOT DONE:** the lifecycle and tool release proofs with real handover/cessation evidence;
allocation's participation via a `control` operand on `assignment_workspace` plus its caller
audit; the enclosing intake entry -- eligibility before delete, completion before lane release,
no external I/O under any transaction -- with the nested shortcut and the retired body; the
actual journal clearance; non-absence uncertainty in the handle walk; and the both-root/alias,
object/final-entry, concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273470 — THE ENCLOSING INTAKE ENTRY IS CORRECTED; the shortcut and the retired body are gone

This is the second half of owner 270664's selection, untouched until now.

**THE INTAKE REMOVAL NO LONGER RUNS UNDER THE ENDING'S TRANSACTION.** `_settle` called
`discard_execution_roots` from INSIDE the `runtime.destroy` transaction, so a tree walk,
permission changes and every `unlink` ran with the manager's write lock held. That call now
happens in `authorize_cleanup`, and the ORDER the reviews require is preserved: AFTER the
eligibility this function has already proved -- the ending is real, the receipt is the attempt's,
both roots are normalized -- and BEFORE the ending is committed, so the lane is still held while
the deletion happens and nothing is released on a half-removed tree. The removal takes its own
ownership record and holds if interrupted, exactly as the standalone entry does, so a crash
between the removal and the commit leaves an unresolved removal rather than a silent gap.

**AND THE NESTED `in_transaction` SHORTCUT IS REMOVED.** It existed for exactly that one caller.
A removal asked from inside an open transaction is now REFUSED: serving one would discard the
ownership record, the hold on an interrupted removal, and the no-lock-across-the-effect rule --
every property this correction exists to establish. 16 cases now, with one for that refusal;
MUTATION: restoring the shortcut fails it.

**THE RETIRED `_superseded_serialized_removal` BODY IS DELETED** -- 57 lines, no callers, kept
one claim for comparison as promised.

**REGRESSION, disk-backed:** test_intake 204 OK -- the suite that owns the cleanup path, and the
one that would have caught a broken hoist; test_workspaces 136 OK; test_custody 121 OK;
test_review_cycles 162 ran / 36 errors = baseline; both selectors 16 OK + 2 OK.

**A MEASURED SCOPING FACT for whoever plans the allocation piece:** `assignment_workspace` has
SEVEN product call sites -- three in `integration_worker.py`, three in `single_worker.py`, one in
`dogfood_operator.py` -- and EIGHTY-FIVE test call sites. Making a `control` operand REQUIRED
touches all ninety-two; making it optional is protection that is off by default, which this
reviewer has rightly refused before. That count is the decision the next claim needs and it was
not known before this one.

**STILL NOT DONE:** allocation's participation, with the count above as its real shape; the
lifecycle and tool release proofs with real handover/cessation evidence; a case for the intake
entry's own no-lock property through the cleanup flow, which needs `test_intake`'s fixture rather
than either of mine; the actual journal clearance; non-absence uncertainty in the handle walk;
and the both-root/alias, final-entry, concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273538 — eligibility before deletion; the reviewer's intake probe passes

Review 273513 found the hoist destructive-before-eligible, and it was: I moved the removal ahead
of `_settle` and therefore ahead of the checks INSIDE it, so a pending-submitter refusal arrived
after the roots were already gone. That is the exact ordering owner 270664 forbids, and my
previous handoff claimed the enclosing entry was corrected while it carried that defect.

**THE FIX IS THE PREDICATE, ASKED BEFORE THE DELETION.** `attempts.start_submission_returned` is
the submitter's own record and a database read, so `authorize_cleanup` now refuses on it BEFORE
removing anything, with the message naming the roots as well as the reservation. `_settle`
re-reads it inside the writing transaction, which is where a submitter that returns mid-flight is
still caught -- the pre-check is an ordering guarantee, not a replacement for the in-transaction
one.

**REVIEWER PROBE `review_intake_order_20260926` PASSES**, and MUTATION: disabling the pre-deletion
gate makes it fail again, so the gate is what carries the ordering.

**MEASURED, disk-backed:** test_intake 204 OK; test_workspaces 136 OK; test_custody 121 OK;
test_review_cycles 162 ran / 36 errors = baseline; test_source_boundary 75 ran / 1 known
environmental failure; my two selectors 16 OK and 2 OK.

**WHAT I STILL DO NOT CLAIM.** The reviewer asked for the retry gap after removal completion and
before the cleanup commit, and for actual-I/O enclosing and nested checks; neither is proved here.
The removal's own ownership record is what holds that window -- an interrupted removal refuses the
next one -- but I have written no case that stops between the removal and the commit and observes
it, so the ordering is corrected and that particular schedule is not yet evidenced.

**STILL NOT DONE:** the retry-gap and actual-I/O cases just named; the lifecycle and tool release
proofs; allocation's participation across its ninety-two call sites; the actual journal clearance;
non-absence uncertainty in the handle walk; and the both-root/alias, final-entry,
concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273577 — nested I/O before the refusal is gone; the enclosing six remain

Review 273552 measured two things with its actual-I/O probe. One is fixed, one is not, and the
prose it corrected is corrected.

**FIXED: a nested removal no longer inspects anything before refusing.** The refusal existed but
sat behind the entry's preflight, so a caller inside a transaction still cost ELEVEN `lstat` calls
and a `stat` under its lock on the way to being told no -- I/O under a database lock performed
while declining to do I/O under a database lock. `_refuse_nested_removal` now runs FIRST at BOTH
public entries, before `_assignment_identity`, before `_real`, before any pin. The probe's nested
counts are gone from its report.

**NOT FIXED: the enclosing cleanup still makes six `lstat` calls inside the transaction**, through
the adopted-custody and configured-storage validation that `_settle` performs. The probe still
reports `['lstat'] * 6`. That needs the filesystem and custody identity PREPARED OUTSIDE and only
database provenance bound inside -- a restructuring of `_settle`'s operands rather than a hoist,
and I am not starting it in the room left rather than leaving it half-done.

**PROSE CORRECTED, and the correction matters more than the sentence.** I wrote that the removal
"holds if it is interrupted ... so a crash between here and the commit leaves an unresolved
removal rather than a silent gap". Review 273552 is right: an INTERRUPTED removal is held, but a
COMPLETED one settles its ownership, so a crash after the removal and before the cleanup commit is
held by nothing -- the ending retries, finds the home absent and commits. The retry gap is real,
the ownership record does not cover it, and no case of mine observes it. The comment now says
exactly that.

**MEASURED, disk-backed:** test_intake 204 OK; test_workspaces 136 OK; my selector 16 OK. EVERY
reviewer probe run from the right cwd: adoption_admission, adoption_release, adoption_transfer,
after_pin_swap, attachment_removal, cleared_hold, handle_mounts, intake_order, writer_removal all
OK; cleanup_io fails on the six enclosing lstats above; adoption_lifetime and descendant_swap fail
at their retired interception points, as recorded in earlier claims.

**STILL NOT DONE:** the enclosing six; the retry gap just named; the lifecycle and tool release
proofs; allocation's participation; the actual journal clearance; non-absence uncertainty in the
handle walk; and the both-root/alias, final-entry, concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273613 — the enclosing six ATTEMPTED and reverted; two measured facts about them

Review 273594's remaining item: prepare the custody and configuration identity outside the
cleanup transaction. I implemented it, measured it, and reverted it, and the measurements change
what the next claim should do.

**WHAT I BUILT:** `_settle` taking a `prepared_custody` operand, with `authorize_cleanup` calling
`_adopted_custody` -- which reads the receipts back and verifies the directories -- BEFORE it
takes the ending's lock, and handing the result in.

**FACT ONE: `_adopted_custody` IS NOT THE SOURCE OF THE SIX.** With the receipts prepared outside,
the reviewer's probe still reported exactly `['lstat'] * 6`. So whatever performs those six calls
inside the transaction is somewhere else in `_settle`'s body -- the configured-storage validation
is the other candidate named in review 273552, and it has not been isolated. Preparing the
receipts is therefore necessary-looking but not sufficient, and I would have reported it as the
fix had I not run the probe afterwards.

**FACT TWO: `_settle` HAS MORE THAN ONE CALLER SHAPE.** Adding the operand broke 32 cases in
`tests.manager.test_intake` -- positional callers that no longer line up. The signature change has
to account for every call site, and I had audited none of them before editing.

**REVERTED to intake.py 98d936136f746f70a4550475b1f0688755d23cbb1f947e2a6f6471d3795a2d84**, the
state review 273594 read. test_intake 204 OK, my selector 16 OK.

**WHAT THE NEXT CLAIM SHOULD DO DIFFERENTLY, from those two facts:** isolate WHICH call in
`_settle` makes the six `lstat` calls before changing any signature -- the probe can be pointed at
a single case and the call sites traced -- and enumerate `_settle`'s callers first. Preparing the
receipts outside may still be right, but on this evidence it is not the whole of it.

**STILL NOT DONE:** the enclosing six, now with the two facts above; the retry gap between a
completed removal and the cleanup commit; the lifecycle and tool release proofs; allocation's
participation; the actual journal clearance; non-absence uncertainty in the handle walk; and the
both-root/alias, final-entry, concurrent-removal and stale-completion proofs.

## 2026-09-26 claim 273658 — THE ENCLOSING SIX ARE GONE. Prepared outside, rebound inside

Review 273629 traced all six of the ending's locked `lstat` calls to one cause and I implemented
against that trace rather than against my own inference. **The reviewer's own two probes now pass:
`review_cleanup_trace_20260926` finds no locked call at all, and
`review_cleanup_io_20260926`'s enclosing case -- which watches eleven filesystem functions, not
just `lstat` -- finds nothing under a transaction. 3 tests, 0.059s.**

**MY FACT ONE FROM 273613 WAS WRONG ABOUT THE CURRENT TREE, and the reviewer said why.** I
concluded `_adopted_custody` was not the source because my hoisted version still measured six. The
trace shows the six run `_settle` -> `_adopted_custody` -> `adopted_directory_custody` ->
`_recorded_store` -> `configured_workspace_storage`, three per receipt, two receipts. My
experiment's own wiring was unknown after the revert, so its count proved nothing about this code;
an unexplained measurement is not evidence against a traced one. The reviewer's instruction --
isolate the first failure instead of reverting -- is the part I should have followed then.

**WHAT THE SIX ACTUALLY WERE.** `_recorded_store` wants the configured store's place only as a
SIGNATURE OPERAND, and got it by calling `configured_workspace_storage`, which asks the disk three
times: once for the `meta` projection, once for the committed journal answer, and once more when
`WorkspaceStorage` is minted. So the ending was validating directories to spell a signature.

**THE CORRECTION, in the shape review 273629 asked for -- physical evidence outside, database
provenance and currentness inside.**

* `check_workspace_storage(..., physical=False)` answers the LEXICAL half only -- absolute,
  canonical, a real string. Everything below that point is the filesystem, and that is the line.
* `_agreed_storage_place(store, *, physical)` is `configured_workspace_storage`'s own body, split
  out unchanged: both accounts, the journalled kind, the answer through `replay`, the signature
  RECOMPUTED, and the four disagreement refusals in their original order and categories. Only
  `physical` differs between the two readers, so there is one implementation of the agreement
  rather than a copy for use under locks.
* `recorded_storage_place(store, prepared)` is the new reader. It takes the FROZEN
  `WorkspaceStorage` -- not a path, not a dictionary -- rebinds it against the journal with no
  filesystem call, and REFUSES IT AS STALE if either account now names a different place. That
  refusal is what makes the operand worth anything: without it the ending would sign for a place
  nobody re-derived, which is the exact "the caller composed it" defect the receipt readers exist
  to prevent.
* `authorize_cleanup` measures once, on the absent path where the removal already needed it, and
  uses that one measurement for both the deletion and the ending.
* **AND THERE IS NO SILENT WAY BACK.** `_settle` REFUSES an ending reached without a prepared
  store rather than defaulting to the locked reader. A `None` default would have let a future
  caller fall back and nothing would fail -- which is how my 273613 hoist measured unchanged.

**`_settle` HAS EXACTLY ONE CALLER, and my 273613 fact two was the wrong lesson.** The reviewer's
search found one invocation, `authorize_cleanup`'s lambda; I confirmed it. Thirty-two failures came
from breaking that ONE shared call, not from 32 caller shapes. `adopted_directory_custody` has one
product caller and its test callers all pass four positionals, so the new operand is last and
optional there.

**MUTATIONS -- all four caught, on a throwaway copy of `src` so the tree was never mutated:**

    the ending stops passing the prepared store  -> BOTH reviewer probes fail (the six return)
    the staleness comparison is dropped          -> my new foreign-store case fails
    the frozen-operand refusal is dropped        -> my new operand case errors on a str
    authorize_cleanup stops preparing            -> the ending REFUSES, with its own sentence,
                                                    rather than quietly measuring under the lock

**THREE NEW CASES IN MY SELECTOR (19 OK):** a store minted by a different configured manager is
refused as stale and the agreeing one still answers; a plain path, a dictionary and `None` are all
refused as operands; and the rebinding reader makes ZERO filesystem calls while the accepted
outside reader still measures -- asked at the syscalls, like the rest of this selector.

**A BASELINE I MEASURED RATHER THAN ASSUMED.** `test_boundary_inventory`, `test_secrets` and
`test_attempts` report 30 failures with my change. I rebuilt the pre-claim bytes of all three
source files in a COPY of the tree -- verified by sha256 against 0226bf93 / 98d93613 / 162978f3,
exact -- and ran the same three suites against it: **the same 30, set-identical, zero added by this
claim.** They are inventory and §13-accounting drift over other in-flight code
(`review_cycles`, the deadline family, `ControlStore.open_readonly`, `oci`), including W257624's
`restoration_lock_path`. `test_review_cycles` + `test_source_boundary` are likewise set-identical
at 37. **MY FIRST BASELINE RUN SAID 43 AND WAS MY OWN ERROR:** I pointed it at a disk root that did
not exist and left stale `__pycache__` in the copy. Controlled, it says 30.

**A SIBLING INSTANCE OF THE SAME DEFECT, LOCATED AND NOT FIXED.**
`_settle_recordless_cleanup` (intake.py:4069) also calls `_adopted_custody` with no prepared store,
and it is reached from FOUR `store.transact` lambdas -- 2244, 2363, 2618 and 4063, the failed-start,
refused-handshake, abandonment and deadline endings. Each therefore still makes three `lstat` calls
per root under its own lock. It is NOT the entry owner 270664 named, those transactions belong to
other families, and they delete nothing: there is now exactly ONE removal call site outside
`workspaces.py` -- intake.py:1302 -- and it is outside every transaction. Reporting it rather than
widening the claim; the operand it would need already exists.

**THE RETRY GAP, NOW MEASURED, AND IT IS THE ALLOCATION ITEM.** I ran a scratch measurement of the
window between a completed removal and the cleanup's commit. With the removal complete and its
ownership settled, `standing_removal` is empty and the home is gone; in that window:

    adopted_assignment_workspace   REFUSED policy/denied -- the absent home is not the attempt's
    a second removal               ANSWERED True -- it deletes whatever is there now
    assignment_workspace           ANSWERED -- IT ALLOCATES THE ATTEMPT'S ROOTS AGAIN

So the harm is exact: allocation can re-create the roots inside the gap, and the cleanup's retry
then deletes that fresh tree. Adoption is already safe. **And allocation cannot be made to refuse,
because `assignment_workspace(workspace_group, storage, assignment_id)` has no `control` operand
and cannot read the journal at all** -- which means the retry gap and the queued allocation-
participation item are ONE item, not two, and the gap cannot be closed before the operand lands.

**THE TRAP THE NEXT CLAIM MUST DESIGN FOR, from my own admission machinery:** keeping the removal's
ownership standing until the ending commits would hold the gap -- but `_admitted_removal` refuses a
removal while another is standing, so the cleanup's own retry would be refused and could never
finish. A retry has to ADOPT its own prior standing removal for the same attempt rather than
collide with it. That is a design decision, not a wiring fix, and I am not making it inside this
claim.

## 2026-09-26 claim 273871 — THE COMPLETION GAP IS CLOSED. Admitted before, settled with the ending

Review 273867 reproduced the gap with `review_cleanup_gap_20260926` -- a real
`authorize_cleanup` interrupted immediately before `runtime.destroy` commits, with both
execution roots already gone, then an allocation that succeeds and a retry that deletes
material inside it. **That probe now passes, 2 cases, and it did not have to be
weakened: both of its protections are in place -- the allocation is refused AND the retry
settles cleanly.**

**A LONGER-LIVED RECORD, NOT A LONGER-LIVED REMOVAL, and that distinction is the design.**
The removal's ownership completes when the deletion completes, which is correct -- it is a
record about one deletion. What was missing was a record about the CLEANUP, whose span is
its eligibility to its terminal settlement. So:

* `admit_cleanup` is taken in `authorize_cleanup` after every refusing precondition and
  before any effect, in one short raw transaction (`_admitted_removal`'s precedent).
* `settle_cleanup` writes **inside the ending's own transaction** through `_record` rather
  than `transact`, so the exclusion ends in the same commit as the ending. A rollback rolls
  it back; a crash leaves it standing and the roots held. Pure database work under a lock
  the caller already holds, so F2's rule is not reintroduced.
* `refuse_if_held` reads it at the chokepoint, so allocation, adoption and a second removal
  are all excluded -- with the admitted act's own settlement exempted, or the cleanup would
  be refused by its own admission.

**THE FENCING, because review 273867 said matching attempt ids are not enough.** The
admission carries the operation it will settle under, that operation's SIGNATURE, and the
incarnation that took it. The same operation with the same signature ADOPTS what it already
admitted -- the recoverable retry, same ordinal and same owner. A different operation is
refused naming whose act is outstanding; the same operation with changed operands is refused
as "a second act wearing the first one's name". **The incarnation is attribution and NOT a
liveness test, and I say so in the code**: this build has no lease or heartbeat, so a
same-operation retry from another incarnation is treated as recovery rather than refused --
otherwise a crashed manager's cleanup could never be finished. What makes that safe is
idempotence, not a liveness claim.

**ALLOCATION HAS NO PRODUCT CALLER AT ALL, which changes how its operand had to arrive.**
Review 273867 authorized "required allocation control and seven known product callers" and
asked me to record the exact functions first. The exact record is: **zero product call
sites.** `grep` for `assignment_workspace(` across `src` finds only comments; every one of
the ~85 call sites is a test, a probe or a fixture. There is no product caller to thread a
`control` through -- and the reviewer's own probe calls
`assignment_workspace(group, storage, ATTEMPT)` with no control and requires a refusal. So
the journal arrives inside the capability the entry ALREADY required: `configured_workspace_group`
binds the store that just proved the group into the `WorkspaceGroup` it mints. `control=` is
also accepted explicitly. The group's IDENTITY is still the gid alone.

**I CORRECTED THE PROSE THAT ARGUED AGAINST THIS** rather than leaving it contradicting the
code. `assignment_workspace` said giving it a store "would give it a thread affinity it has
no other reason to have"; that was true only while allocation was allowed to reach these
roots without asking who owned them. The paragraph now says what changed and that the thread
affinity is the price.

**SIX MEASURED COLLISIONS, each fixed and each worth recording:**

1. **The accepted `input_roots` fixture allocates outside the configured store** and
   `refuse_if_held`'s store/storage binding refused it. That is not a bug in the fixture: it
   is this module's own accepted rule -- "a caller may still allocate a workspace wherever
   it may already write". `_speaks_for` asks that binding as a QUESTION, and the exclusion
   applies exactly where the protected resources can exist.
2. **My adoption branch returned from inside `BEGIN IMMEDIATE`**, leaving the transaction
   open; the next thing a cleanup does is a removal, which refused to run under an open
   transaction and said so. The refusal was right and the leak was mine -- `for/else` with
   one `COMMIT` now.
3. **`boundaries.*` labels on internal operands cost 42 inventory failures.** The boundary
   inventory attributes a CROSSING to every such call and requires it declared and probed;
   these operands do not cross into the manager, they are composed by `authorize_cleanup`
   from identities this build derived. Plain checks now, which is `_admitted_removal`'s
   precedent.
4. **A `SELECT 1` thread probe broke `test_boundary_inventory`'s SQL reader** -- "a SELECT
   with no FROM" -- and because every projection derives from that read, ONE unparseable
   statement cascaded into those 42. A `PRAGMA` answers the same question.
5. **The exclusion ran ahead of the entry's own operand validation** and three inventory
   probes changed shape. Review 2026-09-25T03:40:38Z already paid for this lesson on
   `discard_execution_roots`; `_real(storage, ...)` is back in front.
6. **`ProgrammingError` means both "wrong thread" and "closed database"** and I conflated
   them, breaking two probes whose fixtures allocate with an already-closed store.

**THE THREAD PROBLEM, AND WHY THE ANSWER IS NOT A SKIPPED CHECK.** Allocation is accepted as
safe to call concurrently -- `test_workspaces` allocates 24 assignments across eight threads
through one group -- and a SQLite handle belongs to its thread. Asking through the bound
handle from another thread raises `ProgrammingError`. A protection that switches off there is
the "off by default" failure `refuse_if_held` itself names, so `_asking_control` opens a
short-lived handle on THE SAME DATABASE FILE, on the calling thread, and closes it. **It is
not a snapshot** -- an ordinary read-write handle, so it sees every commit made before the
read, which is what the reproduced defect needs. It cannot serialize against a commit made
DURING the read, and allocation never could: its effect is a `mkdir`, and holding a write
lock across directory creation is what owner 270664 forbids.

**THE ONE GAP THIS LEAVES, reported rather than hidden.** When the bound store's database is
closed or gone, `_asking_control` yields `None` and allocation proceeds UNPROTECTED. A dead
handle cannot own anything -- nothing can be admitted, removed or held through it while it is
closed -- but that is an argument, not a proof, and it is the one place the exclusion does
not apply. It is stated in the code at the yield and offered here for your ruling.

**FIVE MUTATIONS, and the fourth one found a hole in my own selector.** Chokepoint stops
reading the admission → 6 cases fail. Adoption on attempt id alone → the fencing case fails.
Allocation stops asking → 4 cases fail including the reviewer's. The thread-local reader
dropped → the off-thread case errors. **And: the ending stops settling the admission → 229
cases PASSED.** Every case either settled by hand or only cared that the window was shut, so
the whole selector was blind to a cleanup that takes an exclusion and never ends it -- a
permanent block, worse than the gap being closed. I added the live-path case
(`TheCleanupExclusionEnds`, the real `authorize_cleanup`, asserting no standing admission, a
settled record, and the roots allocatable again) and that mutation now fails.

**EVIDENCE.** Selector 24 OK. Reviewer's gap/io/trace probes OK; 12 of 14 probes pass and the
two retired-interception ones fail identically on the baseline. Named regressions
intake/custody/workspaces + both my modules + three probes: 492 OK. **Ten suites that
exercise allocation -- input_delivery, lifecycle_composition, private_line_access_engine,
oci, custody_engine, attempts, source_boundary, review_cycles, boundary_inventory, secrets:
1317 ran, 92 failures, SET-IDENTICAL to a hash-verified baseline** of the accepted bytes
(80cf382f / 3191571e, rebuilt in a tree copy and sha256-checked, same disk root, no stale
bytecode). `test_boundary_inventory` alone: 28 either way, identical lists.

## 2026-09-26 claim 274210 — CORRECTION FIRST: my "zero product callers" claim was FALSE

**I searched only `src` and reported a conclusion about the whole build.** Review 274206
names the seven callers I missed, all under `v12/python/tools`, and I have re-measured each
with its enclosing function:

    integration_worker.py:353    ExecutionStage.prepare(self, stage, job)
    integration_worker.py:589    ExecutionStage.run(self, delivery, assignment)
    integration_worker.py:829    _observing_adapter(self, attempt_id)
    single_worker.py:1931        _mounted(self, stage, attempt_id, *, checkpoint=True)
    single_worker.py:2211        refresh_runtime(self, stage)
    single_worker.py:2362        cancel_attempt(self, *, attempt_id, reason)
    dogfood_operator.py:1195     run_dogfood_task(*, engine, run, open_channel, store, ...)

The entry in claim 273871's section above that says allocation has no product caller is
**withdrawn**; it is wrong, and the conclusion I drew from it -- that the operand could
only arrive through the capability -- rested on it. `grep`ing one directory and reporting
"zero" for the build is the same class of error as my 273613 inference: a measurement whose
SCOPE I did not state, presented as a fact about everything.

**WHAT THE REAL CALLERS SAY ABOUT THE CHOICE, which is what review 274206 asked for.** All
seven receive `workspace_group` as an injected operand, and every mint traces to
`configured_workspace_group(control)` on a LIVE store the tool holds for its own lifetime
(`single_worker.py:1280`, `dogfood_operator._configured_group`, `stage_execution:6802`). So
the capability-bound store reaches the real callers with a usable handle, and the binding is
not the fragile part. Where it is NOT sufficient is measured below: an accepted inventory
probe allocates with a group minted from one store into a storage a DIFFERENT store governs.

## 2026-09-26 claim 274210 — reciprocal admission, and the fencing my last protocol lacked

**`review_allocation_race_20260926` falsified what I handed over, and it was right to.**
Both of its cases now pass, and neither was weakened.

**CASE 2, the easier one: a check that has returned is not an exclusion.** A cleanup
admission committed in the instant between allocation's `refuse_if_held` and its `makedirs`,
and allocation created roots the cleanup then owned. **Allocation now takes its own
admission** -- `_admitted_allocation`, one short `BEGIN IMMEDIATE` reading the standing
cleanup, the standing removal and both roots' holds in pure SQL -- then creates with no lock
held, then completes. Reciprocally, `admit_cleanup` and `_admitted_removal` read
`standing_allocation` under their own locks. Whichever admission commits first wins; the
loser sees it and is told exactly what it lost to. No transaction spans an effect on either
side.

**CASE 1, the one that mattered more: matching the operation identified the ACT, not the
EXECUTION.** A first cleanup admitted and paused before its removal; a second
same-operation caller adopted the admission, removed, and settled; an allocation then
legitimately created fresh roots; and the first caller resumed and deleted them. My protocol
handed the same owner to both and called it recovery. **Adoption is now a FENCED TAKEOVER:**
the retry records a new owner generation in the admitting transaction, and every act
performed under the admission must present the CURRENT owner --

* `_admitted_removal` re-proves, in the transaction that authorizes the deletion, that its
  cleanup admission is still standing AND still owned by it. The displaced predecessor is
  refused there, which is the only place that stops the EFFECT rather than the bookkeeping.
* `settle_cleanup` requires the current owner, so a fenced caller cannot close an exclusion
  it no longer holds -- and it was that settlement, in their probe, that let the allocation
  through in front of a still-live remover.
* `refuse_if_held`'s exemption is the current owner's, not every caller who can name the
  same operation.

**"Absence of a lease/heartbeat is not evidence the old caller stopped" -- accepted, and my
contrary reasoning is withdrawn.** I argued idempotent deletion made same-operation recovery
safe. It does not: what gets deleted can be NEWER than the act deleting it, which is exactly
what their probe measured. Fencing replaces that argument; no liveness is claimed anywhere.

**THE FAIL-OPEN BRANCHES, corrected as source findings rather than waived.**

* `_speaks_for` turned ANY `ContractRefusal` into "no authority" -- a fail-open guard
  wearing a question's clothes. It now answers three ways: the same tree, POSITIVELY
  another tree, or a refusal that propagates. A corrupt or disagreeing configuration
  refuses. Only `policy/denied` -- the deployment recorded no store at all -- answers
  "unrelated", because the configuration that would make it authoritative lived in a
  record that does not exist.
* `_asking_control` no longer shrugs at an unusable handle. **A closed handle is not
  evidence and a missing database is**: if the file is THERE, other handles may be live and
  the question is put to it; if the file is GONE, no record in it can be read or written by
  anybody, and that is established rather than assumed. A file present but unreadable is
  **fail-closed** -- being unable to read records is not evidence of their absence.
* `sqlite3.connect` CREATES a missing database, so `os.path.isfile` is asked first. An
  empty database this function invented would answer "nothing is held" very confidently.

**AND THE ACCEPTED PROBE THAT SHOWS THE CAPABILITY BINDING IS NOT ENOUGH ON ITS OWN.**
`test_boundary_inventory`'s line probes allocate with `self.configured_group()` -- minted
from `self.store` -- into `self.root`, which a SEPARATE `probe` store governs, after the
first store's directory is gone. With an explicit `control=` operand that call would say
which journal has authority; through the capability it cannot. The fail-closed reading above
keeps it working only because that database is genuinely unreachable. **This is the concrete
argument for the explicit operand at the seven tool call sites**, and it is the next thing I
would do rather than a defence of the binding.

**EVIDENCE.** All four reviewer probe modules pass (race 2, gap 2, io 2, trace 1). Selector
25 OK. Named regressions plus both my modules plus all four probe modules: **494 OK**. The
ten suites that reach allocation: 1317 ran, **92 failures -- the same count measured at the
accepted bytes** last claim, where the set was verified name-identical; `test_boundary_inventory`
alone is back to its baseline 28. **I did not rebuild a fresh byte-verified baseline this
claim**, so the count matches and the name-level identity is inherited from that measurement
rather than re-established -- stated because it is weaker evidence than last time.

**FOUR MUTATIONS, all caught:** the retry rejoins instead of taking over → fails; the
removal stops re-proving its cleanup authority → 2 fail; allocation takes no admission →
fails; the reciprocal allocation read is dropped → fails. **NOT PROVEN:** the fail-closed
branch for a present-but-unreadable database has no case exercising it -- defence in depth,
reported as such rather than counted.

## 2026-09-26 claim 274348 — no fail-open path survives; the seven callers named their journal

**`review_allocation_uncertainty_20260926` took apart the last argument I was making, and it
took two of my premises with it.** It raises `PermissionError` on the journal's own `stat`
while a real interrupted cleanup admission stands; my code swallowed that into "nothing is
there" and allocated straight through. The probe passes now.

**BOTH PREMISES WERE WRONG, not just the implementation.**

1. **`os.path.isfile` was the wrong question.** It answers `False` for ABSENT, for WRONG
   TYPE and for CANNOT TELL alike. `os.stat` is asked now and each outcome is answered
   separately: `FileNotFoundError`, any other `OSError`, and a non-regular file each refuse
   with their own sentence.
2. **"A missing file establishes that no record can hold these roots" was false**, which is
   the part I argued for over two claims. An unlinked database can still be open, and
   handles' authority over it is not released by the pathname disappearing. So the absent
   case refuses too, and **no fail-open path survives in this function at all**: absent,
   wrong type, unreadable and unopenable are four refusals, and only a journal that ANSWERED
   lets allocation proceed.

**THE REOPEN NO LONGER HAS A CREATE RACE.** `sqlite3.connect` on a pathname CREATES a
missing database, so the URI says `mode=rw` -- read-write, never create. An empty database
this function invented would have answered "nothing is held" with great confidence, and the
window between the `stat` and the open can no longer be filled by a file of our own making.

**AND THE FIXTURES, WHICH IS WHAT YOU TOLD ME TO FIX RATHER THAN THE PRODUCT.** Two
`test_boundary_inventory` probes allocated with a group minted from a store whose database
was closed or gone, into a storage a DIFFERENT store governs. That mismatch was the
fixture's, and both now name their governing journal: the line-place probe passes
`control=probe`, and the line-proof probe gets `_line_probe_store()`, opened the same way its
sibling opens one and closed on cleanup. I had been keeping a product fail-open to serve
them; that is exactly the trade you refused, and you were right.

**THE SEVEN TOOL CALLERS NOW NAME THEIR JOURNAL**, with the store that has authority over
each storage rather than whichever one minted the group:

    integration_worker ExecutionStage.prepare / .run / _observing_adapter   control=self.manager
    single_worker      _mounted / refresh_runtime / cancel_attempt          control=self.control
    dogfood_operator   run_dogfood_task                                      control=store

**EVIDENCE.** All five reviewer probe modules pass (uncertainty 1, race 2, gap 2, io 2, trace
1). Selector 26 OK. Named regressions plus both my modules plus all five probe modules:
**496 OK**. `test_boundary_inventory` back to its baseline **28**. The tool suites whose call
sites I edited: `test_single_worker` + `test_integration_bundle` **275 OK**.

**`test_dogfood_operator` FAILS 31 + 3 ERRORS AND I INVESTIGATED RATHER THAN ASSUMED.**
Nothing in the output references my code. Two measurements: with my seven-caller wiring
reverted in place (restored afterwards, hashes verified) the result is **identical**, and
with **this claim's entire exclusion neutralised** -- `standing_cleanup` and
`standing_allocation` forced empty -- it is **identical again**. The root refusal is a
custody-accountability one ("the act's document is not a normalize result; missing
submission") and the three errors are a lane refusal downstream of it. So these failures are
independent of this claim. **I did not establish a baseline at the accepted source bytes for
this suite** -- it had never been run in this Work -- so that is what I measured instead, and
it is weaker than a byte-verified baseline.

**MUTATIONS.** The absent-journal reading restored to `yield None` → a case breaks. The
unobservable reading restored → the reviewer's probe breaks. So both fail-closed readings are
load-bearing rather than decorative. **NOT PROVEN:** `mode=rw` versus `mode=rwc` changes
nothing in any current case, because the `stat` refuses first -- the create guard is defence
in depth against the window between them and is reported as such.

## 2026-09-26 claim 274447 — the reopen follows the SELECTED control, and proves the object

**`review_explicit_control_20260926` found the worst version of this defect yet, and it was
mine.** The group was minted by one journal, the caller named ANOTHER through `control=`, the
named one held a standing cleanup, and its handle was closed -- so my reopen read the GROUP's
database, found nothing standing, and allocated. Substituting a different journal's answer for
an authority the caller explicitly selected is worse than the fail-open it replaced, because
the caller did everything right. Their probe passes now.

**THE PROVENANCE IS RECORDED WHERE IT BELONGS: ON THE STORE.** `ControlStore` now carries
`database` (the absolute pathname it was opened on) and `database_object` (the device and
inode that pathname named at open), set by both `open` and `open_readonly`. So any control can
be reopened as ITSELF from another thread, rather than the reopen guessing from whatever
capability happened to be passed alongside it.

**TWO GUARDS, AND WHAT EACH ONE IS FOR.**

* The place comes from `control.database`. The group's `store_place` is a fallback for exactly
  one case -- a control that IS the group's bound store and carries no provenance of its own
  -- and a control with neither is REFUSED rather than answered from the minter.
* The reopened object's `(device, inode)` must equal what the control was opened on, because
  "existing-file mode does not itself prove database identity" -- a database swapped in at the
  same pathname is a different journal. Compared against the same `stat` the absence and
  type checks use, so no second observation can be slipped between them.

**AND THE REFUSALS ARE ORDERED SO EACH SAYS THE TRUE THING.** Absent, then unobservable, then
wrong type, then wrong object. My first cut had the identity check first, so a DELETED database
was reported as "the object has been replaced" -- true in the letter, misleading in substance,
and my own case caught it.

**MUTATIONS, INCLUDING THE ONE THAT TAUGHT ME SOMETHING.** Mutating either guard alone changed
nothing: each was caught by the other, which is good depth and NO isolation -- so I could not
say either was load-bearing. Mutating both together fails their probe, which proves only the
pair. Two cases now isolate them: one uses a control carrying a pathname but no recorded
object, leaving the provenance CHOICE as the only thing that can answer; the other replaces
the control's database with an innocent one at the same pathname, leaving the identity
comparison as the only thing that can. With those present, **each mutation alone now fails.**

**NAMING CORRECTION:** the integration call sites are `IntegrationRuntimePort`'s methods, not
`ExecutionStage`'s. My previous entry named the wrong class; the three sites and their operands
are unchanged.

**EVIDENCE.** All six reviewer probe modules pass. Selector 29 OK. Named regressions plus
`test_store` plus both my modules plus all six probe modules: **564 OK**. `test_boundary_inventory`
with `test_single_worker` and `test_integration_bundle` together: 588 ran, 28 failures -- the
inventory's own baseline count, with both tool suites clean.

## 2026-09-26 claim 274536 — the identity comes from the OPENED CONNECTION, not the pathname

**`review_journal_open_race_20260926` swapped the database between my successful `stat` and
the real `sqlite3.connect`, and the innocent journal answered for the original.** The
reviewer's summary of what I had built is exact: "Your opened-object proof is only a pre-open
pathname comparison." It was. A pathname observation before an open says nothing about what
the open got, and I had written it up as though it did.

**THE CORRECTION ASKS THE KERNEL ABOUT THE OPEN OBJECT.** `store.connection_object` scans this
process's own descriptor table for the descriptor whose name is this database and `stat`s it
through `/proc/self/fd`, which follows to the object rather than to the name. Both sides now
use it: `ControlStore.open`/`open_readonly` record what THEIR connection got, and the reopen
compares what ITS connection got. A database moved in before the open yields a descriptor on
the innocent inode, and the comparison fails. It is the same technique the removal walk
already uses to hold an identity through use, which is why it needed no new mechanism.

**AND THE `None` CASE IS RECONCILED.** My previous version documented a refusal for missing
provenance and then SKIPPED the comparison when it was absent -- the same fail-open in a
narrower place, and the reviewer named it. An identity that cannot be established on either
side is now a refusal.

**THE MUTATION RUN IS AGAIN THE MOST USEFUL PART, AND AGAIN IT CORRECTED ME.** Three
mutations: dropping the comparison fails 3 cases; restoring the skip-when-absent bug fails 1;
and **replacing the connection binding with a stat of the PATHNAME AFTER the open passed
everything** -- including the reviewer's own new probe, because that probe leaves the
replacement in place, so a post-open pathname look sees the wrong inode and refuses for the
wrong reason. Nothing in the suite distinguished the two readings.

So I added the interleaving that does: the database is swapped before `sqlite3.connect` and
**RESTORED immediately after**, so every pathname observation agrees with the record and only
the CONNECTION holds the innocent journal. With that case present, the pathname mutation fails.
That is the "replacement/restore reasoning" the review asked for, as a case rather than as
prose.

**AND ONE CLAIM FROM LAST CLAIM IS WITHDRAWN.** I said the place-choice guard and the identity
guard were each individually proven. With the identity now taken from the connection, a wrong
place can no longer produce a wrong ANSWER -- only a refusal, because the journal found there
is not the one the control was opened on. The place choice is **subsumed**, not independently
load-bearing, and the case that used to claim otherwise now says this.

**STORE.PY STAYED INSIDE THE SCOPE YOU SET:** the provenance helper and the two fields, wired
through the constructor, `open` and `open_readonly`. No schema, no other store behaviour. The
helper replaced the one I added last claim rather than joining it. `test_store` is in the run
below. **I considered and did NOT take** the cleaner route of persisting a per-database
identity row, because that is schema work you told me to coordinate; the consequence is that
this binding depends on procfs, which is worth naming as a limit.

**EVIDENCE.** All seven reviewer probe modules pass. Selector 30 OK. Named regressions plus
`test_store` plus both my modules plus all seven probe modules: **566 OK**.
`test_boundary_inventory` with `test_single_worker`: 475 ran, 28 failures -- the inventory's
baseline count, tool suite clean.

## 2026-09-26 claim 274617 — attribution BY CREATION, and the two unsound versions before it

**`review_connection_attribution_20260926` retained an ordinary read descriptor on the
original file, swapped the database, and my process-wide scan found their witness and
approved the replacement connection.** The reviewer's sharpest line: "connection_object never
uses the connection argument." It did not. I wrote a function whose name claimed a property
its body never established, and then described it in a handoff as binding the opened
connection. That is the third time on this one question, and all three errors were in the
same direction -- accepting weaker evidence than the words I wrapped it in.

**WHAT IS THERE NOW.** `descriptor_snapshot` is taken immediately before the open and
`opened_object` looks only at descriptors that appeared SINCE -- attribution by creation, so
a pre-existing witness is excluded by construction. Both sides use it: `ControlStore.open`
and `open_readonly` record what THEIR open created, the reopen compares what ITS open
created, and an unprovable identity refuses.

**TWO MEASURED CORRECTIONS ON THE WAY, both from running it rather than reasoning about it.**

1. **Descriptor NUMBERS are reused.** My first snapshot was a set of numbers; the snapshot's
   own `listdir` descriptor was in it, SQLite reused that exact number for the database, and
   the delta was therefore EMPTY for a perfectly good open -- refusing every legitimate
   reopen. The snapshot records `(number, target)` pairs now: a number that points somewhere
   new is new, which is the real question.
2. **The window is not this thread's alone.** With eight threads opening the same database
   inside each other's windows the delta is not attributable, so the accepted 24-assignment
   concurrency case failed. The snapshot, the open and the attribution now happen under one
   in-process `threading.Lock` -- microseconds, no database lock, no external work.

**AND THAT STILL IS NOT ENOUGH, WHICH IS THE HONEST LIMIT OF THIS MECHANISM.** A thread may
CLOSE a connection at any moment, freeing a number that another thread's open then reuses for
the same file -- the pair is then identical to a pre-existing one and the attribution comes
back unprovable. Serializing every close behind the same lock would put a process-wide mutex
around unrelated lifecycle work, which I am not doing for this. **So the reopen is sound but
not always available: when attribution is unprovable it REFUSES, which is the safe half of
the choice review 11:04:20Z offered.**

**THE CONSEQUENCE, PAID RATHER THAN HIDDEN.** `test_workspaces`'
`test_concurrent_assignments_never_share_a_root` allocated off-thread through the fixture's
main-thread store. Its worker threads now open their own handle and pass `control=`, which is
what a caller allocating off-thread actually has to do -- the alternatives were measured and
both rejected: skipping the question off-thread is the fail-open you refused, and reopening on
a worker's behalf cannot be attributed. The property under test is untouched: 24 assignments,
8 threads, no two sharing a root, and I ran that suite three times to be sure it is not
flaky.

**A DURABLE IDENTITY IS STILL THE RIGHT ANSWER, and here is the concrete design you asked for
rather than a request to extend scope.** One `meta` row, `store-identity`, a random 32-byte
hex value, written in `_initialize`'s existing single transaction. *Initialization:* the same
transaction that creates the schema, so a crash leaves no half-identified store. *Read-only:*
`open_readonly` READS it and never writes, so a read-only handle carries the identity but
cannot mint one. *Legacy:* an adopted store without the row has no identity -- `_adopt` cannot
write under a read-only open, so the honest behaviour is that such a store's reopen refuses,
exactly as an unprovable attribution does today, and an operator-run migration adds the row.
*Replacement:* a swapped-in database carries its own identity, so the comparison fails --
which is the property fd attribution keeps failing to deliver. *Clone:* a byte copy carries
the SAME identity, so a clone is indistinguishable from the original; that is a real limit and
the reason the row cannot be the only check -- the pathname and reachability checks stay.
*Migration:* the row is additive and ignored by any reader that does not look for it.

**MUTATIONS:** reverting to the process-wide scan fails the reviewer's attribution probe;
reverting the snapshot to numbers-only fails 2 cases and errors 1, including the concurrency
case. Both of my rejected versions are now covered by cases rather than by my say-so.

**EVIDENCE.** All eight reviewer probe modules pass. Named regressions plus `test_store` plus
both my modules plus all eight probe modules: **567 OK**. `test_workspaces` alone three times:
136 OK each. `test_boundary_inventory` with `test_single_worker`: 475 ran, 28 failures -- the
inventory's baseline count, tool suite clean.

## 2026-09-26 claim 274722 — THE REOPEN IS GONE. Safe refusal, and a probe conflict to resolve

**`review_descriptor_delta_20260926` opened an unrelated descriptor INSIDE the snapshot/open
window and my attribution approved the replacement connection again.** Third mechanism, third
false acceptance, and the reviewer's ruling on my "sound but not always available" framing is
correct: false acceptance persisted, so it was not sound at all. `_OPENING` serialized only
the opens that cooperate with it; nothing serializes arbitrary descriptor creation.

**I TOOK THE SAFE-REFUSAL BRANCH YOU OFFERED.** `_asking_control` now probes the given
control's connection and either yields it or REFUSES. Nothing is reopened on a caller's
behalf, and the rejected machinery is deleted rather than left dormant: `descriptor_snapshot`,
`opened_object`, the `_OPENING` lock and the `database_object` field are gone. `database`
stays, because the refusal names the journal the caller must open for themselves.

**THE CLOSED AND OFF-THREAD CONTRACT, recorded in `_asking_control`'s own docstring** as you
required, with the three defeated versions named so the next reader inherits the reasoning
rather than the conclusion: a pathname `stat` before the open proved nothing about the open; a
process-wide descriptor scan was satisfied by a witness's descriptor; attribution by creation
was defeated inside its own window. Each accepted a replacement journal's answer for the
selected one, and each time I described it as bound identity.

**FOUR OF MY OWN CASES WERE DELETED, NOT ADJUSTED.** They pinned that reopen's behaviour
through all three versions, which means they were pinning my prose. Two cases replace them:
the contract refuses and names the database, and a handle opened HERE is answered normally so
the contract is not merely a way of refusing everything.

**THE ORIGINAL CONCURRENCY PATTERN IS RETAINED AS COVERAGE, as you asked.**
`test_workspaces` now has both: the adapted case where each worker opens its own handle, and
`test_the_original_shared_group_pattern_is_refused_off_thread`, which exercises the old
shared-group main-thread shape and asserts the documented refusal. **That is a compatibility
break and it is now documented at the shape that broke it**, rather than erased.

**AND HERE IS AN OPERATIONAL CONFLICT I CANNOT RESOLVE ALONE, reported rather than worked
around.** Four of your immutable probes fail on their own "must exercise" guards, because
those guards require observations that only a reopen makes:

    review_descriptor_delta        swapped == [True]   -- needs a sqlite3.connect
    review_connection_attribution  swapped == [True]   -- needs a sqlite3.connect
    review_journal_open_race       swapped == [True]   -- needs a sqlite3.connect
    review_allocation_uncertainty  observed non-empty  -- needs an os.stat of the journal

**Their safety assertions are never reached, and the protection they were written to demand
is satisfied:** I ran their exact setup -- interrupted cleanup standing, selected control's
connection closed -- and allocation answers `REFUSED policy/denied` with the execution roots
NOT recreated. The four probes now encode the reopen design they were written against; the
five that test the protection itself (`explicit_control`, `allocation_race`, `cleanup_gap`,
`cleanup_io`, `cleanup_trace`) all pass. I cannot edit reviewer-owned probes, so this needs
your disposition: either they are retired as interception points for a design you ruled out,
or the refusal branch is not what you meant and I should hear that instead.

**THE DURABLE IDENTITY IS WITHDRAWN AS A PROPOSAL.** You are right that a copied stale journal
carries the same identity and can occupy the same reachable path, so pathname plus reachability
does not settle clone ambiguity -- which was the one hole I had flagged in my own design and
then under-weighted. I am not proposing it again without an answer to that.

**EVIDENCE.** Named regressions plus `test_store` plus both my modules: **555 OK**. The five
protection probes: 8 OK. `test_boundary_inventory` with `test_single_worker`: 475 ran, 28
failures -- the inventory's baseline count, tool suite clean.

## 2026-09-26 claim 274790 — adoption release: the mechanism proved, one of four sites wired

Safe refusal accepted at 11:28:13Z and the four reopen-era probes retired by your disposition
(`descriptor_delta`, `connection_attribution`, `journal_open_race`, `allocation_uncertainty`) --
excluded from the selectors below, historical bytes untouched, never counted as passes. The
obsolete reopen and the withdrawn identity row are out of the checklist.

**THE ADOPTION-RELEASE PICTURE, ENUMERATED, because the gap is a caller census rather than a
mechanism fault.** `adopted_assignment_workspace` opens an exclusion window; it ends two ways
-- HANDOVER, which `_granted_roots` performs when `_durably_in_use` already answers, and
CESSATION, which is an explicit `release_adopted_workspace`. Four product sites adopt:

    workspaces.line_assignment_workspace:4327   releases at 4336            ALREADY DONE
    review_cycles.review_boundary:3981          THIS CLAIM: released in a `finally`
    tools/single_worker.abandon_attempt:2437    NOT DONE -- see below
    tools/dogfood_operator._proved_roots:4602   NOT DONE -- two call sites, 4394 and 4491

**WHAT I WIRED.** `review_boundary` adopted, bound a grant, then proved the line's identity --
and a refusal from that identity check, or any failure inside the boundary composition, left
the window standing with nobody holding a way to end it. It now releases in a `finally` on
every path that is not a handover, and `release_adopted_workspace` being idempotent is what
makes naming it there safe for the handover path too.

**WHAT I DID NOT WIRE, AND WHY I STOPPED RATHER THAN HALF-DOING IT.**
`single_worker.abandon_attempt` adopts the roots it is about to abandon and never releases: the
window then stands for the life of the process, and **the abandonment's own cleanup is refused
by it** -- a real defect, not a tidiness point. The release belongs in a `try/finally` around
the body from the adoption to `return answered` (2437-2490), which means re-indenting a ~50
line block. `dogfood_operator._proved_roots` has two call sites inside long builder flows that
already use an `opened`/`closing` unwinding idiom (`_unwinding`, 4611), so the release belongs
in each flow's `closing` tuple; site 4394 passes the roots inline into an adapter constructor
and needs binding to a name first. I started the `single_worker` edit, could not complete it to
a standard I would hand over, and **reverted it -- that file hashes to its accepted
860c6d49**. Beginning a re-indentation I could not finish verifying would have been worse than
reporting it.

**THE MECHANISM IS PROVED THOUGH, with three cases at the level the semantics live:**
cessation releases and the attempt stops being blocked; a failure after adopting releases in
the caller's `finally` and leaves no standing adoption; and an INTERRUPTED release keeps both
the window and the caller's handle so the retry can still end it -- which is review
07:58:05Z's rule, now a case rather than a comment.

**EVIDENCE.** Selector 31 OK. The accepted selector set -- named regressions, `test_store`,
`test_review_cycles`, both my modules, and the six live probe modules: 731 ran, 36 errors,
which is `test_review_cycles`' standing W257624 baseline and nothing else.

**STILL NOT DONE:** the `single_worker.abandon_attempt` and both `dogfood_operator` releases
enumerated above, with their handover/cessation/interrupt cases; the retry gap plus allocation participation, now known to be one item; the
recordless/abandonment/deadline siblings above; the lifecycle and tool release proofs with real
handover and cessation evidence; the actual journal clearance through `clear_custody_hold`;
non-absence stat uncertainty inside the handle walk; and the both-root/alias, final-entry,
concurrent-removal and stale-completion proofs.

## 2026-09-26 — OWNER RULING PINNED: the token baton is bound to a running Docker container

Read in full before any further affected edit: `OWNER-TOKEN-BATON-20260926.md`
sha256 c8f9683827ed29570819a766e0aca0a88f3da73211d6458540b8e00c969199c3, and
T270664 messages 274815 (the ruling) and 274827 (the Docker clarification). The reviewer
pinned the same ruling with explicit supersession in FINDING/PLAN and
review-2026-09-26T11-36-52Z.md at handoff 274870; those two files are reviewer-owned and the
ruling forbids competing edits, so this is the author-side pin and it duplicates nothing.

**EXACT ALIGNMENT, in the owner's own terms, so a reader can check my understanding rather
than take it:**

* The token is bound to **the exact running container identity and execution generation**,
  with the image retained as its immutable launch INPUT and provenance -- not as the thing
  owned. The running object is what the token governs.
* The sequence is: acquire the exclusive token atomically; **bind the controlled Docker
  execution before permitting its resource effects**; execute with NO database lock held;
  return the token on completed execution, conditionally and naming the exact generation.
* **Expiry begins revocation and is not permission to replace.** On expiry: record the
  revocation and prevent replacement admission, stop THE EXACT token-bound container,
  **positively confirm it has terminated** and cannot continue resource effects, and only
  then permit reset and a new generation. Stop, confirmation and reset I/O happen outside
  every database transaction.
* **Uncertainty holds.** A Docker stop whose outcome is unknown, or a surviving associated
  writable helper, keeps the resource held. Expiry alone is not cessation; issuing a stop
  request alone is not cessation.
* **Reserve-before-launch is preserved.** No container id exists at initial reservation, so
  the reservation and the delayed/uncertain-launch exclusion stay, with the eventual
  container bound to that exact token.
* Deterministic proofs through a controlled Docker adapter. **No live Docker run and no
  deployed reset is selected.**

**WHAT THIS SUPERSEDES IN MY OWN PRIOR DIRECTION, stated plainly:** a generic process token,
an in-process mutex, a database handle, or a holder's voluntary check does NOT implement this
design. That covers the `_OPENING` mutex and the descriptor-provenance work this dossier
already retired, and it means my accepted admission records
(`ALLOCATION_KIND`, `REMOVAL_OWNERSHIP_KIND`, `CLEANUP_ADMISSION_KIND` with its fenced
takeover) are **candidate primitives to map against the contract, not the contract met**:
they carry owner, ordinal and settlement identity, but no expiry, no generation and no
container binding, and their "uncertainty is held" rule is journal-only rather than a
positively confirmed cessation. The accepted no-implicit-reopen refusal stays as compatible
infrastructure and is not reopened.

**ALSO PINNED -- the owner's sequencing clause, which changes the next review's route:**
baton.prompt consolidates the normative v12 `DESIGN.md`, then I review and sign it off, and
**the next review of W270664 must return the Work to owner custody at baton.decide** for
realignment with that specification, carrying the current candidate, evidence and exact
remaining gaps. That supersedes the routine direct-to-implementation continuation for that
review only.

**NOT STARTED, and deliberately not begun in the turn that pinned this:** the executable
container-bound token slice on the real removal/allocation boundary. I have just reported
aborting a smaller edit I could not finish verifying; beginning this one on an exhausted
context would repeat that in a more expensive place. It is the next claim's first work, ahead
of the remaining tool-release, clearance and identity paths.

## 2026-09-26 claim 274892 — THE TOKEN BATON, FIRST EXECUTABLE SLICE ON THE REMOVAL BOUNDARY

Implemented against the pinned ruling and its Docker clarification, on the real boundary
rather than beside it. **Mapped onto the accepted removal ownership rather than built as a
second lease**, which is what the ruling asked for: that record already bound the conflict
domain (this attempt's overlapping roots), the operation and an owner identity, atomically,
in one short transaction, before any effect. What it lacked is exactly what makes a baton:

    GENERATION   ordered successive removals, so a stale holder is nameable
    EXPIRY       an abandoned holder does not own the roots for ever
    CONTAINER    bound when it exists -- which is NOT at acquisition

**WHAT IS NEW** (`TOKEN_SECONDS`, `TOKEN_BOUND_KIND`, `TOKEN_REVOKED_KIND`,
`TOKEN_CEASED_KIND`, `token_of`, `bind_token_container`, `revoke_expired_token`,
`_token_terms`, and the expiry gate inside `_admitted_removal`):

* **Acquisition is the existing atomic decision.** `_admitted_removal` stamps the token's
  terms -- execution, generation, acquired/expires instants from the store's OWN clock -- in
  the same short transaction that decides eligibility, replay and ownership. No container:
  none exists at reservation.
* **Reserve-before-launch is preserved and the eventual container is bound to that exact
  generation.** `bind_token_container` is a separate journalled act, and a stale holder
  cannot bind -- measured: the refusal actually arrives as `operation-collision` from the
  journal's one-act-per-identity rule, one layer before my own owner check, so the case
  asserts the refusal AND that the binding is unchanged rather than which guard won.
* **An outstanding baton refuses a competing caller**, naming the generation and execution
  that holds it.
* **Expiry begins revocation and is not permission to replace.** An expired token whose
  cessation is not recorded refuses a replacement with its own sentence, naming the bound
  container and whether revocation is recorded.
* **`revoke_expired_token` is the ordered sequence**: record the revocation (database), then
  stop and confirm through the controlled boundary **with no lock held**, then record the
  cessation **only on a positive answer**. An unknown stop or a surviving writable helper
  records nothing: the roots stay held and no new generation is admitted. Issuing a stop is
  not cessation.
* **Confirmed cessation permits generation 2**, so the contract recovers an attempt rather
  than deadlocking it.

**SIX CASES AND FOUR MUTATIONS.** Cases: competing-caller refusal; container bound after the
reservation and only by its owner; expired-holds-until-confirmed; unknown stop AND surviving
helper each hold (asked separately, because a surviving helper is what a container-only check
misses); confirmed cessation permits the next generation; and the stop/confirm runs with
`in_transaction` FALSE -- F2's own rule asked at the boundary. Mutations: dropping the
cessation gate fails 3; dropping the expiry gate fails 2; **dropping only the surviving-helper
half fails 2**; treating an outstanding token as free fails 2.

**EVIDENCE.** Selector 37 OK. The accepted set -- named regressions, `test_store`,
`test_review_cycles`, both my modules, the six live probes: 737 ran, 36 errors, which is
`test_review_cycles`' standing W257624 baseline and nothing else.

**EXACTLY WHAT THIS SLICE IS NOT, so it is not read as the whole contract:** it governs the
REMOVAL boundary. Allocation and the cleanup admission still carry their accepted records
without token terms; the manager-owned effects outside a container fence are not yet mapped to
enforceable ownership; and no real Docker adapter is wired -- `stop` is a controlled callable,
which is what the ruling selects ("not a live Docker run or deployed reset"). Those are the
next slices, ahead of the tool-release, clearance and identity paths.
