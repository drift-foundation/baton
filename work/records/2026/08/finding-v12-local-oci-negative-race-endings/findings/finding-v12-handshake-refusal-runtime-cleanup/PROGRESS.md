# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — the seam exists; the real-engine half does not yet

Claimed W32576 at seq 32740. No Git history or index was mutated.

### PLAN 1: revalidated, and it decided how small this is

`handshake.negotiate_acp` emits `refused/unsupported-version` correctly, and
`attempts.request_cancellation` ALREADY fences at the authority first and only
then orders quiescence — which is exactly the ordering this refusal needs and
the one place it is written. So the missing thing was never an ending; it was
a SEAM between a session refusal and the ending that already exists.

### PLAN 2–3: `handshake.settle_unsupported_version`

Receives the exact `refused/unsupported-version` refusal for an exact
attempt/profile/version, journals THAT fact effectively-once, and delegates
the ending to `request_cancellation`. It duplicates no reconciliation, custody,
retention, force-removal or provider teardown; those keep their owners.

- the refusal keeps its typed identity in what is returned and journalled, and
  **no worker disposition is written** — the axis it moves is the runtime's;
- the operation identity binds attempt, fixed assignment, profile digest and
  the pinned version the agent disagreed with, so a different version is a
  different act;
- only the exact closed pair is carried: `profile-uncertified` and
  `refused/precondition` are rejected, and rejection ends nothing.

### Three of my assertions were wrong, and each time the code was right

- **the retry does not fence once.** `request_cancellation` deliberately
  re-issues the order under the same operation identity — its own docstring
  says so, and that is what makes a cancellation in flight survive a restart.
  I asserted one authority call; the case now asserts what this seam owns, one
  journalled `session.unsupported-version` record however many retries.
- **a different version does not refuse.** It journals its OWN operation,
  which is what "a different act" means. The case counts two records.
- **cross-module subclassing broke the runner.** Importing the attempts base
  into `test_handshake` made unittest collect its inherited tests under both
  modules, and `parallel_test.py` refused on duplicate ids. The class lives in
  `test_attempts.py` beside its base now.

Two earlier drafts also rebuilt the fixture inside a loop and failed on the
re-issued offer rather than on the rule; both build the attempt once now.

## State

The composition seam and its daemon-free cases are in. Passed back.

### Not done, and it is the acceptance's first line

**No real Docker case.** The acceptance requires a genuine
`unsupported-version` refusal reached AFTER a real container exists, which
needs an agent session driven against a live worker — not something the
existing composition fixtures start. The seam is proved at the manager
boundary and the engine half is not attempted, so I am not claiming it.
Restart/retry, identity-mismatch, multiplicity, uncertainty and
sibling-preservation against a real engine are the same gap.

### Gates

- `tests.manager.test_attempts` + `tests.manager.test_handshake` — 203 tests,
  green
- full v12 parallel source — **1674 tests, 6 failures**, every one in
  `test_boundary_inventory` and none this Work's

## 2026-08-28 — [P2] corrected; the four [P1]s are one coupled round I did not complete

Reclaimed W32576 at seq 32818. No Git history or index was mutated.

### [P2] corrected

The duplicate `digest` import in `handshake.py` was mine and is removed.

### The four [P1]s are coupled, and I am not part-doing them

Read together they are one implementation rather than four:

- **[P1] provenance.** The review is right and this is the serious one: the
  operation checks the refusal's SPELLING and calls that its identity. It
  accepts a free `attempt_id`, `profile_digest` and integer, proves no
  `agent_session_ref`, and does not even require the digest to match the
  attempt's recorded profile — so a capability holder could manufacture the
  closed pair and fence a live attempt. Checking a pair's spelling proves its
  type, not its provenance, and I wrote a docstring about typed identity while
  leaving exactly that hole.
- **[P1] identity/collision** cannot be fixed WITHOUT it. The correction is to
  derive one fixed identity from the exact session/refusal act — so the
  session reference the first finding demands is the input the second one's
  identity is made of. Fixing them separately would produce another half-seam,
  which is the defect this campaign keeps correcting in my work.
