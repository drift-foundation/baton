# Verification selectors — W270664

## The bounded command this Work will use

No selector has been RUN for this Work yet; this claim changed no code. The command below is
the one the correction will be verified with, recorded now so the next claim starts from a
named boundary rather than inventing one. The test module does not exist yet.

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w270664 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-workspace-removal-outside-locks \
    timeout --signal=TERM --kill-after=5s 300s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_removal_outside_the_lock

A SEPARATE DISK ROOT from W257624's (`/var/tmp/baton-w270664`, not `-w257624`), so the two
corrections' fixtures cannot share residue.

## Existing coverage that must keep passing

These are the accepted suites that reach the F2 region and are the regression boundary for
any change to it. Their CURRENT state must be measured before the first edit, so that a
pre-existing failure is never reported as a regression and a regression is never excused as
pre-existing:

    tests.manager.test_workspaces
    tests.manager.test_custody
    tests.manager.test_intake

Not yet measured under this Work. Measuring them is the first act of the next claim.

## Evidence obligations

PLAN.md carries the nine cases owner 270664 requires. None is written.

## Selector and baseline as measured — claim 272559

    test_removal_outside_the_lock      (mine, 8 cases, 0.047s, three consecutive runs)

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/tmp/baton-w270664-claude PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-workspace-removal-outside-locks \
    timeout --signal=TERM --kill-after=5s 300s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_removal_outside_the_lock

THE DISK ROOT IS /tmp/baton-w270664-claude, recorded per review 272555: /var/tmp/baton-w270664
is not writable in the reviewer's environment. It is not W257624's root.

CASES: no filesystem call of a removal inside a transaction (observed at the syscalls);
unrelated database progress committing while the deletion is paused; a hold recorded before
admission refusing with the accepted typed refusal; a hold arriving in the interval between
the outer check and the admission, refused by the admission's own re-read; a custody claim
refused while a removal ownership stands; an interrupted removal held rather than repeated;
exact per-call answers with no replay across two acts; an absent home still answering False.

BASELINE AND REGRESSION, same command family, PYTHONPATH src:. :
tests.manager.test_workspaces 136 OK, tests.manager.test_custody 121 OK,
tests.manager.test_intake 204 OK -- measured BEFORE the first edit and again after.

MUTATIONS, three, all three load-bearing: reciprocal custody hook removed; standing-removal
hold removed; admission's hold re-read removed (load-bearing only after the interval case was
added -- the outer check had been covering it).

NOT COVERED, because not implemented: the intake cleanup entry, which still removes under its
own transaction through the unchanged nested branch.

