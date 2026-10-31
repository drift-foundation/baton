# Stage B — owned-probe completeness and its negative self-test (2026-10-30)

K (Claude, interactive copilot as baton.prompt) under the owner-held claim
E384905 (arrangement B); K holds no claim. Answers review-2026-10-30T21-08-28Z /
M384937: CLOSURE-CHECKLIST Stage B only. One file,
`v12/python/tests/manager/test_boundary_inventory.py` (CANDIDATE-SHA256.txt).
No product change, no scans group, no full suite, no engine, live model, Git
mutation or other agents.

## Before / after (same computation as the target test; gap-list-before.txt,
## audit-after.txt, coverage-map.txt)

| list | before | after |
|---|---|---|
| wanted (entry, label) pairs | 1344 | 1334 |
| declared probes | 1106 | 1328 |
| owned, never probed | 239 (33 non-replay + 206 replay) | 0 |
| probed, never owned | 1 (the stop request) | 0 |
| receiving entries / unowned (audit cut) | 2545 / 833 | 2545 / 833 |

Wanted moved 1344 -> 1334: -8 SHADOWED pairs, -2 NO_PROBE entries (`_configured_gid`
`meta`, `meta.value`), -5 covering labels that were standing in for real owners
(`OciAdapter.start` `request.labels.{participant,runtime_attempt_id}`,
`request_runtime_start` `adapter.mounts.{source,target,writable}`), +5 for those
entries' real delegated owners. Exactly those five entries change layer label
under the covering rule below; no other verdict moves (coverage-map.txt,
"REAL-TREE EFFECT"). Declared 1106 -> 1328: +222 Stage B probes
(coverage-map.txt lists them per site).

## The three attribution corrections (each with a remaining-failure rationale)

1. **A delegated label resolves through the delegating call's literal.**
   `OciAdapter.stop` delegates `request` to `_stopped(request, what)`, whose
   label is `{what}`; the call is `self._stopped(request, "a stop request")`.
   `delegated_labels` now fills a `{parameter}` placeholder from the string
   literal EVERY call from the delegating site binds to that parameter
   (`_delegating_literals`); disagreeing or non-literal calls keep the
   placeholder visibly. The one "probed, never owned" pair (declared `a stop
   request`, wanted `{what}`) is the same probe, now matching its owner.
   Other placeholder delegated labels (`record_attempt`'s `{what}, when it is
   given,`; interrogation's `the agent adapter's {operation}`) stay as they
   were: their probes were already keyed by the literal fragment.
2. **A DELEGATED entry is not covered by the whole's owner.** The start's
   `request.labels.participant` is owned by `_labels`' closed document rule
   (`a runtime's labels needs participant`), and the start's mount-plan
   members by `_plan_agrees` (`a declared runtime mount`); the covering
   fallback had been crediting `a start request` / `the runtime adapter's
   start`, labels no spoiling of those members can reach (S4 classified them
   "covering limitation"). `layer_labels` now applies the covering fallback
   only to entries that are not DELEGATED (a delegated entry has an owner of
   its own); five DELEGATED entries added for those members. Real-tree effect:
   exactly those five.
3. **SHADOWED, per pair.** `NO_PROBE` is per entry; four owners are real and
   per LABEL unreachable because the same reader applies an identical or
   stricter rule first under another label. `SHADOWED[(entry, label)] =
   (shadowing label, witness test)`, excluded from `expected()`, checked by
   `test_every_shadowed_pair_is_real_and_its_shadow_refuses_first` (real
   entry, label genuinely owned, witness exists) and each witness DRIVES the
   spoiling and asserts the shadow's label is the one in the refusal:
   - `_record` `replay.{deadline_at,policy,started_at}`: `_pin_of` owns the
     pin under `a pinned runtime deadline` (required=PIN, no optional) and only
     then re-reads the same value through `_record` with the identical set.
   - `_committed` `replay.operation{,.operation_id,.signature_digest}` /
     `a cleanup's operation`: `cleanup_of` owns `taken["operation"]` under
     `{what}'s operation` with required (operation_id, signature_digest) and
     no optional; `_writer_cessation_of`'s rule is strictly looser and later.
   - `admit_context_use` `replay.payload.checkpoint_id` / `provider context
     identity`: a FINALIZE key in an admission request is refused as an extra
     member of the closed admit document (`provider context metadata`).
   - `checkpoint_of` `line_checkpoints.fence.intent` / `a persisted assignment
     fence`: `boundaries.row` holds the JSON column to the same closed member
     set first, and a replaced intent fails the fence digest (three statements
     witnessed).
   `NO_PROBE` (no writer can drive): `_configured_gid` `meta`, `meta.value` —
   `meta.value` is a STRICT TEXT column and the text rule is applied only to
   digit-like text, which always round-trips; witnessed
   (`test_the_meta_group_record_owner_cannot_be_driven`: schema asserted,
   non-numeric value refused under `the recorded workspace group`).

## The probes (222, `stage_b_probes`, grouped by owning helper)

Engine: `borrowed(FixtureClass)` sets up another suite's fixture for ONE probe
and reclaims it with the probe; `corrupt_result(store, mutate, kind=|operation_id=)`
rewrites one committed RESULT (the bytes `ControlStore.replay` hands back
unsigned) with `listed` (whole document -> a list), `dropping(path)` (a required
member missing) or `setting(path, value)` (a member replaced, or an
unrecognised one added — a closed document refuses both). A member a
document owner covers is spoiled at the nearest member that owner can see,
as the row-column probes spoil the column carrying a JSON member. Text and
identity members inside a replayed document are spoiled with a non-text
value (7): a document's own walk already refuses unencodable text inside it
under the DOCUMENT's label, which the first run measured (reach-run-1.log,
48 probes refused at the wrong owner) and this corrected.

