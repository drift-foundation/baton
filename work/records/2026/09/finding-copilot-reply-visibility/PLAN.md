# Completed — 2026-09-08, reviewer claim120004

Accepted at `review-2026-09-08T14-46-00Z.md`. Owner handoff119986 and inspected
`evidence/operator-socket-test.txt` discharge the last operator-side test gate;
current hashes match the independently reviewed candidate. The bounded reminder
change and attachment diagnosis are complete. This supersedes all pending
correction/evidence/acceptance entries retained below. No deployment, restart
or visible-recovery claim; those remain distinct operator actions. No further
implementation or verification is queued by this record.

# Current disposition — 2026-09-08, reviewer claim119916

Correction verified at `review-2026-09-08T14-34-09Z.md`; no source correction
remains requested for its exact three hashes. This supersedes the earlier
changes-requested state retained below.

1. baton.ops supplies M119869's fresh operator-side socket-test result against
   the reviewed candidate directly in `evidence/operator-socket-test.txt`, with
   command, context, outcome and hashes. Retained managed 53-test pass is reused
   but cannot replace this explicit owner requirement.
2. Return through baton.bug to inspect that artifact and complete acceptance;
   keep Work open until then. No socket retry in the managed reviewer context,
   deployment or process restart. Preserve Normal priority.
3. Diagnosis is now the recorded CLI/dispatcher thread attachment mismatch in
   `DELIVERY-119806.md`, superseding the unidentified-client hypothesis below.
   Reattachment/visible recovery remains an operator-context fact to record;
   no frontend defect or reminder-based attachment repair is claimed.

# Diagnostic plan — W119521

Current state, reviewer claim119798: **changes requested** in
`review-2026-09-08T14-17-52Z.md`. The recurring first50 keys can starve the
remaining new obligations or due reminders. Owner/ops must provide the missing
socket artifact requested by M119806 and assign correction to an eligible
implementation context; tuner quarantine is separate. Preserve Normal priority
and the three approved paths. Add both offline starvation regressions and mixed
new attention, then return through baton.bug. Reuse47 retained passing results
as applicable; no socket retry, deployment or restart is authorized here.

1. [done] Verify obligation disposition and preserve original notification,
   turn, thread and final-answer item identities.
2. [done] Distinguish persisted rollout from app-server read hydration: both
   contain the completed final answer and commands.
3. [pending operator context] Identify actual UI client and connected endpoint;
   compare its selected thread with 01a08124-bd0e-7271-aa3c-e0fd5846a8cf.
4. [proposed] Reopen/read that same thread without sending a message. If the
   reply appears, investigate missed live events or reconnect reconciliation;
   if it does not, compare the client's received history with thread/read and
   inspect filtering/rendering, including the final_answer phase.
5. [proposed] On the next natural advisory, correlate thread/turn/item IDs at
   bridge completion and client receipt/display. Inspect subscription and
   per-connection opt-out methods; do not enable unrestricted payload logging.
6. [pending evidence] Assign the smallest correction at the first failing
   boundary. Preserve the priority fix and critical-path worker capacity.
   Any reminder/receipt semantics change is a separately pinned decision;
   do not manufacture another obligation or erase the notification cursor.

2026-09-08 clarification: the operator may have missed the saved reply, so steps
3–6 remain conditional diagnostic options, not evidence of a display defect.
The FINDING now records a proposed ten-minute unresolved-obligation reminder
contract. Confirm and schedule that bounded notifier change separately before
implementation; preserve existing work/failure deduplication and prompt mapping.

## Current approved implementation — 2026-09-08

The owner approval in event119722 supersedes reminder-confirmation-pending
above. Implement the pinned per-obligation timer/generation and legacy migration
in the notifier, add deterministic offline tests, and document operation and
migration. Keep diagnostics3–6 conditional; no UI defect is claimed or needed
to justify the approved reminder feature. No stack/process restart.

Verification question: do reminders expire independently only for still-owed
response obligations, remain stable through busy/rejected retries and reload,
and preserve existing Work/failure delivery semantics? Run the new clock-driven
test class first, then the whole notifier test module once as the relevant
regression sweep. Budget20seconds; no live CLI mutation, model, daemon or network
provider. The existing local Unix-socket test remains part of that module.
Pass exact source/test/docs evidence to baton.bug for independent review.

Size assessment: one approved notifier behavior with its configuration,
persistence, bounded delivery and tests. These share one acceptance contract;
no independently schedulable second feature or UI correction is included.

## Correction outcome — 2026-09-08, claim119876, baton.claude

The P2 starvation is **corrected** within the three approved paths; no
additional path was needed and none was taken. `poll` orders the batch by
priority — fresh attention, then due reminders by their own oldest anchor with
the locator as tie-breaker — retaining the fifty-locator bound, retry identity,
generation accounting, legacy migration, failure pairing and busy/refused
semantics. Five controls added, four of which fail when only the ordering line
is reverted. Whole module 53 tests OK. Candidate hashes, the drain measurement
and the retained regression are in PROGRESS and `evidence/`.

Still outstanding before acceptance, and not mine to supply: the fresh
OPERATOR-side socket-test result against this corrected candidate that
event119869 requires, saved directly in this dossier. The module's socket
control does pass in the managed implementer context and that run is retained at
`evidence/regression-119876.txt`, but it is a different context and is not
offered as the operator artifact.

Diagnostic steps 3-6 remain conditional operator-context work. Nothing here
claims a UI or frontend defect, and the original visibility question is
unchanged. Return through baton.bug for independent re-review.
