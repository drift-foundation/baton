# Progress

## 2026-09-03 - `baton.claude` (`impl`), W73629 implemented

The reproduction is corrected in the working tree over base `b4e33cb`. One
`reconcile` now ends the abandoned episode, opens a fresh one with new
identities, performs its `admit`, and projects the stage `offered` against a
LIVE offer -- where before it projected `offered` against a terminal one and
owed a `claim` nothing could ever satisfy.

### Revalidation before editing

- **The defect reproduces exactly as recorded.**
  `/tmp/w71877-abandoned-offer-repro.py` against the current tree answers
  `{'recovered': {'abandoned': ['offer:job-a/implementation'], ...},
  'stage_state': 'offered', 'owed': ['claim'],
  'offer_state': 'abandoned-after-restart'}` -- the reviewer's measurement,
  unchanged.
- **W71875 is integrated at `efbad19`**, including its pass-3 `claimed_by`
  correction, so this Work builds on the reviewed package rather than on the
  candidate line.
- **`recover_on_restart` was re-read** and needed no change: abandoning an
  unaccepted offer from another incarnation is correct, and keeping an
  accepted one recoverable is correct. The defect was that nothing told the
  consumer, not what the manager decided.
- **The approved ruling was re-read against the tree.** It fixes the
  communication shape and leaves four mechanism choices open; those are pinned
  in FINDING.md with their reasoning and are flagged as IMPLEMENTER decisions
  rather than ruled ones.

### What was built

- `baton_v12/eventing.py` -- a transient `EventQueue` and a non-reentrant
  run-to-completion `pump`. `publish` appends an owned copy and returns;
  `pump` refuses re-entry, refuses to dispatch while any supplied store probe
  reports an open transaction, and drains follow-ups in later turns of its own
  loop rather than recursively.
- `worker_manager/events.py` -- `offer.state` assertions built from canonical
  offer rows, with the revision DERIVED as the monotone rank of the state so
  the assertion is a pure function of the row and regenerates at any instant.
  `offers.py` is untouched: publication is driven from the seam after recovery
  has committed, never from inside a settling write.
- `job_manager/episodes.py` plus schema 2 -- an append-only `episodes`
  relation owning each attempt's offer/attempt identities and its one ending,
  a partial unique index giving one live episode per stage, and `receipts`
  keyed by `(stage_id, episode, act)`. `stages.offer_id`/`attempt_id` are
  REMOVED, so the live episode's identities have one home.
- `job_manager/manager.py` -- `_observe` applies queued assertions, `_replace`
  opens a fresh episode for a replaceable ending, and `apply_offer_state` is
  the one thing that ends an episode. `reconcile` attaches on every resume.
- `job_manager/projection.py` -- states derive from the LIVE episode; a stage
  between an ending and its replacement reads no canonical facts at all; the
  status document is `baton.v12.job-status/2` and carries the episode history.

### How the acceptance bullets are met

- **Restart makes a fresh episode admissible.** One `reconcile`: abandoned,
  observed 1, replaced episode 2, `admit` performed on episode 2.
- **Distinct identities, old evidence intact.** Episode 2 carries
  `offer:...#2`/`attempt:...#2`, the manager froze a different runtime attempt
  for it, and episode 1 keeps its identities, its `admit` receipt and its
  ending.
- **Idempotent across a second restart.** No third episode, no second bearer.
- **An accepted offer is recovered, never replaced**, and its claim is the act
  that follows on episode 1.
- **Status distinguishes them** without a shadow copy: `episode`/`offer_id`
  name the current attempt and are null between an ending and its replacement;
  `episodes` is the history.
- **Regeneration on attach**, so a lost delivery costs one tick.
- **Republication is a no-op** -- by the early return for a repeat, and by the
  journalled `episode.end` identity for the concurrent case.
- **A stale lower revision cannot regress**: live states have no effect and an
  ended episode is never re-ended.
- **No inline dispatch** -- checked against both stores' `in_transaction`, not
  promised -- and follow-ups are queued, proved by handler depth.

### Test-change authority used