| owning helper | reader driven | world | probes |
|---|---|---|---|
| attempts.`_committed_record` | `attempt_preparation_failure_of` | this case's refused preparation | 1 |
| custody.`historical_directory_custody` | itself | test_custody `OneSignedReceiptPerRoot` + `normalize_directory` | 6 |
| deadlines.`_pin_of` / `_record` | `deadline_of`, `observe_deadline`, `advance_deadline` | test_runtime_deadlines `Deadlines` started/reached/advanced | 8 + 18 |
| failure_cause.`_committed` | `attempt_cessation_{intent,outcome}_of` | test_attempt_failure_cause intent fixture + a recorded outcome | 3 |
| intake.`_committed` (ordinary) | `cleanup_of`, `discharge_quiescence_gate`, `authorize_cleanup` (replay, governed) | test_intake `TheCommittedCleanupIsReadableWithoutActing`, `TheQuiescenceGate…` | 57 (with abandoned) |
| intake.`_committed` (abandoned), `_abandonment_declaration`, `_abandon_intent`, `abandon_attempt` | `abandonment_cleanup_of`, `abandon_attempt` (replay, governed) | test_intake `TheAbandonedGate…` | 3 + 1 + 3 |
| intake.`_failed_start_record`, `_refused_session_record` | the two recordless endings, custodian answering absence | this case's `failed_start_world` / `refused_session_world` | 1 + 4 |
| intake.`authorize_cleanup` (replay) | `authorize_cleanup` with a governance whose release is never reached | ordinary world | 2 |
| provider_context.`admit_context_use` | a second `admit` replaying the admission request | test_provider_context `ContextCase` | 33 |
| review_cycles.`_cleaned_review` | `integration_checkpoint` under `no_more_external_acts` | test_review_driver `TheWorkerCompletionTraversesPublicCustody` | 7 |
| review_cycles.`_fixed_intent` / `abandoned_correction_of` | `restore()` retry / `abandoned_correction_of` | test_review_cycles restoration fixture (`interrupted_intent`, `abandoned`+`restore`) | 15 + 27 |
| workspaces.`_committed_workspace_{group,storage}` | `configured_workspace_{group,storage}` | this case's configured deployment | 2 + 2 |
| non-replay: `_destroyed_abandoned` (8), `satisfy_gate` (2), `_verdict_row` (6), `checkpoint_of` row (1), `retentions_of` (1), `request_runtime_start` govern + mounts (4), `OciAdapter.start` labels (2), `tokens.renew` (3), governance `permission` (1), `release_preparation` `why` (1) | the public act of each | abandoned world with a spoiled destroy answer / gate answer; `review_cycle_world`; this case's activated attempt; `seam`; a held token; a configured storage | 29 |

Specific notes, recorded rather than hidden:
- `_pin_of` `replay.policy.duration_seconds` under `a pinned runtime deadline`:
  `boundaries.deadline` also owns the duration, but `_policy` refuses a
  non-positive duration under its own precondition first; the label is
  reached through the document that owns the policy (the covering rule).
- `_committed` `replay.directory_custody` (ordinary): the custody document is
  read only where no writer-cessation record exists, so the probe removes
  that record beside the spoiling; the abandoned reader needed no such step.
- `_committed` members under the ordinary label that the ordinary document
  does not carry (`artifact_ids`, `disposition`, `intent`, `fenced.*`,
  `cleanup.*`, …) are the other callers' reads at the shared helper site;
  each is proved as an UNRECOGNISED member of the closed ordinary document,
  and symmetrically for the abandoned composite.
- `admit_context_use`: nine payload keys of the deliver/finalize/hold actions
  are proved as extra members of the closed admit document.

## The negative self-test

`test_the_missing_probe_check_can_actually_fail` is proved against the
CURRENT baseline: for three answering probes (first, middle, last of the
sorted catalogue), removing the probe makes exactly that entry newly
"owned, never probed", and every newly missing label is one the removed
fragment covered. It no longer restates the emptiness verdict (that is the
target test's), so it detects a deliberate omission whether or not debt
remains, and never reports debt as success.

## Verification (from `v12/python`, `just test-one`)

- Completion gate (after-focused.log): `EveryProbeProvesItArrived` whole
  class (both targets, declared-probe reach over all 1328 probes, the
  shadow/NO_PROBE witnesses, the vacuity guard) plus
  `EveryReceivingEntryHasOneOwner`, `LanesHaveCompleteReceivingCoverage`,
  `StoppedSettlementInventory`, `CallerResolvedReadsClosuresAndReplays`,
  `DynamicTableReadsStayVisible`, `TheAttachmentKeyProbeReachesAdoption`:
  56 run, 54 OK in 40.8 s; the two failures are exactly Stage C's
  (`test_every_boundary_call_belongs_to_an_entry_or_is_declared`: 165
  orphan calls; `test_every_receiving_entry_has_an_owning_validator`: 663
  unowned entries).
- Iterations retained: reach-run-1.log (48 probes refused at the wrong
  owner: the document-walk lesson, the custodian capability for the two
  recordless endings, the covering ancestor for `cleanup.operation.*`, the
  writer-cessation record beside `directory_custody`, the fence shadow);
  reach-run-2.log (one witness still using a surrogate).
- Remaining scans failure ids after Stage B: Stage C's two. 8 -> 2 expected
  on the one scans run after the six (not run here, per the checklist).