- **[P1] the ending.** `request_cancellation` proves fencing and quiescence
  were ORDERED; it does not force-remove, prove absence, settle providers or
  release a lane. My case stopped at `cancel-requested` and I described that
  as the ending reached. It is not.
- **[P1] the engine and race matrix** needs a real session that creates a
  container and then genuinely refuses — the half I already reported as not
  attempted.

**What I did NOT do, and why it is not a hazard meanwhile:** the operation is
unexported, absent from `__all__` and the package surface, and called by no
production path — which the review states. So it cannot be invoked outside the
tests that exercise it. Leaving it is not leaving a live way to fence an
attempt; completing it half-way would be worse than either leaving it or
removing it.

### [P2]'s other half, deliberately not done

`TheCompositionIsOnThePublicSurface` is NOT extended. The review says to
extend it "when the corrected production operation is exported", and exporting
this one before its provenance check exists would put a forgeable ending on
the public surface.

## State

**Returned with one [P2] corrected and four coupled [P1]s open.** The next
round is a single implementation: require and compare the persisted four-part
session reference, derive the operation identity from that act so changed
operands collide, drive the exact runtime through the existing cleanup owners,
and add the Docker and fail-closed matrix. W32576 continues to gate W32382.

## 2026-08-28 — the provenance and identity findings, implemented

Reclaimed W32576 at seq 32868. Two rounds without a delta was enough; these
two are done. No Git history or index was mutated.

### [P1] The refusal is DERIVED, not accepted

The operation no longer takes a `ContractRefusal` operand at all. It takes the
exact persisted four-part session reference, proves it through
`sessions._require_session` — which also refuses a reference naming a provider
session the row does not hold — and then runs `negotiate_acp` ITSELF against
the row's own certified profile. The refusal that reaches the ending is one
this manager derived from evidence rather than one it was handed.

Everything a caller could previously choose is now read from the session row:
the attempt, the profile digest and the assignment. A version the profile
ACCEPTS raises nothing, and the seam then refuses to invent an ending for a
session that negotiated successfully. An execution posture is required,
because a consent session has no runtime to end.

### [P1] One session, one refusal, and changed facts collide

The identity is the session ACT — attempt, posture, epoch, provider session —
and the assignment, profile, pinned and answered versions and the refusal's
own text ride in the SIGNATURE. So an exact retry replays and a second
answered version is an `operation-collision` rather than a second
incompatible account of what one session refused. Both directions are covered
and both count the journalled rows.

Hashing the operands into the identity, as the first version did, is what made
two versions two records.

### A Python detail worth recording

`except ContractRefusal as derived:` deletes the name when the block ends, so
the derived refusal is bound out of the handler before use. Caught by the
tests rather than by reading.

### Still open, and unchanged

- **the ending**: `request_cancellation` orders fencing and quiescence; the
  exact removal, positive absence, provider settlement and reuse ordering are
  not driven here yet.
- **the engine and race matrix**: no real Docker session, and no mismatch,
  multiplicity, uncertainty, restart or sibling cases.
- the operation stays UNEXPORTED and the public-surface guard is unchanged,
  because those are the review's own condition for exporting it.

### Gates

- `tests.manager.test_sessions` — 79 tests, green
- full v12 parallel — **6 failures**, all `test_boundary_inventory`, none this
  Work's

## 2026-08-28 — both provenance races closed

Reclaimed W32576 at seq 32922. No Git history or index was mutated.

### [P1] A historical session row can no longer authorize a cancellation

`_require_session` proves identity and provider-session equality and
deliberately proves NO state — so an old execution epoch in `closed`,
`unknown` or any post-handshake state could be named with a mismatching
version now and derive a fresh cancellation out of history. Checking
`posture == execution` was checking that a row once WAS an execution session,
not that this refusal came from its handshake.

