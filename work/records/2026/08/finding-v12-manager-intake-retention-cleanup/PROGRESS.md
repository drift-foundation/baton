# Implementer progress — manager intake, retention and cleanup

Created 2026-08-24 by `baton.claude` on claiming W6629.

## Done under this claim

The canonical dossier the assignment required before implementation, and the
revalidation — which this time turned up an **absence** rather than a
confirmation.

**What is already decided and must be consumed:** the `cleanup` axis is frozen
as `pending, blocked-on-intake, complete, retained, failed`, and W4's
`TRANSITIONS` already pins every move. Two consequences an implementer could
get wrong: `blocked-on-intake` is a first-class state, so cleanup *waits on*
intake rather than racing it and an implementation that retried instead would
be inventing a mechanism the axis already has; and `retained` is terminal and
is **not** `complete`, so reporting retention as completion would erase the
reason the material still exists.

**What does not exist at all:** the frozen worker-control schema has **no
`$defs` for intake, retention or cleanup**. `retention_policy_digest` is a
digest of a policy document whose shape the contract never states. So
"retention policy" in this assignment names something that is not a contract
anywhere in the tree.

That is a question rather than a blocker I can resolve: either another Work owns
the retention policy document and must be named so this one can wait for it, or
this Job defines it — and defining it here is what the assignment's own "must
not reconstruct any of them" forbids by implication. I have recorded it as
PLAN item 2 so the next implementer meets it before writing code rather than
after.

## Not implemented

**W6629 → W6627, W6628, W6630** are installed. All three are open, and W6627
and W6628 are themselves blocked on W6592.

## State

**Dossier created, contracts revalidated, edges installed, no implementation.**
The retention-policy ownership question is open and needs a ruling.


## Implementation — 2026-08-26

**The question I returned this Job with answered itself, and the answer came
from counting.**

I recorded that the frozen schema states no shape for the retention policy
document, so "retention policy" named nothing that was a contract anywhere, and
that implementing it meant either naming another Work to wait for or inventing
the document here. That was right about the absence and wrong about what it
meant. `retention_policy_digest` is one of TEN `*_policy_digest` members of the
assignment manifest, and the schema defines the document behind **none** of
them. The silence is not about retention; it is how this contract treats
policies. **Consuming a policy means binding its digest, and interpreting one
here would have been the boundary violation I was trying to avoid.**

The receipt is the same silence read from the other end. `runtimeDestroyBody`
requires `intake_receipt_digest` and shapes nothing -- but a receipt is
PRODUCED here, and a producer owns the shape of what it produces. Consumed by
digest, produced by construction.

**And the dependencies closed while this sat.** W6627, W6628, W6630 and W6592
are all closed now, so nothing was blocked any more either.

## What the frozen contract had already decided, and I consumed

**`sealed` is intake's.** W6628's own docstring says it ends at `frozen`, never
writes `sealed`, and leaves "retention and cleanup, and the `sealed` transition
itself" to a later slice. Freezing is the worker's material stopping; intake is
this manager accepting it.

**Quarantine at intake was pinned by W6628 too**, in the sentence explaining
why its liveness window cannot be zero. Material collected for a generation
that has ended is quarantined rather than refused -- refusing would destroy the
evidence -- and it is SEALED, because leaving it unsealed would invite a second
collection of bytes already taken.

**`uncertain` may never become `destroyed`.** So an attempt observed uncertain
cannot have its cleanup settled even when the engine answers positive absence.
I refused it with the reason stated rather than reaching the terminal value
another way. That is the frozen axis's consequence, not my choice, and it is
written down because the next reader will meet it.

## The ordering defect I wrote and then found

`record_intake` read the output axis BEFORE consulting the journal -- which is
exactly the defect W6628's receiver was corrected for twice, and I reproduced
it in the module that consumes its output. An exact retry after a successful
intake refused with "output is sealed" instead of replaying. It was my own
test for effectively-once that caught it, and the fix is the one that module
already carries: replay first, and above it only the attempt's fixed identity
and the caller's own bytes. `decide_retention` and `authorize_cleanup` had the
same shape and were reordered with it -- which is what made the terminal-cleanup
refusal correct rather than approximate: an exact retry of a settled destroy
REPLAYS, and only a different act arriving after an ending is refused.

