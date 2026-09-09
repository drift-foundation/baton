# Progress

Implementation entries belong to the actual change author under a successful
Work claim. No implementation has been reported in this record yet.

## 2026-09-09 — baton.claude, claim 124838

**Claimed first**, at seq124838, before reading the dossier and before any
edit.

### Revalidation

The precondition is exactly as the FINDING states. `end_implementation` step
eight (`freeze_checkpoint`) revokes the writer and step nine
(`authorize_cleanup`) is the last act; the entry then asks `_own_writer` for a
writer "still holding the line", and `_destroyed` is the only other branch. So
one refused cleanup strands the ending, and the manager keeps the stage
`answering` and asks for the same `conclude` every tick — this is one refusal
away from every ordinary ending, not a rare interleaving.

### Delivered — the third re-entry, in the two owned paths

`_fence_settled` decides it. It asks through W124331's accepted
`writer_for_attempt`, so the binding `_own_writer` exists for is made **before**
any state selects a branch: a caller naming somebody else's writer selects
nothing here and meets that helper's own refusal, and an attempt with no writer
answers `False`.

`_cleaning_implementation` finishes it, in the order **prove, then finish**:
the fenced writer bound to this attempt and generation, the line's profile from
that writer rather than from the caller, the assignment this session acts for,
the committed frozen result with its worker-envelope correlation, the intake
receipt, the retention decisions, the immutable checkpoint replayed, the
committed publication read — and only then `authorize_cleanup`. Seven is last
because it is the irreversible one: a resume that destroyed the runtime first
and then found its publication missing would have answered a refusal having
already thrown away the container the evidence is about.

It grants no writer, publishes nothing, freezes no second checkpoint and
invents no active writer. `authorize_cleanup` owns the positive absence it
destroys on; this module neither observes nor asserts it. The answer is the
ordinary ending's member for member.

`_destroyed` is still asked first, so the accepted historical branch keeps
every attempt it had, and an active writer still takes the ordinary path.

### Verified

`tests/job_manager/test_review_driver.py` 159 OK — 101 methods at HEAD, and the
whole HEAD file is an exact **prefix** of the candidate, so the fourteen added
cases are additive and no existing assertion moved. The fixture is the real
one: real offer, claim, activation, runtime start, worker outputs, freeze,
intake, retention, Authority publication and checkpoint, with a single injected
cleanup refusal as the defect's own precondition, and the control store reopened
at the cut.

**Five failures in `tests/tools/test_stage_execution.py` are not this Work's,
and that is measured rather than assumed.** W124782 landed concurrently:
`intake.py` now compares the Authority's answered kind against `RUNTIME_ABSENT`
instead of `QUIESCENCE_GATE`, so the discharge receipt commits and the composed
ending settles on its first tick. Four W122060 cases reach their cut through a
fixture that depended on the ending *not* settling, and the fifth is the
defect-expecting regression for the very defect W124782 fixed. Re-running
exactly those five with `_fence_settled` patched to return `False` — which
removes this Work's whole branch — gives five failures either way;
`evidence/attribution-124838.py` retains the script. That file is W122060's
path, and the parent proposal already authorizes converting those tests once
their owning fixes are available, which is now.

Hashes, modes, every run and the attribution:
`evidence/provider-124838.json`.

**Budget, honestly.** PLAN step 3 asks for the declaration before verification
and I wrote it into this record afterwards; recorded rather than presented as
met. About 38s spent against 20s — the owned module four times (21s), the
affected modules once (11s), and 6s establishing that the five failures above
belong to another Work.

### Next

Independent review at `baton.bug`. Acceptance releases this provider gate only;
W122060's consumer pass and W119114's joined proof are unchanged.