The lifecycle decides the invariant rather than a guess: `not-started →
initializing → ready`, and `ready` is reached only after negotiation succeeds.
So a negotiation refusal can only be evidence from `not-started` or
`initializing`, and every later state is a session whose handshake is over.

**Proved in the same boundary that fixes the record.** The check above the
transaction answers an optimistic read; it is re-proved under the write lock
against the row AND its profile digest, so a session that moved on in between
cannot have its history authorize the ending. A case drives all seven
post-handshake states and requires the attempt to stay `running`.

### [P1] One certified-profile observation, not two

The refusal was derived from `negotiate_acp`'s own read and the signed
`pinned_wire_version` came from a SECOND read. Certification is replaceable
state, so a withdrawal between them answers `None` and faults on the
subscript, and a recertification detaches the signed evidence from the
snapshot that produced the verdict.

`negotiate_acp` now takes an optional pre-read `profile`, so the rule keeps
ONE owner while the caller that must sign a snapshot reads it once. Two cases:
a withdrawal AFTER the record leaves what was signed intact, and a withdrawal
BEFORE the observation is a typed `profile-uncertified` refusal rather than an
untyped fault.

### Still open, and it is the Work's centre

The ending still stops at `cancel-requested`: no force-removal, positive
absence, provider settlement or reuse ordering. No real Docker refusal after a
container exists, and no restart, multiplicity, uncertainty, mismatch,
provider-retry or sibling matrix. The operation stays unexported.

I have now closed the four provenance/identity findings across three rounds
and not started the ending. That is the honest state: the next round is the
cleanup traversal and the engine matrix, and it is one round rather than four.

### Gates

- `tests.manager.test_sessions` — 82 tests, green
- full v12 parallel — **6 failures**, all `test_boundary_inventory`, none this
  Work's

## 2026-08-28 — the [P0] I introduced, closed

Reclaimed W32576 at seq 32968. No Git history or index was mutated.

### [P0] The public certification bypass was mine and is removed

Correcting the two-reads race, I gave `negotiate_acp` an optional `profile=`
operand. `negotiate_acp` is on the public surface, so that let any caller pair
an **uncertified digest with arbitrary bytes** and receive a verdict from
them — a behaviour-bearing mapping included, since the rule subscripts what it
is given.

The review's sentence is the one I should have applied myself: *a
single-snapshot requirement does not authorize widening the public trust
boundary.* I optimised a real defect and paid for it in a place I did not
look.

The rule is factored into a private `_negotiated_against(profile, ...)`. The
public door reads the certified profile and hands it there;
`settle_unsupported_version` reads it once and hands the SAME snapshot there.
One owner for the rule, one observation per act, and no door that takes bytes.

A black-box negative proves it: a caller who passes `profile=` gets a
`TypeError`, and an uncertified digest alone is `profile-uncertified`.

`TheCompositionIsOnThePublicSurface`'s structural guard was repointed at
`_negotiated_against`, where the `client_capabilities` emission now lives. The
assertion is unchanged — exactly one emission, and it is
`check_client_capabilities` over the profile's own member; only the locator
moved.

### Still open, and unchanged from the last handoff

- **[P1] slot ownership**: state is proved, the posture slot is not. Runtime
  absence can release the slot without rewriting the session state, so a
  historical `not-started`/`initializing` row still passes.
- **[P1] replay ordering**: the mutable preconditions run before
  `store.transact`, so an exact retry after a state advance or a withdrawal
  fails rather than replaying. My withdrawal case deletes the profile and
  never retries, so it does not cover the acceptance it names — the review is
  right about that and I am not claiming otherwise.
- **[P1] the ending and the engine matrix**, unchanged.

### Gates

- `tests.manager.test_sessions` + `test_handshake` — 115 tests, green
- full v12 parallel — **6 failures**, all `test_boundary_inventory`, none this
  Work's

## 2026-08-28 — slot ownership and replay ordering

Reclaimed W32576 at seq 33013. No Git history or index was mutated.