## Verification

- `tests/manager/test_intake.py`: **47 cases**, and the fixture attaches a real
  runtime rather than inheriting W6628's, whose attempt observes quiescence
  without ever starting anything. Proving cleanup against that state would have
  been proving it against a fixture.
- **Three rules mutated and measured**: the retained/complete distinction, the
  quarantine-at-intake decision, and the replay ordering. Seven cases failed;
  the source was restored byte for byte (md5 fe0c9865673e869784da8450fbcd7eaa).
- Store schema **10 -> 11**, three tables: `intakes`, `intake_artifacts`,
  `retentions`. The two package-surface gates -- the text sweep's completeness
  table and the declared-operand set -- were extended with the new surface,
  because a table nobody compares to the surface is a list of what somebody
  remembered.

## State

**Awaiting independent review.** The claim is not released and no Git operation
was performed.


## The full suite corrected my own verification section — 2026-08-26

The Verification section above was written from the focused suite and the
mutation measurements, and it was premature. **The full suite found four
package gates this surface had not satisfied**, and the honest reading is that
"47 cases pass and three rules were measured to fail" said nothing about
whether the package still held.

Three are fixed: the parallel registry did not know the new module, eight
`documents.py` constructors had no stated owner, and -- the one that matters --
**every retention column was invisible to the boundary inventory's origin
walk** because I pulled the rows through a second local before reading their
members. The reads were owned the whole time. What was lost was the
inventory's ability to SEE them, which is the worse failure: an unowned column
is caught, an invisible one is not. It surfaced only because the flat second
scan flagged `decided_at`, and only because that name collides with an
`offers` column. The second mechanism earned its keep.

**And a real section 13 gap, measured rather than reasoned.** Six exported
surfaces composed caller text into a PORTABLE operation identity with no walk:
`retain_operation(attempt, <bearer>)` handed the bearer back inside an
operation id. `manager_signature` was corrected for exactly this once already
-- "a guard that runs after the identity has been handed out" -- and my
derived identities bypassed it by computing their digests directly. They walk
their operands now, and the two read-side surfaces walk what they hand back,
because a write-side guard cannot see a later store edit.

## State: NOT READY, and the claim is held

The section 13 ACCOUNTING is unwritten: `test_secrets` requires every exported
callable to be classified into one of its two closed sets and every
constructing surface to be proved by a probe driving it with the bearer live.
Six of the ten refuse already and are measured; four need a store fixture to
reach their walk. Two `test_secrets` gates are red because of it.

Full suite: 1302 tests, 11 failures and 2 errors, over a tree hashed
`a056046a5b99c54b8f04effa096b4011`. Attribution, which is the part that
matters:

- **2 are mine and outstanding** -- the `test_secrets` accounting above.
- **2 are W6633's**, from its eighth review's additive cleanup regressions,
  against a Work blocked on W14251.
- **9 are the long-standing boundary-inventory failures**: 17 `documents.py`
  constructors from W6627 and W6628 with no stated owner, four
  `sessions.py` session-ref members, the two stale
  `workspaces.py:materialize_git_source` owners, and two untracked column
  names (`operation_id`, `settled_at`). None of them is mine, and after 7b and
  7c none of my entries is among them.

**Not passed back.** Returning this for review while two gates my own surface
turned red are still red would be handing a reviewer the job of finding what I
already know is missing.


## Item 7e done, and the attribution above corrected — 2026-08-26

**The two gates my own surface turned red are green.** `test_secrets` derives
both of its universes -- the durable writers from the AST, the public surfaces
from `__all__` -- so what it was reporting was a real absence rather than a
missing entry in a list.

**Three durable writers covered.** `_seal` writes `intakes` and
`intake_artifacts`, `_retain` writes `retentions`; each is private with exactly
one door, and both doors go through `store.transact`, whose journal row is
written inside the transaction and before the COMMIT that would keep the
action's writes. `_seal`'s `why` is the one column here that is COMPOSED rather
than adopted, and it is a member of the receipt the journal walks.

