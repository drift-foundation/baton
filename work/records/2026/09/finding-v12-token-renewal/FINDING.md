# Child B — renewal and expiry arbitration

Bound dossier for v11 Work W275775, "V12 G1: Renewal and expiry arbitration". Created by
baton.claude on first execution, 2026-09-27, because owner 275775 requires a flat permanent
dossier bound and the exact paths pinned BEFORE any edit.

Parent umbrella W275617. Predecessor W275774 (Child A) was ACCEPTED and CLOSED by the owner
at seq 281287, outcome satisfying, so its token owner and API are the accepted input here
and are not reopened.

## Authority and exact selection

Owner brief T275775 (seq 275775), read in full on claim 281291:

> Use accepted child A token owner/API; bounded same-generation renewal, expected deadline
> revision, host-clock expiry competition, renewal exhaustion, idempotent replay, lost
> replies and stale observations. Prove renewal cannot revive expired/revoked ownership or
> defeat Job limits; retain real production enforcement.

Excluded: consumer migration, new scope, broad suites, live provider or engine, deployment,
cleanup, Git mutation. Graph edge 275778 (Child A blocks this) cleared at 281288; edge
275784 records that W275776 restart consumes this Work's acceptance.

## The governing specification, pinned by digest

    v12/DESIGN.md   239151a039b8a609347cdd73e97d181213fede1f2821a5d01ee5a9768c975934   61178 bytes

The requirements this Work must satisfy, read at that digest:

* **TOK-9**, second and third paragraphs. The host MAY explicitly renew a still-unexpired,
  unrevoked token for the same resource, generation, operation and execution under the
  selected bounded policy. Renewal is an atomic conditional control-store decision with a
  durable operation ID, an EXPECTED DEADLINE REVISION and a recorded new deadline. It
  creates no new writer and does not reset Job execution limits. Same-operation replay
  returns the recorded renewal without extending again; a lost reply grants nothing beyond
  the committed authority state. Renewal and expiry compete against that same current
  state: a stale expiry observation cannot revoke a later successfully renewed deadline,
  and once expiry or revocation wins renewal MUST refuse -- no heartbeat, late request or
  clock adjustment revives the token.
* **Section 17 renewal proof row.** "Valid same-execution renewal is recorded once;
  competing expiry/renewal serialize; stale expiry cannot defeat a committed renewal;
  expired/revoked/stale/cross-execution renewal refuses; lost reply/replay does not extend
  twice."
* **DB-1 … DB-7** continue to apply: no external I/O inside a transaction, and the
  conditional decision is one short write.

If DESIGN.md changes, this digest is stale and the pin must be re-read rather than assumed.

## Exact owned paths, pinned before editing

    v12/python/src/baton_v12/worker_manager/tokens.py        exclusive custody, from c2039970b589
    v12/python/tests/manager/test_boundary_inventory.py      entry declarations only
    v12/python/tests/manager/test_dependencies.py            operand declarations only
    work/records/2026/09/finding-v12-token-renewal/          this dossier and its selectors

`tokens.py` was Child A's exclusive custody; Child A is closed, so custody passes here with
this pin. Every other module -- `attempts.py`, `intake.py`, `workspaces.py`, `oci.py`, the
job manager and the deployment tools -- is READ-ONLY for this Work unless a concrete
consumer gap is found, reported and pinned first. No consumer migration is authorized.

Historical inputs, read-only: the parent dossier
`baton:work/records/2026/09/finding-v12-shared-resource-token` and Child A's
`baton:work/records/2026/09/finding-v12-token-lifecycle` with its accepted reviews,
candidate manifests and selectors. W270664 evidence is preserved and untouched.

## What the tree already has, and what it does not

Measured at c2039970b589, before any edit:

