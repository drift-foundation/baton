# Progress

Not started. W71459 currently owns overlapping v11 integrator-policy paths;
this leaf must not change them until that ownership has ended and its reviewed
ruling is available.

## 2026-09-05 — baton.claude — the W71918 revalidation gate (PLAN item 2)

PLAN item 2 is the implementation entry gate and it is the whole of this turn.
W71918 closed satisfying and is committed at `b37446a`, so this reads accepted
code rather than a record's prose.

**No material mismatch on any of the five named axes.** Three are satisfied
more strongly than this contract assumed. No production byte was written.

**Three clarifications are returned**, all of them places where this record's
text reads as one thing and the accepted provider makes it two. They are
narrow, and none of them invalidates the ownership split, the ordering model or
the crash semantics.

### What W71918 delivered, read from the accepted tree

At `b37446a`: `baton_v12/checkpoint_profiles.py`,
`worker_manager/review_cycles.py`, schema, attempts, source_boundary and
workspaces changes, and `REVIEW-CYCLES.md`. Public surface reused here:
`create_line`, `grant_writer`, `record_progress`, `freeze_checkpoint`,
`attach_review`, `record_verdict`, `integration_checkpoint`,
`audit_checkpoint`, `line_status`, `checkpoint_of`, `line_of`, `writer_of`,
`writer_boundary`, `review_boundary`; and `GitCheckpointProfile` with
`checkpoint_ref`, `status_vector`, `tree_vector`, `diff_vector`,
`update_ref_vector`.

### Axis by axis

**1. Checkpoint identity — satisfied.** A line is keyed `(authority_uuid,
work_id)` under the workspace store's reserved `.baton-review-lines/`
namespace; an assignment id cannot select that namespace and ordinary attempt
cleanup cannot remove it. Revisions increment on each freeze and every older
checkpoint stays resolvable — `audit_checkpoint` re-resolves one with
`current=False`, so it does not require the line's current HEAD.

**2. Verdict binding — satisfied, and wider than this record asked for.**
`CHECKPOINT_VERDICT_COLUMNS` binds line, checkpoint, attachment,
`authority_uuid`, `work_id`, `review_assignment_generation`, reviewer worker /
participant / principal, disposition, `checkpoint_digest`, `revision`,
`base_object`, `head_object`, `tree_object` and `path_set_digest`. It adds two
this record did not name: the frozen review RESULT with its manifest digest,
and the committed review FENCE, each with its own digest. A verdict also
requires the reviewer's runtime to be positively quiescent, its disposition
`completed`, its output frozen and its verification `passed`.

**3. Immutable custody — satisfied, and stronger than assumed.** This record's
own open question was whether a checkpoint could be kept immutable while the
same line later becomes writable. The answer is mechanical: freezing requires
the writer attempt's runtime to be positively quiescent, atomically revokes the
database grant, fences that assignment generation through its Authority
session, and previously minted writer boundaries recheck the live grant at
adoption AND at mount composition — so revocation invalidates capabilities
already in memory. No writable mount can coexist with read-only review. Review
admission also refuses a reviewer sharing worker, participant or principal with
the checkpoint's producer.

**4. Path-set evidence — satisfied.** The profile freezes only a clean
committed worktree and records exact base, head, tree, sorted path set,
path-set digest and retained reference under
`refs/baton/checkpoints/<line-id>/<revision>`. That retained ref is the
concrete answer to this record's abstract "durable object transport", and the
implementation should name it as such rather than inventing a second one.

**5. Integration eligibility — satisfied.** Only an `accepted` verdict creates
an `integration_eligibility` row, and `integration_checkpoint` re-proves the
whole chain rather than trusting it: line accepted, checkpoint frozen and
current, every verdict operand equal to the checkpoint's own evidence, both
result and fence digests recomputed, the attachment ended and bound to the
completed review attempt, and the fence still current.

### The three clarifications returned

**A. There are TWO eligibility surfaces, and the cross-binding between them is
unstated.** This record's eligibility bullet reads as one check requiring
`verification=passed`, `review=accepted` and `approval=approved`. In the
accepted provider those are different things in different places:
`review_cycles` proves CUSTODY eligibility and never reads an Authority
proposal, verification or approval receipt — its `port` is used only to fence
an assignment generation. Authority owns the policy receipts, exactly as this
record's ownership split says.

So an entry is eligible only if BOTH surfaces pass AND they are talking about
the same bytes. That cross-binding — the proposal digest Authority's receipts
name must be the checkpoint digest `integration_checkpoint` returned — is the
one operand nothing currently requires, and it is precisely the sort of thing
that gets assumed rather than checked. It should be a stated eligibility
operand before code depends on it.

**B. Eligibility is REVOCABLE, and the queue has no state for that.**
`integration_checkpoint` requires the accepted checkpoint to still be the
line's `current_checkpoint_id` with the line `accepted`. A `changes-requested`
verdict or any later freeze therefore makes a previously eligible entry
permanently ineligible.

That is correct behaviour — it is this record's own "advancing the line never
transfers an earlier verdict to the later checkpoint", enforced rather than
documented. But this record's queue holds an entry between enqueue and lease,
and its terminal/recovery states do not name the case where an entry that was
eligible at enqueue can no longer be leased. The queue needs an explicit
revoked/superseded state, and the "re-read and validate the immutable
eligibility snapshot" step under the live lease needs to say what happens when
that revalidation refuses for this reason rather than for drift.

**C. The line identity is NOT the target identity.** W71918 keys a line by
`(authority_uuid, work_id)`. This record requires a `canonical_target_id`
shared by every producer that can reach the same checkout, "including distinct
Authorities if the deployment permits them to share that checkout". Those are
orthogonal on purpose — one names what is being integrated, the other names
what it is integrated INTO — but they are adjacent enough to be conflated, and
a queue keyed off the line identity would silently give each Authority its own
lock, which is the exact failure this record's queue-key acceptance test
exists to catch. The contract should say plainly that the target identity is
never derived from the line identity.

### Disposition

Stopped at the gate with no production edit, as PLAN item 2 requires for an
affected contract. The affected part is narrow: the eligibility model
(clarifications A and B) and one sentence of the identity model (C). Everything
else in the reviewed contract stands against the accepted provider — the
ownership split, the enqueue/rank/lease/fence model, the execution order, the
crash semantics, and the test-change authority.

## 2026-09-05 — baton.claude — the seam decision, pinned before code (PLAN item 3)

Implementation is released and the corrected plan is the one I am building to.
This turn surveyed the two eligibility surfaces against the accepted tree and
resolved the one thing this record left OPEN, because AGENTS.md is explicit
that a confirmed decision is written into the finding before implementation
depends on it — and this one changes what the first line of code may reach for.

### What the survey found, and why it is a decision rather than a detail

The Authority `Session` exposes `proposal`, `receipt`, `receipts`,
`canonical_target` and `integration_attempts` as reads and `integrate` as a
transition. `AuthorityPort` — the participant-bound face the Job Manager
actually composes — exposes none of them: `project_work`, `assignment_of`,
`cancel`, `slot_holder`, `claim`, `publish_answer`, `settle_operation`,
`claim_signature`, and nothing else.

So the POLICY surface this Work must cross-bind against, and the integration
receipt it must write after a real import, are not reachable through the seam
the generic manager holds. Reaching them would have meant widening
`AuthorityPort` — which W71877's item 2e already refused to do for a read it
wanted, on the ground that the participant-bound session boundary is not a
convenience surface. Had I started coding from the contract's prose I would
have discovered that at the first call and been tempted to widen it.

`FINDING.md` now carries the ruling: **one separately injected trusted
integration profile**, on the pattern W71918 established for checkpoints,
holding the `baton.merge` import, the Authority policy reads and the
`integrate` transition together — because splitting them would let a
deployment supply a real Authority face with no importer, or an importer with a
stub Authority, and the whole point is that the receipt follows the bytes.
Possession of a live lease with its monotonic fence is an operand of every
profile call, so a bypass has no fence to present.

### The shape the next slice implements

Recorded here rather than in the finding because it is design, not decision,
and review binds bytes rather than intentions:

- `job_manager/integration.py`, mirroring how `scheduler.py` was added, with
  the Job store advancing 4 → 5 in one transactional migration — and the
  schema-3 validation W71877 added means the 4 → 5 step will be held to
  proving the whole prior shape the same way.