### [P1] The slot is a separate axis, and it is proved

State and slot are deliberately different things: runtime-absence evidence
releases the posture slot WITHOUT rewriting the session state, so a historical
`not-started`/`initializing` row survives the state check while its posture
belongs to nobody — or to a newer epoch. The refusal must come from the
session that currently HOLDS the execution posture.

Proved inside the same transaction that fixes the record: the slot must exist,
be `occupied`, and name this exact epoch. Two negatives — a released slot and
a newer epoch holding it — and both pin the reason.

### [P1] Replay is a fact about an act that already happened

The identity and signature carried the profile, the pinned version and the
refusal text, all read from state. So a committed refusal stopped replaying
the moment its session advanced or its profile was withdrawn, which is the
opposite of what effectively-once means.

Both are made of CALLER OPERANDS ONLY now — the four-part reference and the
answered version — so `store.replay` runs before any mutable precondition is
consulted, and what a caller can CHANGE still collides. The state, slot and
profile proofs moved entirely inside the transaction, which also gave the
state rule one owner instead of an optimistic copy above a deciding one.

**My previous withdrawal case deleted the profile and never retried**, so it
did not cover the acceptance it named — the review was right. The new case
advances the session to `closed`, releases the slot AND withdraws the profile,
then replays the exact call and gets the one committed record. A second case
does it through a newly opened store handle, because a restart is a new
process reading the same file.

### Still open, and it is now one thing

The ending: force-removal, positive absence, provider settlement, reuse
ordering, and the non-skipping Docker/restart/race/sibling matrix. The
operation stays unexported until it reaches that ending.

### Gates

- `tests.manager.test_sessions` — 86 tests, green
- full v12 parallel — **6 failures**, all `test_boundary_inventory`, none this
  Work's

## 2026-08-28 — the remaining ending is blocked, and I found out why by trying

Reclaimed W32576 at seq 33056. The provenance and replay findings are all
accepted. No production code was edited this round.

### The ending cannot be composed from here, and this is the chain

Revalidated rather than assumed, and it is short:

- `authorize_cleanup` requires an **intake receipt**;
- `request_intake` requires a **frozen** result;
- `request_freeze` requires a **terminal `worker_disposition` already
  recorded** — `output.py` says the handled turn outcome gates it and a proof
  the caller can write is not proof;
- and a handshake refusal produces **none**. `request_cancellation` and
  `_order_quiescence` observe only `execution_runtime`, and **nothing in
  production ever writes `worker_disposition = cancelled`.** Checked on the
  tree.

So the freeze → intake path is unreachable for this ending. Writing a
disposition to open it is exactly the defect W32382's review caught in my own
test, and exactly what W32648 was created to remove.

### It is the same wall W32648 already pinned

W32648's PROGRESS records the identical finding for the post-create failure —
"the custody path for this ending is NOT freeze → intake" — and pins the
answer both endings need: a manager-owned failure record distinct from any
worker disposition, and **quarantine** as the no-envelope custody rule.
W32648 pinned it and has not implemented it.

So `block work=W32576 on=W32648`, seq 33059. This is a discovered technical
dependency rather than a way to avoid the work: I went looking for the ending
and found there is no door to it yet.

### What is left here once that lands

The ending traversal and the Docker/restart/multiplicity/uncertainty/
mismatch/provider-retry/sibling matrix, unchanged. The operation stays
unexported until it reaches the ending.

## State

**Blocked on W32648, unclaimed.** Every provenance, identity, slot and replay
finding is corrected and accepted; the one remaining half has a real gate.

## 2026-08-29 — the ending, built on the door W32648 opened

Reclaimed W32576 at seq 37155. The block cleared: W32648 landed
`authorize_failed_start_cleanup`, which is the first instance of the shape both
endings needed — a manager-owned durable record authorizing a removal that has
no intake receipt behind it.

### What I asked and what I got

