# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

Not started; approver decision required before implementation.

## 2026-09-02 — `baton.claude` (implementer)

The line above is kept as the state it recorded. The approver ruled on
2026-08-28 and reaffirmed the ruling on 2026-09-02, so PLAN item 4 was
executed under it: the Python offer boundary is corrected, the obsolete
bearer-carrying decline expectations are replaced, and the regressions the
ruling names are added. Awaiting review.

### Revalidation before the change

Read fresh and re-checked against the tree rather than against the record:

- **Confirmed.** `work/.../finding-worker-control-api-manifests/SPEC.md` §6.1
  states the asymmetry ("`claim_token` is `null` for a decline"), §12 rule 14
  states that schema proves only the null/string shape while the manager
  additionally proves the binding, and §13 keeps the bearer off the wire for a
  decline. §14 decisions 6–8 pin it and mark W151 §7 superseded. The runtime
  conformance SPEC carries obligation `C-08` and its three cases.
- **Confirmed.** The stale half is exactly where the finding says: the Python
  `accept_offer` proved possession BEFORE it branched on accept versus decline,
  so a decline carrying the bearer settled the offer `declined` and a decline
  without one was refused `refused/capability`.
- **Confirmed.** An exact acceptance retry was refused `refused/already-terminal`
  merely because the verifier it correctly presented was now spent.
- **Confirmed.** The two live durable rulings do not conflict; nothing needed a
  new supersession note, so `FINDING.md` and `PLAN.md` were not edited.

### What changed

`v12/python/src/baton_v12/worker_manager/offers.py`, `accept_offer` only:

1. **Absence is a value the boundary can prove.** A module-private `_NoBearer`
   sentinel, spelled like the authority's own `ABSENT`, is the default of the
   `bearer` operand. A decline is written by OMITTING the operand; `None` and
   `""` are carried values, not spellings of absence. It is deliberately not
   exported: the package's `__init__` is outside this Work's path set, and a
   caller declines by leaving the operand off, so nothing needs the name.
2. **The shape rule runs before the binding comparison.** A decline carrying
   any bearer value is `integrity/schema`, raised before anything is compared
   or written, so the offer row and the journal are untouched.
3. **Possession is proved only for an acceptance**, unchanged otherwise:
   constant-time comparison against the stored verifier, `refused/capability`
   for a missing, wrong or foreign bearer.
4. **An exact repeat of a committed decision replays it**, decided before the
   single-use and terminal-state refusals. An acceptance replays the frozen
   acceptance columns through `documents.offer_accepted`; a decline replays
   through `_settle_terminal`, so the store's own journal answers both the
   replay and the collision.
5. **The decline act mints nothing and holds nothing.** It consumes the
   verifier in the same compare-and-swap that makes the offer terminal, and it
   no longer opens a `held_secret` scope, because on this path the manager is
   never handed the secret.

Expiry, the per-Work CAS, the acceptance CAS and the claim path are unchanged.

### Two decisions a reviewer should weigh

- **The acceptance replay is keyed on the acceptance FREEZE, not on
  `state == 'accepted'`.** Submitting the claim moves the offer to `claimed`
  and does not unmake the acceptance that operation committed, and §10.2 says
  an exact committed reply replays. Keying on the state would have refused the
  retry as soon as the claim was submitted — the same "failing a retry for
  being a retry" defect one step later. The five acceptance columns have one
  writer and the terminal transitions compare-and-swap from `issued`, so their
  presence is a sound record of "this offer was accepted".
- **§13's hold on the decline path is gone because there is nothing to hold.**
  The old scope existed for a decline whose `reason` QUOTED the bearer; that
  decision is now refused one step earlier as a carrying decline. A worker that
  declines correctly but quotes its own bearer in the reason would still put
  that text in the settlement, and this manager cannot detect a secret it was
  never given. The leak is inert — the same act spends the verifier, so the
  quoted value authorizes nothing afterwards — but it is a real narrowing of
  what the walk covers on this one path, and it is stated here rather than left
  for a reviewer to find. No new detection rule was invented for it; that would
  be a ruling this record does not carry.

### Tests

`v12/python/tests/manager/test_offers.py`

- `accept()` is unchanged and a `decline()` fixture is added beside it, which
  omits the operand; `**overrides` is how a case puts one back.
