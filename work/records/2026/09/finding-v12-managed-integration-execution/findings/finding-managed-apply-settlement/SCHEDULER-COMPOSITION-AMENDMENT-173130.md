# Scheduler composition boundary after managed cleanup

2026-09-15T00:37:40Z — baton.tuner, implementing claim173130, W170385.
**Observed scoped blocker; proposed amendment, not completion or acceptance.**

## Measured behavior

The selected producer amendment is implemented: exact derived commit/tree and
Git modes survive ordinary retained preparation custody. The ordinary composed
path now publishes the derived proposal through the actual parent assignment,
uses three actual JudgmentExecution instances and scoped independent receipts,
admits the parent apply before start, runs the real worker entry/workload through
a deterministic fake engine boundary, freezes/intakes its output, fences and
cleans its actual runtime, performs the real disposable target/ref plus receipt
transaction, records Authority integration and released lease, routes/discharges
the parent and releases the root. Step27 passes that traversal; step30 repeats
it with207 other selected checks (208 total, all passed). This is simulated
provider/engine evidence, not live OCI or model certification. Final downstream
dependency behavior and the other finite groups remain unproved.

Step29 is the concrete blocker regression:
`tests.tools.test_managed_apply.AnOrdinaryManagedIntegration.test_reopen_after_target_effect_before_coordinator_settlement`.
It performs the real target transaction and loses the reply before recording its
effect at the coordinator. The test witnesses root `open` and publication
`intended`, closes the composition and both stores, proves the old Authority
handle closed, and reopens the ordinary composition over the same durable files
and external fake engine state. On the next sweep, before continuation:

- `job_manager/manager.py:145` calls `scheduler.reconcile_allocations(store, held)`.
- `scheduler.py:583` sees the parent's actual `cleanup=retained` and calls release.
- `scheduler._move` reaches the existing integration root guard at467.
- `integration_capacity.releasable` correctly refuses: the root remains open
  because target/coordinator/Authority/final routing is not fully settled.
- The refusal escapes the sweep before its later launch/conclude pass can
  recover the target receipt. It is a nondurable refusal (scheduler's default),
  not a fabricated settled failure or a poisoned durable release receipt.

Evidence: run-170385-step-29.log, SHA256 recorded in partial-173130.json.
Measured1.473166s (exact ledger value authoritative), test process group gone.
Step28 reached the same target cut but first failed a fixture spelling (`intent`
versus actual `intended`); step29 corrects that assertion and reaches the genuine
scheduler conflict. No scheduler or manager bytes were edited to bypass it.

## Why the root guard is required

Closing root admission at collection time would let that cleanup shortcut release
logical integration capacity before the applicable target/result outcome exists.
The current partial implementation therefore keeps the root open until final
success is retained and parent handoff/discharge completes. Misreporting the
cleanup axis, weakening the root guard, writing a successful parent outcome early,
or driving target effects from an observation reader would conceal the problem.
A coordinator restart between cleanup and settlement must remain an ordinary
pending integration, with its capacity held and continuation still reachable.

## Exact proposed scope amendment

SLICE3-SCOPE-172905.md, selected by172982 and retained by173126, explicitly says:
> Reuse-only: generic Worker Manager/OCI transport/attempt lifecycle, scheduler
> uniqueness/release guard, schema/migrations

It lists no scheduler source path and directs a concrete inability to compose
through these owners back for scoped selection. The selected producer amendment
adds only reconciliation_task.py/reconciliation_entry.py; it does not add the
scheduler. This is why claim173130 returns through baton.bug instead of silently
editing a reuse-only owner. It is not a test budget/context limit or a request to
waive the eight-group acceptance.

**Proposed:** add exactly
`baton:v12/python/src/baton_v12/job_manager/scheduler.py` for a narrow
`reconcile_allocations` composition guard: before an automatic release request,
ask the integration-capacity owner whether a registered root remains unreleasable;
when it does, retain the allocation and continue the sweep to the owning managed
continuation. Keep the atomic guard in `_move` authoritative and unchanged.
Do not change allocator uniqueness, reservations, principal scheduling, runtime
cleanup facts, release semantics for non-integration allocations, or protocol.
The already selected integration_capacity.py may expose the read-only answer.
The already selected test_managed_apply.py and test_managed_integration_capacity.py
can carry bounded regressions; no additional test path is requested.

Independent review should validate this diagnosis and choose the narrow amendment
or demonstrate an honest composition inside the existing scope. It should not
accept the current partial implementation as complete. Scheduler baseline bytes
are pinned in partial-173130.json for that review.

## Preserved implementation and exact remaining work

partial-173130.json SHA256
`121835535c31a0d7a09a9cebc3ca2a534c5025ae92bd42c63a2ed909d5f64009`
is an **incomplete checkpoint**, not an import proposal. It inventories all30
selected paths, names16 changed in this claim, preserves their exact bytes under
partial-173130/, and carries a delta against baseline-173130/. The earlier
partial172988 and its atomic Git profile remain intact. No Git state changed.

After scope disposition, resume the original full Work, including:

1. Correct the pending-cleanup scheduler interaction and pass the retained
   target-effect restart regression without a second CAS or early release.
2. Finish the selected integration-owned durable failure/outcome reader and
   projection. Known preparation failure must cancel planned apply and settle
   the parent/root without a fake parent claim/runtime. Known apply harness
   failure must retain real evidence, perform no target publication, complete
   cleanup, and remain exceptional with dependent gates closed. Current partial
   apply failure only refuses after cleanup; it is **not** complete failure
   settlement. integration_capacity.py/projection.py are still baseline bytes.
3. Complete reopen after retained adoption/publication, final receipt/handoff,
   nonaccepting judgment/mapping/stale-boundary cases, visible unknown target
   effect, Job host_verification override/traps, and final dependency assertions.
   Reuse the accepted group2 uncertain-start/manual recovery evidence; do not
   reintroduce deferred automatic recovery or broad matrices.
4. Revalidate exact custody/request bindings, source/target storage isolation,
   final historical receipt proof and selected worker command timeout/cleanup
   behavior. Current passing ordinary traversal is not independent acceptance
   of every new request/reader/error branch.
5. Preserve baseline/change ownership, run the bounded regression selection,
   produce the complete immutable candidate and return baton.feat with
   set-next=baton.feat. Keep W170387 and W161230 gated; no helper-only closure.

Verification accounting: claim173130 steps06–30 total75.25487356405938s;
prior author steps01–05 remain3.207571343984455s; all author runs total
78.46244490804384s. Prior reviewer0.32740256300894544s stays separate. All30
supervisor groups are proved gone; no timeout or supervisor signal was needed.
Step30 passed208 tests in9.655877s (exact ledger authoritative); the intentionally
failing restart regression is excluded from that green selection and remains
explicitly outstanding. Logs include every fixture/implementation failure;
none is hidden or relabelled as a pass. No live model, actual OCI engine,
image build, install, broad discovery or schema/protocol change occurred.

Repository diff checking still reports the pre-existing stage_execution.py:1923
trailing whitespace. It exists in both baselines; this claim's exact delta has
no added trailing whitespace. No required source/dossier was unreadable in this
claim. Step12 also named a nonexistent test method; that selector executed no
test and its error is recorded, not treated as product coverage.