Last round I put the question in the thread: two endings need one custody path,
and it should not be built twice — if W32576 should own it instead of W32648,
say so. No answer came. W32648 then built a door shaped for its own record
only. So I built the third sibling here rather than blocking a second time on a
question that had already gone unanswered once, and I am naming the duplication
it creates rather than leaving it to be discovered.

### The ending

`authorize_refused_session_cleanup(store, port, adapter, *, session_ref,
retention_policy_digest)`.

**It takes the SESSION REFERENCE, not the attempt**, and the shape of the
record forces that. The refusal is filed under the session act — attempt,
posture, epoch, provider session — so an ending named by attempt alone would
have to GUESS which session's refusal it was settling on an attempt with more
than one. The attempt is read from the proved session row, never taken as a
free operand.

The order is the one both siblings establish: replay first, then fence at the
authority, then refuse a terminal cleanup, then refuse an uncertain runtime,
then remove the exact attached identity, positively observe absence, settle
every delivered root on that absence and nothing else, end at `retained`, and
release the lane last.

### Why a third sibling and not a widening

`authorize_cleanup`'s whole authorization is an intake receipt. `request_intake`
needs a frozen result; `request_freeze` needs a terminal worker disposition
already recorded. A handshake this manager could not complete produces neither
— and writing a disposition to open that door would be a fabrication AND a lie:
the worker did not cancel, complete or reject a plan. It never got to say
anything. The engine suite asserts that door is still shut rather than only
asserting the new one works.

`authorize_failed_start_cleanup` is the other non-receipt ending and it is not
this one. A start that failed and a handshake that refused are different facts
with different records — the first says a container was created and never ran
the assignment, the second says a container is RUNNING an agent this manager
cannot speak to. M34998/M34999 makes the member sets closed against each other
precisely so one authorization cannot be spent on the other's ending, and a
fourth surface obeying that rule is what the ruling asks for.

So: `documents.CONTRACTS["session.unsupported-version"]` and
`["destroy.refused-session-command"]`, `OciAdapter.destroy_refused_session`
(over the SHARED `_removed` core — two implementations of an ordered teardown
are two orders that agree until they do not),
`intake.refused_session_destroy_operation` and the ending above.

### The record names the runtime it authorizes destroying

W32648's [P0] taught this on the other ending and it transfers exactly: an
authorization and a command built from two independently read facts combine
into one act. So `settle_unsupported_version` now records `runtime_id` — read
from the attempt row under the same write lock that fixes the refusal — and
refuses a session with nothing attached. `_refused_session_record` verifies the
row's KIND, decodes the answer through the journal's own reader, owns it as
`documents.SESSION_UNSUPPORTED_VERSION`, and compares six members against the
world.

### Deliberate duplication, named rather than hidden

`_settle_recordless_cleanup` is `_settle_failed_start_cleanup`'s logic with the
lane reason as an operand. **The two should be one function and I did not merge
them**: W32648 owns that code and it is out for independent review as I write
this, so collapsing them would edit another Work's open round. The merge is a
one-line change once it closes. It is in the source comment, here, and in the
pass-back.

### What the harness caught

Eleven mutations, eleven named cases — `evidence/w32576-mutations-2026-08-29.txt`.

Two guards measured **zero** on the first run and both were my own gaps. The
runtime-naming refusal in `settle_unsupported_version` had no case at all.
Worse, `test_a_record_naming_another_runtime_authorizes_nothing` PASSED with
the comparison removed: it edited the ATTEMPT, which moves the operation
identity with it, so the case was passing on a refusal raised somewhere else
entirely. It edits the RECORD now, and a second case drives the four session
members.

### Registries the new surface had to be added to

`test_dependencies` (the `refusal_record_digest` operand — a third word rather
than a reuse, for the reason the commands are siblings), `test_text_sweep`,
`test_secrets` §13 accounting, and `tools/parallel_test.py` plus its guard.
Each of those caught the omission on its own; none of them was edited to make
something pass.

### The boundary inventory, measured rather than waved at

