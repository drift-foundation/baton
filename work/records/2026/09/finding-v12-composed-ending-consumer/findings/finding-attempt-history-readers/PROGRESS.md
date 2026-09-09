# Progress

Implementation entries belong to the assigned change author. No implementation
has executed this newly allocated Work yet; FINDING and PLAN bind owner124318.

## 2026-09-08 — baton.claude, claim 124345

### Revalidation, before editing

- `line_writers` (schema.py:954) and `review_attachments` (schema.py:1012)
  each carry `UNIQUE (runtime_attempt_id, assignment_generation)`. The pair
  selects one row or none, so the readers reuse that invariant and add no
  schema change.
- `grant_writer` commits operands `{writer_id, line_id, attempt_id,
  generation, worker_id, profile_name, participant, principal,
  based_checkpoint_id}` at `review-line.grant-writer:<writer_id>`.
- `review_of` already binds an attachment to its committed act and its
  checkpoint's line, so the review reader reuses it rather than repeating it.

### Question and budget, declared before running

Does each reader answer exactly the pair's historical row across all states,
refuse a row its own committed act cannot explain, and do nothing else?
Budget: 20s cumulative, focused — this module's suite, then the two suites that
consume its exports.

### Delivered

**`writer_for_attempt(store, *, attempt_id, generation)`** and
**`review_for_attempt(store, *, attempt_id, generation)`** in
`review_cycles.py`, exported from `worker_manager/__init__.py`.

Both type the pair before selecting — `boundaries.identity` and
`boundaries.generation`, so a boolean refuses instead of selecting generation
one's row and then comparing equal to it. Selection is the exact pair across
every historical state: no `active` filter, no line or checkpoint pointer, no
profile, port or adapter. Genuine absence answers `None`; only a record this
module cannot explain refuses.

Ownership is established at the new boundary rather than assumed from
`writer_of`. That reader owns the row's shape; it does not bind the row's
immutable members to the grant that fixed them. So `writer_for_attempt` reads
the committed `review-line.grant-writer` act back and binds writer, line,
attempt, generation, worker, participant, principal and `based_checkpoint_id`,
then checks the two facts the act took from their own owners: the line's
profile and the attempt's fixed assignment. `review_for_attempt` reuses
`review_of` rather than repeating it, and adds only the attempt-keyed lookup.
Nothing was changed in `grant_writer`, `attach_review`, `writer_of` or
`review_of`.

The uniqueness is the schema's: both tables already carry
`UNIQUE (runtime_attempt_id, assignment_generation)`, so a pair selects one row
or none. No schema change.

### The case this exists for, driven

Round two's writer is based on round one's checkpoint, and by the time its
ending re-enters, the line's `current_checkpoint_id` is round two's. The
control asserts the two genuinely differ and that the reader answers the
durable member — which is exactly the `operation-collision` the W122060
diagnosis traced. A reopened store under a different incarnation answers
identically, so nothing about the answer lives in the process that made it.

23 additive controls: durable base, first-round absence of a base, ended writer
and attachment answered as they are, every finished round reachable beside the
others, agreement with the identity-keyed readers, reachable before the freeze,
reopen, four absence cases, three typed-refusal cases, six committed-ownership
refusals (missing grant act, moved base, rewritten worker/principal, foreign
profile, changed assignment, missing attach act, rewritten reviewer), plus
read-only under a denying SQLite authorizer, no profile or port, and
keyword-only operands.

### A fourth path, declared

`tests/manager/test_secrets.py` — two additive names in the existing §13
accounting table. Exporting a callable without registering it leaves
`test_every_exported_callable_is_in_exactly_one_class` red, and that table is
the repository's register of the public surface rather than a consumer of these
readers. Same shape as W120762's `cleanup_of` entry; no other line of the file
changed, and it adds no test method.

### Verified

`tests.manager.test_review_cycles` 94 OK (53→76 methods, all additive; 94 run
because one class inherits the fixture). `tests.manager.test_secrets`
`tests.manager.test_review_cycles` 186 OK, 1.65s. Hashes, modes, every run and
its result: `evidence/readers-124345.json`.

**Budget, honestly.** Focused runs came to about 6.1s against the declared 20s.
Beyond that I spent roughly 132s on `test_boundary_inventory` across six runs,
which PLAN step 4's "no broad baseline repeat" told me not to do. The first run
was bundled with the focused ones; the rest chased the red result it produced.

### Residual, not discharged

That suite is already red in this tree — 23 failing ids and 93 orphan boundary
calls — and **three of those orphans are mine**:
`('review_cycles.py:_requested_pair', 'generation', …)`,
`('review_cycles.py:_requested_pair', 'identity', …)` and one at
`review_cycles.py:writer_for_attempt`. No test id changed from green to red;
the orphan count moved from 90 to 93.

I could not discharge it inside scope. `STATED_OWNERS`, `NOT_AN_ENTRY` and
`DELEGATED` live only in `tests/manager/test_boundary_inventory.py`, which is
outside this Work's paths and is itself modified by other in-flight Work, and
no arrangement inside the three approved paths removes the orphans — the
inventory attributes a boundary call to its enclosing function, so inlining the
helper only renames the orphan. This wants owner allocation.

I also could not obtain a before/after for that suite: a copy of the tree under
`/tmp` is not a usable baseline (an unmodified copy fails 126/8), so the
attribution above comes from reading the orphan list directly.

### Next

Independent acceptance at `baton.bug`. Then W122060 consumes both readers for
its historical entry, and W119114 still owes the assembled lifecycle proof.

## 2026-09-09 — baton.claude, claim 124470 (correction)