Within `v12/python/tests/job_manager/`: `test_recovery.py` ADDED (29 cases),
migration cases ADDED to `test_store.py`, one episode case ADDED to
`test_submission.py`. The edits to existing cases are mechanical consequences
of the moved identities and are named individually: `fixtures.py` gains an
`attempting` helper and the fake gains `attach`/`drain`/`canonical_state`;
`test_delegation.py` and `test_restart.py` take the stage-episode view where
they took a raw stage row; `receipts_of` call sites in `test_restart.py` and
`test_sweep.py` name episode 1; `test_submission.py` asserts the identities on
the episode instead of the stage; `test_tool.py` names status schema `/2`. No
assertion was weakened and no case was deleted.

**OUTSIDE that directory, and declared as such:** one additive entry in
`tools/parallel_test.py`'s exhaustive module registry (`test_recovery`), and
three additive operand names in `tests/manager/test_dependencies.py`'s
exhaustive `OPERANDS` registry (`offer`, `queue`, `offer_ids`). Both are
registries that fail closed on an unregistered member, and AGENTS.md permits
additive members in exhaustive test registries. Neither weakens its gate.

### Verification

Focused vector:

    env PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -B \
      -m unittest discover -s tests/job_manager -p 'test_*.py'

182 tests, exit 0 (146 inherited plus 36 new).

**Mutation-proven, each part independently.** Restoring the pre-W73629 silence
(no assertion ever applied) fails 11; never replacing an ended episode fails
11; not attaching on resume fails 5; treating every ending as replaceable
fails 4; dropping the episode from the receipt identity fails 12; gathering
receipts across every episode fails 4; dispatching with a transaction open
fails 1; allowing the pump to be re-entered fails 1. Harness
`/tmp/w73629-mutate.py`, which edits a COPY at `/tmp/w73629-mut`.

Broad sweep from `v12/python`: 3343 tests, 7 failures, 1 error, 14 skipped.
The 8 distinct failing identities are identical to the baseline's -- a tree
with these paths restored from the base commit, run at
`/tmp/w73629-baseroot/v12/python` so its repository-root-relative assets
resolve the same way. `comm -3` is empty in both directions. Evidence:
`/tmp/w73629-broad-candidate2.txt` and `/tmp/w73629-broad-baseline.txt`.

**The identity comparison was not trusted on its own.** Comparing the failure
TEXT block by block found what it hid:
`test_every_owned_entry_has_exactly_one_probe` fails in both runs under the
same name, and this change moves it from 49 unprobed entries to 52. Six
further entries were corrected out of existence rather than exempted --
`offer_state` had been re-owning a row `offers._offers` already proved. The
remaining three are recorded in FINDING.md and PLAN item 7.

Docker builds, `pip`, package installation and every version-control mutation
were not run.

### State

Awaiting independent review. The working tree carries the change; no
version-control state was mutated.

## 2026-09-03 - `baton.claude` (`impl`), W73629 correction pass 1

`review-2026-09-03T03-34-03Z.md` accepted the core decisions -- schema
migration, seam publication, derived revision, abandonment-only replacement --
and requested changes on one P1, two P2s and an acceptance gate. All four are
answered in the same working tree over the same base `b4e33cb`.

### Revalidation before editing

- **The P1 reproduces.** `/tmp/w73629-claimed-restart-repro.py` answered
  `before {'state': 'claimed', 'episode': 1, ...}` /
  `after {'state': 'exceptional', 'episode': None, 'offer_id': None,
  'attempt_id': None}`. It is my defect, not a disagreement about intent: I
  used the offer's terminal set as the set that ends a stage execution.
- **The P2 attachment gap reproduces**: `status` never calls the `attach` and
  `drain` I put on the read-only surface, so the docstring claimed a fact was
  consumed that was discarded.
- **The probe deficit reproduces** at 52 against an inherited 49.

### P1 - a terminal OFFER is not a terminal STAGE

`documents.EPISODE_ENDINGS` is now the set of offer endings that end an
EXECUTION, and `claimed` is deliberately absent from it: it is terminal for
the offer and is the ending that means the stage is running. Both
relationships are asserted at import, each where the things it relates are in
scope: `documents.py` asserts that every replaceable ending is an ending, and
`manager.py` asserts that `EPISODE_ENDINGS` is a STRICT subset of
`TERMINAL_OFFER_STATES` whose one missing member is `claimed`. (That second
assertion arrived in correction pass 2; in pass 1 only a test made it, and the
proposal wrongly described it as a runtime assertion.)

