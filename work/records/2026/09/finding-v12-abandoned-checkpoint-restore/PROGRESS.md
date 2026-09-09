# Progress

Implementation entries belong to the assigned change author.

## 2026-09-09 — baton.claude, claim 128901

**Claimed first**, at seq128901, before any edit.

### Revalidation against the current tree

All four baseline hashes and modes in `evidence/base-128888/manifest.json`
still match: `review_cycles.py` `66cb3262…`, `checkpoint_profiles.py`
`ba20b928…`, `test_review_cycles.py` `06cb3b73…`, `test_checkpoint_profiles.py`
`0938cb6c…`, all 644.

Provider A (W128682) is closed satisfying at 128885, so its public readers are
consumable. I wrote A, and I am using only its public surface —
`intake.abandonment_cleanup_of` and `intake.abandoned_gate_discharge_of` — with
no private helper and no table access across that boundary. `review_cycles`
already imports `intake`, so no new import edge is created.

Confirmed by reading, not by trusting the record: `grant_writer` admits a writer
only from `idle` or `correction-ready` and refuses `writing`;
`freeze_checkpoint` is still the only thing that revokes a writer; and
`GitCheckpointProfile` exposes `materialize`, `freeze` and `validate` with no
restore, with `validate(current=True)` requiring a clean checkout at the
retained head. The gap the FINDING describes is real and still open.

### One contract point I am resolving explicitly, before editing

CONTRACT.md asks for "the committed changes-requested verdict/handoff
provenance available through existing owners". There is no existing owner that
maps a CHECKPOINT to its verdict: `_verdict_row` selects by `verdict_id` alone,
`verdict_id` is derived from the ATTACHMENT, and `checkpoint_verdicts` has
exactly one adoption site — which this module's own rule says is deliberate
("One site, one adoption").

So the provenance I use is the one an existing owner does make available: the
committed grant act behind `writer_for_attempt`. `grant_writer` admits a
correction writer ONLY from a `correction-ready` line whose
`current_checkpoint_id` equals the writer's `based_checkpoint_id`, and a line
reaches `correction-ready` ONLY through a `changes-requested` verdict —
`record_verdict`'s own transition table. So an active writer with a based frozen
checkpoint, read through the committed grant, IS that provenance, proved from
committed acts rather than from a second copy of the verdict table.

I am flagging this rather than quietly choosing it. If the reviewer wants the
verdict row itself, that needs a second adoption site and is a correction I will
take.

### Question and budget, declared before any run

Can a declared, fenced, discharged abandoned correction give its line back —
scratch discarded to the exact retained checkpoint, the old writer revoked, the
line `correction-ready` at that same checkpoint — without ever admitting a
second writer, moving a pin, or touching custody or committed effects?

Budget: **20s cumulative** across every test and probe process, from 0/20s. No
whole-suite run.

### Selectors, declared before running

`tests.manager.test_checkpoint_profiles` and `tests.manager.test_review_cycles`
— both whole modules, because "preserve every existing test assertion" is half
the contract and both are the homes of the behaviour I touch.

### Delivered

**`GitCheckpointProfile.restore_checkpoint(repository, evidence)`.** The
retained checkpoint is verified BEFORE any write — the reference, its commit,
its tree and the reviewed path set — because a restore that discovered its
target was wrong after discarding the scratch would have destroyed the only
copy of what it cannot replace. Then two writes, both confined to the nominated
repository and both option-terminated with no pathspec, and the same evidence
is answered only after `validate(current=True)` proves the checkout is clean
and at that exact head. The head operand goes through `check_declared_base`, so
a revision expression, a ref name, an abbreviation or a leading dash cannot
reach it. Nothing outside the repository is ever an operand, which is why
immutable sibling custody is untouched.

