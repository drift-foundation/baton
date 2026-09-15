# Proposed delivery redesign — W161230, claim166444

**For owner selection under M166352. Recommended: keep the selected ordinary
worker architecture, but replace the monolithic completion handoff with two
executable checkpoints and a durable continuation record.** No evidence yet
requires new protocol machinery. The observed obstacle is repeated helper-only
returns and the author's reported inability to fit the remaining work in one
working context. Neither another budget grant nor another isolated helper
review addresses that obstacle.

## What is real today

Slice1 contract/storage/capacity work is accepted. Slice2 has six modified
source/test paths and useful request, capacity, I/O, observation and ending
helpers. Its ordinary managed preparation entry and complete producer-to-
collected-result execution path are absent. Current Integration.reconciled
still drives host preparation/causal observation. The newest request comparison
also still admits float representations rejected by its manager.

The selected implementation packet remains SLICE2-SCOPE-165724.md SHA256
4c18e791a29516b92d5afaba93c2042f5adaefa60bd57b7c54b13a04acba4fa0.
Its source/test set and generic reuse-only boundaries remain the patch scope.
The following changes order and resumption, not the acceptance requirements.

## Proposed checkpoint A: one real preparation through normal collection

Implement one deterministic success path across the existing layers before
adding further disconnected helpers:

1. tools/integration_bundle.py produces the semantic request and immutable
   source artifacts in the ordinary input manifest. The enclosing manifest
   supplies its own input digest; the embedded request must not hash itself.
2. reconciliation_task/entry and the non-built recipe execute the configured
   preparation through baton_worker.main(agent=...). Consume the actual validated
   launch, preserve the original Job limits, materialize private source states,
   run the configured causal sequence, and emit declared candidate/report
   artifacts. No Authority or writable target capability reaches preparation.
3. tools/integration_worker.py composes existing worker_operations with the
   selected capacity intent and actual Authority child Work/offer/claim. Parent
   offer remains pending while the same actor holds preparation; use the one
   reserved root, not a second actor/allocation or invented claim receipt.
4. StageExecution consumes actual frozen/accepted/retained worker artifacts
   through integration.reconciliation adoption, releases the preparation member
   only after ordinary ending/cleanup, and leaves apply planned/root retained.

The proving test starts the real worker fixture process at the normal simulated
engine boundary. It fails if coordinator-host preparation executes, requires
real normal input/output and accepted custody, and checks capacity before start.
A status-only mock or direct helper call does not qualify. The output is runnable
preparation behavior; checkpoint A is explicitly NOT slice2 or Work acceptance.
All mutations outside selected paths still require concrete scope selection.

## Proposed checkpoint B: finish the existing slice2 acceptance matrix

Starting from that executable path, complete strict limits/identity checks,
refusal/cancellation/cleanup, causal failure prefixes and defaults, immutable
measurement, and the already selected replay/cutpoint/no-duplicate-execution
matrix. Use real disposable owners and deterministic worker fixtures. Include
wrong source/task/assignment/custody cases, leader-first/TERM-resistant ending,
and capacity-before-start observations. Complete DEPLOYMENT-SLICE2-DRAFT.md;
main DEPLOYMENT remains W32577-owned. Independent review accepts slice2 only
when this complete matrix and exact candidate are ready.

## Resumption contract and responsibility

Implementation owns one short append-only PROGRESS checkpoint naming the last
runnable command/result, exact changed files, next wiring edit and unfinished
acceptance cases. Continue across context compaction from that record. If the
managed runner cannot resume within its turn, report the exact observed limit
and preserve the checkpoint; the next author claim resumes at the named edit.
Do not restart helper review merely because a context ended. No second hidden
context, participant, parallel agent, Git branch or new provider is proposed.
Reviewer evaluates executable checkpoint evidence and final acceptance; its
feedback does not become an approval prerequisite for every internal edit.

## Full closure is still larger than checkpoint B

Full W161230 also needs the derived apply/target-effect and receipt producer,
final-failure/root-settlement behavior and integration verification currently
reserved for slice3. Prepare its concrete selection packet once the actual
preparation/adoption operands exist. This proposal does NOT authorize those
later changes, close W161230 on slice2, or release W156162/W161234 early.

If the ordinary lifecycle cannot support checkpoint A, return the exact missing
API/incompatible invariant from its real wiring attempt; only then propose a
bounded product architecture change against that evidence. The current claim
has reported a context limitation, not such an architectural contradiction.

## Owner decision

Select this composition-first, resumable delivery plan within the existing
slice2 path set, or select a different product scope explicitly. The recommendation
preserves correctness and useful accepted work and supplies an observable next
result. Do not send the unchanged monolithic helper-correction loop back again.
Cumulative stopwatch caps remain removed; sensible per-run limits, cleanup,
focused deterministic evidence and independent acceptance remain mandatory.
No actual engine/model/image execution, broad discovery or cleanup grant.