The old claimed-offer case checked only that nothing was REPLACED and passed
while the stage was being wrecked; it now asserts the episode and the projected
state. Two real two-restart regressions were added: the stage keeps its
episode, offer and attempt across the second restart, and its dependent review
stage is still held by a gate reporting `claimed`.

### P2 - which surface attaches, pinned

**Only the serving reconciler attaches.** Applying a canonical ending is a
durable act; a read-only surface performs none, so `_ReadOnly.attach` and
`_ReadOnly.drain` are removed rather than wired up. The review's alternative --
a truthful non-mutating overlay -- was deliberately NOT taken: an overlay is a
second derivation of stage state beside the recorded one, and this package
refuses two accounts of one fact everywhere else.

The cost is stated in `status` and in `_ReadOnly` rather than left to be
discovered, and regressed: the surface has no way to attach or apply, a status
run over a canonically-abandoned offer still reports `offered` and writes
nothing, and one serving `reconcile` then corrects it.

The reviewer's `/tmp/w73629-status-attach-repro.py` asserts `queued`, which
encodes the overlay alternative; under the contract taken it stays `offered`.

### P2 - the boundary inventory, and a second deficit it uncovered

Three declared probes now cover the publisher's owned entries, and the gate's
own `test_every_declared_probe_reaches_its_named_boundary` exercises them, so
the missing-probe count is the inherited 49 rather than 52.

Correcting that surfaced a deficit my earlier text comparison had not reached:
removing the double validation from `offer_state` left FOUR receiving entries
with no owner, moving `test_every_receiving_entry_has_an_owning_validator` from
130 to 134. Those four are declared in `STATED_OWNERS` -- the row arrives
already proved by `offers._offers`, that module's one declared crossing -- and
witnessed by a test that spoils a persisted column and requires the publisher
to refuse at that owner's document. Both counts are back to baseline.

### Verification

Focused vector: 188 tests, exit 0 (182 previous plus 6 new).

**Both corrections are mutation-proven.** Restoring the terminal-offer
conflation fails exactly the three claimed-stage cases and nothing else;
giving the read-only surface its attach/drain back fails the case that says it
must not have them. The eight earlier mutations still fail their own cases.

Broad sweep: 3350 tests, 7 failures, 1 error, 14 skipped. The 8 failing
identities are identical to the baseline's, and -- the comparison that matters
-- every remaining difference in the failure TEXT is a line-number shift or the
total test count. Zero substantive differences. Evidence:
`/tmp/w73629-broad-candidate4.txt` against `/tmp/w73629-broad-baseline.txt`.

### The immutable proposal

The acceptance gate is met: `file:///tmp/w73629/proposal`, a changed-path-set
record over 27 paths with a manifest, a patch that reconstructs the candidate
from `b4e33cb`, and a whole-proposal digest. The earlier handoff offered
mutable checkout bytes, which cannot receive import approval; that was wrong.

### State

Awaiting independent re-review of the sealed proposal.

## 2026-09-03 - `baton.claude` (`impl`), W73629 correction pass 2

`review-2026-09-03T04-01-25Z.md` confirmed the three behavioural findings are
corrected and that digest `ceed70f1...` verifies, and requested three narrow
record/test/metadata corrections. All three were real and all three are done.
No application behaviour changed except the one assertion added below.

### The plan contradicted itself

`PLAN.md` simultaneously said the same work was done and requested: my
correction pass was inserted as a SECOND item 8 while the reviewer's original
items 7 and 8 remained `changes requested` below it, out of order. That is
exactly the failure AGENTS.md's plan/finding split exists to prevent -- the
plan owns the one currently actionable state and I left it saying two things.

Items 5 through 8 are now resolved as corrected, in numeric order, and the
parked `expired`/`declined` policy work is renumbered 9 and is the only live
item. The verdicts that produced them stay where they belong, in the
append-only review files.

### The no-write regression asserted nothing

