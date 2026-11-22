# V12 recovery: owner decision and successor admission

Canonical Work: 2b077949-W385624; parent W9901.

Stage 1-B: supported owner read/decision surface binds exact failure, report, candidate, original/corrected verifier and context, approved profile identity/digest and selected stages. New linked manager-owned verification/review-only successor, never implementation redispatch. Prove authorization, replay/collision, cancellation, cessation, candidate integrity and exact stage/profile agreement. Post-verification expiry holds owner item; owner-authorized review-only successor requires valid exact evidence and unchanged approved limits. Depends on accepted Stage 1-A.

Accepted contract: work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-team-hierarchy-shared-approvers/STAGE-1-CONTRACT.md (52c2c640fdbb791e70ae61edf7ef7db7190bacd767d6d044f678517d2e09e1bc). Normative v12/DESIGN.md REC-8 and independent review work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-team-hierarchy-shared-approvers/review-2026-11-22T05-18-37Z.md apply. This allocation is not completed implementation or a live-run selection.

## Stage 1-B delivered — 2026-11-22

Implemented at source `ce6e1b2bf12519a84a3792f06562b7727dfe3021` (delivered
Stage 1-A), against the accepted contract
`work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-team-hierarchy-shared-approvers/STAGE-1-CONTRACT.md`
(SHA-256 `52c2c640fdbb791e70ae61edf7ef7db7190bacd767d6d044f678517d2e09e1bc`),
normative `v12/DESIGN.md` REC-8 and the accepted review
`review-2026-11-22T05-18-37Z.md`. Evidence:
`evidence/native-stage-1b-385624/`.

### What is now supported

- **The owner read/decision command.** `manager recovery-item` and
  `manager recovery-decide`, dispatched from `tools/job_manager.py` beside
  `cancel-job` and `settle-stopped`, so both are reachable from the installed
  bundle through `baton-v12-stack manager ...`. The read presents the
  delivered Stage 1-A owner item and its diagnosis (resolved out of the Worker
  Manager custody that holds it and held to the digest this store journalled),
  the original failed verifier argv and its declared execution context, the
  retained candidate, the four digests a decision binds in the exact spelling
  `decide` compares them in, the proposed correction, the approved profile and
  its digest, the selectable stage sets, what has already been decided, and
  whether the asking participant holds the decision capability at all.
- **The owner decision.** `job_manager.retained_recovery.decide` binds owner
  identity and provenance (W16821's decision document: endpoint, principal,
  the WORK's own effective scope, role, grant provenance, policy generation),
  the owner's own operation key, the immutable inputs, the exact approved
  profile identity and digest and the selected stage set. It refuses an
  unauthorized actor, a grant in another scope, a wrong failure/report/
  candidate digest or base/head, a wrong account of the original verifier, a
  "correction" that is the command that failed, an absent execution context,
  an unapproved profile or profile digest, a stage set this contract does not
  offer, `implementation` by name, and evidence that changed under the owner.
  `denied` and `held` record an attributable disposition and launch nothing.
- **The manager-owned successor admission.**
  `retained_recovery.admit_successor` is a NEW admission and not
  `fresh_attempt`: it composes the same four owners under the same rules
  (host cessation/resource exclusion, Work authorization REUSED and never
  minted, the deployment binding and its servability selector, the instance
  guard plus a per-admission invocation lock), reserves the successor identity
  and its durable intent before any other owner is touched, re-asks the host
  after the reservation, and submits one Job carrying exactly ONE `review`
  stage under the owner-approved control profile. No implementation stage, no
  correction allowance, no dependency on the failed Job.
- **Post-verification expiry.** `record_verification` is the supported account
  of a successor's verification (its CONTRACT is this slice's; the execution
  that fills it is W385625's), and a review-only decision is authorized only
  against still-valid exact evidence: this failure's own expired successor,
  its journalled PASSED verification of this exact candidate under this exact
  approved command and context, the result digest the lineage names, and the
  candidate still validating now. Absent, mismatched, cancelled or unknown
  refuses and never becomes permission to verify again.

### Owner-approved profile, pinned

`stage1-verification-review/1` is held as data in
`job_manager/retained_recovery.py`, reproduces the owner's published bytes and
is proved at import against SHA-256
`5a6a420e416caab0942f9709939ae01f1f2d9dabbd13e09ff3b03ea08d2932fb`. Unlike
`stage1-analysis/1` it is ALSO a `job_control.PROFILES` entry, because this
execution does run verification commands and its five numbers are exactly
`PROFILE_MEMBERS` — so the admitted successor Job is enforced by the accepted
LIM-5 control rather than by a second account of the same ceilings. The module
proves at import that the enforced entry and the owner's definition state the
same bounds, and `CONTINUATIONS` records zero for it explicitly.

### Admission/execution boundary, stated truthfully

This slice admits a successor and executes nothing. The approved corrected
verifier has not run, no retained candidate has been materialized into a
workspace and no candidate has been handed to review: W385625 owns the
verifier execution adapter and the final loop. The admission answer therefore
carries `readiness`, which names the acts still owed (`verification: owed` or
`omitted`, `review: owed`) rather than letting a Job id read as a completed
recovery.

### Defect found by this slice's own acceptance — `advance_watermark`

**Observed.** Two concurrent `recovery-decide` commands against one Job store
both reached `job_control.refuse_uncertain`, which calls
`advance_watermark`; both found no `control.watermark` row and both inserted
one, and the loser raised `sqlite3.IntegrityError: UNIQUE constraint failed:
meta.key` from inside a caller's transaction. A raw integrity error is a FAULT
where the caller was entitled to an ordinary refusal or a committed act.

**Cause.** `advance_watermark` read the row and then inserted or updated it.
A read-then-write check is not a check when another writer may write between
the two. This is Baton's defect and not this slice's misuse: the same pre-
transaction call exists in `fresh_attempt.admit`, so REC-7's own operation is
reachable the same way; it simply had no concurrent-CLI acceptance.

**Correction.** One `INSERT ... ON CONFLICT(key) DO UPDATE ... WHERE
excluded.value > meta.value` statement, so the two writers meet in the
database. Semantics are unchanged: the row moves only for a later instant and
the effective watermark is answered. Instants compare lexicographically by the
frozen grammar `boundaries.instant` holds them to, which is what makes
SQLite's text comparison the same answer Python's `>` was. Proved by
`tests.job_manager.test_retained_recovery_admission`'s concurrent-decision
case and by the unchanged `tests.job_manager.test_job_control`.

### Additive Authority read — `authorize_capability`

`Authority.holds_capability` answers a BOOLEAN, which is exactly what W16821
corrected: a boolean cannot be recorded beside the act it authorized. The
decision document was reachable only through `Core.authorize`, which the
public face deliberately does not expose, so an owner-facing consumer obliged
by REC-8 to bind owner identity and provenance had to compose that provenance
itself. `Authority.authorize_capability` exposes the existing seam as the
document it answers with, for one capability and never a route, and performs
no transition. Enumerated in `tests/authority/test_boundary.py`.

### Not changed

No broad refactor, no general editor or launcher, no live recovery or model
test, no full-suite run, no Git mutation and no host import. Stage 1-A's five
records, the original failure, its candidate, its task, its command, its
deadlines and its Job are byte-identical across the whole path, proved on the
control store's own bytes and on the Job store's rows.
