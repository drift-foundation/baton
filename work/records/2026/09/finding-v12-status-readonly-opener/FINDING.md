# V12 status uses writable openers

Owner E316900 on W236087 authorizes bounded follow-up implementation. Discovery: baton:work/records/2026/09/finding-v12-managed-session-resume/review-2026-09-30T15-26-48Z.md and REVIEW-EVIDENCE-316831.json. Prior live correction/restore acceptance is preserved.

Confirmed source defect: tools/job_manager._status calls _job_store -> JobStore.open and ControlStore.open. JobStore.open uses sqlite3.connect and may initialize/adopt/request WAL; status advertised as read-only is not filesystem-read-only. Exact generated status for completed316689 failed at _objects with OperationalError; files existed. Verified stable copies succeeded through supported CLI. Owner environment cause is not fully established; no corruption conclusion.

Scope: make status paths genuinely observational using supported validated read-only Job/Control openers, including status with/without control and applicable observation factory. Preserve authority/schema/path validation and existing status shape. Do not change submit/serve semantics, introduce raw SQL operational workarounds or repair deployed stores. Revalidate existing JobStore.open_readonly and ControlStore read-only facilities before implementing. Relevant files tools/job_manager.py, job_manager/store.py, worker_manager/store.py and narrowly required tests.

Acceptance: focused temporary-store tests run status without directory/database write authority, missing stores refuse without creating files, wrong authority/schema refuse without migration or mutation, no-control and control status preserve output, applicable observe remains observational. Include realistic post-close WAL/sidecar conditions; do not use chmod alone as proof when test runs with bypassing privileges. Assert no new store/journal/schema writes attributable to status. Mutating commands retain existing behavior. Return independent review with candidate hashes and measured focused verification; no live run or deployed repair.

Independent top-level record because this follow-up may outlive accepted W236087. No containment or blocking edge to W236087; no dependency on the other follow-up. No broad hardening gate.

Ledger binding: W316915, routed baton.impl at creation under E316900. Sibling follow-up W316918 is independent, not a prerequisite.


## 2026-09-30T15-46-18Z — partial opener acceptance; WAL capability decision

Verdict: PARTIAL ACCEPTANCE of validated read-only opener selection; original full filesystem-read-only acceptance NOT MET. Return to owner for the concrete capability boundary decision below, not satisfying closure. Candidate hashes match; independent focused13 PASS0.053s. REVIEW-EVIDENCE-317007.json. No broad rerun or deployed access.

Code review: _status now uses JobStore.open_readonly through _observing_job_store and ControlStore.open_readonly for both ordinary and observe branches. Submit/serve retain their writable opener. Additive tests cover missing/empty/wrong-authority/wrong-schema refusal, non-migration, unchanged store bytes, compatible status shape and observer invocation. Existing assertions were not weakened. Accepted improvement prevents accidental initialization/migration through status and removes a writable fallback.

Unmet original criterion: a cleanly closed WAL database without sidecars cannot be read by this candidate under an unwritable directory. The test now expects refusal, rather than the originally requested successful status. Where writes are possible, unchanged() permits new -wal/-shm/-journal files; these remain writes attributable to status even if database content does not change. Therefore this does not fix the triggering post-completion directory-access shape or establish no store/journal writes. Author honestly reports that limit; the test pass does not waive the accepted requirement. Do not label the whole Work fixed or silently supersede its acceptance text.

Concrete owner decision: accept this narrower supported mode (validated read-only SQL handle, possible SQLite sidecar creation, fail closed when required sidecars cannot be accessed), with corresponding product documentation and explicit waiver/supersession of the full directory/no-sidecar criterion; OR retain the original filesystem-read-only requirement and select a bounded consistency-safe snapshot/reader design to meet it. That second path needs a stated consistency/lifecycle contract, not an automatic immutable=1 fallback on potentially live data. Current scope selected reusing existing validated openers; choosing snapshot semantics or reducing supported capability is the concrete unresolved design boundary. No new implementation or waiver is inferred here.

Clarification to test commentary: sequentially copying a live database and its sidecars does not, by itself, prove a consistent snapshot. The new copy case prepares a quiescent fixture and proves that case only. Previous W236087 copies were completed-run files with no sidecars and source hashes checked before/after. Do not turn either into advice to copy arbitrary active stores. Also the permission-refusal case relies on an unprivileged process; file digests prove absence of writes, not that root cannot bypass chmod. Future portable coverage should establish denied write capability explicitly when claiming that boundary.

Observation-factory test uses a minimal observer; author reported adjacent real-stage status hardening tests. No claim that every arbitrary observer cannot access another writable resource. Store opener guarantees and known product observation paths are the bounded claim. No corruption conclusion or deployed repair; owner-environment failure cause remains only partly classified.