- Replaced, as the 2026-09-02 ruling authorizes: the decline half of
  `test_the_bearer_is_single_use_across_every_outcome` (it carried a bearer,
  and its acceptance half asserted that an exact retry is refused). It now
  settles each decision through that decision's own operand set and asserts
  what single use still means — the OTHER decision cannot happen afterwards and
  rewrites nothing. `test_a_decline_cannot_be_replayed_into_an_acceptance` is
  the same case with a bearer-free decline.
- Added `TheDeclineCarriesNoBearer`: the positive decline (terminal, verifier
  spent atomically, none of the five acceptance freezes written); a carrying
  decline refused `integrity/schema` for this offer's own bearer, another
  offer's, `""`, `None` and a non-text value, with the row and the journal
  unchanged and the offer still declinable; exact decline replay, including at
  a later instant; a reworded decline refused `refused/operation-collision`
  with the committed decline still replayable; a differently bound decline
  refused before and after the commit; a late decline still settling the row
  `expired`; and a decline of an offer another act accepted refused
  `already-terminal` with the frozen claim identity intact.
- Added `test_an_exact_acceptance_retry_replays_the_committed_acceptance`
  (including past `submit_claim`) and
  `test_a_wrong_acceptance_retry_is_refused_rather_than_replayed`.

`v12/python/tests/manager/test_secrets.py`

- `test_a_decline_that_quotes_the_bearer_is_refused` asserted `secret-leak`
  from a bearer-carrying decline, which the ruling removes. Replaced by
  `test_a_decline_that_carries_the_bearer_is_refused_before_it_settles`:
  `integrity/schema`, the bearer never live, and neither the public refusal nor
  the store carrying it. Added
  `test_declining_holds_no_bearer_and_leaves_nothing_behind`.

`v12/python/tests/manager/test_boundary_inventory.py`

- The stated rule for `offers.py:accept_offer`'s `bearer` now states both
  halves, and its witness is renamed
  `test_the_bearer_is_acceptances_capability_and_no_declines`: three acceptance
  refusals, three carrying-decline refusals, and the bearer-free decline that
  settles — so the rule refuses a carried value rather than the decision.
- `test_prose_rides_the_signature_that_records_it` declines without the bearer;
  its surrogate-reason assertion is unchanged.

`v12/python/tests/manager/test_lifecycle_composition.py`

- One obsolete call site: the declined-offer lifecycle case drops the bearer.

Nothing else was touched. `FINDING.md`, `PLAN.md`, both SPECs, the schemas, the
generated conformance cases, the evidence digests and the dogfood machinery are
unchanged.

### Verification actually run, and what it could not reach

The required vector is

```
env PYTHONPATH=v12/python/src python3 -B -m unittest -v \
  v12.python.tests.manager.test_offers \
  v12.python.tests.manager.test_secrets.TheBearerIsHeldForTheActsThatSpendIt \
  v12.python.tests.manager.test_boundary_inventory.StatedRules
```

In this isolated copy it cannot complete, for reasons that are the environment's
and not the change's, and the same limits hold on the unmodified baseline:

- `test_offers` runs whole and passes: **71 tests, 0 failures** (62 before).
- `test_secrets` and `test_boundary_inventory` do not IMPORT here. They pull in
  `.test_interrogation`, `.test_handshake`, `.test_output` and `. input_roots`,
  none of which is part of the supplied copy, and
  `test_boundary_inventory.StatedRules` also reads
  `finding-worker-control-api-manifests/evidence/vectors.json`, which is not
  supplied either.
- The sandbox has Python 3.11 with no `pip`, no writable exec mount and no
  `jsonschema`; the distribution requires Python ≥3.13 and pins
  `jsonschema==4.26.0`. `jsonschema` 4.17.3 was installed into the user site
  (pure Python; 4.26.0's `rpds-py` extension cannot be mapped from a `noexec`
  filesystem). Under 3.11, `custody.py`'s PEP 701 multi-line f-string does not
  parse at all, which is what the AST-derived inventory classes walk.

So the vector was driven two further ways, both outside the tree:

1. **The three targets, with the absent sibling modules stubbed** to raise
   `SkipTest` when used, so a case that depends on one is visibly skipped rather
   than quietly passing: **148 run, 127 passed, 33 skipped** (all naming an
   absent fixture), **1 error** — `test_the_input_pair_is_owned_by_the_contracts_own_composite`,
   which reads the absent `vectors.json`. No failures.
