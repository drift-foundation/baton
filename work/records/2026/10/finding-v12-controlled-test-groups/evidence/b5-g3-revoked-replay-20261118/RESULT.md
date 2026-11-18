# G3 — exact committed replay after revocation (OWNER-REVOKED-REPLAY-20261118.md; M385098, corrected per M385100)

K, copilot under owner claim E384905, no claim held. Ruling pinned before implementation (owner file,
FINDING/PLAN/CLOSURE, DESIGN DB-7 clarification). Source: 2e330649 + the uncommitted accepted G6 and G1
candidates + this slice's four files; content digest f3e320de… identical before and after every run
(`source.json`, `source-after.json`).

## Correction after review 2026-11-18T04:17:54Z

P1 (reproduced by the reviewer's `returned-probe.py`): the first cut keyed the replay branch on "revoked
and unfenced", and a revocation record outlives the return it precedes (the reclaim revokes, settles,
then returns), so a RETURNED generation -- and one SUPERSEDED by a replacement acquisition -- also
replayed. Fixed: `tokens._revoked_and_still_held(control, domain, generation)` is the branch's one
predicate and it requires ALL of: a revocation record; no settlement fence; no return record; no newer
acquisition in the domain. Everything else re-proves ownership first exactly as before. The reviewer's
probe now answers REFUSED in both phases (`reviewer-returned-probe-after.log`).

Caller proof gap: `maintenance.prepare` orders `journal_launch -> _created -> bind -> admit_activation`,
and its journal-first dispositions had no case for an OUTSTANDING, REVOKED, unbound generation -- with
the launch now replaying, a retry would have CREATED a fresh container before `admit_activation`
refused. Fixed in the caller: a new disposition refuses (`already-terminal`, "…REVOKED… its committed
launch is history and not permission to create a container…") before any engine call, beside the
existing returned and bound dispositions. Measured at the real create boundary with the module's
counting engine double: `engine.seen == []`, nothing created, generation stays revoked/unreturned/unbound,
`effects_permitted` False, and the generation is no longer an `unresolved` cut of this facility (it is
the reclaim's to settle).

## What the product now does (tokens.py `_acting_record`, maintenance.py `prepare`)

Under the write lock, when the generation is revoked AND still held (predicate above), the exact
same-operation/same-signature replay is read first; if found it is answered with no write. Otherwise the
old order: `_owning` (fence, revoked, owner, returned, judged expiry, ambiguity, deadline), then replay,
then record. So an exact committed launch or binding replays only while the revoked holder still holds;
new acts, changed operands, foreign owner, other generation, returned, superseded and fenced generations
refuse as before; `admit_activation` (its own `_owning`) refuses after revocation; renewal's own preflight
(`_extended` -> `_owning`) is unchanged, so an exact renewal retry after revocation still refuses -- the
ruling says a committed act MAY be answered and selects the smallest correction; reported, not changed,
and explicitly not this finding per the review.

## Witnesses

`test_stopped_settlement.RevokedGenerationReplay` (8): exact launch replay answers and writes nothing
(twice); new binding / changed operands / new renewal / foreign owner / other generation refuse and write
nothing; a committed renewal is not replayed after revocation and nothing extends; the fence refuses the
committed launch, a binding and a renewal; expiry of the revoked generation grants nothing and a
competitor waits; a bound generation's activation refuses after revocation; revoked+RETURNED keeps every
guard for launch, binding, renewal and activation and the replacement generation's own acts are untouched;
superseded-without-a-visible-return is refused by the fourth condition alone (store row + hidden return).
`test_maintenance.ARepeatedPreparationDecidesAtTheJournalBeforeTheEngine.test_a_revoked_launched_unbound_preparation_creates_nothing_on_retry`:
the caller proof above. Plus the two G3 ids.

## Verification (focused; no group/full/Docker/live)

| run | result | log |
|---|---|---|
| RevokedGenerationReplay (8) + the maintenance class (4) + the two G3 ids | 14 OK | witnesses-and-g3-ids.log |
| reviewer's returned-probe.py (both phases) | REFUSED, REFUSED | reviewer-returned-probe-after.log |
| test_stopped_settlement, tools test_stopped_settlement_joined, job_manager native_stop_restart + serving_renewal + native_permission, test_attempt_failure_cause, test_authoring_enforcement, test_maintenance, boundary_inventory.StoppedSettlementInventory | 371 OK, 22 s | token-regressions.log |

Candidate: `CANDIDATE-SHA256.txt` (tokens.py, maintenance.py, test_stopped_settlement.py, test_maintenance.py);
`candidate.diff` against 2e330649 (4 files, +314/-1). Four `v12-foreign-*`/`v12-substituted-*` roots left by
test_maintenance during the regression run were listed and removed (`leaked-roots-*.txt`); /var/tmp back to
the 376 baseline. Nothing else changed this slice.