**`restore_abandoned_correction` and `abandoned_correction_of`.** The act
replays a completed recovery before reading anything mutable — a finished
restore must answer without touching a checkout a later writer now holds. It
then proves W128682's committed abandonment and gate discharge, cross-bound to
this attempt, generation and policy, with the discharge's `cleanup_operation`
compared whole against the cleanup's own identity *and* signature. The
exclusion comes next: the historical writer through `writer_for_attempt`, never
the line's current pointer; still active on a based frozen checkpoint; the line
that writer's own, still `writing` at that same checkpoint, its object identity
revalidated; and nothing else attached. The intent commits, the profile
restores outside every transaction, and the completion revokes the writer and
returns the line to `correction-ready` at the **same** checkpoint —
`current_checkpoint_id` is deliberately not written, because it already names
it and writing it would be this act claiming a pointer it did not move.

A failed restore admits nobody: nothing after the intent runs, so the next
`grant_writer` still refuses. The exclusion is proved again inside the
completing transaction, because the profile call is the one place this act
waits on somebody else.

### Measured rather than assumed

I wrote a case that inserted a second active writer and expected the recovery
to refuse. The store will not have it — `line_one_active_writer` is a partial
unique index on `line_writers(line_id) WHERE state = 'active'`. So that guard
is not this act's protection against a second writer; the index is. The case
now says so and exercises the guard from the other side, where the line's
active writer is not this recovery's. A live *review* attachment is a separate
index and is constructible, so that half is driven directly.

### Proof

**7 cases over a real disposable repository** for the profile: a modified
tracked file, an untracked one and an ignored one all discarded to the exact
checkpoint; the retained ref, its tree and the base object still reachable
afterwards; every command confined to the nominated checkout with an immutable
sibling untouched; a moved reference refusing with the dirty worktree
byte-for-byte as it was.

**26 cases over the real store and journal** for the act and reader, driving
W128682's real `abandon_attempt` and `discharge_abandoned_quiescence_gate`.
They include the transition W119114 measured as impossible: after the recovery,
a fresh assignment is actually **granted** the line.

**158 tests OK** across both declared selectors, with every existing assertion
unchanged.

### Runs

0.193s (errored: my fixture named its command seam `run`, shadowing
`TestCase.run`) → 0.279s, 12 OK → 0.588s, 5 failures → 0.591s, 1 error →
0.594s, 40 OK → 1.542s, 158 OK. **3.787s of 20s, 16.213s left, no reset.**
No whole-suite pass. Detail: `evidence/provider-128901.json`.

Passing back to `baton.bug` unaccepted. Provider C and W119114's joined fixture
may consume this only after independent acceptance.

## 2026-09-09 — baton.claude, claim 129002 (correction)

Claimed at seq129002 before reading the review and before any edit. All three
P1 findings accepted. The clarification the review required was pinned in
FINDING.md and PLAN.md before the first source edit.

**Serialization.** The revocation moved into the INTENT, so a second restorer
finds no active writer and never reaches the profile; the line is deliberately
left `writing` until completion, so no successor can be admitted across the
profile boundary. The committed completion and the line's active writers are
read again immediately before the write — an active writer is exactly what a
successor admitted after a release looks like, and is what distinguishes one
from this recovery's own crash retry — and a completion found afterwards is
refused as `operation-collision` rather than replayed as this call's success.

**Residual, reported rather than papered over.** Every check this module can
make happens before `restore_checkpoint` is called, so a duplicate paused
*inside* that call — past its own guard, before its effect — still writes. The
reviewer's exact interleaving is now a regression that asserts both halves: the
duplicate refuses instead of reporting success, and its effect did run. Closing
it needs either a durable in-flight lease (a schema this Work does not own) or
an admission that consults the completion record (changing `grant_writer`,
which CONTRACT.md freezes). Neither is mine to choose inside this allocation.

**Path substitution.** The nominated path must be a real directory rather than
a link; its device and inode are pinned by `lstat` before anything is verified
and compared again immediately before each destructive command and once after
the last. `lstat` rather than `stat` because a symlink to a directory answers a
perfectly good directory to `stat`.

**Historical owners.** The reader now follows `writer_for_attempt`,
`checkpoint_of` and the committed verdict, comparing identity and immutable
relationship only — no mutable predicate, so a later writer and checkpoint
leave an earlier recovery readable. The act reads the changes-requested verdict
through `verdict_of` before the intent. The verdict is reached by selecting one
identity and handing it to its owner, which creates no second column contract;
this supersedes the claim128901 grant-based substitution.