The new surface put **nineteen** owned-but-never-probed entries into the
inventory, and the suite is red at baseline for other Works' entries — so
"the suite passes" was never a claim available here. The delta is what I can
state: 47 unprobed before, **30 after**, with seventeen of mine probed and the
probes PROVED to arrive (`test_every_declared_probe_reaches_its_named_boundary`
— OK, 411s).

Two of mine remain, and the transcript shows they are not this round's gap:
`_destroyed`, `_destroyed_failed_start` and `_destroyed_refused_session` all
leave exactly the same pair unprobed — the provider ending and its
`lifecycle_state`. One gap in the shared `_provider_ending` shape, inherited by
each sibling that calls it.

**The inventory caught a defect in my own fixture**, which is what that check
exists for. My first `refused_session_world()` left the session's fence answer
naming the shared offer fixtures' authority while `output_world` had re-pointed
the session at its own Work — so all four injected probes were refused by
`request_cancellation` for an authority mismatch and never reached the
observation boundaries they named. A probe that fails for an earlier reason
proves the earlier reason. Four named failures, then the fence answer was
aligned. `evidence/w32576-inventory-2026-08-29.txt`.

## State

**The ending is built and the acceptance's engine half is real.** Passed back
for independent review.

## 2026-08-29 — the record's own meaning, and the duplication removed

Reclaimed W32576 at seq 37523.

### [P1] A record that said `accepted` still authorized destruction

The finding is exact and the gap was mine. `_refused_session_record` proved the
record NAMES this attempt, this runtime and this session — six comparisons —
and then digested `decision`, `category` and `code` **without reading them**.
The contract carries those three members precisely so a later reader can know
what was decided, and this reader was not that. A row whose decision had
become `accepted` kept its exact member set and all six identities, and
authorized a removal.

The verdict is now required as a CLOSED TRIPLE before the digest is computed:
`decision == "unsupported-version"`, `category == "refused"`,
`code == "unsupported-version"`. All three rather than the obvious one —
`refused` is a category shared with every other refusal this manager raises,
and `unsupported-version` in `decision` is a word a record could carry while
its typed pair said something else.

Two more the review named, and both are the refusal's own evidence rather than
its identity. **The wire versions must still be integers and must still
DISAGREE**: an unsupported-version answer is exactly a version that is not the
pinned one, so two integers that agree describe a negotiation that succeeded
and authorize nothing. **The profile must be the session's**, compared against
the persisted row.

That last comparison is against `row["profile_digest"]` and NOT against a
certification lookup, which the review asked for by name and which matters:
reading certification here would make an exact retry stop working the moment a
profile was withdrawn — the effectively-once defect this Work already corrected
once on the recording side, reintroduced at the reading one. A case withdraws
the profile and requires the ending to settle anyway.

### [P2] The duplication, and a premise I did not re-check

`_settle_recordless_cleanup` and `_settle_failed_start_cleanup` are one
function now, with the lane reason as an operand and the failed-start ending
calling it.

The review is right about why it should already have been. I wrote the copy on
the ground that W32648 owned that code and was out for review — and **W32648
closed satisfying at seq 36991, before this Work was claimed at 37155**. I
checked that the BLOCK had cleared and did not check that the REVIEW had, then
stated the stale premise confidently in a source comment, the dossier and the
pass-back. Three places, none of them true when written. The comment now
records what actually happened rather than the reasoning that turned out to be
expired.

### Mutations

**Fifteen mutations, fifteen named cases** —
`evidence/w32576-mutations-2026-08-29.txt`. The four new guards each measured
non-zero on the first run this time.

### Gates

- `test_refused_session_cleanup` **31 OK**; `test_sessions` 86,
  `test_handshake` 33, `test_intake` 74, `test_attempts` 228,
  `test_dependencies` 21, `test_text_sweep` 3, `test_secrets` 90, `test_oci`
  83 — OK;
- the complete serial registry, all ten modules, driven directly.

## State

**Both findings are corrected.** Passed back for independent review.