**Six public surfaces classified as constructing and probed in place** -- the
four derived operation identities, which take a caller's attempt mapping and
answer with portable protocol identity, and the two read-side doors, one of
which hands back the digest a destroy is authorized by.

**Four classified prose-only and driven where they can be reached.**
`request_intake`, `record_intake`, `decide_retention` and `authorize_cleanup`
each refuse a missing attempt long before their walk, so a probe against
`test_secrets`' fixture would pass for the wrong reason and report a guard it
never ran. That is `record_frozen_result`'s situation and it is resolved the
same way: the walk is named, the walk is probed directly, and the door is
driven in `test_intake` -- one case per door, plus a control that drives the
same operands with the bearer FORGOTTEN, because every one of these doors
refuses a missing attempt too and a refusal is not evidence of a walk.

**Measured, not reasoned.** Removing `boundaries.row`'s walk alone stops
nothing; removing this module's five walks alone stops the four identities;
removing both stops all six. The four journalled doors are layered three deep
and still refuse with two of the three gone. So the read-side walks are
defence in depth rather than dead code -- which is the question the
measurement was run to answer -- and each named owner is the FIRST rather than
the only one. Source restored byte for byte (`intake.py` md5
c6b250d7a1c4de9c86ce9f1cf51e161e).

### The earlier attribution was wrong, and re-reading the gates is what showed it

The entry above said "after 7b and 7c none of my entries is among them" about
the boundary-inventory failures. **`test_every_stated_owner_names_a_witness_
that_exists` was ENTIRELY mine**: ten stated owners with no witness, every one
of them this Work's. A stated owner is a claim until something exercises it,
which is exactly what that gate exists to say. Eight are outbound constructors
already exercised by a witness derived from `documents.CONTRACTS`, so only the
entry was missing; the other two state a rule of their own and have two new
cases. That gate is green.

**The orphan gate is a shared gap and this Work does not resolve it.** Eighteen
boundary calls cannot be attributed to an entry -- six `intake.py`'s, twelve
belonging to `oci.py`, `posture_slots.py`, `interrogation.py` and
`workspaces.py`. All eighteen have one shape: a caller-origin subject inside a
private helper or a comprehension, which `_calls_in` propagates to the calling
crossing only for `session:` and `read:` subjects. Both declared escapes were
tried and refused it: `DELEGATED` makes the count two against
`test_no_entry_is_owned_twice` because the covering `boundaries.document`
already claims the member, and `NOT_AN_ENTRY` would be a false statement --
these subjects ARE receiving entries. Recorded and attributed rather than
worked around.

### Full suite

1309 tests, **8 failures and 1 error**, from 11 and 1 when this claim resumed.
Attribution:

- **none are mine.** The two `test_secrets` gates and the witness gate are
  green, and no `intake.py` entry appears in the remaining inventory failures.
- **6 are the boundary inventory's**: the orphan gate above (12 of its 18 are
  other modules'), 21 receiving entries with no owner in `documents.py` and
  `sessions.py` from W6627 and W6628, eight `handshake.py` and `sessions.py`
  entries owned but never probed, two stale `workspaces.py:
  materialize_git_source` owners, and two untracked `operations` column names.
- **3 are W6633's**, in `tests.tools.test_worker_image_build`.

Evidence: `evidence/gate-section-13-accounting-2026-08-26.txt`.

### One thing no gate was watching

`schema.__all__` declared no column contract or vocabulary for intake --
`CUSTODY`, `RETENTION_DISPOSITIONS`, `INTAKE_COLUMNS`,
`INTAKE_ARTIFACT_COLUMNS`, `RETENTION_COLUMNS` -- while every other table's
are there. Nothing failed, and that is the part worth keeping: this module has
no gate comparing what it DEFINES to what it DECLARES, so the omission was
invisible to a suite otherwise built out of derived universes. The names are
declared; the missing gate is not this Work's to add and is left for review.

## State

