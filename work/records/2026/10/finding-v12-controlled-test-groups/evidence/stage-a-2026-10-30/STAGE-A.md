# Stage A — duplicate port owner at the discharge gates; lane coverage's cleanup ending (2026-10-30)

K (Claude, interactive copilot as baton.prompt) under the owner-held claim
E384905 (arrangement B); K holds no claim. Answers review-2026-10-30T20-37-39Z /
M384935: CLOSURE-CHECKLIST Stage A only. One file,
`v12/python/tests/manager/test_boundary_inventory.py` (CANDIDATE-SHA256.txt).
No product change, no scans group, no full suite, no engine, live model, Git
mutation or other agents.

## A.1 `EveryReceivingEntryHasOneOwner.test_no_entry_is_owned_twice`

Before (before.log): `('caller', 'intake.py:discharge_quiescence_gate', 'port')`
and the abandoned gate's `port` each counted TWO claims: the site's layer label
`the authority session's gate discharge` AND the CONSTRUCTED_BY default
(`port` -> `authority_port.py:AuthorityPort.__init__`).

What actually validates (measured, not inferred):
- At the site, `boundaries.capability(getattr(port, "satisfy_gate", None),
  "the authority session's gate discharge")` (intake.py:1603 and :3564, since
  017d87a3, 2026-09-09) executes first and refuses a port lacking the member.
  The inventory already declares a probe for exactly `(entry, label)` that
  hands `object()` and reaches that label (S4 probes; the probe-reach test
  passes before and after). The new witness executes it directly: `object()`
  is refused with the gate label in the message; the real `AuthorityPort`
  passes the check and is refused later, without that label.
- The constructor, `AuthorityPort.__init__`, owns exactly two things: the
  claim-signature derivation (capability, `caller:claim_signature`) and the
  participant text (`session:participant`). It states nothing about the
  members a later act requires; a `satisfy_gate` requirement cannot live there.
- So the entry has ONE actual validator, at the site; the constructed default
  is a default for the thirty other `port` entries whose sites state no
  requirement, not a second owner of these two. `owner_of` already ranked the
  layer first; only the duplicate COUNT disagreed with it.

Change: one helper, `ownership_claims(entry)`, now computes the claim vector
used by `test_no_entry_is_owned_twice`, the lanes exact-one check and the
W375444 settlement slice (three copies of the same expression before). It
drops the constructed default ONLY when the site's owners for exactly this
subject are all `capability`-kind (a member requirement). Any other kind at
the site -- `document`/`row`/`text` of the whole operand, i.e. the blanket
revalidation 4bz forbids -- still counts as a second owner. Not an exemption
table: no site or entry is named; the rule is by validator kind and subject.

Real-tree effect (real-tree-effect.txt): of 2545 receiving entries, exactly
the two gate `port` entries change vector ([layer, -, -, constructed] ->
[layer, -, -, -]); no other verdict moves; zero entries owned twice after;
the only constructed operands with a site owner are these two.

Negative evidence: `test_re_validating_a_constructed_operand_is_still_owned_twice`
(synthetic source through the patched `_sources`): `boundaries.document(store,
...)` of the constructed `store` at a site counts 2 claims; the
`getattr(port, "satisfy_gate")` capability requirement counts 1; an ordinary
operand 1. `test_the_double_ownership_check_can_actually_fail` unchanged, OK.
Positive real-tree pin: `test_a_required_member_of_a_constructed_operand_is_owned_once_at_the_site`
(constructor's exact owner set, site label, `owner_of` = layer, claim vector,
declared probe present, direct execution of both refusals at both gates).

Noted, not acted on: `deadlines.py:advance_deadline` performs the same
`getattr(port, "satisfy_gate", None)` requirement inside a tuple loop
(deadlines.py:362-366) that discovery does not resolve, so its `port` entry is
owned by the constructed default only. Not a Stage A failure; no discovery
extension without a remaining-failure rationale (checklist). Stage C's
classification is where it belongs if it surfaces.

## A.2 `LanesHaveCompleteReceivingCoverage.test_public_start_and_cleanup_supply_owned_lane_values`

Before: `'cleanup settled retained' != 'cleanup settled complete'` inside the
`_release_lane` interception, and `settled["cleanup"] == "complete"` after.

Accepted contract: W285465 under the owner supersession at 294568/294616 and
review 2026-09-28T10-23-30Z (intake.py:1403-1423): completion REMOVES NOTHING
AND ADMITS NOTHING; `authorize_cleanup` hands `_settle` `preserved=True`, and
`_settle` ends `retained` when anything is kept, quarantined OR preserved
(intake.py:5437). The lane suite's own cases were aligned to this under
W384870 B3 (test_runtime_lane.py:357-362, :1054-1055). The inventory's lane
coverage case predated it. Measured: `_settle` has one caller
(intake.py:1426), which always passes `preserved=True`, so `complete` is not
reachable from `authorize_cleanup` today; the AST pin on the `ending` IfExp
(`("retained", "complete")`) in `test_private_lane_writer_provenance` still
holds and is untouched. Recorded as an observation; no product edit (out of
scope and not a Stage A failure).

Change: the case expects `retained`, cites the ruling, and no longer asserts a
literal reason inside the interception: it records the `why` the real
`_release_lane` received and asserts it equals
`f"cleanup settled {settled['cleanup']}"`, the ending `_settle` actually
reached. Preserved unchanged: identity owned before each write, lane
reference equal to the attempt's derived reference, occupy reason pinned to
the derived start operation, order occupy -> release, one lane then none.

## Verification (from `v12/python`, `just test-one`)

- after-focused.log: the two targets, the three ownership witnesses
  (new 2 + existing negative), the whole `LanesHaveCompleteReceivingCoverage`
  class and `StoppedSettlementInventory`: 12 OK in 16.0 s.
- owner-class-and-probe-reach.log: the whole `EveryReceivingEntryHasOneOwner`
  class plus `EveryProbeProvesItArrived.test_every_declared_probe_reaches_its_named_boundary`:
  15 run, 13 OK, the 2 Stage C failures remain exactly
  (`test_every_boundary_call_belongs_to_an_entry_or_is_declared`,
  `test_every_receiving_entry_has_an_owning_validator`); every declared probe
  still reaches its boundary.
- Remaining scans failure ids after Stage A (not re-measured as a group, per
  checklist): Stage B's two (`test_every_owned_entry_has_exactly_one_probe`,
  `test_the_missing_probe_check_can_actually_fail`) and Stage C's two. 8 -> 4
  expected on the one scans run after the six.
