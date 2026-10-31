# Stage C -- every remaining ownership row dispositioned (2026-10-30)

K (Claude, interactive copilot as baton.prompt) under the owner-held claim
E384905 (arrangement B); K holds no claim. Answers M384939 / review
2026-10-31T00:30:29Z (CLOSURE-CHECKLIST C): the two target tests
`EveryReceivingEntryHasOneOwner.test_every_boundary_call_belongs_to_an_entry_or_is_declared`
(165 orphan calls) and `test_every_receiving_entry_has_an_owning_validator`
(663 unowned entries). Owner checkpoint a8cbc974 noted. No scans run yet in
this slice (next, per the checklist). No live model, engine daemon, Git mutation
or other agents.

## Baseline, preserved under both count definitions

| list | 8876bf95 (before this Work's inventory) | Stage B end | after the three discovery corrections | end |
|---|---|---|---|---|
| receiving entries | 2295 | 2545 | 2580 | 2580 |
| unowned (acceptance test's cut) | 688 | 663 | 646 | 0 |
| unowned (audit script's cut: no CONSTRUCTED_BY, no stated rows) | -- | 833 | -- | 170 (`audit-after.txt`) |
| orphan boundary calls | 190 | 165 | 77 | 0 |

(`lists-at-8876bf95.txt`, `lists-before.txt`, `lists-after-discovery.txt`,
`orphans-after-discovery.txt`.) The two cuts still differ by definition and are
both reported; the audit's "unowned" never counted CONSTRUCTED_BY and now also
does not count the stated rows added here, so its number is the debt the audit
would show a reader who trusts only layer labels.

## The disposition map

`disposition-map.md` lists every one of the 663 entries and 165 calls with the
rule that answers for it now, generated from the live tables
(`disposition_map.py` in scratch; the map is the evidence). By kind:

| entries | count | mechanism |
|---|---|---|
| missed attribution | 56 | the three discovery corrections, STAGE_C_DELEGATED rows (each probed) |
| genuine gap, repaired | 11 | product repairs below, now layer-owned at the door and probed |
| protected elsewhere | 596 | STAGE_C_STATED rows (reason per row), each family held by `StageCProtections` |

| calls | count | mechanism |
|---|---|---|
| claimed | 99 | claims anywhere a read/session stem is owned; delegated stems (incl. S1's launch member rows re-keyed) |
| declared | 66 | NOT_AN_ENTRY rows with the reason: a second rule on an owned value, a per-member loop call (W39666), a journal row read through `operation_record`, a JSON column re-owned member by member, a private write check (lanes precedent), a per-call capability's answer |

The 596 "protected elsewhere" rows group into families (full per-row text in
the map and in the test file):

- 44 `control` store doors -- the W275774 precedent (`tokens.py` states `control`
  as a capability proven by use; the same reason, the same minting site).
- 30 `documents.py` constructors' `**members` -- PLAN 4bz outbound canonical
  constructors; `_emit` closes the member set, values are owned by the next
  receiver; witness: no caller outside the package, missing/extra names refuse.
- 25 replays handed back unread; witness: no `replay.<member>` entry at the site.
- 36 operands composed by this package's own callers (derived journal keys,
  admission documents, roots this manager created); witness: every call site
  hands an owned or composed value.
- 21 public doors over an attempts row already owned at its read; witness as above.
- 13 mint-gated constructor operands; witness: the mint is package-private and
  its minters are pinned (custody and maintenance mint the configured group).
- 13 token-journal documents read back by `token_of`/`generation_of` (owned when written).
- 10 label operands (`what`), 10 default-answering readers (`payload_of` and kin).
- the rest: inline exact-type / closed-set / bounded checks and private helper
  refusals, named per row; a refusal table in `StageCProtections` drives one
  representative of each helper and inline rule.

## Missed attribution: the three discovery corrections (each names its rows)

1. **Claims anywhere a read or session stem is owned** (`_boundary_claims`): a
   read stem names its read site and a session stem names the one crossing, so
   the owner call may sit where the value is consumed -- the rule `_owned_here`
   already applied on the owner side since S4 had no counterpart on the claim
   side, which is why 59 of the 165 orphans were the owners of entries the
   inventory already called owned (`deadlines._pin_of` projections, `_committed`
   readers, `_attempt_row` projections). Rows: the 55 read-stem orphans and the
   `unstarted_cancellation_of`/`_owned_fences` session-stem orphans.
2. **Session-stem owner fallback** (`_owned_here`): `project_work.work_id` and
   `.fenced_generations{,.cause,.reason}` are owned by `attempts` where it
   consumes the projection; `_crossings` guarantees one member has one crossing.
   Rows: 5 injected entries at `AuthorityPort.project_work`; `.generation` is an
   inline integer rule there, stated.
3. **Tuple-returning helpers** (`_returned_origins`, `_source`, `visit_Assign`):
   `_recorded_discharge` / `_recorded_abandoned_discharge` return
   `record, committed`, and the callers unpack and hand the document to
   `_adopted_discharge` / `_adopted_abandoned_discharge`. Before this the two
   `replay` entries were unowned and 21 owner calls were orphans; now 35 member
   entries exist at the two read sites, owned by the receipts' rules under the
   two readers' labels, and probed through the gate-discharge worlds of
   test_intake (committed result rewritten behind the build; both the read path
   and the replay path). The same correction made `deadlines._record`'s
   `replay.authority_operation_id` (probed) and `replay.policy.action`
   (SHADOWED by the pin owner, same witness as the pin members) and
   `_verdict_row`'s `review_fence.intent.assignment` (probed) visible.

STAGE_C_DELEGATED (every row probed in `stage_c_probes`): the session reference
at handshake's two doors and intake's refused-session cleanup (`sessions._session_ref`),
`AttemptLogs.__init__`/`ExchangeDelivery.__init__` for adopt/materialize
attempt ids, `failure_cause._identity` for the cessation identity composers,
`oci._network`, `OciAdapter._quiesced` (seal), `OciAdapter._stopped`
(stop_expired), `provider_context._text` for context_delivery's five doors and
provider_context's `context_use_of`/`finalize_context_use`,
`_finalize_context_use`/`_receipt` for the two readers (through test_provider_context's
finalized world), `_document` for the certification evidence and the launch
delivery whole, `_text` for seven delivery members (`attempt_id` is SHADOWED:
the delivery's attempt is compared with the job's before `_text`, witnessed),
`oci._engine` for custody.surviving_helpers. S1's launch member rows pointed at
the whole document's stem; the seven members with their own rule are re-keyed
to it and their probes spoil the value.

## Genuine gaps, repaired (product.diff; each reproduced before the fix)

| door | before | repair |
|---|---|---|
| attempt_logs capture_state/locators/read/follow/record_capture `delivery` | `locators(7)` -> AttributeError from `_room` | `_delivery`: exactly AttemptLogs (exchange.py's own rule); `locators` also types `reported` as a mapping |
| exchange.discard `root` | `discard(7)` -> TypeError in os.path.join | `boundaries.text(root, "an exchange delivery root")` as adopt/materialize already do |
| custody.custody_holds `assignment_id`, `which` | an unknown root/attempt read silently as "no holds" | the two checks every sibling door makes (identity; check_custody_root) |
| custody.allowed `seconds`, `most` | `allowed("abc", 120)` -> ValueError | a non-number remainder/ceiling refuses integrity/schema |
| intake.reclaim_expired_resource / settle_revoked_resource `attempt_id` | an unencodable id reached sqlite (UnicodeEncodeError) | `boundaries.identity` as every sibling door |
| the governor at reclaim/settle (required) and abandon_attempt/authorize_cleanup/finalize_quiescent_assignment (optional) | `govern=7` -> AttributeError, for the three endings AFTER the ending committed | `boundaries.capability` on the acts each door performs, before any read or effect |
| workspaces.revoke_expired_token `stop` | `stop=7` -> TypeError after the revocation committed | typed as a capability at the door |
| OciAdapter.start `bind` | `bind=7` -> TypeError after the container was created | typed as a capability at the door |
| workspaces admit_cleanup / bind_token_container / revoke_expired_token `assignment_id` | the three standalone admission doors (no caller inside the package) took the id as a bare journal key while every other workspace door holds it to `_assignment_identity` | `_assignment_identity` first (DELEGATED, probed) |

Each new owner has a probe; the expiry doors type the adapter first so the
pre-existing adapter probes keep their refusal.

## Open owner decision carried (not decided here)

`workspaces.settle_cleanup` `connection` is never read while its docstring
states a transaction contract (B2 Case H). The row states the fact (an unread
operand reaches no effect); whether the body should use the connection is the
owner's call and is reported, not papered over.

## Verification

- Completion gate classes (`focused.log`): EveryReceivingEntryHasOneOwner (both
  targets, stale/duplicate/constructor checks), EveryProbeProvesItArrived (both
  Stage B gates, every one of 1455 probes reaching its named boundary, the shadow
  and NO_PROBE witnesses), StageCProtections, LanesHaveCompleteReceivingCoverage,
  StoppedSettlementInventory, CallerResolvedReadsClosuresAndReplays,
  DynamicTableReadsStayVisible, StatedRules: 171 run, 171 OK in 102.8 s.
- Test modules of every repaired door (`product-modules.log`; test_workspaces,
  test_maintenance, tools.test_single_worker, test_intake, test_custody,
  test_attempt_logs, test_exchange, test_oci, test_attempts,
  test_runtime_deadlines, test_attempt_failure_cause, test_provider_context,
  test_reconciliation_worker): 2078 run, 1 failure --
  `tools.test_single_worker...test_a_real_observing_status_run_mutates_no_durable_state`,
  which is in the 2026-10-29 baseline failure list (a B5 singleton, unrelated to
  these doors: a durable-file listing difference). An earlier batch (sixteen
  modules, 1946 run) showed six failures and five errors, every id in the same
  baseline list (TheContextLaunchIsClosed, TheVersionMovesWithTheMember,
  DockerEndedRuntimeAdoption, test_it_takes_no_agent_and_no_runtime_capability).
  Nothing regressed; B5 stays B5.
- Reach-run corrections on the way (logs retained in scratch only): first run of
  the new probes had 10 misses -- posture and session_epoch are owned under their
  own rules so the covering label is reached by dropping the member; the
  finalize world needs the delivered state before the ending; the expiry doors
  type the adapter first, so the governor probes hand a capable adapter; the
  delivery's attempt_id is compared before `_text` sees it (SHADOWED, witnessed).

## Scans group

Run 1 (`scans-group-run-1.log`): collected 477 = executed 477, passed 473,
optional skipped 2, failed 2 -- both in inventory housekeeping classes the
focused set had not included: `EveryStatedOwnerHasAWitness` (every stated row
must name a witness method; the 596 stage C rows named none) and
`HelperDeclarationsHaveExactAccounting.test_same_adopted_call_and_origin_can_be_projected_at_several_sites`
(a synthetic case whose expectation encoded the old claim path: a projection
resolved through an equivalent claimed copy; under the claims-anywhere rule the
projection is claimed directly by the read's own entry, which the case now
asserts -- stricter, same residual, documented in the test). Repairs: a witness
registry for the stage's rows (`_stage_c_witness`: each family -> the
StageCProtections test that holds it; `control` rows -> the W275774 witness),
the witness lookup accepting StageCProtections beside StatedRules, and three new
family witnesses (label operands reach only the refusal prose; STRICT columns
read as their declared type; replayed journal members have no second layer
owner). Test-expectation edits are recorded here under the standing
test-change authority; nothing was weakened to pass.

Run 2 (`scans-group-run-2.log`): collected 480 = executed 480, passed 478, optional skipped 2, required skipped 0, failed 0, errors 0, fixture skips/errors 0, duplicates 0, unaccounted 0 -> accounting OK (the three new witness tests are the +3 collected)

## Corrections after review 2026-10-31T02:06:09Z (M384941)

The reviewer's `counterexamples.py` (evidence/review-stage-c-20261031/) is kept
as the independent reproduction; `reviewer-counterexamples-after.log` is the same
script against the corrected tree, `forged-custody-member.py` / `-after.log` is
K's own reproduction of the audited intake release, `allowance-after.log` the
allowance cases.

### P1 -- owned input is traced, never assumed

`StageCProtections._handed_owned` accepted a read, a session crossing, an
unknown origin and a private caller's parameter as "owned". Replaced by a
trace (`_owned_value`): a read or crossing counts only when the receiving entry
it names (or a covering parent) is OWNED; a public caller's operand counts
only when its entry is owned; a private helper's parameter counts only when
EVERY caller hands it something the trace proves in turn (bounded, loop-guarded);
a composed expression counts when every leaf does -- literals, package
constants, package function and constructor calls over proved arguments, local
assignments and loop iterables followed; anything else names the gap. Three
synthetic witnesses: the reviewer's raw-row sample is rejected ("no owner
answers"), an unowned public operand and an unresolved name are rejected, an
owned row / typed operand / composition are accepted. Every
STAGE_C_ADOPTED_ROW_DOORS and STAGE_C_INTERNAL row was re-evaluated under the
trace: all 29 operands of the 22 rows (19 STAGE_C_INTERNAL operands, 5 adopted-row
doors with their row operand, plus the member rows beneath them) are proved at every
call site; no row had to be un-stated. Three rows were proved only after the trace
learned real binding shapes the first version could not follow, each a soundness gap
in the TRACE, not in the code: tuple unpacking (`chain, admitted = _use(...)`,
`bound, _domain, generation, _token = token_bound_runtime(...)`), comprehension and
`with` targets, a parameter read inside a nested closure (`asking(_connection)` in
`_eligible`, the `transact` closures in `prepared_workspace_governance`), and a
lambda's parameter, which is whatever the package call the lambda is handed to
invokes it with (`attempt_cessation_outcome_of` hands `_read` the identity builder;
its `row` and `generation` are `_read`'s own `_attempt_row` read and
`token_bound_runtime` result). A public door's parameter that is not a receiving
entry at all (the store handle, a callable) is not an input the inventory tracks.
The loop guard is per (helper, parameter) hop with an eight-hop depth bound, so a
lambda's invoker may legitimately lead back to its caller's own operands. The
forwarded row for `replayed_as_signed`'s `operation_id` was NOT provable (the
forwarding check cannot see a method call through a handle, so it was asserted,
not held); the read now validates the identity itself (`boundaries.identity`) and
the row is layer-owned and probed.

### P1 -- replay protection demonstrated, and the token gap closed

The claim "owned when written, compared on read" was tautological and false
for the decision the reviewer drove: `replay` binds the signature, not the result
bytes, and `token_of` decided `expired` from a rewritable `expires_at`. The
`_document` docstring that said otherwise was wrong and is corrected.

Correction, within the accepted contract: the token acquisition, launch,
binding, return, revocation, activation and settlement-fence records -- and the
workspace removal-ownership, token binding/revocation/cessation, cleanup
admission/takeover/settlement, restoration-lock records, and the settlement
selection -- are written with the SIGNED OPERANDS AS THE RESULT. One shared read
(`store.replayed_as_signed`) now compares the replayed result whole with the
signature's own operands and refuses any difference; every one of those readers
goes through it. The renewal, expiry and timing-ambiguity judgements record a
decided instant the signature does not cover: their signed operands are verified
as a subset of the result and the decided members are owned by shape
(`a resource-token judgement record`, instants). Binding the decided instant
itself needs the record's operands to carry it, which changes W275775's
identity/replay semantics -- an exact decision for the owner, not taken here.

Witness `test_a_corrupted_self_signed_record_refuses`: the reviewer's token case
(clock 2030, expiry rewritten to 2099) now refuses with "signed operands" instead
of answering `expired=False`; the same corruption on a removal-ownership token
term, a cleanup admission's owner, a takeover's owner, a lock's device and a
settlement selection refuses, while the untouched records read back whole.

Audit of the rows that shared the tautological witness:
- intake `_resource_cessation` (abandon_attempt / authorize_cleanup replay
  members): a forged `directory_custody` member in a committed ending RELEASED
  the resource with no cessation evidence (`forged-custody-member.log`: honest
  ending with its writer cessation releases 1; with that evidence deleted, 0;
  with a forged member, 1). Corrected: the member is re-proved through the
  committed normalizations (`_custody_already_committed`, which is where the
  ending records it from) before it can derive a cessation; forged member now
  releases nothing (`-after.log`, witness `test_a_forged_custody_member_releases_nothing`).
- stopped_settlement `_read`: the selection is self-signed and verified; the
  outcome and receipt record an observation beside a signature over the request
  and are NOT signature-bound -- W375444's REPLAY_DEBT, pinned by name in
  StoppedSettlementInventory, stated as such, not declared protected.
- the remaining journal and key-column rows (handshake's merged refusal, the
  deadline cleanup's carried members, review_cycles' compared rows, settlement
  restoration's re-read ids) are held by
  `test_replayed_or_keyed_members_are_compared_carried_or_re_read`: every read
  of the member is a comparison operand, carried into an answer, handed to a
  reader, or tested for presence; branching on a bare value fails it.

### P2 -- finite allowance on every path

`custody.allowed(None, "bad")` returned "bad" (the ceiling was never checked on
the unbounded path); `allowed(1, inf)` and `allowed(nan, 120)` escaped as
OverflowError / ValueError. `_finite_seconds` now refuses a bool, a non-number
or a non-finite float for both the ceiling (on every path) and the remainder,
through the declared integrity/schema vocabulary; None, flooring and the
non-positive-answers-zero rule are unchanged (`allowance-after.log`; refusal
table rows and the positive cases in `test_stated_rules_refuse_what_they_say`).

### Rows and files affected

The journal rows moved with the read: the self-signed `tokens._document`,
workspace reader and settlement selection rows are now the 24 stated
`store.py:replayed_as_signed` rows (the one verified read: `replay` and 20 members,
`kind` compared by `replay`, `what` a label; `operation_id` layer-owned by
`boundaries.identity`), each stated row witnessed by the corruption test and the
identity by a caller probe. `_document` keeps the judgement path as 14 layer-owned
entries (`replay` and 13 members) with 17 probes: the whole record replaced, each
required member dropped, each decided instant (`renewed_at`, `expires_at`,
`observed_at`, `decided_at`, named explicitly in the product now so the owner labels
are exact) replaced by a non-instant, driven through `token_of` (renewal) and
`journal_launch` (expiry judgement written by a refused late renewal). Members no
judgement record carries (`container`, `launch`, `permission`, `started`,
`expired_at` -- read from the self-signed records, verified whole) are probed by
spoiling the judgement document itself, as the Stage B `both(...)` rows do. Product files touched by this
correction: store.py (the shared read), tokens.py, workspaces.py,
stopped_settlement.py, custody.py, intake.py. Digests refreshed in
CANDIDATE-SHA256.txt.

### Verification of the correction

- Reviewer's reproduction rerun (`reviewer-counterexamples-after.log`): the token case
  now raises ContractRefusal "records a result that differs from its signed operands";
  the owned-input sample is rejected by the trace ("no owner answers").
- `forged-custody-member-after.log`: honest ending 1 release, no evidence 0, forged
  member 0. `allowance-after.log`: None/'bad', 1/inf, nan/120 refuse; None/120 -> 120,
  lambda/120 -> 0, 5.9/3 -> 3.
- Gate classes (`focused-m384941.log`): EveryReceivingEntryHasOneOwner,
  EveryProbeProvesItArrived, StageCProtections, EveryStatedOwnerHasAWitness,
  LanesHaveCompleteReceivingCoverage, StoppedSettlementInventory,
  CallerResolvedReadsClosuresAndReplays, DynamicTableReadsStayVisible, StatedRules,
  HelperDeclarationsHaveExactAccounting: 191 run, OK, 152.8 s.
- Product modules of every touched module (`product-modules-m384941.log`:
  attempt_failure_cause, attempts, authoring_enforcement, custody, intake, maintenance,
  review_cycles, runtime_deadlines, stopped_settlement, workspaces, store, sessions):
  1557 run, OK. An earlier batch that also took test_ended_runtime_adoption and
  tools.test_single_worker showed only the 2026-10-29 baseline ids (two
  DockerEndedRuntimeAdoption cases, the single-worker status run); nothing regressed.
- Lists (`audit-after-m384941.txt`, `export-m3` in scratch): receiving entries 2591
  (2580 + the shared read's rows), unowned 0, orphan calls 0; owner kinds layer 1078,
  stated 968, delegated 374, constructed 171; probes 1473 declared for 1476 wanted
  pairs, 0 owned-never-probed, 0 probed-never-owned. `disposition-map.md` regenerated
  (2591 entries, 0 unowned, 0 orphans; calls claimed 99, declared 66).
- Scans group run 3 (`scans-group-run-3.log`): collected 485 = executed 485, passed
  482, optional skipped 2, failed 1: `test_dependencies...test_the_manager_imports_only_the_ruled_validator`
  -- the allowance correction had imported `math` in custody.py and the manager's
  dependency rule names its standard-library modules exactly. The rule was kept and
  the import removed (`_finite_seconds` tests NaN by self-inequality and the two
  infinities by equality). Run 4 (`scans-group-run-4.log`), after that removal and the
  M384981 ordering correction (`evidence/cleanup-ordering-20261031/RESULT.md`): SCANS4
- Owner Git checkpoint 4989ce76 ("WIP: checkpoint Stage C corrections and accepted B4
  integration-worker repairs") landed mid-correction; `product.diff` is against
  a8cbc974 (the Stage C base) and `CANDIDATE-SHA256.txt` names the current bytes of
  the two test files and ten product modules.