2. **All four supplied test modules, in a scratch copy** whose `custody.py`
   f-string is rewritten to parse under 3.11 so the AST inventory runs, against
   BOTH this tree and the pristine baseline. Outcomes are identical except for
   the added and renamed cases: **3 failures and 6 errors on both**, all
   environmental (the 3.11 rewrite, the absent `vectors.json`, and `docker` not
   on `PATH` for the lifecycle gate). Nothing that passed on the baseline
   changed.
3. The two inventory entries this change ADDS — `offers.accepted_at` and
   `offers.intent_digest`, read by the acceptance replay — were checked against
   the inventory's own rules: each is owned exactly once, by
   `boundaries.row(..., "a persisted offer")` at `offers.py:_offers`, like every
   other column of that row; and `column_probes` derives a probe for each from
   the table contract, which was driven by hand and refuses with
   `integrity/schema` naming "a persisted offer".

**The vector must still be run intact** — Python ≥3.13, `jsonschema==4.26.0`,
the full test package and the W6 evidence present — before this is integrated.

### Remaining, and not done here

- The W6 seal evidence `.../finding-v12-local-conformance-proof/evidence/w6-seal/decline-bearer.json`
  measured the stale behaviour. It and any register or case digest it feeds are
  outside this Work's authorized path set and are untouched; regenerating them
  is deliberate follow-up, not a silent side effect of this change.
- Not staged, committed, merged, or applied to the host checkout.

## 2026-09-02 (second entry) — `baton.claude` (implementer)

The entry above is kept exactly as it recorded its own state. This is the
correction turn for `review-2026-09-02T13-54-46Z.md`, taken from the retained
run1 checkpoint whose tree digest is
`sha256:48aac3978aef2b7b7b06f01cce981b046dcebe83ca0fa84f454877c2a9ed0b2e`.
Both P1 findings are corrected and nothing else about the ruled contract is
touched. Awaiting review.

### The two corrections

**[P1] A foreign participant-bound session could decline another
participant's offer.** `accept_offer` proved the offer/attempt/Work binding and
— for an acceptance only — possession, and never compared the live session. The
ruling authorizes a decision by the caller's participant authority AND the exact
binding (`FINDING.md:43-45`); once the bearer left the decline path, the second
half was the whole proof, and an offer's binding is ordinary coordination data
rather than a secret. `offers.py:accept_offer` now compares `port.participant`
against the participant the offer froze at issue and refuses
`refused/capability` naming both identities. Both sides are already owned — the
port proves its binding when the session enters the manager, the row's column
contract proves what was frozen — so this is the relation and not a second
crossing, and PLAN 4bz's no-blanket-revalidation rule is intact.

Placement, deliberately: after the carrying-decline SHAPE refusal and before
every binding comparison, replay shortcut and settlement.

- Before the replays as well as the settlements, which is what the review asked
  for: a committed acceptance's answer carries the frozen claim identity and a
  committed decline's carries the recorded settlement, and replaying either to
  a session that does not hold the authorization would answer a question it was
  never party to.
- Still AFTER the shape rule, so the existing invariant that a bearer-carrying
  decline is refused `integrity/schema` with nothing compared or written stays
  literally true. A foreign session that also carries a bearer is refused for
  the carried token rather than for its binding; neither refusal settles or
  replays anything, so the property the review required holds either way.

**[P1] Concurrent exact acceptance retries collided when their observation
instants differed.** `accepted_at: now` was a member of the acceptance intent
digest, the digest is the operand of the `offer.accept` operation signature, and
the derived `claim_operation_id` came from it too. The sequential replay hid it,
because a retry that reads an already-accepted row never reaches the derivation;
two concurrent retries both read the offer `issued`, derived two digests, and
the one that lost the write lock met the winner's journal row under a signature
of its own — `refused/operation-collision`, which is failing a retry for being a
retry, the same defect this Work had already corrected one step earlier.

`accepted_at` is removed from the digest. Every remaining member is frozen at
ISSUE, so one offer has one acceptance identity however its caller reads the
clock, and both callers commit under one operation signature. Nothing is lost:
`accepted_at` and `settle_by` remain committed columns and members of the
answer, and the loser replays the winner's recorded bytes — so both callers
receive the FIRST accepted instant beside the one fixed claim identity, which is
what the retry was asking for. `claim_operation_id` is now a pure function of
the offer's frozen facts, which is if anything stronger for restart recovery:
`offer_id` is the table's primary key, so one offer still has one derived claim
identity and no reissue can collide with it.

### Preserved, and checked rather than assumed

