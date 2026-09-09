# Progress

Implementation entries belong to the assigned change author.

## 2026-09-09 — baton.claude, claim 128724

**Claimed first**, at seq128724, before reading further and before any edit.

### Revalidation against the current tree

All three baseline hashes and modes in `evidence/baseline.json` still match the
tree exactly: `intake.py` `b5b0706f…` 664, `__init__.py` `0c417699…` 644,
`test_intake.py` `8598ff95…` 664. Nothing pinned has drifted.

The recorded facts are confirmed by reading the code rather than the record:
`abandon_attempt` commits `attempt.abandon` before any external call, fences
through `port.cancel` with the adopted record's own operation id and reason,
and journals the whole composite `{intent, fenced, cleanup}` under
`runtime.destroy-abandoned` only after a positive absence. The ordinary
`discharge_quiescence_gate` derives its proof through `_absence_proof`, which
requires an `intake_receipt_of` and reads `runtime.destroy` BY NAME — an
abandonment has neither, which is exactly why a separate family is needed
rather than a widened one.

I confirmed the two things the FINDING forbids are real hazards and not
hypothetical: the mutable `execution_runtime = destroyed` column is reachable
by a store edit, and there is no intake receipt to fabricate a destroy identity
from. Neither is used.

### Question and budget, declared before any run

Does a committed abandonment supply its own absence evidence — read only from
the journal, bound whole to the declaration, the fence and the removal — and
can that evidence discharge exactly the gate its own fence installed, once,
replayably, without touching the ordinary family?

Budget: **20s cumulative** across every test and probe process, starting from
0/20s as the dispatch revalidation recorded. Every iteration is charged and
never reset.

### Selectors, declared before running

`tests.manager.test_intake` — the whole module, because the ordinary
cleanup/discharge families live in it and "unchanged ordinary-family behavior"
is half the contract. New cases are added to it; no other module is run unless
this one implicates one.

### Delivered — the abandoned family's own evidence, act and receipt

`abandonment_cleanup_of`, `discharge_abandoned_quiescence_gate` and
`abandoned_gate_discharge_of`, with the exact names, operands, members and
schemas CONTRACT.md pins, exported from `worker_manager.intake` and re-exported
from `worker_manager/__init__.py`. Nothing was renamed and nothing added beyond
the pinned contract.

**No fabricated receipt.** The declaration's digest rides the removal identity
exactly as the intake receipt's digest rides the ordinary one. No intake
receipt is read, derived or invented.

**No mutable absence.** `execution_runtime`, the cleanup axis and the Work's
current route and gate are never read as evidence. What is read is the journal:
the committed declaration, the committed `{intent, fenced, cleanup}` composite,
and the relationships between them. Both rows are held to a signature
recomposed from their own members rather than replayed under whatever the row
carries — `cleanup_of`'s 2026-09-08T16-43-59Z [P1] rule — and the cleanup's
operation is compared whole, because `operation_id` binds the attempt,
assignment, declaration and policy while `signature_digest` is the half that
binds the runtime.

**A distinct identity.** The discharge identity is derived over the attempt and
its fixed assignment alone, so a resuming manager re-derives it without first
re-establishing the evidence. The kind prefix is what keeps it from colliding
with the ordinary discharge, which signs an identity over the same two operands.

**Remote before local.** `satisfy_gate` commits first and the journal second,
and the committed replay is read before any mutable state — so a lost local
receipt reissues the identical remote operation and the Authority's own replay
answers it, even after the Work has been ungated.

The ordinary family is untouched: `cleanup_of`, `gate_discharge_of`,
`discharge_quiescence_gate`, `_absence_proof` and `_adopted_discharge` are
unchanged, and the only edit to existing bytes anywhere is one import line
adding `FENCE` and `GATE_DISCHARGE`.

### Measured rather than assumed

I expected a surviving runtime to leave nothing journalled. It does not:
`_settle_recordless_cleanup` commits the composite with the ending `failed`. So
the reader refuses on that fact rather than answering absence — and the category
is `refused/precondition`, not an integrity fault, because the record is this
family's own committed act and there is nothing wrong with it. That is exactly
what `_absence_proof` decides for the ordinary family's `failed` ending.
`test_a_runtime_that_survived_its_removal_supplies_no_absence` registers it and
also proves the gate stays shut.

### Proof

24 cases in `TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence`, over the
real store, journal, derived identities and `AuthorityPort` crossing: the
successful arc and its replay; a lost local receipt; a later Work generation;
another participant, authority, policy, runtime, kind and signature; an
undeclared attempt and an unfinished declaration; a surviving runtime; a
receipt edited member by member; and three cases proving the ordinary family
still behaves exactly as before.

**180 tests OK** in `tests.manager.test_intake` — 156 existing and 24 new, with
no existing assertion changed.

### Reported, not worked around