## Claim 272653 — cleared-history correction

    test_removal_outside_the_lock      (mine, 9 cases, 0.054s, three consecutive runs)
    review_cleared_hold_20260926       (reviewer's, 1 case, OK)

Same command and same disk root /tmp/baton-w270664-claude. NEW CASE: cleared history is not a
hold -- no history, cleared-only and MIXED histories through one predicate, with the live
episode of the mixed one refusing via the outer check's accepted policy/denied refusal.
MUTATION: restoring the every-recorded-episode reader fails it. Regressions unchanged at
136 / 121 / 204 OK.

## Claim 272688 — labelling corrections

Same selector, same disk root. 9 cases OK, 0.053s, three runs; reviewer cleared probe OK;
regressions 136 / 121 / 204 OK. No new case; two corrections to existing ones. One red run
while my first attribution fix demanded a `root` field that the `_record_hold` episode does
not carry -- recorded because the fix, not the original defect, caused it.

## Claim 272727 — absent-but-unresolved

Same selector and disk root. 10 cases OK, 0.058s, three runs; reviewer cleared probe OK;
regressions 136 / 121 / 204 OK. NEW CASE: an absent home with an unresolved removal refuses
rather than answering False, with the ordinary absent-home answer preserved beside it.
MUTATION: letting the absence shortcut answer regardless of an unresolved removal fails it.
One red run while the home was only partly removed and the admission's refusal answered first.

## Claim 272758 — object pinning across the admission

Same selector and disk root. 11 cases OK, 0.062s, three runs; reviewer cleared probe OK;
regressions 136 / 121 / 204 OK. NEW CASE: a home replaced between admission and effect is
refused as identity-mismatch and the substitute survives, staged by swapping the directory
from inside the admission. MUTATION: dropping the pinned-object comparison fails it.

## Claim 272806 — withdrawal, no behaviour change

Same selector and disk root: 11 cases OK, 0.065s. Prose only. The reviewer's
review_after_pin_swap_20260926.py still FAILS and should, until the deletion is bound to a
directory descriptor rather than compared by stat.

## Claim 272826 — descriptor binding attempted, measured, reverted

The attempt ran 11 cases in 10.055s with 6 ERRORS, all one cause: `_remove`'s root `os.lstat`
of a `/proc/self/fd/N` magic symlink answers procfs, so its own cross-device mount refusal
rejects every real child. Reverted; selector back to 11 OK 0.063s twice and regressions
136 / 121 / 204 OK on the unchanged bytes ec97b942.

## Claim 272864 — descriptor-bound destruction

Same selector and disk root: 11 cases OK, 0.063s, three runs. REVIEWER PROBES:
review_after_pin_swap_20260926 now OK (it failed on the previous bytes);
review_cleared_hold_20260926 OK. Regressions 136 / 121 / 204 OK.
MUTATION: dropping the opened-versus-admitted object comparison makes the after-pin-swap probe
fail again -- that comparison, not the parent-entry one, is what carries the property.

## Claim 272924 — descendant re-proof attempted and reverted

The attempt failed with 6 errors in the selector and 2 in tests.manager.test_workspaces, cause
not isolated; reverted to 53e5a03b. Verified after the revert: 11 cases OK 0.064s,
after_pin_swap OK, cleared_hold OK, 136 / 121 / 204 OK. review_descendant_swap_20260926 FAILS
and is the open defect.

## Claim 272962 — the handle-retaining walk

Same selector and disk root: 12 cases OK, 0.068s. NEW CASE: a descendant replaced by a symlink
at the first thaw of the removal pass cannot reach outside material -- the reviewer's schedule
adapted to the interception point the handle walk actually uses, because their `_thaw(path)`
probe no longer triggers and a non-triggered probe is not proof. MUTATION: restoring the
path-based `_remove` fails it. Regressions 136 / 121 / 204 OK. review_after_pin_swap OK.
review_descendant_swap_20260926 now fails at its own first assertion (its swap never fires),
which is recorded rather than read as a pass.

## Claim 273016 — reciprocal exclusion at the chokepoint

Same selector and disk root: 13 cases OK, 0.072s twice. NEW CASE: an unresolved removal refuses
adoption and a custody claim. One existing assertion follows the message to the chokepoint's
broader sentence. MUTATION: removing the chokepoint reading fails the new case. Regressions
136 / 121 / 204 OK; after_pin_swap and cleared_hold OK.

## Claim 273092 — symmetric admission

Same selector and disk root: 14 cases OK, 0.086s. NEW CASE: removal and adoption exclude each
other in BOTH orders -- an admitted adoption refuses the removal and leaves the roots untouched,
and an interrupted removal refuses adoption at its own admission; plus a successful adoption
settles its own window and the removal afterwards succeeds. REVIEWER PROBES: adoption_admission
now OK (failed on the previous bytes), after_pin_swap OK, cleared_hold OK. Regressions
136 / 121 / 204 OK.

MUTATIONS, three: removal ignoring a standing adoption fails MY case; adoption not admitted at
all fails the REVIEWER's probe and NOT mine (my case admits the window directly to stage the
reverse order); never settling the window fails my case only after the successful-adoption
assertion was added.

## Claim 273158 — REGRESSION BOUNDARY CORRECTED

THE NAMED BOUNDARY WAS TOO NARROW AND IT COST A REGRESSION. Add permanently:

    tests.manager.test_source_boundary
    tests.manager.test_review_cycles

