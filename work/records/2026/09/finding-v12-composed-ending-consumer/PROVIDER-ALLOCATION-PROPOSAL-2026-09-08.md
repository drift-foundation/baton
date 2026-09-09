# Attempt-keyed historical writer and review readers

**Approved 2026-09-09, owner event124318.** baton.slaw approved this exact
proposal, including the three paths, both contracts, committed-history and
typed-identity requirements, additive tests, all exclusions, High serial
baton.impl execution returning baton.bug, and the20-second focused budget.
Create/bind the provider and gate W122060 on actual independent acceptance;
retain W119114's dependency and full lifecycle obligations. This supersedes
all pending-approval language below; approval does not accept implementation.

**Proposed for owner allocation; no implementation authority yet.** Prepared
by baton.codex under W122060 claim122105 after the unchanged handback122089.
The owning FINDING pins the confirmed gap. Consumer scope remains four files.

## Recommended accountable delivery

Create one High-priority provider Work, serial baton.impl returning baton.bug,
with its own permanent child dossier beneath this record:
`baton:work/records/2026/09/finding-v12-composed-ending-consumer/findings/finding-attempt-history-readers/`.
Gate W122060 on its actual independent acceptance; W119114 keeps its W122060
gate and final lifecycle acceptance. Allocate exactly these paths relative to
`v12/python/`:

1. `src/baton_v12/worker_manager/review_cycles.py`: add the two local readers
   and only their necessary private validation/selection helpers.
2. `src/baton_v12/worker_manager/__init__.py`: export both public readers.
3. `tests/manager/test_review_cycles.py`: additive focused public reader tests.

Preserve all existing assertions and operation/reader behavior. Do not change
schemas, journal formats, deployment paths, shared inventory or test registries.
If a required correction cannot fit these paths, report it before expansion.
No new live runtime/Authority/engine or Git authority follows from allocation.

The two readers supply the same missing historical selector boundary to the
same consumer ending. They share one owner module, identity validation and
existing fixture; a bounded three-file provider is independently acceptable.
Separating them into overlapping serial Works would not separate a new
implementation boundary. The consumer ending and full lifecycle already have
their own independent acceptance gates.

## Exact proposed public contract

    writer_for_attempt(store, *, attempt_id, generation) -> writer row or None
    review_for_attempt(store, *, attempt_id, generation) -> attachment row or None

Validate attempt identity and generation with existing typed boundaries before
selection; boolean generations refuse. Select by the exact pair across all
historical states, without an active-state filter, current line/checkpoint
pointer, profile, port, runtime adapter or remembered selector. Both tables
already enforce UNIQUE(runtime_attempt_id, assignment_generation); reuse that
owned invariant and pin it in focused evidence, without schema changes.

No matching row for a valid pair answers None, including a never-recorded
attempt or another generation. A selected malformed, foreign or uncommitted
record raises ContractRefusal, never None or an unchecked parser/type error.
The selected identity must belong to the requested pair and to the durable act
that created it. No inserts, updates, transaction/savepoint creation, physical
line revalidation, remote reads or external acts occur. Return the established
row shape with its current historical state; revoked writers and ended reviews
are valid history, and those mutable states are not forced back to the original
grant/attachment result's active state.

**Writer ownership needs more than writer_of alone.** That existing reader
owns row shape; it does not bind the row's immutable members to the committed
grant. The new reader must establish the grant identity and committed journal
correlation inside the owner. Compare exact typed immutable selectors and
operands, including writer/line/attempt/generation, worker, participant,
principal, profile identity and based_checkpoint_id, with the owned writer,
line and fixed assignment facts. Validate the consumed committed signature/
result and its deterministic operation identity; foreign records, missing acts
and changed original base checkpoint refuse. An active result in the committed
grant is historical evidence, not a demand that the writer still be active.
Keep any added stricter validation private to the new boundary; do not silently
redesign writer_of or grant_writer.

**Review ownership reuses review_of** for committed attachment/row/checkpoint
correlation, with exact requested-pair and selector validation at the new
entry. Validate any additional persisted values the new reader consumes before
comparison or return. Do not repeat current eligibility, independence or
profile admission through attach_review. An ended attachment remains readable
after correction advances the line. Existing review_of behavior stays intact.

The owning module may derive its own deterministic IDs; consumers must not
copy those derivations, parse journal signatures or query provider SQL.

## Focused acceptance and retained limits

Use the actual public grant/attachment operations with existing local fixtures.
Prove both readers return their existing writer_of/review_of row shapes for the
correct pair, before and after writer revocation/review ending. Reopen the
store, forget IDs, and advance the real line through public correction and a
later checkpoint; the earlier pair still selects the original writer/base and
attachment/checkpoint. Same worker on later attempts must not confuse them.

Controls: absent pair; wrong generation; boolean/malformed inputs; wrong
selected row identity; changed attempt/generation/base checkpoint or reviewer
binding; missing/wrong-kind/uncommitted/malformed journal; and a foreign act
filed under the selected operation. Correlate typed generation values rather
than Python bool/int equality. Independently prove no SQL writes/transactions
or profile/Authority/adapter access during positive and negative reads.

Record the concrete question and cumulative budget before execution. Proposed
budget20s: new controls, then affected review-cycle module once if needed;
reuse accepted provider/component evidence instead of broad suites. Return
exact candidate hashes/modes, commands, outcomes and fixture limitations for
independent acceptance. This provider proves discovery and ownership only;
W122060 still owns executable ending recovery and W119114 the assembled proof.

## Owner decision requested

Approve this exact one-provider allocation, three paths, two public contracts,
additive-test boundary, High serial implementation/review route and actual
acceptance dependency; or identify an existing public owner that already
supplies these historical selectors. No implementation has started and no
provider dossier/Work has been pre-created as if approval existed.