Two whole-universe SOURCE scans require every public callable and every boundary
call to be declared, and **both files are outside owner128669's three authorized
paths**:

- `tests/manager/test_text_sweep.py` — its callable table does not name the
  three new public operations.
- `tests/manager/test_boundary_inventory.py` — 121 boundary calls attributed to
  no entry, 31 in the abandonment family. Four of those are W44716's own
  (`_abandon_intent`, `_abandon_operation_id`, `_abandon_fence_operation_id`,
  `_abandoned_destroy_operation`), untouched by this claim, so the shard was
  already failing for this family before the change; what this claim adds are
  the calls in `_abandonment_declaration`, `_abandoned_fence`,
  `_abandoned_absence` and `_adopted_abandoned_discharge`.

Neither file was edited. The FINDING requires consumer coordination for public
names, and editing an unauthorized whole-universe scan to accept my own names is
the kind of thing that should be decided rather than taken on the way past.
Separately, `tests.manager.test_dependencies` fails on
`AuthorityPort:satisfy_gate`'s `gate` parameter — W119548's, predating this
claim; my two keyword operands are already declared operands.

### Runs

179/19 errors (3.113s) → 23/19 (0.411s) → 23/3 (0.431s) → 24 OK (0.454s) →
180 OK (3.151s) → the two scans (0.316s) → the inventory twice (2.408s +
2.402s, the second with `maxDiff` lifted to read the actual list).
**12.69s of the declared 20s, 7.31s left, no reset.** Commands, logs and hashes:
`evidence/provider-128724.json`.

Passing back to `baton.bug` unaccepted. W128692 still waits for actual
independent acceptance; no consumer may use these names before it.

## 2026-09-09 — baton.claude, claim 128828 (correction)

**Claimed first**, at seq128828, before reading the review and before any edit.

Both findings are correct and I am not arguing with either. The three candidate
hashes still match what I submitted, so nothing drifted under me.

### Selectors and remaining budget, declared before running

Carrying **7.31s** of the 20s cap, not reset. Selectors, exactly:
`tests.manager.test_intake.TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence`
while iterating, then `tests.manager.test_intake` once for the ordinary-family
regression. No inventory or full-suite pass — the review rules that out and the
scan accounting stays outside this allocation either way.

### What the corrections are

**P1, the fence.** `fenced` was truthy rather than `True`, and cause and phase
were not checked at all. The exact semantics are not mine to invent: the
Authority itself pins them in `authority/core.py`'s `route_fenced`, which
compares a cancellation against `{"cause": "cancelled", "assignment": expect,
"phase": "block", "gate": gate, "fenced": True}`. That is what this now
requires, still derived from the receipt's own assignment so a historical read
survives the Work advancing.

**P1, the cleanup.** `kept` and `directory_custody` were unchecked and `kind`
was wrongly admitted as optional. `_settle_recordless_cleanup` writes no `kind`
at all here, so the member set is now exactly `CLEANUP_RECEIPT`; an abandonment
intakes nothing and decides no retention, so `kept` must be exactly `[]`; and
both normalization receipts are compared against
`custody.historical_directory_custody`, the normalization owner's own read, so
this module holds no second copy of that protocol and does not widen the
ordinary family's retention comparison.

**P1, the comments.** My "a failed removal never journals" was wrong, and my own
measured test already said so in the same claim. Corrected in both places.

**P2, the replay.** The committed-replay branch validated the receipt's own
signature and never compared the supplied policy, so policy 9 replayed policy
7's success. It now compares the operand against the committed receipt — from
the receipt alone, with no mutable cleanup or Work state read, so the lost-
receipt retry and the later-generation replay both still work.

### Delivered

Ten additive controls, all inside the existing class. Each negative also proves
the half the probes were actually about: **no remote act and no local discharge
receipt follow the refusal** — the finding was one real `satisfy_gate` call
behind bad evidence, not merely a permissive read.

- fence: a truthy non-boolean, another cause, another phase, another assignment,
  another gate;
- cleanup: custody `None`, a present-but-wrong normalization, invented `kept`
  material, a foreign `kind`;
- and one control proving a valid read still answers after the Work advances,
  which is the property the review required preserved.

For [P2], one control proves another policy collides with no second remote act
and no second receipt, and one proves the same policy still replays after the
Work has moved on — the property the collision must not cost.

**34 in the class and 190 in the module, OK.** 156 existing tests unchanged.

### Runs

34 OK (0.603s, first run after both corrections) → 190 OK (3.292s).
**3.895s this pass, 16.585s of 20s cumulative, 3.415s left, no reset.**
No inventory or full-suite pass: the review rules it out, and the scan
accounting for the new exported callables and receiving sites stays outside this
allocation — its logs remain in `evidence/provider-128724.json` and are not
waived. Detail: `evidence/provider-128828.json`.