Read whole current FINDING/PLAN/PROGRESS/candidate, E317004/events317007/T316915. Reviewer owns records, author owns job_manager.py/test_tool.py/PROGRESS. W316918 is independent; do not reopen accepted W236087 live restore. No live provider/engine, deployed store access/cleanup, integration, credentials or Git mutation. Owner receives exact accepted improvement and unresolved criterion, with no approval request to rerun ordinary tests.

## 2026-10-18T01:06:05Z — filesystem-read-only interpretation (superseded at 01:24:52Z)

Slawomir confirmed in the interactive context: "status should be read only",
after the distinction between SQL read-only access and SQLite sidecar writes
was explained. Status must perform no filesystem writes, including creation or
modification of SQLite sidecars. The original successful-status requirement
without database/directory write authority remains; merely refusing the known
closed-WAL/no-sidecar case does not complete this Work.

This resolves and supersedes the September 30 pending capability choice: the
narrower SQL-only guarantee is not selected. Preserve its accepted opener
improvement and partial review as history. DESIGN OBS-1 carries this explicit
boundary. Select a bounded consistency-safe reader design through normal
implementation and independent review; no particular snapshot mechanism is
mandated. Do not treat live data as immutable without proof or copy live DB and
sidecar files sequentially and claim a consistent snapshot.

Revalidated canonical detail at snapshot318828: Work parked at baton.decide,
unclaimed, no open blockers or obligations; no executor owns edits. Prompt owns
this decision/checkpoint/spec clarification only. Existing product/test ownership
and claim requirements remain. No live run, deployed repair or cleanup, Git act,
or reopening of W236087/W316918 is authorized by this ruling.

## 2026-10-18T01:24:52Z — owner clarifies database-state read-only contract

Owner asked whether status could simply open SQLite read-only and fail otherwise,
then clarified: "from our perspective, we just care about the database state,
what sqlite does to deliver that is perhaps not our concern". Prompt's earlier
interpretation of "status should be read only" imposed a stronger filesystem
requirement than the owner intended.

Confirmed contract: use validated SQLite read-only connections; do not change
application data or schema, initialize/migrate stores, or retry with writable
access. SQLite-managed sidecars and normal locking are acceptable. Report an
open/query refusal clearly; status need not succeed in an unwritable directory
with missing WAL sidecars. Do not build a custom snapshot reader solely to avoid
SQLite-managed effects. Preserve ordinary consistent SQLite observations and
authority/schema checks; this does not authorize unsafe immutable live reads.

This explicitly supersedes the original filesystem-no-writes and guaranteed
success-without-directory-write acceptance, the 01:06:05Z interpretation, and its
matching DESIGN/PLAN wording. Earlier partial review remains truthful history;
the existing accepted opener improvement is the starting point for bounded
revalidation, documentation/test alignment and independent review. No blanket
acceptance of current unreviewed changes is implied.

At snapshot318960 Claude holds W316915 claim318857/episode318855. Prompt changes
only decision records/PLAN and DESIGN; implementation/test/PROGRESS ownership
stays with Claude. Coordinate this clarification through T316915, preserve claim
and prior work, and let the Handler reconcile the current candidate with this
smaller acceptance contract. No live run, deployed repair/cleanup or Git mutation.

## 2026-10-18T01:45:33Z — independent review of narrowed candidate

Candidate318857 hashes match; 165 focused cases passed independently in0.854s.
Selected SQLite read-only opener behavior remains accepted in principle under
the 01:24:52Z ruling. Changes requested in review-2026-10-18T01-45-33Z.md:
R1, a non-database file with byte19=2 is falsely diagnosed as a cleanly closed
WAL/permission problem; R2, restore prior claim316919 PROGRESS history instead
of replacing it. One bounded correction, direct implementation handoff.
No custom reader, live/deployed operation or specification change requested.

Separate author-reported projection consistency concern independently reproduced
as KeyError after public submit commits between status reads. W319114 records
that pre-existing defect, parked with no dependency/containment edge on W316915;
its eventual solution must preserve DB-1/DB-4. Current PLAN names the correction
milestone and ownership; human Git checkpoint remains pending acceptance.

## 2026-10-18T01:56:12Z — independent acceptance of candidate319137

Review review-2026-10-18T01-56-12Z.md accepts the exact candidate manifest
ceb895bbf581ca4ca7cf692b5de44ae03f42263061dcc68403563dd9e44569a1 under the
01:24:52Z owner contract. All product/test/record hashes matched; independent167
cases passed in0.856s. R1 now gates the conditional hint on SQLite's own extended
error code, without header/history inference. R2 restores both historical
progress accounts to their original digests and appends the current account.
This resolves the preceding changes-requested disposition; prior evidence stays.

Pass to owner for acceptance and required human Git checkpoint; no commit made.
SQLite sidecar limits and separately parked W319114 remain explicit. No deployed
repair, live execution, integration or Git mutation is claimed.
