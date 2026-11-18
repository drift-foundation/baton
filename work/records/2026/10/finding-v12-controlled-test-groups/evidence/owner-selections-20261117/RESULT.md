# Owner selections implemented — renewal option A, settle_cleanup option 1 (M385028)

K, copilot under owner claim E384905, no claim held. Ruling:
`RESUME-DECISIONS-20261117.md`. Packets: `evidence/stage-c-2026-10-30/RENEWAL-DECISION.md`,
`SETTLE-CLEANUP-DECISION.md`. Clarification pinned in the owning renewal record:
`work/records/2026/09/finding-v12-token-renewal/FINDING.md` (2026-11-17 entry).

## Renewal option A (tokens.py)

- `RENEWAL_DECIDED_KIND = "resource-token.renewal-decided"`, identity
  `_renewal_decision_id(domain, generation, revision)`.
- `_extended.extend(connection)`: after every condition is re-proved under the write lock,
  writes the DECISION record with `control._record` -- operands = result =
  `{version, domain, generation, revision, renewed_at, expires_at}` -- then returns the
  request result as before. `_acting_record` commits both or rolls both back. The request
  record's identity, signed operands and lost-reply replay are unchanged; a changing clock
  is still not part of retry identity (test: replay under another clock, one record each).
- `_verified_renewal(control, domain, generation, revision, request)`: reads the decision
  through `store.replayed_as_signed` (result == signed operands, else refuses); refuses an
  absent decision ("no committed decision record" -- every pre-correction renewal), a
  decision naming another version/domain/generation/revision ("a decision about another
  renewal"), and a request whose `renewed_at`/`expires_at` differ from the decision ("the
  request result was changed after the renewal was decided").
- Every read and replay passes through it: `_renewals_of` (token_of, `_owning` for every
  owner-gated act, `_judge_expired`, the renewal preflight) and the direct `renew` retry
  (`_acting_record`'s replayed result is verified before it is answered).
- No migration or adoption of old result bytes; no DESIGN text change; same `operations`
  schema.

## settle_cleanup option 1 (workspaces.py)

After the admission-shape check and before any read or write: refuse unless
`connection is control._connection` and `connection.in_transaction`. The guarantee is
stated accurately in the docstring: `in_transaction` proves an open transaction on this
store's connection; the write-lock mode is the accepted `transact` caller's
`BEGIN IMMEDIATE`. Writes stay through `_record`. The inventory row for `connection` is
restated as this inline proof, witnessed by
`StageCProtections.test_a_cleanup_settlement_runs_only_inside_its_endings_transaction`.

## Folded in: the wrapper P1 (review 2026-11-17T19:43:26Z, M385032)

`_callee_gap` admitted a same-module/self/package callee and `_owned_construction` then
traced only the ARGUMENTS, so a package wrapper around a producer (`_read()` returning
`json.loads(...)`, `os.environ.get(...)`, or the same as a method) owned its result by
membership. Correction (test_boundary_inventory.py, StageCProtections):

- `_owned_call_result`: a package callee's result is owned only when EVERY value it
  returns is traced at the callee's own site (its own scope, not nested defs; a callee
  that yields fails closed), with that callee's origins; a returned parameter is traced
  through every caller by `_owned_caller`, so the call's arguments are proved through the
  returns rather than separately. Memoised per callee within one trace (sound: the proof
  is caller-independent). Aliased package modules (`context._document`) resolve to their
  module. A package constructor is construction (its attributes are traced when read).
  A package callee whose source the inventory does not read fails closed, except the
  contracts layer's two manifest validators (`check_manifest_structure`,
  `check_content_manifest`: schema + digest + no-secret walk over an owned copy), admitted
  as validators, and the five composers of their arguments (`digest`, `digest_of_bytes`,
  `canonical_text`, `name_value`, `sample_of`).
- A validator call (`boundaries.<rule>(...)`, the two above) is recognised BEFORE `_source`
  strips the layer to its argument's origin.