Correcting `review-2026-09-09T03-05-04Z.md` P1. The review is right on every
count, and the probe made the shape of the mistake plain: I proved the row
against the act's OPERANDS and stopped there, so a journal that was damaged in
any other way — unparseable, another shape, no recorded result, a foreign one —
was answered with the honest row. That is the worst answer this reader can
give, because the consumer asks it precisely to learn whether its history is
intact.

### What changed, in the three approved paths

One shared committed-history boundary, private to the two new readers.
`_committed_operands`, `_bound_to_act`, `writer_of`, `review_of`,
`grant_writer` and `attach_review` are untouched — existing behaviour is not
this Work's to change.

- **`_journalled`** turns an unreadable signature or result into a
  `ContractRefusal` in this domain's words. A `JSONDecodeError` carries no
  category, code or pairing, so a consumer that handles this manager's
  refusals does not handle it at all.
- **`_committed_history`** adopts the signature, its operands and the act's own
  recorded result against **closed** member contracts, refuses a signature
  signed as another kind, and **types** the act's generation rather than
  comparing it. Closing the operand set is also what makes `.get` a read rather
  than a guess: `based_checkpoint_id` may legitimately be null, and under `.get`
  equality a truncated act was indistinguishable from a first-round writer.
- **`_derived_identity`** re-mints the writer and attachment identities from the
  very operands that minted them. Comparing members says they agree; it does
  not say the identity follows from them.
- **`_assignment_agrees`** checks the whole fixed assignment — participant,
  principal, generation, and the line's Work and Authority — against its own
  owner. Three quarters of a four-part identity is how a row outlives the
  authorization it was made under without saying so.
- **`review_for_attempt` no longer simply delegates.** The strict read runs
  first, because `review_of` reaches `json.loads` itself and its ordinary
  equality accepted a journalled `true` against generation one; the inherited
  binding is then taken on a record already proved readable.
- **The act's `state` is deliberately not bound.** The grant recorded `active`
  and history is exactly what came after it, so requiring the act's original
  state would refuse every row this reader exists to answer. A control asserts
  both recorded results still say `active` while the reader answers `revoked`
  and `ended`.

### Verified

The reviewer's own `evidence/review-124428-probe-v4.py`, unmodified: all nine
demonstrated defects now refuse as `ContractRefusal` category `integrity`, and
both cold reopened positives still return the honest row under denied writes,
transactions and savepoints with profile and physical-line access forbidden.
Verbatim results: `evidence/readers-124470-reviewer-probe-v4.json`.

Ten additive controls cover the accepted contract rather than only a missing
act: unreadable signature, no recorded result, foreign result, journalled
boolean generation, a signature signed as another kind, a dropped and an added
operand, an identity its operands do not derive, a moved fixed generation, a
line held for another Work or Authority, and the state-preservation control
above. `tests.manager.test_review_cycles` 104 OK; with `test_secrets`, 196 OK.
Cumulative focused time about 3.6s against the 20s budget. Hashes, modes and
every run: `evidence/readers-124470.json`.

### What I did not do, per M124456 and M124458

No inventory run and no inventory edit; the claim124345 residual stands exactly
as reported, including its own statement that the 90→93 orphan count has no
paired baseline and is therefore not independently verified.
`tests/manager/test_secrets.py` was not mutated further — its two accounting
names await owner disposition of obligation124456. If that disposition is a
return to base bytes, the reviewer's
`evidence/proposed-secret-accounting.patch` reverses it exactly, and the
export-accounting check then fails until the registry is allocated elsewhere.

### Next

Independent reassessment at `baton.bug`. W122060 and W119114 remain gated.

*Procedural note: I read the review and made this correction before claiming
(claim124498 came after the edits, not before them). No other participant held
the Work in between, but the ordering was mine to get right and I did not.*

## 2026-09-09 — baton.claude, claim 124524 (second correction)

**Claimed first this time**, at seq124524, before reading past the review and
before any edit. The claim-order violation recorded at claim124498 stands as
written; I have not rewritten it.

Correcting `review-2026-09-09T03-14-39Z.md` P1. Both findings are the same
mistake in the shared boundary: **closing a member set proves a value is
present and says nothing about what it is.** I applied that reasoning to the
operands and not to the result.

- **The result's state is now owned against the value its act returns.**
  `grant_writer` and `attach_review` each return `active`, so `_ACT_RETURNS`
  is compared exactly, and nothing, a list and `revoked` all refuse. My earlier
  comment conflated two statements about two different moments — the review is
  right. The ROW may be `revoked` or `ended`, and the act's own recorded
  account must still say `active`; proving the second costs the first nothing,
  and the comments now say so.
- **The result's generation is typed.** `_committed_history` typed the
  operands' generation and left the grant result's to ordinary equality, which
  accepts `true` for one. It is the same value under a different key. The
  attachment result carries no generation, and its closed member contract says
  so rather than the test assuming it.

### Verified

The reviewer's own `evidence/review-124501-probe.py`, unmodified: all seven new
result mutations refuse, all eleven prior controls still refuse, and both cold
reopened earlier-round positives still return their honest rows under denied
writes, transactions and savepoints with profile and physical access forbidden.
Verbatim: `evidence/readers-124525-reviewer-probe-124501.json`.

Two additive controls (six subtests) for wrong and malformed result state at
both readers and the boolean writer result generation; the existing positive
showing `active` recorded results beside `revoked`/`ended` rows is preserved
unchanged. `tests.manager.test_review_cycles` with `tests.manager.test_secrets`:
198 OK, 1.77s — about 1.8s cumulative this pass. Hashes, modes, runs:
`evidence/readers-124525.json`.

`tests/manager/test_secrets.py` was not touched; its bytes still hash to
owner124487's approved `9104bf90…`, verified in the evidence, and the 198-test
run includes its accounting check. No inventory run.

### Next

Independent reassessment at `baton.bug`. W122060 and W119114 remain gated.