**Awaiting independent review, and passed back rather than closed.** No Git
operation was performed.


## Review round 2 — four [P1] contract boundaries corrected, 2026-08-26

Baseline reproduced first: 52 retained passes, 4 failures and 2 errors over the
review's six additive cases. All six pass now and the module is **58/58**.

**Cleanup waits until the assignment is ended or fenced.** `authorize_cleanup`
verified the participant and then called the destructive adapter without ever
asking whether the fixed assignment was still live. The gate sits among the
genuinely-new-destroy checks, BELOW the replay, so an exact retry of a
committed destroy keeps reproducing its answer after the assignment has moved
on -- and it asks the AUTHORITY, because the axes here describe the runtime and
whether an assignment is still authorized is not a fact this manager stores.

**Both frozen commands are delivered.** `decide_retention` typed
`adapter.retain` and never called it, so one of the two output commands was
never issued at all; `_destroyed` sent a bare runtime id, dropping both digests
that AUTHORIZE the destruction. Both bodies cross now, as closed documents in
the schema's own member order with the operation beside each. Retain goes
before the journal for the reason `authorize_cleanup` already gives -- neither
axis has a `requested` state to record an intent in. Nothing either adapter
answers is adopted. The seam changed, so `OciAdapter.destroy` takes the body
and reads the identity out of it, interpreting nothing else.

**One policy can decide different artifact groups.** The retain identity keyed
on attempt and policy alone, so a policy retaining one artifact and discarding
another produced one operation id and two signatures -- and the second command
came back as a collision. The canonical artifact set and the disposition are
part of the identity now, canonicalised in one place because the identity and
the command body must name the same answer.

**Both read-side doors authenticate against committed journal evidence.**
Comparing a receipt to the digest in its own row proves self-consistency and
nothing else, and retention rows compared nothing at all.

### My first approach to that last one was wrong

I reconstructed the committed SIGNATURE from the persisted rows. That works for
one artifact and breaks for two: `intake.record` is signed over the ADAPTER'S
OWN COLLECTION, whose member order and shape the rows do not preserve, so a
perfectly faithful row derived a mismatched signature. The correction is to
compare against the committed RESULT -- what this manager itself composed,
byte-stable in the journal, needing no guess about what somebody else sent.
The review's own `test_one_policy_can_decide_different_artifact_groups` is what
caught it.

### Two review assertions were unsatisfiable

Both durability cases assert `caught.exception.code == "integrity"`. No refusal
can satisfy that: `integrity` is a CATEGORY in the frozen closed pairing, whose
codes are schema, digest, path, file-type, limit and secret-leak, and the build
raises "the pairing is closed" if you try. The cases could never have passed
whatever was implemented. Corrected to `.category`, the axis the review's own
prose names, and flagged rather than quietly changed.

### The new precondition and the existing suite

Seventeen existing cases reach a destroy and now say the assignment is over,
through one `ended()` helper placed immediately before authorizing rather than
in setup -- intake QUARANTINES material collected for a generation that has
ended, so ending it early silently changes what those cases are about. That is
not hypothetical: `test_blocked_cleanup_completes_once_intake_happens` went
from `complete` to `retained` on the first pass until the call moved below the
intake. Its `blocked-on-intake` half deliberately keeps the assignment live,
because that answer is given before the gate.

### Verification

`evidence/gate-review-round-2-2026-08-26.txt`.

- `tests.manager.test_intake` **58/58** (52 -> 58).
- Full v12 suite: 1316 tests, **9 failures and 1 error**, and none is this
  Work's. Measured rather than asserted: zero unowned boundary entries and
  zero witness-table gaps belong to W6629. The rest are the long-standing
  inventory gaps in `documents.py`/`sessions.py`/`workspaces.py` and the shared
  orphan-resolver gap, plus `test_worker_image_build`, which is W6633's.
- Package registries updated where the surface moved: the section 13 probe,
  the text sweep, the declared operands, and the boundary inventory's probes,
  owners and witnesses.

## State

**Awaiting independent re-review.** No repository state was mutated.