AND THEY REQUIRE A DISK-BACKED ROOT. Both refuse a tmpfs BATON_V12_DISK_ROOT outright ("W71917
refuses a workspace on memory"), so on /tmp they report 62 and 162 meaningless failures. Use
/var/tmp/baton-w270664-claude for these two; /tmp/baton-w270664-claude remains fine for the
focused selector and for workspaces/custody/intake.

BASELINE ON CURRENT BYTES, disk-backed: test_source_boundary 75 ran / 2 failures --
test_a_foreign_mount_under_a_root_refuses_before_anything_is_removed, which is MY regression
introduced at 53e5a03b, plus an environmental scratch-mount list difference; test_review_cycles
162 ran / 36 errors, W257624's known intake.py setUp condition.

BISECTION OF THE REGRESSION: ec97b942 OK, 53e5a03b FAILED, ce7d5c59 FAILED.

## Claim 273206 — the mount case adapted; boundary measured disk-backed

    test_removal_outside_the_lock      14 OK
    tests.manager.test_workspaces      136 OK
    tests.manager.test_custody         121 OK
    tests.manager.test_intake          204 OK
    tests.manager.test_source_boundary 75 ran / 1 failure (was 2)
    tests.manager.test_review_cycles   162 ran / 36 errors (W257624's intake.py setUp)

ALL of these on BATON_V12_DISK_ROOT=/var/tmp/baton-w270664-claude, which is disk-backed; the last
two refuse a tmpfs root outright.

THE MOUNT CASE IS ADAPTED, not weakened: the foreign-device simulation is applied at both
observations -- os.lstat by pathname and os.fstat by (device, inode) -- and the case asserts its
injection FIRED before asserting the refusal. The remaining source_boundary failure
(test_the_runtime_gets_exactly_the_declared_bounded_scratch) fails identically on ec97b942, so it
predates this Work.

## Claim 273250 — actual-use lifetime

    test_removal_outside_the_lock       14 OK        (disk-backed root)
    tests.manager.test_workspaces       136 OK
    tests.manager.test_custody          121 OK
    tests.manager.test_intake           204 OK
    tests.manager.test_source_boundary  75 ran / 1 known environmental failure
    tests.manager.test_review_cycles    162 ran / 36 errors = W257624 baseline (was 39 while
                                        line_assignment_workspace leaked a window)

REVIEWER PROBES: adoption_admission OK, after_pin_swap OK, cleared_hold OK.
review_adoption_lifetime_20260926 now FAILS AT ITS OWN INJECTION (0 != 1): it hooks
_settled_adoption expecting a call DURING adoption, which was the defect and no longer happens.
Recorded as a retired interception point, not as a pass; my both-orders case carries the property.

## Claim 273441 — a second selector for real rows

    test_removal_outside_the_lock       15 OK   (Workspace fixture; disk-backed root)
    test_real_rows_exclude_removal        2 OK   (NEW, mine; subclasses the accepted ReviewCycles
                                                 fixture for real lines/attempts/writers)

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w270664-claude PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=src:.:/home/sl/src/baton/work/records/2026/09/finding-v12-workspace-removal-outside-locks \
    timeout --signal=TERM --kill-after=5s 300s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_removal_outside_the_lock test_real_rows_exclude_removal

WHY TWO MODULES: the Workspace fixture cannot insert writer or attachment rows -- foreign keys --
so the durable-use query and the grant-side exclusion could only be proved on the accepted
ReviewCycles fixture. Both mutations now fail: dropping the durable-use read, and dropping
grant_writer's standing-removal read.

## Claim 273658 — the enclosing entry, and a hash-verified baseline

    test_removal_outside_the_lock        19 OK  (16 + 3 for the prepared-store rebinding)
    test_real_rows_exclude_removal        2 OK
    review_cleanup_trace_20260926   }
    review_cleanup_io_20260926      }     3 OK  0.059s -- BOTH REVIEWER PROBES, now green
    tests.manager.test_intake }
    tests.manager.test_custody }        461 OK  8.049s
    tests.manager.test_workspaces }

THE THREE INVENTORY SUITES ARE NOT A PASS AND ARE NOT MINE TO FIX:

    test_boundary_inventory + test_secrets + test_attempts   834 ran / 30 failures

and the baseline that makes that number mean something -- the pre-claim bytes of workspaces.py,
intake.py and custody.py rebuilt in a COPY of the tree, sha256-verified as
0226bf93 / 98d93613 / 162978f3, same disk root, no stale __pycache__:

    same three suites on the baseline                        834 ran / THE SAME 30

set-identical, so this claim adds none of them. Same method for
test_review_cycles + test_source_boundary: 37 either way, identical lists.