Bearer-free decline and its `integrity/schema` refusal of any carried value;
possession proved in constant time for an acceptance only; the attempt, Work and
authority binding comparisons and their `refused/precondition` code; expiry as a
settlement on both paths; the per-Work issue CAS; the `issued`-only terminal CAS
in `_settle_terminal`; the acceptance CAS; the decline minting and holding
nothing. `FINDING.md`, `PLAN.md`, both SPECs, the schemas, the generated
conformance cases, the evidence digests and the dogfood machinery are unchanged.

### Tests

`v12/python/tests/manager/test_offers.py` — additive only; no existing case was
edited or weakened.

- `TheDecisionIsTheBoundParticipantsAlone`: a foreign session's decline refused
  `refused/capability` with BOTH the row and `offer.declined:offer-1` unchanged
  and the offer still declinable by the bound session; a foreign session's
  acceptance refused even while carrying the exact bearer, with the row and
  `offer.accept:offer-1` unchanged; a foreign session refused the REPLAY of an
  already-committed acceptance and an already-committed decline, after which the
  bound session still replays both unchanged; and the participant compared ahead
  of the binding it names.
- `ConcurrentExactRetriesShareOneOperationIdentity`: two managers on their own
  connections, held at a barrier inside `transact` so both pass their read of
  the issued row before either takes the write lock, accepting the same offer at
  two different instants. Both receive the same committed answer member for
  member, the row is written once, its `accepted_at` is one of the two observed
  instants and is the one both callers were told, and the fixed claim identity
  derives from the committed intent. Its companion case pins the intent's
  OPERAND SET — the seven facts frozen at issue, and a derivation that also
  carried the accepted instant is a different digest — because no sequential
  call can tell whether the clock went into the digest it merely replays.

These are the durable equivalents of the two immutable cases in
`test_w33937_review_probes.py`, which is untouched.

### Verification actually run, and what it could not reach

The supplied exact vector is the only command run:

```
env PYTHONPATH=v12/python/src python3 -B -m unittest -v \
  v12.python.tests.manager.test_offers \
  v12.python.tests.manager.test_secrets.TheBearerIsHeldForTheActsThatSpendIt \
  v12.python.tests.manager.test_boundary_inventory.StatedRules \
  v12.python.tests.manager.test_w33937_review_probes
```

In this isolated copy all four targets fail at IMPORT and no test body runs:

```
ModuleNotFoundError: No module named 'jsonschema'
Ran 4 tests in 0.000s
FAILED (errors=4)
```

Two independent environmental blockers, neither of them this change's and both
present on the unmodified files in the same copy:

- the distribution requires `jsonschema==4.26.0` and the sandbox has no
  `jsonschema` and no authorization to install one; and
- the distribution requires Python `>=3.13` and the sandbox has 3.11.2, under
  which `worker_manager/custody.py` does not parse at all (PEP 701 multi-line
  f-string, `SyntaxError` at line 752).

The immutable `test_w33937_review_probes` fails identically and for the same
import, which is the evidence that the failure is the environment's: this turn
changed neither that module nor anything it imports before `jsonschema`.

Nothing else was run. In particular no unittest discovery, no broader suite, no
baseline comparison, no `pip`, and no dependency setup — the previous packaging
attempt exhausted its tmpfs on exactly that work after its own focused gate had
already passed, and repeating it would buy nothing. The only other command used
on the source was `ast.parse` over the two edited files (and over `custody.py`,
to establish the second blocker above), which executes nothing and writes
nothing. Every Python invocation ran under `PYTHONDONTWRITEBYTECODE=1` with
`-B`; the copy contains no `__pycache__` directory and no `.pyc` file.

**The vector must still be run intact** — Python >=3.13, `jsonschema==4.26.0`,
the full test package and the W6 evidence present — before this is integrated.
The change is offered on that condition and not as a passing gate.

### Remaining, and not done here

- The W6 seal evidence
  `.../finding-v12-local-conformance-proof/evidence/w6-seal/decline-bearer.json`
  still measures the stale behaviour, and it and any register or case digest it
  feeds remain outside this Work's authorized path set. Regenerating them is
  deliberate follow-up.
- Files changed this turn: `v12/python/src/baton_v12/worker_manager/offers.py`,
  `v12/python/tests/manager/test_offers.py`, and this `PROGRESS.md`. Nothing
  else in the copy was modified.
- Not staged, committed, merged, or applied to the host checkout.