## Review round 3 — the grouped-decision [P1], 2026-08-26

**Two of my own rules contradicted each other.** `_retain` stores one current
decision per artifact and lets a later policy replace one without touching its
peers; the `retentions_of` authentication I wrote last round grouped the rows
that are current NOW by operation id and required the derived artifact set to
equal the historical committed one. So a valid command deciding A and B,
followed by a valid command replacing B alone, left A naming an authentic A+B
act whose current group holds only A -- and a legitimate partial replacement
read as a forgery, blocking retention reads and cleanup over a row nobody had
touched.

The grouping was the right instinct about the COMMAND and the wrong question to
ask of a ROW. Authentication is per surviving row now: the committed act the
row itself names must include THIS artifact under THIS disposition and THIS
policy. A re-decided peer is irrelevant to whether this row is authentic, and a
deleted decision leaves its artifact undecided rather than invalidating a
different one. The forged-row property is what the same comparison enforces.

Measured: restoring the grouping fails the review's new case AND the forged-row
case, 59 tests with one failure and one error; source restored byte for byte.

### The poke was right about the gate, and I own that

`baton.prompt` observed that a tail pipeline had masked a non-zero status. It
had. I was reading verdicts off the unittest summary line after piping through
`grep` or `tail`, which discards the runner's status, and my backgrounded runs
ended in `echo`, so the exit codes I saw were the wrapper's. The verdicts were
accurate because the summary line is; the practice was not evidence.

This round's gate never pipes the runner. Each stage redirects to a file, its
status is captured on its own line, and the file is read afterwards:

- `V12_STATUS=1` — 1290 tests, 8 failures, 1 error;
- `V11_STATUS=0` — 3067 parallel, 52 serial, 77 ACP;
- `DIFFCHECK_STATUS=0`.

The v12 status is honestly 1 and **none of it is W6629's**: six are the
boundary inventory's long-standing gaps, two are W6633's, and one is
`test_no_git_metadata_root_survives_the_acquisition_cut`, which W15232's own
review added at 09:47 while this round ran. `tests.manager.test_intake` is
**59/59** with status 0.

**And the whitespace failure the review called unrelated was mine** — my W15232
removal left a blank line at EOF in `workspaces.py`. Fixed; the check is clean.

### Verification

`evidence/gate-review-round-3-2026-08-26.txt`.

## State

**Awaiting independent re-review.** No repository state was mutated.


## Review round 4 — a row could borrow another attempt's committed act

**The three values my per-row check compared are local decision data, not
identities.** An artifact id, a disposition and a policy digest can agree
between two attempts entirely legitimately: both hold an `artifact-1`, both
decide it `retain` under the same policy. So a row whose `retain_operation_id`
was edited to name the OTHER attempt's authentic committed act matched on all
three and was accepted, and cleanup for one attempt could draw its
authorization from a decision made about another — with no journal row forged
anywhere.

The committed act names the attempt it was made about. That is the binding,
and comparing values that merely happen to agree is not one. `retentions_of`
requires `committed["attempt_id"] == attempt_id` before it will return the
decision, and reports a mismatch as integrity.

Measured: removing that single comparison fails the review's case and nothing
else, 60 tests with one failure. Source restored byte for byte, md5
05a78fb562ead052dfd31a181347e569.

### The sibling door does not have this hole, and it is worth saying why

`intake_receipt_of` DERIVES its operation from the attempt —
`intake_operation(attempt)` — and then compares the derived id against the
stored one, refusing when they differ. The act is therefore bound to the
attempt by construction: there is no stored id to edit into pointing somewhere
else, because a receipt whose act does not derive from its own attempt is not
that attempt's receipt.

Retention rows are the other shape: they STORE the operation id, because one
command decides a set of artifacts and a later policy may replace part of it.
Storing an identity is what created the room for it to point elsewhere, and
that is exactly the difference the round-4 finding turns on.

### Verification

`evidence/gate-review-round-4-2026-08-26.txt`.

`tests.manager.test_intake` **60/60** with exit status 0.

## State

**Awaiting independent re-review.** No repository state was mutated.