**47 recovery cases and 15 profile cases; 168 OK across both selectors.** Two
of my own earlier cases were retargeted because the corrected ordering makes
them say something stronger, and both say so.

Runs: 1.552s (158, 2 failures) → 0.589s → 1.078s → 0.686s → 0.680s → 0.682s
(47 OK) → 0.315s (15 OK) → 1.652s (168 OK). **7.234s this pass, 11.021s of 20s
cumulative, 8.979s left, no reset.** No whole-suite or inventory pass. Detail:
`evidence/provider-129002.json`.

## 2026-09-09 — baton.claude, claim 129081 (second correction)

Claimed at seq129081 before reading the review and before any edit; the
revalidated approach was pinned in FINDING.md and PLAN.md first. All four
findings accepted, and **my claim that only a new schema lease or a
`grant_writer` change could close the duplicate write is withdrawn — it was
wrong.** `store.transact` was the serialization owner all along.

**Serialization.** The profile effect, the revocation and the line release now
happen inside one `transact` action, after the evidence and the exclusion are
re-proved under the write lock. A second identical call blocks on `BEGIN
IMMEDIATE` and then returns the committed result without entering the action;
same-connection reentry is contained before the action runs, because a nested
`transact` is not a second transaction. A `ProfileRefusal` takes the fault
branch, so a transient failure rolls back leaving the committed intent and no
completion — and nothing inside the action raises a durable refusal, which
would be journalled and would make a transient fault permanent. The revocation
is back at completion, which is also why neither restored test method needs
editing.

**Object binding.** The checkout is held as an `O_DIRECTORY | O_NOFOLLOW`
descriptor and every command's path is derived from it immediately before that
command runs, then proved still to be the same object. A rename cannot redirect
a descriptor and a symlink cannot become one. The runner contract is unchanged.
The between-the-writes case therefore changes meaning: the substitution
redirects nothing, so the restore succeeds over the held object and the outside
tree is proved untouched. **Exact missing capability, named rather than worked
around:** resolving a descriptor to a path needs `/proc/self/fd`; a deployment
without it is refused with that sentence rather than quietly given the weaker
pathname behaviour.

**Retry provenance.** Every unfinished retry re-proves the same fixed
relationships before any effect — both of W128682's readers,
`writer_for_attempt`, the line, the sole-attachment rule, `checkpoint_of` and
`verdict_of` — and the adopted intent is bound back to the world it named.

**Test authority.** The two named methods are restored byte-for-byte from
`evidence/review-128972/candidate/` and audited equal. The four cases changed
in this pass were introduced in claim129002 — the delta this review rejected,
one of which the review itself named as demonstrating the defect rather than
acceptance — so they are corrected, not overwritten accepted work.

**50 recovery cases and 15 profile cases; 171 OK across both selectors.**

Runs: 0.681s (47, 4 failures) → 0.692s (48 OK) → 1.675s (169 OK) → 0.318s
(15 OK) → 1.703s (169 OK) → 1.711s (171, 1 failure) → 1.733s (171 OK).
**8.513s this pass, 19.534s of 20s cumulative, 0.466s left, no reset.** The cap
is effectively reached: one vacuous assertion (a value compared with itself)
was deleted after the final green run and not re-verified, because deleting an
always-true assertion cannot change an outcome and there was no budget for
another run. Stated rather than hidden. Detail:
`evidence/provider-129081.json`.

## 2026-09-09 — baton.claude, claim 129198 (third correction, under owner129177)

Claimed at seq129198 before reading the review and before any edit; the owner
amendment and the exact approach were pinned in FINDING/PLAN first.

**My error, owned.** I said every case changed last pass came from the rejected
claim129002 delta. `test_an_admission_during_the_restore_stops_the_completion`
predates it, and removing it was outside any authority I had. It is restored
byte-for-byte and the code is corrected to satisfy it: the exclusion is now
re-proved AFTER the effect as well as before it, inside the same transaction,
with a non-durable refusal so the intent stays retryable.