- `integration_targets` keyed by the `canonical_target_id` that trusted target
  configuration supplies, never derived from line, Authority, Work, proposal,
  checkpoint or target revision; `integration_entries` immutable and
  Authority-namespaced, carrying BOTH surfaces' identities and their
  differently defined digests side by side — `checkpoint_digest` beside
  `candidate_digest` and `proposal_manifest_digest`, never equated;
  `integration_leases` with a unique live-target constraint and a monotonic
  fence; and an import-boundary journal for restart reconciliation.
- Two refusal dispositions, as the targeted review fixed them: an ordinary
  policy, scope or target failure before mutation terminally refuses that
  immutable entry, while an integrity, digest or ambiguous-custody failure
  blocks the target and retains the fenced account. Neither is called
  revocation — the targeted review corrected my earlier claim that an accepted
  checkpoint can be revoked by ordinary line advancement, and it cannot: only
  `changes-requested` reaches `correction-ready` and it creates no eligibility
  row, while `accepted` is terminal.

### State

No production byte written this turn; `git status` over `v12/` is empty. The
decision the record asked implementation to record is recorded, so the next
slice builds against a pinned ruling rather than discovering it at the first
call.

## 2026-09-05 — baton.claude — two corrections to my own ruling, and one I cannot make

The seam review found three things in the section I pinned last turn. Two were
mine to correct and are corrected in place; the third is an owner ruling and is
written up with both options and their real costs rather than chosen.

### Corrected: colocation is not atomicity [P1]

I wrote that one capability makes "read the policy, import, then record"
INDIVISIBLE. That is false, and the sentence is superseded in place rather than
quietly edited, because a reader who took it at face value would build without
the reconciliation the three domains actually require.

One object is one WIRING unit: it removes a class of misconfiguration — a real
Authority face with no importer, an importer with a stub Authority — and that
argument stands. It creates no atomicity across the scheduler's SQLite, the
target filesystem and the Authority's SQLite. The explicit durable cutpoints
between preflight, import, verification and receipt completion, and the restart
reconciliation over them, remain obligations of this record; the profile's
shape discharges none of them.

### Corrected: a fence value is not a live grant [P1]

I wrote that possession of a live lease is an operand of every profile call.
An operand is a VALUE and a value can be replayed — which is precisely the
mistake W71918 already corrected for its writer grant, and precisely why its
previously minted boundaries recheck the LIVE grant at adoption and again at
mount composition. I had that example in front of me in the same revalidation
and still wrote the weaker rule.

The rule is now the same one: before any canonical mutation and again before
Authority completion, the target store's owner re-evaluates the live grant
against the exact target, entry, lease and fence and refuses if it is not still
held; uncertain work prevents lease release rather than ending it. The
integration Session is also stated as separate and narrow — `AuthorityPort`
stays exactly as it is, and the profile validates every proposal and receipt
document it is handed rather than trusting the shape.

### Returned: the lock domain [P0]

This one is not mine to decide, and it is a real contradiction between two
accepted rulings rather than an implementation choice.

W83781 binds each `JobStore` immutably to one Authority UUID. The integration
relations were going to live there, so a live-target unique index in that
database is unique only WITHIN one Authority — two Authorities configured for
one canonical checkout would each hold their own store, grant their own lease,
and import into one working tree. This record's own identity model says every
producer reaching the same checkout maps to one queue identity "including
distinct Authorities", and its acceptance clause requires a queue-key test
proving exactly that. Both rulings are live and they disagree.

`FINDING.md` now carries both ways out with their costs. **A**, the reviewer's
recommendation: a target-global coordinator keyed by `canonical_target_id`
alone, satisfying the clause as written and costing a third durability domain
with its own schema, migration, open/adopt rules and reconciliation — which
makes the cutpoints the [P1] above insists on harder rather than easier.
**B**: one Authority per target, mechanically enforced at configuration, costing
nothing structurally and superseding the cross-Authority sentence and its
acceptance clause outright.

And it names the third option that must not happen: building A's contract
against B's mechanism, leaving the cross-Authority sentence standing while the
lock sits in an Authority-bound store. That is the state the review found, and
it is the one shape neither ruling permits — the acceptance test would be
unimplementable and a deployment reading the contract would believe it was
protected.

I recorded no recommendation of my own beyond the reviewer's. The choice is
between accepting a new coordination domain and narrowing the deployment
model; both are decisions about what the product is. Nothing in the code
depends on the answer yet, so whichever is ruled starts from the same place.

### State

Still no production byte; `git status` over `v12/` is empty. Implementation
resumes once the lock domain is ruled — everything else in the seam decision
now stands as corrected.

## 2026-09-05 — baton.claude — PLAN item 3 implemented: the target-global coordinator

The owner ruled **A**, so this turn built it. Three production modules and one
test module, all new; nothing existing was edited except one registry line.

```
v12/python/src/baton_v12/integration/__init__.py     21
v12/python/src/baton_v12/integration/schema.py      237
v12/python/src/baton_v12/integration/store.py       276
v12/python/src/baton_v12/integration/queue.py       653
v12/python/tests/integration/__init__.py              0
v12/python/tests/integration/fixtures.py             89
v12/python/tests/integration/test_coordinator.py    628
v12/python/tools/parallel_test.py            (+1 entry)
```

The working tree over `v12/` holds exactly those three paths and nothing else.

### What the seam owns, and what it refuses to own

`IntegrationStore` is the third durability domain the ruling accepted. It is
`JobStore`'s mechanism — `transact` as the atomic boundary, `replay` as what
makes a repeat return the first outcome — over a database that records **no
Authority binding at all**. That absence is the whole point and is the one
place the class deliberately differs from its sibling rather than resembling
it: W83781 binds a Job store to one Authority UUID, so a live-target index
there is unique only within one Authority, and binding this store would put
the same defect back one layer down.

