# Drive accepted proposals through serialized integration

Ledger Work: W103077

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/`

## Confirmed scope — 2026-09-06

Build the production driver that consumes an accepted checkpoint and verdict,
publishes the proposal, resolves the complete accepted-candidate account,
admits it to the target-global coordinator, obtains and revalidates the live
lease, invokes fenced model-driven integration, and records completion or the
operator-held recovery state. Reuse accepted Authority, checkpoint,
integration, and recovery interfaces. Do not own reviewer launch,
changes-requested correction, or shared process/configuration assembly.

The leaf must name disjoint production and test paths before implementation
and prove replay at every durable cutpoint without trusting caller-owned
documents or a replayable fence value. Adding and editing focused tests inside
the named path set is explicitly authorized.

## Reviewed contract — 2026-09-06

**Ordering correction:** Authority proposal publication cannot consume an
already accepted checkpoint: `Authority.publish` is assignment-owned, while
checkpoint freeze has already cancelled and fenced that producer generation.
This driver therefore exposes two durable phases. `publish_candidate` consumes
the manager-frozen implementation result and its owned proposal manifest and
publishes under the still-live producer assignment before W103076 calls
`freeze_checkpoint`. `admit_accepted` later consumes that immutable proposal
beside the exact accepted checkpoint/verdict, writes or replays the separately
attributable verification, technical-review, and configured-approval receipts,
and calls `admit_candidate`. Publication is not acceptance, and a rejected or
changes-requested checkpoint never enters the coordinator.

**Observed reusable interfaces:** Authority already owns proposal and receipt
immutability; `integration.admit_candidate` re-resolves the full accepted
producer account before enqueue; `integrate_next` owns target-global lease,
pre-mutation live-grant cutpoint, model delivery, settlement, and ordinary
running/held answers; `hold_interrupted`, `held_status`, and
`abandon_held_lease` own restart uncertainty. The driver adds durable
orchestration identities and selection only. It neither duplicates these
accounts nor releases/repairs a held target.

**Required policy boundary:** all proposal members come from the owned frozen
proposal manifest, Job, assignment, and Authority target—not from a caller's
summary. The closed deployment supplies participant-bound verification,
review, approval, and integration sessions plus the exact approval policy
generation. An accepted W71918 verdict can select the configured receipt path,
but cannot invent approval authority. Every Authority receipt is re-read and
cross-bound before enqueue.

**Required restart boundary:** derive proposal, receipt, entry, lease, and
attempt operation identities from their complete immutable operands. On every
sweep, adopt an existing proposal/receipts/entry/delivery before performing
the next act. `running` keeps the live lease; any restart after the integration
port was asked calls the accepted interrupted-hold operation rather than
starting another writer or optimistically settling retained output. Only an
ordinary uninterrupted `integrate_next` result may settle; manual recovery
remains explicit and target-blocking.

**Frozen path ownership:** production paths are new
`v12/python/src/baton_v12/integration/driver.py` and existing
`integration/__init__.py`. Focused tests are new
`v12/python/tests/integration/test_driver.py`. No other production or existing
test path is authorized without targeted review. Registration in
`tools/parallel_test.py` belongs to W103083.

**Required regressions:** publish before fence and refusal after fence; exact
publish/receipt/admission replay; changed proposal-manifest or policy-generation
collision; no enqueue for missing/failed/unaccepted/denied receipts; accepted
checkpoint cross-wire refusal before queue mutation; empty queue; one live
target lease; pre-mutation and pre-completion live-grant loss; running result;
successful/refused settlement; foreign/mixed/ambiguous output held; restart
before run versus after run; held status and explicit abandonment only after
positive quiescence; and no duplicate target write or Authority integration
receipt.

## Re-review correction and targeted scope expansion — 2026-09-06

The two P0 findings in `review-2026-09-06T16-57-02Z.md` are confirmed. The
earlier statement that the driver can reuse `integrate_next`'s complete
successful settlement unchanged is superseded: that leaf chooses any target
queue head and releases an integrated lease before returning, while this
driver holds sessions and evidence for one selected proposal. Those contracts
cannot be safely composed without a narrow correction at their seam.

**Exact-head decision:** W103077 remains a proposal-bound operation; it does
not become a deployment registry or dynamically select another Authority's
stores and sessions. The coordinator grant therefore takes the exact admitted
`entry_id` as a required, signed operand and grants it only when it is the
target's smallest queued rank. If another entry is ahead or another live lease
already owns the target, this proposal receives no grant, burns no fence,
publishes no delivery, invokes no runtime, and writes no integration receipt.
That no-act must remain retryable after the prior entry completes; it must not
commit an empty lease operation under the proposal's stable lease identity.
The transaction rechecks exact entry, FIFO head, target, and absence of a live
lease together before inserting the grant. This preserves target-global FIFO
and makes the coordinator-selected entry identical to the driver-selected
proposal rather than trusting a post-grant comparison.

**Authority-completion decision:** an `integrated` runtime result is not yet a
terminal coordinator result. After bounded output adoption, verification,
positive runtime quiescence, and the existing completion-side `live_grant`,
the driver writes/replays the exact Authority integration receipt and re-reads
that receipt from the Authority. Only an exact receipt for this proposal,
candidate, target, actor, and integration identity permits the coordinator to
record the integrated settlement and release the lease. Authority refusal,
lost reply, process interruption, receipt mismatch, or any later coordinator
failure leaves the lease unavailable to another writer and reaches the
accepted operator-held recovery path. A restart after the port was asked never
creates a missing receipt or settles retained output, whether the Authority
receipt is absent or already present.

An already terminal integrated/released entry is replayable only by re-reading
and cross-binding an Authority receipt that already exists. The terminal read
must never call `integrate`, because that call cannot distinguish replay from
creation. The uninterrupted success path may call it exactly once under the
live grant, then re-read it before coordinator settlement.

**Expanded frozen path ownership:** the original three paths remain owned.
The minimum existing production seam additionally authorizes edits to
`v12/python/src/baton_v12/integration/execution.py` and
`v12/python/src/baton_v12/integration/queue.py`. Focused existing-test changes
are explicitly scheduled and authorized in
`v12/python/tests/integration/test_execution.py` and
`v12/python/tests/integration/test_coordinator.py`. No schema, store, recovery,
Authority, other production, or other existing-test path is authorized by
this expansion. If the correction cannot preserve the contract inside these
seven paths, return for another targeted review before editing elsewhere.

## Mechanical test-call scope expansion — 2026-09-06

**Observed:** the exact-entry correction makes `entry_id` a required signed
operand of `grant_lease`. The already accepted W101490 runtime suite has three
direct calls that omit it: its common one-entry setup and the first and second
grants in the predecessor-runtime scenario. The already accepted W101493
recovery suite has one common helper that omits it. Running those two modules
against the corrected surface executes 104 tests and produces 97 setup errors,
all from the missing keyword; the remaining seven tests pass.

**Confirmed:** W103077 may mechanically add the already-enqueued exact entry
to those four call sites: `entry-1` in the runtime setup, `entry-1` and
`entry-2` in the two-grant runtime scenario, and `entry-1` in the recovery
helper. This compatibility maintenance does not reopen or change the closed
W101490/W101493 contracts and authorizes no assertion, expected behavior,
fixture structure, prose, or other edit in those files.

The frozen path set therefore expands by exactly:

- `v12/python/tests/integration/test_runtime.py`
- `v12/python/tests/integration/test_recovery.py`

All prior restrictions remain. The complete W103077 candidate is now limited
to the nine named paths in this finding.

## Nine-path candidate re-review — 2026-09-06

The candidate matches the frozen nine-path set and the exact-entry FIFO
correction is sound, but the completion sequence still has an unreplayed
durable cutpoint.

**Observed P0:** `execution.complete_integrated` commits
`settle_integrated` and then `release_lease` as two coordinator operations.
A process death between them leaves the entry `integrated` and its lease
`live`. On restart, `driver._terminal` re-reads the exact Authority receipt and
returns `integrated` without finishing the lease release. A measured
reproduction returned `integrated / integrated / live`; the next target entry
remains excluded forever despite the successful answer.

The same intermediate state invalidates the ordinary exception fallback:
after settlement commits, `hold_interrupted` cannot turn the already
`integrated` entry into the `held` state required by `block_target`.

**Required correction:** terminal replay distinguishes an integrated entry's
lease state. For a released lease it only re-reads/cross-binds the existing
Authority receipt and returns. For a live lease it re-reads/cross-binds that
receipt, reconstructs the owner-bound assignment from the lease/profile,
replays the already committed settlement, and completes the exact lease
release without calling the Authority `integrate` act or the model port. An
absent, mismatched, or non-live/non-released lease fails closed and never
offers the next entry.

Add an injected process-death/cutpoint regression after `settle_integrated`
and before `release_lease`. Restart must issue no Authority integration and no
runtime call, must replay the exact existing receipt, release the exact live
lease, and then permit the next FIFO entry. No path expansion is required.

## Release-tail candidate re-review — 2026-09-06

The release-tail implementation is sound when `_terminal` receives the live
coordinator entry, but the production driver supplies the immutable first
enqueue result instead.

**Observed P0:** `admit_accepted` assigns `entry` from `admit_candidate` and
passes it directly to `_terminal`. On an exact restart, `admit_candidate`
replays `enqueue`'s first result by design. That result records the entry as
`queued` even when `entries_of` now proves the materialized entry is
`integrated`. A measured completed-entry replay printed `queued integrated`
for those two answers. Consequently `_terminal` is skipped. A released lease
then refuses as incompatible with the stale queued entry; a live release tail
enters the ordinary live-lease path and cannot perform the terminal release
replay.

The new cutpoint regression masks this production seam by mocking
`admit_candidate` to return a copied current `integrated` entry. It therefore
proves `_terminal` in isolation, not restart through the real admission replay.

**Required correction:** after replaying admission, select exactly one current
entry with the derived `entry_id` from the coordinator's semantic read and
cross-bind its immutable eligibility to the freshly resolved accepted account
before terminal dispatch. Then run the existing release-tail logic against
that current entry. The restart regression must use real `admit_candidate` /
`enqueue` replay for this seam rather than substituting the terminal state.
Prove both integrated/live tail completion and integrated/released read-only
replay through the production path. No path expansion is required.

## Final independent review — 2026-09-06

**Confirmed:** `admit_accepted` now treats admission replay as immutable
operation history, refreshes exactly one current coordinator entry by its
derived identity, and cross-binds that entry's eligibility to the newly
resolved accepted account before terminal dispatch. The integrated/live and
integrated/released regressions traverse real `admit_candidate`/`enqueue`
replay and no longer substitute a current entry.

The complete nine-path candidate matches the digests recorded in
`review-2026-09-06T17-42-37Z.md`. Independent focused and integration-suite
verification passes, compilation and whitespace checks pass, and no defect or
scope drift remains. W103077 is independently signed off.