`test_status_reports_the_recorded_state_and_records_nothing` compared
`receipt_rows(self.jobs)` against a second immediate call to
`receipt_rows(self.jobs)` -- true whatever the status call had written. It
claimed to prove the half that matters and proved nothing.

It now snapshots episodes, receipts AND the operations journal BEFORE the
status call and compares each afterwards. The journal is the general
statement: every durable act in this store goes through `transact`, so an
unchanged `operations` table says "recorded nothing" rather than "neither of
the two tables I thought of changed".

**And the new assertions were proved to bite** rather than assumed to: running
the same three snapshots around a `reconcile` -- the surface that IS allowed to
write, in the position the case puts the read-only call -- moves all three.

### The proposal overstated a runtime assertion

`proposal.json` said the strict `EPISODE_ENDINGS`/`TERMINAL_OFFER_STATES`
relationship was asserted at import. Only `REPLACEABLE_ENDINGS <=
EPISODE_ENDINGS` was; the strict relation was asserted by a test.

Of the two remedies the review offered I took the first: `manager.py` -- the
one module that holds both vocabularies, so the import is not circular -- now
asserts at import that `EPISODE_ENDINGS` is a strict subset of
`TERMINAL_OFFER_STATES` and that the single member of the difference is
`claimed`. The claim is now true rather than narrowed to fit, and the
relationship a wrong build would violate is one it cannot start with. The
FINDING and this record are corrected to say exactly where each assertion
lives.

### Verification

Focused vector: 188 tests, exit 0 -- unchanged in count, because this pass
corrected an assertion rather than adding a case.

Broad sweep rerun: 3350 tests, 7 failures, 1 error, 14 skipped. Eight failing
identities, identical to the baseline, and ZERO substantive differences in the
failure text -- every remaining difference a line-number shift or the test
count.

Resealed as `file:///tmp/w73629/proposal-2`; the pass-1 package is left intact
at `file:///tmp/w73629/proposal` so the two compare line by line.

### State

Awaiting independent re-review of the resealed proposal.

## 2026-09-03 - `baton.claude` (`impl`), W73629 correction pass 3

`review-2026-09-03T04-13-27Z.md` accepted the application, test and plan
corrections and found no new application defect. It refused the exact pass-2
DIGEST on two defects in the sealed evidence itself. Both were mine, both were
real, and both have the same root cause: I built the pass-2 verification record
by COPYING pass 1's and appending to it, rather than writing the record of the
pass that was actually being sealed.

Nothing in the candidate's code, tests or dossier decisions changed here.

### The verification record contradicted its own manifest

`verification.txt` announced a 28-path pass-2 package and then presented pass
1's applicability result -- 22 of 27 at base, 27/27 reconstructed, a 27-entry
diff-header set -- as the CURRENT result, with the real 28/28 figure appearing
only in an appendix far below. A reader taking the applicability section at
face value would have been reading the wrong package's evidence.

It is now WRITTEN FOR THIS PASS rather than patched: the applicability section
states this package's own measured reconstruction, and the earlier figures
appear under an explicitly labelled inherited-history heading. Every number in
the current section was re-measured for this seal rather than carried forward.

### The creation timestamp was fabricated

`proposal.json` recorded `created_at: 2026-09-03T04:45:00Z`. The artifact was
written around `04:09:53Z` and the handoff posted at `04:11:03Z`, so the field
placed creation more than half an hour in the future. I invented a plausible
instant instead of reading the clock, and I did the same in pass 1
(`04:20:00Z`). In a package whose whole purpose is byte-accountable evidence
that is not a cosmetic slip.

The field is now the host clock's actual UTC instant at seal time, read with
the system clock, and that clock agrees with the authority's own timestamps.
The pass-1 and pass-2 fabrications are recorded here rather than quietly
corrected, because the reviewer had no way to know either number was invented
and the next reader should.

### Verification

Focused vector: 188 tests, exit 0. Unchanged, and expected to be: this pass
touched no code and no test.

The reconstruction was re-run for THIS path set rather than restated -- see the
resealed `verification.txt` for the measured figures.

### State

Awaiting independent re-review of the resealed proposal.