`queue.py` decides two things and refuses a third. It decides WHICH entry a
target integrates next (rank, allocated inside the enqueue transaction) and
WHO may integrate it (one live lease, decided by a partial unique index rather
than by a caller's read-then-write). It decides **nothing** about eligibility:
`enqueue` takes an already-proved account as one closed document and stores it
as evidence, because building that account is item 4's and it sits above this
seam. No Git, no filesystem and no Authority session reaches the module.

The 17-operand entry retains both digest families side by side and equates
neither, as the targeted review ruled.

### Four things I got wrong first and measured rather than argued

**The fenced verbs demanded a live grant before they consulted the journal.**
That is right for a first attempt and fatal for a repeat: releasing a lease
ends it, so a caller retrying after a lost answer met its own completed work
and was told "the grant is no longer live". `_recorded` now asks the journal
first in `release_lease`, `settle_integrated`, `refuse_entry` and
`abandon_lease` — an exact repeat replays, and only a request the journal has
never seen goes on to prove its grant. This is the same shape W71917's
recovery seam was corrected for, and I reproduced it anyway.

**`activate_target`'s "already activated under another configuration" refusal
was unreachable.** With the operation identity keyed on the target alone, a
changed document is a signature mismatch on one id and comes back as the
generic `operation-collision` — so the specific check below it could never
run and a caller was told nothing about targets. The identity now carries the
document digest, which makes two configurations two operations and puts the
refusal back where it can speak. Found by writing the test that asserted the
pair, not by reading the code.

**`enqueue` left its uniqueness to the index.** A second entry id for one
candidate would have arrived as a raw `sqlite3.IntegrityError` escaping the
boundary as something no caller can act on. It is now an explicit denial
naming the entry and rank the candidate already holds.

**`refuse_entry` would end anybody's live lease.** It is the verb that hands
the target to the next caller, so it now proves the live grant when the entry
is leased, and re-reads under the write lock in case the entry was leased
between the proof and the transaction. `block_target` deliberately does NOT
demand a grant, and the asymmetry is the safety argument rather than an
oversight: blocking only ever removes permission, and demanding a grant for it
would leave exactly one state — a live lease whose holder is gone — that
nobody could ever act on. That ordering is what makes `abandon_lease`
implementable: block first (available to anyone), then end the grant the
recovery accounts for, and the target stays blocked because repair is explicit.

`boundaries` has no `count`; `generation` is the existing owner of "a whole
number, not a bool, not text that looks like one", and the schema calls the
fence exactly what it is — the target's monotonic lease generation. I used it
rather than minting a second owner for one property in a module this record
does not own.

### Verification

55 focused cases, all passing. They cover target activation and the key never
being derived from any narrower identity, rank allocation and enqueue replay,
the one-candidate-one-place denial, both digest families retained, the
one-live-lease race driven by two real connections to one database file,
monotonic fencing, `live_grant` refused for a stale fence / another entry /
another target / a released lease / a blocked target, both settlement
cutpoints, the two refusals as distinct dispositions, nothing expiring on its
own, the explicit recovery, and the store's adopt rules.

`TwoAuthoritiesContendOnOneLock` is the acceptance clause this record names:
two distinct Authority UUIDs enqueue into one canonical target, share one
ordered queue, and contend on one lease.

Full suite: 4002 tests, 10 failures. **The failures are the same failures
without my bytes, and I measured that rather than counting names.** Moving
both new directories out of the tree and re-running the two suites that fail
statically produced a byte-identical failure list — the diff of the sorted
`FAIL:`/`ERROR:` lines is empty. Those six are `test_boundary_inventory` (5)
and `tests.authority.test_catalog` (1); the inventory's failing sets name only
`attempts.py`, `handshake.py`, `intake.py`, `sessions.py`, `workspaces.py` and
`exchange.py` entries — its `PACKAGE` is `worker_manager`, which my package is
not in. The other four are Docker-engine residue: their contents name
`baton-w6633-test-*` and `baton-runtime.start-*` objects left in the local
engine by other suites, and no byte of mine starts a container, builds an
image or reaches the daemon.

The registry gate passes: 83 modules registered, 83 discovered. The
whitespace gate is clean and no new file carries trailing whitespace.

### Two obligations I am NOT claiming to have discharged

`test_boundary_inventory` walks `worker_manager` only, so this new package's
receiving entries have **no inventory** — no owner table, no probe, no witness.
That gate belongs to another record and I did not expand it; whether item 7's
matrix should carry an equivalent for `integration` is a real question and I
am raising it rather than answering it quietly.

And this is item 3 alone. Items 3b and 5–6 — the closed integration boundary,
the Git-aware profile, the real import, the Authority receipt and the restart
reconciliation over the durable cutpoints — are untouched. `live_grant` exists
and is proved at both cutpoints; what it guards has not been built.

## 2026-09-06 — baton.claude — the item 3 review's five findings, corrected

Review `review-2026-09-06T02-15-48Z.md` requested changes: two [P0] and three
[P1]. All five are corrected, each one driven as a refusal by a focused case,
and the reviewer's own reproduction is re-run below. Scope over `v12/` is still
the same three paths — the new package, the new suite, and the one registry
entry.

### [P0] An unresolved lease could be released, and my suite blessed it

The finding is right and it is the worst kind: `release_lease` proved only that
the lease was live, so a holder could end its grant with the entry still
`leased`, and the next queued entry was offered while the first still recorded
unresolved canonical work. The serialization this whole store exists for was
one call away from being undone.

What I should sit with is the second half of the finding.
`AGrantIsProvedLiveWhereItIsUsed.test_a_released_lease_does_not_pass` DROVE
that transition and asserted only that the old grant had stopped being live.
The case passed, so the hole read as covered. A test that performs an unsafe
transition in its setup and then asserts something true about the aftermath is
not neutral — it is a standing statement that the transition is allowed. I
wrote it while thinking about grants and never asked what the entry was doing.

The correction: an ordinary release now ends only a lease whose entry is
`integrated`, and the ending it records must agree. The other two endings are
FUSED to the transition that makes them true — `refuse_entry` ends the lease in
the same transaction that refuses the entry, so at no instant is the lease over
and the entry unresolved.

`NoLeaseEndsOverUnresolvedWork` now asserts the negatives the reviewer asked
for: the refused release moves no entry state, no lease state, no target fence,
and the next entry is still not offered afterwards.

**One exception, named rather than left to be found.** `abandon_lease` does end
a live lease whose entry is `held`, which the finding's literal wording
excludes. It is the recovery path and I did not narrow it, because what makes
ending a lease safe is not the entry's state but the TARGET's: abandoning is
reachable only on a blocked target, and a blocked target offers nothing to
anybody. `test_abandoning_does_not_reopen_the_target` is the evidence — after
the recovery the target is still blocked and the next grant is refused. If the
reviewer reads the rule as absolute rather than as a rule about serialization
advancing, this is the place to say so.

### [P0] A block that was not about the live grant

Also right, and the cross-wiring was worse than it looked: a block naming entry
B while entry A held the lease left A `leased`, B `held`, and let the recovery
end A's grant against B's block.

`block_target` now takes the whole grant as operands — target, entry, lease,
fence — and refuses unless a live lease with exactly those values exists. The
account it persists (new `targets.blocked_account`) names that entry, lease,
fence, integrator and attempt, and `abandon_lease` cross-checks THAT account
instead of re-deriving a plausible one from the target state.

It still does not demand that the caller HOLD the grant, and that is the same
safety argument as before rather than a leftover: a crashed holder cannot
present its own grant, so a block gated on holding one would leave a target
whose holder is gone permanently unblockable and unrecoverable. Naming the
grant exactly is what closes the cross-wire; holding it is what would close the
recovery path.

A second block is refused too, since it would replace the account the recovery
checks against. `ABlockIsAboutOneExactGrant` covers cross-entry, cross-lease,
stale fence, cross-target, repeated block, replay, and a recovery aimed at a
lease no block was about — each asserting the original account is unchanged.

The no-live-lease queued block is now REFUSED rather than defined. Item 3 has
no unreconcilable account without an import, and an unusable candidate is
`refuse_entry`'s; inventing a second blocking transition to keep a call
signature would have been the wrong direction.

### [P1] Redundant evidence nothing compared

The narrow fix was to validate the stored `eligibility` document against the
seventeen columns on every read. I did the wide one instead and want the
disagreement about it on the record: **the second copy is gone.** The account
is assembled from the columns at the read, so a row and its account cannot name
different proposals — the state the reviewer demonstrated is now
unrepresentable rather than caught. This is the rule `boundaries.generation`
already states about bounds: a second owner of one fact is the thing to remove,
not the thing to police. The removal is lossless because the account is closed
over exactly those members.

The redundancy that genuinely must stay is now proved where it is read:
`target_of` refuses a document whose schema, identity or digest disagrees with
its row, `lease_of` refuses a lease holding an entry queued against another
target, and a settlement is validated against the shape its state requires.

### [P1] Adoption did not validate the schema it relies on

Correct, and the specific case is the sharp one: dropping
`leases_one_live_per_target` and reopening was accepted, and that partial index
is not an optimization — it IS the one-live-lease exclusion.

`_adopt` now compares the complete owned shape: every table and index, its
columns, constraints, foreign keys and index predicates. The expectation is
MEASURED by running `SCHEMA` into a throwaway database and reading back what
SQLite stored, so it cannot drift from what `_initialize` writes the way a
hand-written expectation would. Missing objects, unexpected objects, altered
definitions and unexpected metadata keys are each refused with nothing changed.

Three normalizations (comments, identifier quoting, punctuation spacing) let a
differently-SPELLED identical definition through; case is deliberately NOT
normalized, because folding it would make `IN ('open')` and `IN ('OPEN')`
compare equal.

One thing this uncovered: `_statements` split on every `;`, so a semicolon
inside a schema comment cut a `CREATE TABLE` in half and the store failed to
build at all. It now splits where `sqlite3.complete_statement` says a statement
ends.

### [P1] The Authority namespace accepted anything

`enqueue` owned `authority_uuid` as generic text. It now applies the Authority
package's own predicate at admission and again on every persisted read, with
only the exception type translated — the same reuse, for the same stated
reasons, that `job_manager.schema.check_authority` performs. A third spelling
of "32 lowercase hex" would be exactly the drift that stays invisible until two
components disagree about one identity. It proves syntax and nothing else, and
says so.

### The open inventory question, answered

The review closed the question I had left open. I took the second of the two
options it offered — equivalent exhaustive focused cases rather than a
dedicated receiving-boundary inventory — because `test_boundary_inventory` is a
static AST walk owned by another record over `worker_manager`, and expanding
its universe is that record's change to make, not this one's. What this package
now has instead: `PersistedEvidenceIsProvedWhereItIsREAD` for documents and
redundant relationships, `TheStoreIsAdoptedByOwnershipRatherThanResemblance`
for the owned schema, and identity cases at both the admission and the read.
If the reviewer wants the inventory itself extended, that is a coordination
question between the two records rather than something I should do quietly.

### Verification

85 focused cases, all passing (55 before).

The reviewer's five reproductions, re-driven with the operands the corrected
signatures require, at `/tmp/w71878-item3-recheck.py`:

```text
premature-release   REFUSED policy.denied  states ['leased','queued'] live fence 1
cross-wired-block   REFUSED policy.denied  states ['leased','queued'] target open
cross-wired-abandon REFUSED policy.denied
split-evidence      proposal-other proposal-other  (one owner: they cannot differ)
split-target        REFUSED integrity.schema
malformed-authority REFUSED integrity.schema  entries []
missing-safety-index REFUSED integrity.schema  "Nothing was changed"
```

The reviewer's script as written no longer runs: `release_lease`,
`settle_integrated`, `refuse_entry` and `block_target` all take more operands
now, so it stops at a `TypeError` rather than a refusal. That is a signature
break in a package nothing else consumes yet, and it is deliberate — the
caller states the grant it believes it holds instead of being told what it
holds — but it is a break and the re-run above is the adapted script, not
theirs.

Full suite: 4002 tests before, 4032 now, 10 failures, and the failure list is
byte-identical to the one recorded yesterday: five `test_boundary_inventory`,
one `test_catalog`, and four Docker-engine residue cases naming other suites'
objects. Registry gate passes; no new file carries trailing whitespace.

## 2026-09-06 — baton.claude — the re-review's three findings, corrected

`review-2026-09-06T02-39-45Z.md` confirmed the two [P0] serialization defects
fixed and requested changes on three more. All three are corrected. 110 focused
cases (86 before, 55 at the first hand-off); scope over `v12/` is still the same
three paths.

### [P1] The blocked account was shaped but not cross-bound

Right, and the half that matters is the half I missed. The write transition
built the relationship correctly, so I proved the account's member TYPES on
read and stopped — which means a RESTART believed a contradictory one. The
re-review changed only the stored entry id to the target's still-queued entry
and `target_of` handed it back; changed only the account's reason and watched
`blocked_reason` and `blocked_account.reason` come back disagreeing.

That is worse than storing nothing, because `abandon_lease` checks against this
account: evidence that names the wrong grant makes the recovery end the wrong
one, which is exactly the [P0] the previous round closed, re-entered through
the read path. `_block_account` had an unused `canonical_target_id` parameter,
which is a fair description of how far the first correction actually reached.

`target_of` now adopts the whole thing as ONE relationship: the account's reason
must equal the row's, its entry must exist on this target, be `held`, and carry
the same reason and detail in its settlement; its lease must exist on this
target and agree on entry, fence, integrator and attempt; and that lease must
be live or properly abandoned, with its recovery accounting for the same
attempt. Eleven corruption cases in `ABlockedTargetIsONERELATIONSHIP` drive one
member each and assert the target is refused rather than returned.

### [P1] Settlement and ending variants were not semantically owned

Also right. I closed the member SETS and left the shapes open — the same defect
`boundaries.alternative` records against itself in its own docstring, which I
had read while building this. A `held` settlement with an integer reason came
back intact, and an `abandoned` lease whose ending had been changed to
`{"outcome": "integrated"}` read as valid.

There are now two owners. `_settlement` takes the entry state and proves the
variant: imported paths are a collection of durable text, a verification is a
document, a refusal or held reason is text with a document detail. `_ending`
uses `boundaries.alternative` with `outcome` as the discriminator over three
closed variants — `integrated`, `entry-refused`, `abandoned` — and then proves
the outcome is one the lease's STATE may carry, so a released lease cannot end
abandoned and an abandoned one cannot end integrated. An abandonment's recovery
is cross-checked against the lease's own attempt, and again against the blocked
account.

Each helper runs at the caller's door and at the persisted read, because a
document validated on the way in and trusted on the way out is one lock on two
doors — the shape `boundaries.sealed` records having been caught at twice.

I did NOT name a verification account's members. What it must contain is item
5's, which owns the bounded final-byte, mode and Work verification that
produces it; naming them here would be this record deciding another one's
contract. A document, and this seam says no more.

### [P1] Two mutation boundaries discarded the owned snapshot

The sharpest of the three, and the least defensible. `settle_integrated` and
`refuse_entry` called `boundaries.document(...)` and threw the answer away,
then signed and persisted the caller's own dictionary. `own`'s docstring says
in as many words that it snapshots every member exactly once so that "the value
we validated is the value we used" is a fact rather than an intention — and
discarding its return gives that fact away while leaving the call site looking
correct.

The re-review's demonstration used the injected clock, which is a capability
this store already accepts, so the seam is deterministic rather than a race: one
call validated and journalled `['reviewed.py']`, stored and returned
`['other.py']`, and the exact retry of the reviewed value replayed the other
one.

Both now assign and use the owned snapshot. I audited every public document
operand in the package rather than fixing the two that were named, and recorded
the result in the module docstring: the target, the eligibility account, both
settlements, the block account, the lease ending and the recovery all bind the
boundary's answer. The nested checks inside the helpers — a settlement's
`verification`, an ending's `detail` — deliberately do not rebind, because they
are members of an already-owned snapshot rather than second doors.

`TheValueValidatedIsTheValueUsed` drives the clock mutation against
`settle_integrated`, `refuse_entry` and `block_target`, and asserts both the
stored account and the journalled signature are the validated ones.

### Verification

110 focused cases, all passing.

The re-review's reproduction, adapted, at
`/tmp/w71878-item3-rereview-recheck.py`:

```text
cross-wired-persisted-block REFUSED  entry-2 is queued rather than held
split-block-reason          REFUSED  blocked 'integrity', account says 'other-reason'
split-block-detail          REFUSED  block and settlement account differently
split-block-fence           REFUSED  block and lease disagree about the grant
abandoned-as-integrated     REFUSED  a lease recorded 'abandoned' ends abandoned
cross-attempt-recovery      REFUSED  granted to attempt-1, recovery says attempt-9
non-text-held-reason        REFUSED  a settlement's reason is durable text
validated-a-stored-b        ['reviewed.py'] replay ['reviewed.py']
```

The first review's five reproductions still refuse
(`/tmp/w71878-item3-recheck.py`). As with that round, the reviewer's own script
no longer runs to completion: it checks a refusal and then reads the same value
again unguarded, and the second read now raises — which is the correction
working rather than a new fault.

Full suite: 4032 tests before this round, 4057 now, 10 failures, and the failure
list is byte-identical to the recorded baseline for the third consecutive round
— five `test_boundary_inventory`, one `test_catalog`, four Docker-engine
residue cases naming other suites' objects. Registry gate passes; no new file
carries trailing whitespace.

### Where this leaves the slice

Every finding from both reviews is closed. Two rounds have now found defects
whose common shape is worth naming for whoever picks up 3b: both [P0]s and two
of these three [P1]s were places where the WRITE transition was correct and the
READ, the retry or the restart trusted what the write had left behind. The
store is a receiving domain on the way out as much as on the way in, and this
package needed telling three separate times.

## 2026-09-06 — baton.claude — the third review's [P0]: one relationship pass

`review-2026-09-06T02-53-42Z.md` confirmed the previous round's three
corrections and found a [P0] underneath them. It is corrected. 117 focused
cases (110 before); the same three paths over `v12/`.

### The finding, and what it says about my last two rounds

I validated the blocked relationship only when `targets.blocked_account` was
PRESENT, and let each public read prove its own half. So setting the target row
back to the perfectly legal `open` shape — `state='open'`, both block columns
null — left a `held` entry and an `abandoned` lease that every door accepted
separately, and `grant_lease` then leased the next queued entry past unresolved
held work.

That is the first review's [P0] again, arriving through restart evidence
instead of through a verb. **Validating a relationship only when one side
ADMITS to it lets the corrupted absence choose the permissive branch** — which
is the sentence I should have written for myself two rounds ago, because both
earlier corrections have exactly this shape: the write was right, and the read
believed whatever the write appeared to have left.

### The correction

Every public read of this store now goes through ONE pass. `_relationship`
adopts the target row, all its entries and all its leases together, and
`_prove` checks the whole graph before anything is returned. `target_of`,
`entries_of`, `lease_of` and the internal `_entry` are projections of that pass
rather than four readers with four opinions, and `grant_lease` reaches it
before selection because it reads the target through the same door.

It is not recursive, which the review asked for explicitly: raw rows are
adopted in one place, the invariants read only what the pass already holds, and
no invariant calls a public reader. The previous shape had `_blocked_relation-
ship` calling `_entry` and `lease_of`, each of which re-read and re-validated;
that is gone.

What `_prove` states:

- every lease's entry is this target's — a foreign key says the entry exists,
  not whose it is;
- at most one live lease;
- a live lease is over work still in progress (`leased`, `integrated` between
  the two cutpoints, or `held` while blocked);
- **and the other side of it** — a `leased` entry with no live lease is the
  stranded state the first review's [P0] was about;
- a blocked target's account cross-binds as before, and the held entries are
  exactly the one it names, and any abandoned lease is exactly the one it names;
- **an open target has no held entry and no abandonment.** Held work exists
  because an import could not be reconciled; an abandonment exists because a
  block was recovered. Neither can be true of a target open for business.

Item 3 defines no repair, so nothing here reopens a target. Whatever 3b or item
6 adds must reconcile the held entry and the recovery account in the SAME
transaction that reopens, or this invariant is false the moment it runs — the
review said so and it is now in the module's own commentary rather than only in
a dossier.

### Verification

117 focused cases, all passing. The new ones are two classes:
`TheStateGraphIsProvedFromBothSides` erases the block both while its lease is
live and after its recovery, calls `target_of`, `lease_of`, `entries_of` and
`grant_lease` independently, and reads the RAW rows afterwards to prove the
held entry, the lease, the target fence and the next queued entry are
unmoved — the public readers cannot be used for that assertion, because they
are what must refuse. It also drives the stranded-lease and live-lease-over-
settled-work halves on their own.

`TheGraphDoesNotDependOnWhatThisProcessREMEMBERS` fabricates the same split
state with SQL alone, so no verb of this package ever ran against those rows.
That is the case a restart actually presents, and it was the review's last
sentence.

The reviewer's reproduction, adapted, at `/tmp/w71878-item3-third-recheck.py`:

```text
live-block-erased/target|lease|entries|grant           all REFUSED
recovered-block-erased/target|lease|entries|grant      all REFUSED
rows unmoved [('entry-1','held'), ('entry-2','queued')] [('abandoned',)] [(1,)]
```

Both earlier reproduction sets still refuse. As in the two previous rounds the
reviewer's own script stops early, because it checks an outcome and then reads
the same value again unguarded.

Full suite: 4057 tests before this round, 4064 now, 10 failures, byte-identical
to the recorded baseline for the fourth consecutive round. Registry gate
passes; no new file carries trailing whitespace.

### The cost I am not hiding

Every public read now adopts and proves a target's whole graph — all its
entries and all its leases — where it used to adopt one row. For a long-lived
target that is O(queue) work on every call, and `grant_lease` does it inside
its write transaction. I chose correctness first because a partial validation
is exactly what produced three rounds of findings, and because item 3's queues
are bounded by what one checkout can integrate. If it needs to be cheaper the
honest way is a narrower pass with an explicit argument for what it may skip,
not a return to per-reader opinions; I did not want to make that argument
speculatively, so it is recorded here as a known property rather than
optimized away.

## 2026-09-06 — baton.claude — the fourth review's [P0]: the whole lifecycle

`review-2026-09-06T03-06-14Z.md` confirmed the state-graph pass closed the
erased-block [P0] from every door, and found that the pass proves selected
state PAIRS rather than a lifecycle. It is corrected. 120 focused cases (117
before); the same three paths over `v12/`.

### The finding

`_prove` checked live leases, held entries and abandonment against blocking,
and said nothing about a RELEASED lease's entry or about an entry that already
had a lease history. So resetting an integrated, released entry to its
schema-valid `queued` shape passed all four doors and selection leased the same
candidate again — an import whose durable account already says it completed,
offered a second time.

That is the third time a correction of mine held in the cases I thought of and
not in the shape underneath them: selected pairs are how a lifecycle gets
checked in the places somebody remembered.

### The correction

`_prove_entry` now states each entry's whole lifecycle against every lease it
has ever had:

- `queued` has no lease at all — nothing returns to queued;
- `leased` has exactly one live lease;
- `integrated` has exactly one, live between the two cutpoints or released with
  the `integrated` ending;
- `refused` has none when it was refused before selection, or exactly the one
  released lease its refusal fused;
- `held` has exactly the lease the blocked account names, live before the
  recovery or abandoned after it;
- and the target's fence is the greatest fence it has ever granted, zero only
  when it has granted none.

The lease side is now implied rather than separately listed: every lease
belongs to an entry, and every entry constrains all of its leases.

### The case the graph cannot see, and what closes it

An entry refused BEFORE any grant carries no lease, so nothing in the state
graph distinguishes its `queued` shape from an entry never offered — and the
review's rule is that no entry returns to `queued`. The residue that survives
is the journal: `transact` recorded `entry.refuse:<entry>` and a recorded act
is a statement about a state that must still hold.

So `_agrees_with_the_journal` cross-binds recorded decisions to present state:
`entry.integrated`, `entry.refuse`, `target.block`, `lease.release` and
`lease.abandon`, each looked up by the identity its own act would have
committed under.

**Only one direction, and I measured the other one out.** "Every terminal entry
has a recorded act" is false for the duration of the act itself, because
`transact` writes the journal row after the action returns — so
`settle_integrated` legitimately reads an `integrated` entry whose record does
not exist yet. I wrote that rule, watched it break 54 of this suite's own
cases, and removed it rather than leave a check that is true only between
transactions.

**What it does not catch, said plainly:** a DELETED row. The identities looked
up are built from the rows that are present, so an entry or lease removed
outright leaves nothing to disagree with. Catching that needs the journal read
the other way round — every enqueue this target ever recorded — which the
operation identity does not support without a scan, and which no review has
asked for.

### One thing I found while building the journal check

`target.block`'s operation identity was `"target.block:" + target + ":" +
entry`, and two ids joined by `":"` do not compose uniquely when either may
contain one: target `a` with entry `b:c` and target `a:b` with entry `c` spell
the same operation. The signature would catch it as a collision rather than
replay the wrong act, so this is a confusion rather than a safety hole — but an
identity that can collide is not an identity. Both composite ids
(`target.activate` and `target.block`) now carry a digest of the pair, which
cannot collide however the prefix is read.

### Verification

120 focused cases, all passing. `TheWholeLifecycleIsProved` is the
table-driven matrix the review asked for: eight corruptions — integrated and
refused entries reset to queued, an integrated entry released as
`entry-refused`, a released lease moved onto a queued entry and onto an
unrelated settled one, an entry given a second historical lease and a live one
beside its ended one, and a target fence drifted from its history — each driven
at all four doors, each asserting the entry rows, the lease rows and the target
fence are exactly as the corruption left them and that no lease was granted.
The held-reset-to-queued case has its own blocked base.

It also carries `test_the_ordinary_lifecycle_still_reads`, because a matrix in
which everything refuses would pass while proving nothing: the sound store
reads back integrated/queued/refused, its released lease, its fence, and offers
the next entry.

The reviewer's reproduction now refuses at all four doors with the entry still
queued and no second lease granted. All three earlier reproduction sets still
refuse.

Full suite: 4064 tests before this round, 4067 now (the matrix is one
method over thirty-two sub-cases, so the count moves by three), 10 failures, byte-identical
to the recorded baseline for the fifth consecutive round. Registry gate passes;
no new file carries trailing whitespace.

## 2026-09-06 — baton.claude — the fifth review's two [P0]s: the journal is the history

`review-2026-09-06T03-22-15Z.md` confirmed the lifecycle correction and found
two [P0]s underneath it. Both are corrected. 138 focused cases (120 before);
the same three paths over `v12/`.

### The findings, and the shape they share

**The immutable entry account was still mutable on restart.** Changing
`checkpoint_id` and `candidate_digest` in place was accepted by every reader,
so selection would hand the integrator different evidence from the accepted
evidence that entered the queue — and because the original checkpoint no longer
appeared in `entries`, that same original candidate became admissible again
under a second entry id.

**Deleted history permitted duplicate integration.** Delete the released lease
and the integrated entry, wind the fence back to zero, leave the journal
untouched: the store satisfied the owned schema, read as an empty target, and
accepted a new entry for the exact same Authority and checkpoint, at fence 1
again, and granted it.

Both are the same defect I keep writing. The previous pass built operation
identities *from the rows that were present* and asked only whether a terminal
decision name existed — so it could not see a row that had been rewritten, and
by construction could not see one that was gone. I named the deletion gap in my
last round and said no review had asked for it. The reviewer's answer is the
right one: the journal still holds the act, so this is a provable contradiction
rather than unknowable loss, and calling it a blind spot did not make it one.

### The correction

`_agrees_with_the_journal` now proves the materialized rows and the durable
history against each other in both directions:

- every committed activation, enqueue and grant relevant to this target has its
  materialized row, and that row still matches what the act recorded — the
  target's identity, document, digest and adoption instant; the entry's target,
  id, allocated rank, enqueue instant and all seventeen operands of the
  immutable account; the lease's target, entry, holder, attempt, allocated
  fence and grant instant;
- every target, entry and lease row has the act that made it, **against this
  target's acts** rather than against the journal at large — an enqueue
  recorded for another target does not account for a row sitting in this one,
  which is what moving a row between targets would otherwise look like (my own
  new case found that; the first draft used a global lookup);
- the fence is the greatest in the durable history, not the greatest lease row
  that remains — which is precisely what a deleted lease was handing back;
- terminal acts and endings stay cross-bound both ways, with the fused release
  that `refuse_entry` performs recognised as the second act that can produce a
  released lease;
- and `lease_of` no longer answers `None` for a lease this store recorded
  granting: absence is an answer only when nothing says otherwise.

The journal rows are adopted like any other persisted input — `OPERATION_COLUMNS`
through `boundaries.row`, the signature decoded and its kind checked against the
row's, its operands checked against a closed per-kind contract, and a kind this
build does not own refusing the read rather than being skipped.

### The one window, and why it is exact

A materialized transition and its journal row commit together, so no external
reader can observe one without the other. Inside `transact` there is exactly one
instant where they differ. The reviewer was right that my in-action read was not
a reason to weaken the external invariant, and right about the shape of the fix:
`IntegrationStore` now names the act currently between its write and its record,
by operation identity, and the history proof excuses **that identity and nothing
else**. A general "no record yet" branch would readmit every fabricated row;
`test_a_pending_act_excuses_only_itself` drives an enqueue with a fabricated
ghost row present and proves the ghost is still refused.

### The cost, again stated rather than hidden

Every public read now scans the whole `operations` table and adopts every
committed row. The review accepted a global scan for this slice; what it buys
is that a deleted row stops being invisible. An indexed target binding is the
way to make it cheaper and would need its own schema and adoption proof.

### Verification

138 focused cases, all passing. `TheJournalIsTheDurableHistory` covers: every
one of the seventeen account operands mutated in place, one at a time; a
reassigned rank; an entry moved to another target (refused from both targets);
a deleted queued entry, a deleted live lease, a deleted integration and a
deleted target row; a fence wound back below its durable history; the original
checkpoint re-admitted after its history was deleted; and four malformed
journal records — signed as another kind, of a kind this build does not own,
with short operands, with a result missing a member, and a signature that does
not decode. Each drives the applicable doors of `target_of`, `entries_of`,
`lease_of`, `enqueue` and `grant_lease`, and asserts the refusal moved neither
the materialized rows nor the journal.

The positive half is kept explicitly: first execution, exact replay of the
activation and the enqueue (each returning the FIRST outcome, which is what
makes them replays), and a reopened store proving the same history.

The reviewer's reproduction now prints REFUSED on all eight lines. All four
earlier reproduction sets still refuse; one line of my own first recheck script
changed, because the account mutation it demonstrated as "unrepresentable" is
now refused outright.

Full suite: 4067 tests before this round, 4085 now, 10 failures, byte-identical
to the recorded baseline for the sixth consecutive round. Registry gate passes;
no new file carries trailing whitespace.

## 2026-09-06 — baton.claude — the sixth review: the journal proves one exact signed act

`review-2026-09-06T03-39-13Z.md` confirmed the two previous [P0]s closed and
found a [P0] and a [P1] underneath them. Both are corrected. 149 focused cases
(138 before); the same three paths over `v12/`.

### [P0] The signed enqueue was not bound to its own result

I compared the recorded result to the materialized row and to nothing else. So
rewriting BOTH redundant surfaces — the row and the journalled result — left
two witnesses agreeing with each other and a signed request that contradicted
them, and selection believed the two. That is the immutable-account defect
again with one more surface edited, and the reviewer's sentence is the one that
matters: the original signed request is still present and proves the
contradiction, so selection must not trust the mutually agreeing pair over it.

Three surfaces now hold one relationship, in that order: every act's operands
are owned, its identity is RE-DERIVED from those owned operands and compared to
the id it is filed under, its result is adopted as that kind's exact variant
and proved to be the result *of that signed request*, and only then is the
materialized row compared to the result. The generated members — rank, fence,
the instants — necessarily come from the result, which is why the result has to
earn the right to be evidence first.

`_identity_of` is what closes the other half the review named: identities were
read off the row and never recomputed, so a noncanonical one could stand in for
another committed act.

### [P1] Operands were shaped, not typed, and SQL NULL escaped raw

The operand table closed the key set and validated none of the member semantics
it was being trusted for, so a signed account whose `candidate_digest` was the
integer 7 was evidence. **A member set is not a shape — the third time this
record has had to say that**, which is why the operands now go through the
admission owners themselves rather than a second spelling of them:
`_owned_target`, `_owned_account`, `_settlement`, `_ending`, `_recovery`, the
same functions `activate_target` and `enqueue` call. Those two verbs were
rewritten to call them, so "the same rules used at admission" is one function
rather than a claim.

And a committed row with a SQL NULL result reached `json.loads` and escaped as
a raw `TypeError`. It is now a typed refusal. The one legitimately absent
result — a grant over an empty queue, which commits, records `null` and creates
no lease — is the typed empty variant and is the only kind allowed one.

### Duplicates, and the pending act

`_no_duplicates` refuses two committed acts for one logical subject. Only the
activation case is reachable — the derived identity makes a second act for an
entry or a lease impossible through the primary key — and its docstring says
so rather than implying the check is doing more than it is.

The pending act is now adopted through the same owner and its identity
re-derived, and what it excuses is a row that MATCHES WHAT IT ASKED FOR. Its
operation identity alone is provenance a caller chooses; its signed operands
are not.

### Verification

149 focused cases, all passing. `EveryRecordedActIsProvedWhole` drives, for
each of the eight kinds, an ill-typed signed operand; for each of the seven
where it is reachable, a signed request that no longer matches its own result
(`target.activate` is absent on purpose — its identity is derived from the
document, so changing the document changes which act it is rather than making
one act disagree with itself); the row-and-result-rewritten-together [P0],
including that the original candidate is still not admissible a second time; a
noncanonical operation id; two activations of one target; a SQL NULL result; a
wrong-variant result; the typed empty grant; and a pending act whose operands
do not describe the row it wrote. Every refusal is asserted to leave the
targets, entries, leases and journal exactly as they were.

The positive half is kept: a complete history reads, replays both the
activation and the enqueue as their first outcomes, and reopens; a blocked
history reads back its account and its abandoned lease.

The reviewer's reproduction now prints REFUSED on all seven lines. All five
earlier reproduction sets still refuse.

Full suite: 4085 tests before this round, 4096 now, 10 failures, byte-identical
to the recorded baseline for the seventh consecutive round. Registry gate
passes; no new file carries trailing whitespace.

### What six rounds of this have been about

Every finding since the first has had one shape: a rule that held where I had
thought to apply it and not where the same fact could arrive from another
direction. Selected state pairs instead of a lifecycle; one redundant surface
instead of both; rows present instead of history; a result instead of the
request behind it. The correction each time has been to move the proof to
whatever the last surviving witness is — which is now the signed act, because
nothing downstream of it can be rewritten without contradicting it.

## 2026-09-06 — baton.claude — the seventh review: the retry is a read, and the order is a witness

`review-2026-09-06T11-10-42Z.md` found two [P0]s. Both are corrected. The two
owner clarifications pinned in FINDING.md after that review are carried out in
the same round, because they change the same schema and shipping them
separately would mean two incompatible stores inside one unaccepted candidate.
173 focused cases (149 before); the same three paths over `v12/`.

### [P0] Every exact retry bypassed every proof this module has

`IntegrationStore.replay` read one row, compared the caller's raw signature
text and returned `json.loads(result)`. So the operand contract, the derived
identity, the result variant and the whole materialized relationship were
reached by ordinary reads and by first executions — and by nothing else. The
retry path, whose entire reason to exist is making a transition effectively
ONCE, was the single door in this package that believed the journal without
reading it.

The reviewer's second reproduction is the one that matters, and it is worth
stating plainly rather than as a category: `settle_integrated` is the
post-import cutpoint whose success is what lets Authority completion follow. A
fabricated committed act carrying the exact settlement signature made it report
success while the entry was still `leased` and nothing had settled. A later
ordinary read refuses the contradiction — after the transition already answered
success, which is the wrong side of the boundary.

`replay` now takes a required `witness` and has NO default, because a default
is how the one path that skipped everything got there. The store keeps what it
owns — the transaction, the operation identity, the durable order, the adoption
of an operation row — and owns no queue semantics at all. `_proved` is the one
semantic owner: it adopts the act's operands through their admission owners,
re-derives the identity from them, adopts the result as that kind's variant and
proves it is the result OF the signed request, then proves the entire
materialized relationship the act belongs to. `_transact` names that witness
once, so "every public mutator reaches it" is a fact about one function rather
than a list somebody maintains.

The ordering the fifth round established is untouched: the journal is still
asked BEFORE a now-ended live grant is checked, because releasing a lease ends
it and a retry after a lost answer would otherwise refuse its own completed
work. **Asked first was never an argument for trusted first**, and the docstring
now says so where the next reader will be tempted again.

### [P0] A generated decision had no witness that a rewrite could not reach

`enqueue` cannot sign the rank it is about to allocate and `grant_lease` cannot
sign the fence it is about to burn. So rank, fence and selection had exactly
two witnesses — the recorded result and the materialized row — and the reviewer
rewrote BOTH, moving entry 1 behind entry 2 at rank 3. The signed enqueue was
present and true throughout; it simply never said anything about rank, so
nothing contradicted the pair and selection followed the reversed queue.

The third witness is the ORDER. `operations` gains `seq`, allocated as
`MAX(seq) + 1` inside the act's own transaction by exactly the rule `enqueue`
allocates a rank by, and proved dense from one at every read. It is not a value
about a decision; it is the position the act holds among every act this store
committed, and an `UPDATE` to a result or an entry row cannot reach it. From it
`_generated_by_the_order` derives all three: the Nth enqueue of a target
allocated rank N, its Nth grant that took a lease burned fence N, and replaying
the enqueues and settlements before each grant says which entry that grant
could have selected. The target's fence is the count of its grants rather than
the greatest surviving value anywhere.

**The bound, stated rather than implied.** §13 forbids a durable secret here, so
nothing in this store is unforgeable: a writer who also rewrites `seq` presents
a self-consistent alternative history and this seam cannot tell it from the
real one. `test_reordering_the_journal_contradicts_the_results_it_reorders`
drives that honestly — reordering moves the disagreement rather than removing
it — and I would rather record the limit than let the density proof read as
tamper-proofing.

**Why not a content chain.** I built one first: a per-act digest over the
previous act's digest and this act's bytes, which would make any rewrite
anywhere visible. I took it out. It would have fired FIRST on every corruption
this suite drives, masking the semantic refusals underneath it — the signed
request, the result variant, the relationship — so the proofs that actually
carry the safety argument would have become unreachable in practice and
untested. And it buys nothing a rewriter cannot recompute, because the digest
is public. Ordering evidence is the narrow thing the finding asked for, so
ordering evidence is what this is.

### The owner clarifications: the core vocabulary is VCS-neutral

Pinned in FINDING.md after the review: the coordinator, Job Manager, Worker
Manager and protocol are VCS-neutral. Core Baton mechanically owns serialized
target admission, the live fenced grant, exclusive target write access,
quiescence and durable settlement; it does not parse or validate commits, refs,
branches, trees, ancestry or merges, and v12 requires no VCS-aware adapter to
exist. `base_object`, `head_object`, `tree_object` and `transport_ref` were
version-control operands sitting in the core eligibility account, and `checkout`
was one in the core target document.

They are gone. A closed, versioned binding replaces them on the entry:
`profile_kind`, `profile_version` (counting from one) and
`profile_account_digest`. The coordinator retains the DIGEST of the
profile-shaped account and never the account, so it refuses a changed profile
account without knowing what one is; the operands themselves travel in the
Work's generic inputs, outputs and logs. The clarification refuses an opaque
unvalidated document by name, and a digest is not one. The target document is
now `schema`, `canonical_target_id` and `description`: the coordinator locks a
NAME, and where the named thing lives is the profile's.

`TARGET_SCHEMA` moves to `baton.v12.integration-target/2` and the store to
`SCHEMA_VERSION` 2. No migration is invented and version 1 is a shape only this
unaccepted candidate ever carried; two different shapes both calling themselves
version 1 is exactly the drift a version exists to prevent.

`TheCoordinatorVocabularyIsVCSNEUTRAL` is a GATE over the column and member
names rather than a paragraph, because the way that vocabulary arrived the
first time is that each operand looked locally reasonable one at a time. It
fails the moment one of those nouns is added back, whatever the prose beside it
says, and it reads identifiers rather than commentary so that the schema may
still explain what was removed and why.

### Three defects my own matrices found, not the review's

- A settlement carried on a `queued` or `leased` entry document reached
  `SETTLEMENT_MEMBERS[state]` and escaped as a raw `KeyError`. The schema's
  CHECK makes it unrepresentable in a ROW; a recorded result is under no CHECK,
  and the retry matrix corrupted a block's result into a queued entry to find
  it.
- `revive_refusal` adopts persisted TEXT and this package handed it
  `json.loads(...)`, so every replay of a durable refusal would have answered
  `integrity.schema` "this is a dict" instead of the refusal it was replaying.
  Never reached before, because no verb here raises a durable refusal yet — the
  retry matrix is what stood in front of it.
- A version counting from one accepted zero: `boundaries.generation` counts
  from zero, the columns' own CHECKs say `>= 1`, and the gap reached SQLite as a
  raw `IntegrityError` escaping this package as something no caller can act on.
  True of `assignment_generation` since the first draft; `profile_version`'s
  own type matrix is what surfaced it. Both now go through
  `_counted_from_one`.

### Verification

Focused: 173 cases, all passing.

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_coordinator
    -> Ran 173 tests, OK

`EveryRetryIsPROVEDBeforeItIsAnswered` drives, for each of the eight kinds, a
corrupted first outcome met on the retry path, asserting the refusal moves no
target, entry, lease or journal row; the reviewer's two reproductions at the
doors they entered by; a row that no longer matches its own result; a committed
SQL NULL result; a malformed sealed refusal; a well-formed one that still
replays AS the refusal it was; and the positive half — every kind's sound retry
returning its first outcome, twice.

`TheORDERIsTheWitnessForWhatWasGENERATED` drives the coordinated rank rewrite at
every door, a grant retargeted past a lower queued rank with the lease row and
the result rewritten together, a typed empty grant recorded while work was
queued, a coordinated fence rewrite across result, lease row and target
counter, a journal position leaving a hole, and the reordering case that states
the limit. Duplicate and missing ranks are asserted UNREPRESENTABLE rather than
caught, because `UNIQUE (canonical_target_id, rank)` and `NOT NULL` are where a
state that must never exist belongs. The positive half is a long mixed history:
a queued entry refused before it was ever offered, selection skipping it,
FIFO across two Authorities, both fences, and exact replays returning their
first outcomes.

`TheCoordinatorVocabularyIsVCSNEUTRAL` proves the name gate, the target
document's shape, that a removed operand cannot return through the account,
that the profile binding is typed member by member, and that what the store
retains is the digest rather than the account.

Broad sweep, both phases of the host's safe parallel harness:

    PYTHONPATH=src:. python3 tools/parallel_test.py
    -> parallel source: 554 shards, 3885 tests, 6 failures, 0 errors, 3 skipped
    PYTHONPATH=src:. python3 tools/parallel_test.py --phase serial
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4120 tests, 10 failures, and the failure list is byte-identical to the recorded
baseline for the eighth consecutive round: five `test_boundary_inventory` cases
and one `tests.authority.test_catalog` case, whose failing sets name
`worker_manager` entries this package is not in, plus four Docker-engine
residue cases naming `baton-w6633-test-*` and `baton-runtime.start-*` objects
left in the local engine by other suites. No byte of mine starts a container,
builds an image or reaches the daemon. The serial phase is invoked explicitly
because the canonical gate's fail-fast ordering stops the serial registry when
the parallel one fails, and the parallel one fails on the baseline.

The reviewer's reproduction refuses on all three lines, and the entry the
fabricated settlement claimed to have integrated is still `leased` afterwards:

    PYTHONPATH=src:. python3 /tmp/w71878-item3-seventh-recheck.py
    joint-rank-rewrite-read REFUSED integrity
    joint-rank-rewrite-grant REFUSED integrity
    corrupted-exact-replay REFUSED integrity
    fabricated-settlement-replay REFUSED integrity
    entry row still leased

The reviewer's own `/tmp/w71878-item3-seventh-review.py` now raises its refusal
rather than printing ACCEPTED; its third case's direct `INSERT INTO operations`
needs a `seq`, which `/tmp/w71878-item3-seventh-recheck.py` supplies. All five
earlier reproduction sets still refuse.

`git diff --check` passes and no new file carries trailing whitespace. The
registry gate passes.

### What I am not claiming

The receiving-boundary inventory obligation is unchanged from the earlier
rounds: `test_boundary_inventory` walks `worker_manager`, this package is not
in it, and item 7 still owes either a dedicated integration inventory or the
equivalent exhaustive focused coverage. The three new columns and the profile
binding are inside that gap like everything else here.

And the profile boundary decides nothing about profiles. Which kinds a
deployment offers, what an account contains, and how one is selected belong to
the records that own them; item 3 binds a kind, a version and a digest, and
interprets none of the three.

## 2026-09-06 — baton.claude — the eighth review: a proof is only as good as the state it observed

`review-2026-09-06T11-45-47Z.md` confirmed both [P0]s and the VCS-neutral
boundary and found two [P1]s underneath them. Both are corrected under the
owner disposition that authorizes one final implementation round for exactly
those two. 186 focused cases (173 before); the same three paths over `v12/`.
No automatic interruption recovery is added and item 3b and items 4-9 are
untouched.

### [P1] The witness was semantically complete and transactionally incoherent

I moved the proof to the last surviving witness seven times and never asked
what STATE the proof was reading. `_relationship` read a target row, then its
entries, then its leases, then the whole journal — four autocommit statements —
so an ordinary grant committing between two of them left the pass holding a
composite that never existed: a target at fence 0 beside a journal at fence 1.
It then reported that as corruption.

That is the worst answer available. Nothing was corrupt, the schedule was the
one this store exists to serialize, and the caller was an exact retry that owed
its first outcome. A proof assembled from independently committed reads is not
a proof; it is two proofs about two states, and the second one is about a state
the first never saw.

`IntegrationStore.snapshot` is the read transaction. Every semantic proof runs
inside one — the relationship pass, the lease and entry projections, and the
replay witness including the operation row it decides on — and it is RE-ENTRANT
on purpose: inside `transact` the write transaction the caller already holds IS
the observation, and opening a second would be an error rather than a stronger
guarantee. The fenced verbs' ordering is untouched, because a snapshot changes
what a read observes and not when it happens.

**`BEGIN DEFERRED`, and WAL.** The review allowed conservatively taking the
write lock. I did not, for a reason worth recording: this reads and never
writes, so IMMEDIATE would serialize two coordinators' reads against each other
for no coherence gain. And under a rollback journal even a DEFERRED reader
blocks every writer for the duration of its snapshot — in a store whose entire
premise is two Authorities contending for one target, that turns one
coordinator's ordinary read into the other's five-second timeout, and the
review's own reproduction would have deadlocked by construction rather than
interleaving. So the store asks for WAL, AFTER the ownership decision and never
before, because a database this build refuses must be left exactly as it was
found.

It is a request rather than a requirement, and the difference is stated in one
case of its own: coherence belongs to the read transaction and holds in either
journal mode, so a filesystem that cannot give WAL yields a correct store with
a narrower concurrency story. `test_the_store_asks_for_wal_so_a_reader_does_
not_block_a_writer` exists so that such a filesystem fails one case with a
plain answer instead of failing the two interleaving cases mysteriously.

### [P1] Refused rows were the half of the journal nothing owned

`replay` branched on `state == "refused"` and revived the sealed refusal before
the witness ran; `_history` skipped a refused row the moment its generic
columns and its position had been checked. So the two sentences I wrote last
round — "every retry is proved" and "a kind this build does not own refuses the
read" — were true of committed rows and of nothing else. The review demonstrated
both halves: an exact refused retry answered its policy refusal over a journal
with a hole in it, which the very next ordinary read found; and a schema-valid
refused row of kind `unknown.kind` sat in a sound target's journal while every
door answered normally.

`replay` no longer branches on the recorded outcome at all — this module owns
no queue semantics, so it cannot own the difference between a committed act and
a refused one either. Both go to the witness. `_recorded_act` owns a refused
row's kind, typed operands, derived identity and dense position (the sealed
outcome itself `OPERATION_COLUMNS` already owned), the witness proves the
relationship the act was refused against, and only then is the refusal revived.
`_history` adopts refused rows the same way and keeps them out of the committed
projection, because a refused act changed nothing — which is what makes it a
refusal — and must not appear in the rank, fence or selection derivations.

For a refused `lease.abandon` there is neither a target in the operands nor a
result to name one; that case reaches the relationship through the lease the
act is about, and the durable history either way.

### What this round did not do

No automatic retry, acceptance, receipt completion, cleanup, release, discard
or reassignment was added, and nothing here reopens a blocked target: both
corrections are read-side proofs. `abandon_lease` remains the one explicit
operator-driven recovery and still does not reopen the target. Item 3b and
items 4-9 are untouched, and the receiving-boundary inventory gap is unchanged.

### Verification

Focused: 186 cases, all passing.

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_coordinator
    -> Ran 186 tests, OK

`OneProofObservesOneSnapshot` fires the interleaving grant from a second
connection inside `_target_row` — the exact boundary the review named, so there
is no timing to be lucky about — and proves the sound exact retry returns its
first outcome, that the interleaved grant really committed (otherwise the class
would prove coherence by proving nothing happened), that an ordinary read is
coherent across the same interleaving, that the snapshot yields to a
transaction already held, and that a refusal inside a snapshot does not strand
the connection.

`RefusedActsAreEvidenceToo` drives the sound durable-refusal control, the
journal hole under a refused retry, an unknown kind, an ill-typed signed
operand and a noncanonical derived identity — each through both the ordinary
read and the exact refused replay where the door is reachable — a rewritten
committed act beside a sound refusal, and that every refusal moves no target,
entry, lease or journal row.

Broad sweep, both phases of the host's safe parallel harness:

    PYTHONPATH=src:. python3 tools/parallel_test.py
    PYTHONPATH=src:. python3 tools/parallel_test.py --phase serial

    -> parallel source: 556 shards, 3898 tests, 6 failures, 0 errors, 3 skipped
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4133 tests, 10 failures, and the failure list is byte-identical to the recorded
baseline for the ninth consecutive round: five `test_boundary_inventory` cases
and one `tests.authority.test_catalog` case, whose failing sets name
`worker_manager` entries this package is not in, plus the four Docker-engine
residue cases. The serial phase is invoked explicitly because the canonical
gate's fail-fast ordering stops the serial registry when the parallel one
fails, and the parallel one fails on the baseline.

The reviewer's reproduction:

    PYTHONPATH=src:. python3 /tmp/w71878-item3-eighth-review.py
    interleaved-sound-retry ACCEPTED
    refused-retry-with-hole integrity schema ... dense from one
    ordinary-read-with-hole integrity schema ... dense from one
    unknown-refused-kind REFUSED integrity schema operation 'unknown:1'
      records kind 'unknown.kind', which this build does not own

The first line is the sound retry returning its first outcome, which is what
`ACCEPTED` means there; my own case asserts the returned entry and rank rather
than only the absence of a refusal. All six earlier reproduction sets still
refuse.

`git diff --check` passes, no new file carries trailing whitespace, and the
registry gate passes. The parallel registry's note now says that the cases
using two connections — the threaded grant race and this round's interleaving —
open both against their own database file inside the case.