RUN IT THE SAME WAY EVERY TIME OR THE BASELINE LIES. My first attempt reported 43 because the
disk root did not exist and the copy carried compiled bytecode from the unreverted source.

MUTATIONS (applied to a copy of src, never to the tree):

    _recorded_store(store) instead of (store, prepared_store)  -> both reviewer probes fail
    the staleness comparison dropped                           -> selector fails
    the frozen-operand refusal dropped                         -> selector errors
    authorize_cleanup stops preparing                          -> the ending refuses loudly

THE TWO REVIEWER PROBES AT RETIRED INTERCEPTION POINTS still fail identically on the baseline --
review_adoption_lifetime (0 != 1) and review_descendant_swap ([] != [True]). Measured both ways;
neither is counted as a pass and neither is caused by this claim. The other nine pass.

RUN THE PROBES FROM /home/sl/src/baton/v12/python, never from this dossier. Eleven identical
import errors this claim, from a `cd` into the dossier directory. It is the same mistake as before.

## Claim 273871 — the completion gap, and the ten suites that touch allocation

    test_removal_outside_the_lock        24 OK  (20 + 4 for the cleanup exclusion, one of
                                                 them on the REAL authorize_cleanup path)
    test_real_rows_exclude_removal        2 OK
    review_cleanup_gap_20260926           2 OK  <- the reviewer's reproduction, unweakened
    review_cleanup_io / _trace            3 OK
    tests.manager.test_intake }
    tests.manager.test_custody }        492 OK  8.589s  (with both my modules and 3 probes)
    tests.manager.test_workspaces }

THE TEN SUITES THAT REACH ALLOCATION, measured against the accepted bytes rather than
asserted: input_delivery, lifecycle_composition, private_line_access_engine, oci,
custody_engine, attempts, source_boundary, review_cycles, boundary_inventory, secrets.

    with this claim      1317 ran / 92 failures
    accepted baseline    1317 ran / 92 failures   <- SET-IDENTICAL, zero added

The baseline is workspaces.py rebuilt to 80cf382f... and intake.py to 3191571e... in a COPY
of the tree, both sha256-verified, same disk root, no stale __pycache__.
test_boundary_inventory alone: 28 failures either way, identical lists.

MUTATIONS (all on a copy of src; the tree is never mutated):

    chokepoint stops reading the cleanup admission  -> 6 selector cases fail
    adoption on matching attempt id alone           -> the fencing case fails
    allocation stops asking the journal             -> 4 cases fail, incl. the reviewer's
    the thread-local reader is dropped              -> the off-thread case errors
    the ending stops settling the admission         -> PASSED 229 cases at first

THE LAST ONE IS THE POINT OF RUNNING THEM. Nothing in the selector could see a cleanup that
takes an exclusion and never ends it -- a PERMANENT block, worse than the gap being closed.
TheCleanupExclusionEnds now runs the real authorize_cleanup and asserts the admission is
settled and the roots are allocatable again; the mutation fails.

STILL RUN EVERYTHING FROM /home/sl/src/baton/v12/python. Cost me two wasted runs again.

## Claim 274210 — reciprocal admission and fenced takeover

    test_removal_outside_the_lock        25 OK  (+1 reciprocal allocation case; the retry
                                                case rewritten for the fenced protocol)
    review_allocation_race_20260926       2 OK  <- BOTH reviewer race cases, unweakened
    review_cleanup_gap / _io / _trace     5 OK
    named regressions + all of the above 494 OK  8.921s
    ten allocation-touching suites      1317 ran / 92 failures

92 IS THE COUNT MEASURED AT THE ACCEPTED BYTES LAST CLAIM, where the set was verified
name-identical. THIS claim did not rebuild a byte-verified baseline, so the name-level
identity is inherited rather than re-established -- weaker evidence, said plainly.
test_boundary_inventory alone is back to its baseline 28.

MUTATIONS (on a copy of src):

    the retry rejoins instead of taking over          -> fails
    removal stops re-proving its cleanup authority    -> 2 fail
    allocation takes no admission                     -> fails
    the reciprocal allocation read is dropped         -> fails

NOT PROVEN, reported rather than counted: the fail-closed branch for a database that is
present but unreadable has no case exercising it.