- `self.a, self.b = helper(...)` binds the attributes (tuple targets).
- Composers added with justification, each in the test's own tables: `uuid.uuid5`/`uuid3`
  (deterministic derivation of traced arguments; not uuid4); `os.open`/`fstat`/`stat`/
  `lstat`/`scandir`/`listdir`/`walk` (the kernel's answer about a traced path or handle of
  the manager's own storage -- a descriptor, a stat result, entry names -- not content
  anybody handed in; reading THROUGH a descriptor stays unowned); `quote`/`unquote`/
  `urlsplit`/`urlparse` (re-spellings and partitions of traced text); `object()` (an
  opaque sentinel); a composing builtin's constructor method (`dict.fromkeys`). A library
  CONSTANT (`os.O_RDONLY`, `stat.S_IRWXU`, `uuid.NAMESPACE_OID`: the all-capitals name) is
  fixed by the library; `os.environ`, `sys.argv` and every lower-case module value stay
  unowned. `digest`/`digest_of_bytes`/`hashlib.sha256` are identity-shaped DERIVATIONS:
  their argument's content cannot cross as content and a key is bound by what its lookup
  verifies, so the argument is not traced (this is what stops the `_id(prefix, value)`
  helper's forty callers from fanning every proof out to every value ever keyed).
- Shapes the trace now follows exactly (each a real binding form found by the audit, not an
  exemption): a store `transact(...)` call's result is its action's return (the lambda body
  or the named function's returns), traced -- the replayed branch answers journal result
  bytes `replay` does not bind, the W375444 REPLAY_DEBT class, stated and not papered over;
  a callable PARAMETER that is invoked (`reader(...)`) is followed to what every caller
  hands -- a lambda, a local bound to one, or a package function -- for a private helper, and
  fails closed as an injected capability for a public door; a nested function's parameter
  (`def walk(parent, ...)`) is whatever every call of it inside its enclosing function hands,
  recursive calls included; a generator's yields are traced like returns; function-level
  imports (`from .store import manager_signature` inside a body) classify like module ones;
  a rebound name (`report = _qualification_review(...); report = _document(report, ...)`) is
  traced through its rebinding, which consumed the earlier value; a parameter cycle
  (`_transition -> _operation -> _id -> _transition`) is under proof by the outer frame and
  adds no source. Depth bound 16 function hops (12 module-binding hops) with the per-hop
  loop guard.

Witnesses: `test_the_owned_input_trace_follows_a_package_wrapper_to_what_it_returns`
(the reviewer's three wrapper universes, a wrapper returning its unowned parameter, a
generator wrapper -- all rejected; validated wrappers, a wrapper returning its OWNED
parameter and a validated method accepted). `reviewer-wrapper-probes-after.log` and
`reviewer-trace-probes-after.log`: all six REJECTED. Operand audit under the final trace
(`operand-audit.txt`): 28 of 28 traced at every call site, 0 failures (48 s; the failure sequence that drove the trace rules is in work/scratch/w384870-c/audit-28-w1.txt onwards). Rows whose proof depended on the shortcut and how
they are proved now: `context_output_declaration outputs` and `copied_manifest
max_bytes/max_entries` (through `check_manifest_structure`, now an admitted validator);
`serving_argv facts/profile` (through `provider_context._document` ->
`boundaries.document`, the validator-first rule, and `uuid.uuid5`); `discard_tree place`
(`self.assignment_roots` bound by tuple unpacking from `_roots`, whose returns are a
`boundaries.document` or an `AllocatedRoots` instance). None un-stated.

## Tests (focused first; no scans/Docker/B4/full/live)

- `test_stopped_settlement.RenewalDecisionRecord` (9): honest renewal writes both records
  and reads through both (decision == its signed operands; request signs no clock); lost
  reply under another clock replays the same renewal with no second decision and a skipped
  revision refuses; rewritten request `expires_at` and `renewed_at` refuse at token_of, the
  direct renew retry and an owner-gated act; corrupted decision refuses ("signed
  operands"); missing decision refuses and adopts nothing; decisions naming another
  revision/generation/domain refuse; a fault after the decision rolls both halves back and
  the next honest renewal is the first; the expiry judgement cannot be fed by a corrupted
  renewal (no EXPIRED record written).
- `test_workspaces.CleanupSettlementRunsInItsEndingsTransaction` (5): foreign connection,
  own connection outside a transaction and None refuse before any write; inside `transact`
  it settles and commits and a replayed ending settles nothing twice; a fault after the
  settlement rolls it back with the ending.
- Pinned regression `StageCProtections.test_an_honest_renewal_moves_the_deadline_once_and_a_lost_reply_replays_it`
  and the corrupted-record witness unchanged. The selected focused set -- the 9 renewal tests, the 5
  cleanup tests, these two witnesses and the cleanup-settlement witness -- is 17 run, OK
  (`focused-selected.log`). Corrected 2026-11-17: this line previously said 16.
- Reviewer's `renewal-probe.py` rerun (`reviewer-renewal-probe-after.log`): refuses
  "the request result was changed after the renewal was decided" instead of answering
  `expired` False.
- Product modules of every renewal reader and the cleanup ending path
  (`product-modules.log`): 1396 run, OK, 38.5 s. Corrected 2026-11-17 (review 2026-11-17T23:24:47Z):
  this line previously carried the unfilled placeholder PRODUCT_MODULES.
- Inventory gates (`gates.log`): StageCProtections, EveryReceivingEntryHasOneOwner, EveryProbeProvesItArrived, EveryStatedOwnerHasAWitness, HelperDeclarationsHaveExactAccounting, StatedRules, StoppedSettlementInventory, Lanes, CallerResolved, DynamicTable: 199 run, OK, 144.1 s (gates.log)
- Digests: `CANDIDATE-SHA256.txt`. Diff against the committed checkpoint 6477a8db:
  `candidate.diff`.

Paths touched: tokens.py, workspaces.py, intake.py (K's product paths; intake.py carries the M385024
governor-answer validation already in this candidate's diff and digests, omitted from this summary
until 2026-11-17); tests
test_stopped_settlement.py (new class, two imports), test_workspaces.py (new class),
test_boundary_inventory.py (restated row + witness). Codexpc's four engine fixture modules
untouched. Coordinator's review of M385024 at 6477a8db is not affected: those bytes are
committed; this candidate is the working tree over them.
