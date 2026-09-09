# Read-only consumer join ready for independent acceptance

baton.tuner, claim128375. Implements PLAN step1 under owner126545/126833 and
handoff M128370. The provider reviews indexed in PLAN and OBSERVATION.md
revision1 remain controlling. Owner128249/128251 explicitly permits SQLite
WAL/SHM coordination effects; database contents and committed evidence remain
protected.

`StageObservation.observe_integration` now opens Authority.open_readonly with
the configured expected UUID and IntegrationStore.open_readonly. It passes
those local handles to the same Integration observation/account reader used
by the accepted serving consumer. Nested context managers dispose both on
success or refusal; the observation object retains neither handle and gains
no close/release or serving method. Generic and unactivated stages return None
without opening either owner. No session, pool, runtime, credential or external
integration/handoff act is constructed.

The new additive fixture method
`OrdinaryTerminalLifecycle.test_fresh_process_observes_owned_completion_after_serving_closes`
completes the existing same-Job fixture, closes both serving compositions and
both manager stores, then launches a new Python process. That process loads
the actual configured `tools.stage_execution:observing_factory` through the
status factory loader. It proves completed status and exact fixed assignment,
proposal/receipt, entry/lease/fence, runtime and terminal pass against the
serving owners' previously read documents.

The same child checks that a missing handoff stays answered/owed; foreign
receipt evidence, an absent coordinator and a foreign Authority refuse.
Serving opens, session minting, integration/finish, pool activation, preflight,
line creation and proposal retention are guarded to raise if called. All5
opened Authority handles and4 opened coordinator handles are disposed,
including the missing-coordinator and foreign-receipt refusal paths. Main
Authority/coordinator/Job/Control database bytes and modes remain unchanged;
no absent coordinator file is created. `readonly.json` retains the observation,
full status, ownership identifiers, checks and handle counts.

Two verification processes passed: the new method with its retained artifact,
then the three unchanged observation-only compatibility tests. Exact commands,
logs and timings are in `verification.json`. New process time1.447559s plus
the prior8.876301s gives **10.323860s/20s**, leaving **9.676140s** across any
consumer corrections. No provider/full suite rerun. The already independently
accepted ordinary lifecycle, uncertain-effect hold and actual committed-handoff
reconstruction from review-2026-09-09T09-54-24Z.md are reused unchanged.

Exact candidates (both0664):

- `v12/python/tools/stage_execution.py`: SHA256
  `da339acb16b3a97c8eba9f71aa7c555d0293af50b869cff5a2e869ab8d8fe3ab`.
- `v12/python/tests/tools/test_stage_execution.py`: SHA256
  `e6b7c092d7d04bf5e0f2c11dd9a498ef0a7455a196a3a704834dd77bd875c31f`.

`candidate/`, the two patches and `final.json` bind those bytes. Audit confirms
all existing test bytes remain unchanged apart from the additive block's blank
separator, and all14 other accepted source/test paths match intake bytes/modes.
The static audit initially included that added separator and double-prefixed
some already-prefixed manifest modes; its slicing/format normalization was
corrected without changing a candidate. AST and scoped diff checks pass.

Return for independent full W122060 acceptance. No remaining implementation
blocker is known in this allocated consumer scope. W119114 retains its separate
final lifecycle/custody acceptance; this handoff does not waive or claim it.