## Claim 274348 — no fail-open path, and the seven callers' journal

    test_removal_outside_the_lock        26 OK  (+1: an unaskable journal refuses)
    review_allocation_uncertainty         1 OK  <- the PermissionError-on-stat probe
    race / gap / io / trace               7 OK
    named regressions + all of the above 496 OK  8.945s
    tests.manager.test_boundary_inventory      28 = its baseline count, after both fixture
                                               authority mismatches were fixed
    tests.tools.test_single_worker }
    tests.tools.test_integration_bundle }     275 OK  19.836s

tests.tools.test_dogfood_operator: 359 ran / 31 failures + 3 errors, AND TWO CONTROLS --
identical with my seven-caller wiring reverted in place (restored, hashes verified), and
identical again with this claim's whole exclusion neutralised (standing_cleanup and
standing_allocation forced empty). No failure in that output references my code; the root
refusal is custody accountability. NOT a byte-verified baseline: this suite had never been
run in this Work, so these two controls are what stands in for one.

MUTATIONS:

    the absent journal read as an absent record (my old premise)  -> a case breaks
    the unobservable journal read as empty (isfile behaviour)     -> reviewer probe breaks

NOT PROVEN: mode=rw vs mode=rwc changes no current case, because the stat refuses first. The
create guard is defence in depth against the window between them and is reported, not counted.

## Claim 274447 — the reopen follows the selected control

    test_removal_outside_the_lock        29 OK  (+2: one isolating each provenance guard)
    review_explicit_control_20260926      1 OK  <- the two-real-stores substitution probe
    the other five probe modules          8 OK
    named regressions + test_store + all of the above   564 OK  9.361s
    test_boundary_inventory + test_single_worker + test_integration_bundle
                                        588 ran / 28 failures = the inventory's baseline
                                        count; both tool suites clean

MUTATIONS, AND WHY THE FIRST TWO RUNS PROVED LESS THAN THEY LOOKED LIKE:

    place from the group minter instead of the control   -> at first OK (!)
    the (device, inode) identity check dropped           -> at first OK (!)
    BOTH together                                       -> reviewer probe fails

Each guard was catching the other's mutation: real depth, no isolation, and no right to call
either load-bearing. Two cases now isolate them -- a control with a pathname but no recorded
object, and a database swapped in at the control's own pathname -- and with those present each
mutation alone fails:

    place from the group minter (isolated)   -> fails
    identity check dropped (isolated)        -> fails

## Claim 274536 — the opened connection, not the pathname

    test_removal_outside_the_lock        30 OK  (+1: swap before the open, restore after)
    review_journal_open_race_20260926     1 OK  <- the swap-between-stat-and-connect probe
    the other six probe modules           9 OK
    named regressions + test_store + all of the above   566 OK  9.444s
    test_boundary_inventory + test_single_worker   475 ran / 28 = the inventory's baseline

MUTATIONS, AND THE ONE THAT PASSED:

    the connection-identity comparison dropped        -> 3 cases fail
    the skip-when-provenance-absent bug restored      -> 1 case fails
    a stat of the PATHNAME AFTER the open instead     -> PASSED EVERYTHING, including the
                                                        reviewer's own new probe

The third is the important one. That probe leaves the replacement in place, so a post-open
pathname look also sees a wrong inode -- nothing in the suite distinguished "the name now" from
"the object this connection has". The new case swaps BEFORE the open and RESTORES after, so
every pathname observation agrees with the record; with it present:

    a stat of the PATHNAME AFTER the open (isolated)  -> fails

WITHDRAWN FROM THE PREVIOUS ENTRY: the place-choice guard is NOT independently load-bearing
any more. With the identity taken from the connection, a wrong place can only cause a refusal,
never a wrong answer.

## Claim 274617 — attribution by creation, and its stated limit

    test_removal_outside_the_lock        30 OK
    review_connection_attribution         1 OK  <- the retained-witness probe
    the other seven probe modules        10 OK
    named regressions + test_store + all of the above   567 OK  9.404s
    tests.manager.test_workspaces        136 OK, run THREE times (0.889/0.893/0.931s)
                                         because its concurrency case was adapted
    test_boundary_inventory + test_single_worker   475 ran / 28 = the inventory's baseline