* `RENEWAL_LIMIT = 4` is DECLARED, with its semantics recorded beside it ("exhaustion does
  not free the resource; it means the holder must finish or be revoked"), and **nothing in
  the tree consumes it**: `grep -n "renew" tokens.py` answers the profile comment, the
  constant, and `"renewals": 0` in the acquisition document. There is no renewal act.
* Therefore every deadline reader answers the ACQUISITION's `expires_at`: `token_of`
  composes `expired` from it, `_owning` refuses an ordinary holder past it, and
  `Governance.overdue` and the expiry reclaim path read it through those two. A renewal
  that did not move what these read would be a renewal in name only, so the arbitration is
  the substance of this Work rather than a second act beside it.
* Child A's accepted acquisition record already carries `renewals: 0` and a recorded
  `seconds` operand, so the shape a renewal has to extend exists and is versioned
  (`TOKEN_VERSION = 1`).

## Residual debt inherited, NOT accepted and NOT this Work's scope

Child A's final review recorded these as explicitly unaccepted residuals; they stay
recorded and are not reopened or waived here: H4's missing negative coverage in
`tests/integration/test_driver.py`; the four `test_execution_limits` cases whose capture
wrapper omits `scratch`/`umask`; the sixteen unregistered modules in the parallel-runner
registry; W257624's optional-runner prose (H5); and the 103 unowned `workspaces.py`
boundary entries with older or unresolved provenance, plus the tree-wide aggregate.

## 2026-09-27T02-43-54Z — Independent first review: renewal corrections

Claim281381/handoff281371/thread275775. Author18PASS0.049s independently; new edge probes
2tests0.008s reproduce limit-replay refusal and same-manager clock-rollback expiry revival.
Review-2026-09-27T02-43-54Z.md binds evidence and corrections; matching manifest records exact bytes.
Expected-revision reader/API convention contradictory; populated Job-limit and scheduled
expiry/renewal arbitration proofs remain. Missing PLAN operational finding repaired by
reviewer checkpoint creation. No consumer migration or whole restart scope added.

## 2026-09-27T03-02-01Z — Original corrections verified; stale expiry judgement race reproduced

Claim281506/handoff281498/thread275775.35authorPASS0.119s, adapted edgeV2 twoPASS0.009s.
New review_stale_expiry_judgement_20260927.py1FAIL0.005s: old deadline observation writes
sticky expiry after competing successful renewal, even observed_at before current deadline.
_judge_expired write lacks conditional current-state arbitration. Review-2026-09-27T03-02-01Z.md records
exact schedule and finite correction; C2/C3/C4 bounded proofs accepted, C1/C5 remain.

## 2026-09-27T03-12-19Z — Stale-deadline fix verified; clock gap remains within C1

Claim281582/handoff281578.41existing checksPASS0.143s; new clock-gap1FAIL0.005s.
Clock rollback between _owning expiry refusal and separate _judge_expired write skips
durable judgement, propagates expired refusal, then permits retry renewal. Exact immutable
probe review_expiry_clock_gap_20260927.py. Preserve current conditional stale-renewal fix
while binding authoritative expiry/ambiguity to its observed revision. C1/C5 remain only.
See review-2026-09-27T03-12-19Z.md and matching manifest. No scope/graph/live/Git expansion.

## 2026-09-27T03-21-53Z — two remaining C1 atomicity failures

Claim281652/handoff281638/thread275775.48 checks PASS0.163s; two new deterministic
probes FAIL0.008s. Separate expiry/ambiguity transactions can both decline and permit
rollback revival; deadline and revision read separately can hold a successful newer renewal
using an older deadline. Author C1-closed claim not accepted. See review-2026-09-27T03-21-53Z.md
and matching candidate manifest plus review_judgement_atomicity_20260927.py. C2/C3/C4
remain accepted; C1 then C5 are the finite remaining steps. No scope/graph change.

## 2026-09-27T03-31-52Z — Child B independently accepted

Claim281715/handoff281712/thread275775 at281716. C1 atomic decision and coherent
observation fixes independently pass updated real two-handle schedules. C1-C5 complete.
Review-2026-09-27T03-31-52Z.md and matching candidate manifest bind acceptance.52 focused
checks PASS0.182s plus boundary witness PASS; broader operand inventory60 failures are
identical with/without candidate public surface, remain unaccepted residual debt. Exact
comparison artifact retained. Historical _deadline_of probes no longer reach the seam;
new review_final_arbitration_20260927.py supersedes their current-proof role without
rewriting evidence. Child C restart/integrated recovery and parent remain unfinished.
Pass accepted delivery to owner; no graph, Git, live execution or consumer migration.
