# Read Authority evidence without write-capable opening

W126880, parent W122060. Owner M126833 approved the exact three-path Authority
half of `../../READ-ONLY-OPENING-ALLOCATION-2026-09-09.md`, additive tests only,
baton.impl returning baton.bug. Pinned by reviewer under parent claim126878.

Confirmed baseline: Authority.open in authority/api.py delegates to Store.open,
whose initial read-only probe is followed by BEGIN IMMEDIATE, schema application
and persistent WAL configuration. The private probe is not a supported owner
reader. Source review and disposable public evidence are in
`../../review-2026-09-09T09-31-41Z.md` and
`../../evidence/consumer-126729/FINDING.md`. Reuse that evidence, including its
permission-probe limitation; no fresh live-store inspection is required.

The consumer's separate status process lacks an already opened Authority. Its
ordinary serving path has one and continues independently. This provider owns
only safe opening of the existing owner, not receipt policy, integration,
terminal handoff, or the final read-only factory.

Pinned API: `Authority.open_readonly(path, *, expected_authority_uuid=None,
clock=None, new_uuid=None)` returns the existing public Authority reading and
disposal interface backed by a non-writing owned store. Deployment callers must
supply expected_authority_uuid. Implement the supporting Store opening within
its owner. Preserve the current public readers and serving open/create behavior.
Any equivalent within-scope API clarification is recorded before implementation,
not silently changed; no additional owner approval is needed for such a detail.

The accepted allocation's full non-initialization, schema/UUID binding,
no-persistent-change and coherent committed/WAL-read requirements apply.
Do not treat a live database as immutable, copy its main file, bypass private
ownership checks from the consumer, or repair an unreadable store. State any
sidecar/filesystem access limit precisely and refuse rather than fall back to
write-capable opening. Mutation attempts through the resulting public handle
must refuse before any write/external effect. No new session or close authority.

## 2026-09-09 — independent review126983, changes requested

Confirmed artifact creation in partial-sidecar states and an unprotected
serving-shutdown opening window. Exact diagnosis, executable disposable probe,
candidate bytes and verification are in `review-2026-09-09T10-04-51Z.md`.
This supersedes the implementation's claim that the existence preflight ensures
no persistent changes. Keep the approved API/path allocation and visible-refusal
rule; no acceptance or workaround is granted. Diagnose the opening boundary
before a further guard-only repair. W122060 remains gated on this provider.

## 2026-09-09 — review127071, partial correction and owner disposition

`review-2026-09-09T10-17-37Z.md` independently confirms that fixed partial-sidecar
states now refuse without creation, superseding that portion of review126983.
Serving shutdown still creates artifacts before the post-read refusal. This
remaining failure is not discharged by detection or by the new refusal test.
Decision support is `OPENING-BOUNDARY-DECISION-2026-09-09.md`. The strict rule
remains current unless explicitly amended; no further guard-only allocation,
cleanup or assumed writer-lifetime guarantee is authorized. W122060 stays gated.

## 2026-09-09 — owner M128249 explicitly amends sidecar effects

Owner M128249 supersedes owner126833's blanket no-artifact requirement for
SQLite-managed WAL/SHM creation and maintenance during mode=ro opening,
including refused opens. This supersedes the strict-sidecar acceptance rule and
pending-disposition status above; earlier observations/reviews remain history.
The exact current contract is the amendment at the top of
`../../READ-ONLY-OPENING-ALLOCATION-2026-09-09.md`. Database contents and
committed evidence, coherent reads, UUID/schema checks, mutation refusal and
serving behavior remain protected. No database creation, schema change,
checkpoint, application cleanup, permissions change or write-capable fallback.

The three paths stay fixed. Only sidecar-effect expectations may change in
tests/authority/test_store.py; all other assertions remain. PLAN schedules the
conversion before edits. Candidate bytes still match review127071 at reviewer
claim128257; they are not accepted under the amendment until implemented and
independently reviewed. Reconcile and carry usage; no new planning Job.

## 2026-09-09 — independently accepted, review128304

`review-2026-09-09T14-00-25Z.md` accepts candidate128271 under the explicit
owner128249 amendment, superseding the pending-implementation/acceptance status.
Accepted bytes are retained in evidence/accepted-128304. Independent50-test
and exited-writer WAL evidence confirms the preserved guarantees. The same
review corrects earlier reviewer arithmetic; charged usage is3.464s/20s.
W122060 still requires W126887 acceptance and its own bounded read-only join.