MUTATIONS:

    back to the process-wide descriptor scan   -> the attribution probe fails
    snapshot by descriptor NUMBER only         -> 2 fail, 1 errors (incl. concurrency)

Both of the unsound versions I shipped earlier are now covered by cases rather than by my
say-so.

THE LIMIT, RECORDED WITH THE EVIDENCE: attribution by creation is unprovable when another
thread closes a connection inside the window (number reuse), and that case REFUSES. The
accepted concurrency case therefore allocates with a per-thread control now -- the sound way
for an off-thread caller -- rather than relying on a reopen that cannot be attributed.

## Claim 274722 — safe refusal, and four probes that can no longer observe their staging

    test_removal_outside_the_lock        26 OK  (4 reopen-era cases DELETED, 2 added)
    tests.manager.test_workspaces       137 OK  (the adapted concurrency case plus the
                                                retained original-pattern refusal case)
    named regressions + test_store + both my modules   555 OK  9.120s
    the five protection probes            8 OK  (explicit_control, allocation_race,
                                                cleanup_gap, cleanup_io, cleanup_trace)
    test_boundary_inventory + test_single_worker   475 ran / 28 = the inventory's baseline

FOUR REVIEWER PROBES FAIL ON THEIR "MUST EXERCISE" GUARDS, NOT ON THE PROTECTION:

    review_descriptor_delta        swapped == [True]   needs a sqlite3.connect
    review_connection_attribution  swapped == [True]   needs a sqlite3.connect
    review_journal_open_race       swapped == [True]   needs a sqlite3.connect
    review_allocation_uncertainty  observed non-empty  needs an os.stat of the journal

Nothing reopens the journal any more, so none of those observations happen and their `refused`
assertions are never reached. Their scenario was run directly to see what the product does:
interrupted cleanup standing, selected control's connection closed -> allocation answers
REFUSED policy/denied and the execution roots are NOT recreated. Reported to the reviewer for
disposition; reviewer-owned probes are not mine to change and a non-triggered probe is never
counted as a pass.

NO MUTATIONS THIS CLAIM. The mechanism they would have tested was deleted, and mutating a
refusal into an acceptance is what the four probes above would have caught if they could still
observe their own staging -- which is exactly the gap being reported rather than papered over.

## Claim 274790 — the current selector set, after the retirements

FOUR PROBES RETIRED by review 2026-09-26T11:28:13Z and EXCLUDED from this set:
review_descriptor_delta, review_connection_attribution, review_journal_open_race,
review_allocation_uncertainty (all _20260926.py). Their must-trigger hooks needed a reopen
that no longer exists. Historical bytes untouched; never counted as passes. The earlier
adoption_lifetime and descendant_swap retirements stand.

THE LIVE SET:

    test_removal_outside_the_lock        31 OK  (+3 adoption release/failure/retry cases)
    test_real_rows_exclude_removal        2 OK
    review_control_refusal_20260926            <- the new refusal evidence
    review_explicit_control / allocation_race / cleanup_gap / cleanup_io / cleanup_trace
    tests.manager.test_intake / test_custody / test_workspaces / test_store
    tests.manager.test_review_cycles

    all of the above together     731 ran / 36 errors
                                  = test_review_cycles' standing W257624 baseline, nothing else

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w270664-claude PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=src:.:/home/sl/src/baton/work/records/2026/09/finding-v12-workspace-removal-outside-locks \
    timeout --signal=TERM --kill-after=5s 600s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest <the modules above>

NO MUTATIONS THIS CLAIM. The three new cases cover a mechanism whose product wiring is one of
four sites done, so the mutation worth running is the missing wiring itself -- reported as
remaining scope rather than dressed up as coverage.

## Claim 274892 — the token baton slice

    test_removal_outside_the_lock        37 OK  (+6 token-contract cases)
    the accepted set together           737 ran / 36 errors = test_review_cycles' standing
                                        W257624 baseline, nothing else

MUTATIONS (on a copy of src):

    the cessation gate dropped                  -> 3 fail
    the expiry gate dropped                     -> 2 fail
    ONLY the surviving-helper half dropped      -> 2 fail
    an outstanding token treated as free        -> 1 fail, 1 errors

The third is deliberate: a container-only cessation check is exactly what the owner's ruling
warns against, so it is mutated separately from the stop check rather than together with it.