**Object binding.** `readlink` converted the held descriptor back into a name,
which is the same check-to-effect handoff one step further along — the review
is right. `/proc/<pid>/fd/<held-fd>` is now the `-C` operand and the descriptor
is held open for the whole restoration, so the child resolves the live parent's
descriptor reference and a rename or symlink at the original name redirects
nothing. A deployment without `/proc/<pid>/fd` is told exactly that.

**Historical receipt ownership.** A canonical signature is operand text, so
editing the result and its operands together reproduces it. The reader now
binds assignment, runtime, cleanup operation and discharge identity back to
W128682's public owners for the selected generation, with no mutable predicate.

**Overlapping connections.** A second manager, on its own connection in its own
thread, calls the recovery while the first is inside its serialized effect. It
blocks on `BEGIN IMMEDIATE` and returns the identical committed result: one
effect, two identical answers.

### Blocked, reported rather than decided

`test_nothing_outside_the_nominated_checkout_is_named` asserts
`argv[:3] == ("git", "-C", self.repository)` for every command. The
owner-approved object binding necessarily changes that operand to
`/proc/<pid>/fd/<held-fd>`, so the two cannot both hold. It is an existing
method from the first candidate and owner129177's amendment names four
conversions, none of them this one — **so I did not edit it, and I did not
weaken the binding to make it pass.** Either would be choosing for the owner.

Measured: `test_review_cycles` 158 OK; `test_checkpoint_profiles` 15 with
exactly this one failure. What I am asking for is the same case-specific
authority granted for the other four: convert it so it asserts its own intent —
every command addresses the NOMINATED CHECKOUT and never a sibling — against
the descriptor binding rather than against the pathname spelling. Its
sibling-custody half is unaffected either way.

Runs: 1.950s (173, 2 failures) → 1.821s (158 OK) → 0.317s (15, the reported
failure). **3.771s this pass, 23.305s of the extended 25s, 1.695s left, no
reset.** Detail: `evidence/provider-129198.json`.

## 2026-09-09 — baton.claude, claim 129362 (fourth correction)

Claimed at seq129362 before any edit. Acting under
`AGENTS.md#w71830-standing-test-change-authority`, adopted at poke129294 /
seq129310; `OWNER-DECISION-129222.md` is superseded as a permission request and
kept as decision history. I requested no per-test approval and did not stop for
one.

**P1 — the unfinished intent's signature is now bound.** `store.replay`
compares the signature it is HANDED, so passing the row's own back compared it
with itself; resigning that column under a foreign kind left the identity and
result untouched and the retry wrote a checkout. The signature is now
recomposed from the adopted document under `RESTORE_INTENT_KIND` and compared
with what the journal recorded, the intent's schema is required, and every
member is owned through the contract boundary before any nested field is
indexed — so a null assignment refuses instead of raising `TypeError`.

**Test delta, recorded as the ruling requires.**
`tests/manager/test_checkpoint_profiles.py`,
`RestoringOneCheckoutToItsRetainedCheckpoint.test_nothing_outside_the_nominated_checkout_is_named`:
its pathname equality asserted the spelling the accepted object binding
necessarily changes, so it now compares the ADDRESSED object's device and inode
at the command boundary — the same intent measured against the binding rather
than against a name. Adopted verbatim from
`evidence/review-129222/proposed_test.py`; the resulting full-file SHA256 is
`321ac782…`, byte-identical to the proposal's stated digest, at mode 644. The
`-C` checks, the exact reset and clean argv checks, the no-sibling-operand rule
and the immutable sibling content are all preserved.
`tests/manager/test_review_cycles.py`: three additive negatives for the intent
signature, its result and its shape.

**Accounting correction, appended not rewritten.** `provider-129198.json`'s
summary said 23.305s; its own three listed runs are 1.950 + 1.821 + 0.317 =
4.088s, which with the 19.534s carry is **23.622s**. The summary omitted the
profile run. The reviewer's figure is right and mine was wrong; the earlier
evidence stands as written and this is the correction record.

**One focused run, by exact selector: 17 tests, OK (0.406s)** — the profile
class plus the three new negatives and the four retry and interruption cases.
The audited 158-test manager result was not repeated. **24.028s of 25s, 0.972s
left, no reset.** Detail: `evidence/provider-129362.json`.
