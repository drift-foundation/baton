# W285465 — recovery criteria after host initial preparation selection

Prepared by baton.tuner for W286800/286803; authority T286800/286800 and
T285465/286802. Read with current DESIGN TOK-7, HOST-1, DB-1 and section19, and
W285464 FINDING's September27 owner selection (handoff286782). This replaces only
initial-preparation assumptions in the preserved W285806 RECOVERY-PACKET.md.
No implementation acceptance or API shape is asserted. W285464 is active; its
accepted delivery must supply the actual interfaces and durable records.

## Start from the accepted predecessor

After W285464 acceptance and successful W285465 claim, inspect its latest review,
manifest and host-preparation checkpoint. Map the criteria below to actual caller
boundaries and durable records; pin exact operation/attempt/resource/claim and
checkpoint identities, writer lifetime tracking, completion semantics and task
admission/launch correlation. Record exact focused selectors before execution.
Use the selected ordinary no-context/no-review path. No maintenance executor is
required for fresh private allocation, staging, input/task publication or initial
permissions. Do not extend this exception past task handoff or use it to justify
host reset, deletion or retained-custody mutations.

Use real coordination/control state with deterministic filesystem interruption
and engine/provider substitutes at normal boundaries. Reopen fresh handles over
the same persisted state rather than replacing it with an empty store. Preserve
external writer/engine observations across manager restart. Each cut must visibly
fire at its actual boundary; a helper-only replay or swallowed injection is not
proof of connected recovery. Bound and clean up test-owned processes through the
authorized harness; no second live manager or uncontrolled writer.

## Host preparation cuts and required outcomes

| ID | Actual cut or conflict | Required evidence after recovery |
| --- | --- | --- |
| HP1 | Interrupt partial directory allocation, source staging/mountpoint creation, task/input publication or initial permission setup; select a cut in each affected phase. | Identify exact partial attempt, prove exclusive ownership and classify incomplete state. No task admission or launch from partial data. After proven writer cessation, resume only through the accepted preparation contract or retain an actionable hold; no improvised host reset/deletion. Sibling bytes and identities remain unchanged. |
| HP2 | Filesystem preparation completes before durable completion publication. | Existing files alone do not prove completion. Reconcile exact resources and writer state using accepted rules before publishing or consuming completion. A crash cannot bypass claim/eligibility checks or duplicate conflicting preparation. |
| HP3 | Durable completion commits before task admission. | Fresh handles validate correlated completion, current claim/eligibility, resource and checkpoint identity, and absence of unfinished writers. Matching valid state proceeds to exactly one task; completion is not irrevocable admission authority. |
| HP4 | Interrupt or time out while a host writer/helper remains able to finish, including a delayed completion after recovery begins. | No launch, reuse or replacement while that capability is uncertain. Deadline or manager exit alone is insufficient. Release the controlled writer and prove cessation through the real accepted mechanism before recovery progresses; late evidence cannot settle another attempt/generation. |
| HP5 | Restart at HP1–HP4 with process-local tracking lost. | Recover from durable identity and observable writer facts. An empty map cannot imply no writer. If proof is unavailable, persist an actionable unknown hold with the exact resource/operation; no fabricated completion or automatic hold clearing. |
| HP6 | Change prepared resource/checkpoint/source identity, claim eligibility or exclusive ownership between completion and task admission. | Reject stale admission, zero task launches; do not silently repin to substituted bytes or resources. Exercise competing admission and unrelated sibling progress under the accepted ownership mechanism. |
| HP7 | Replay matching completion through fresh handles, then replay mismatched attempt/resource/operation evidence. | Matching settled preparation is consumed without duplicate filesystem work or task dispatch; mismatches refuse/hold without side effects. Counts distinguish preparation writes, durable completion, task admission and task create/start. |
| HP8 | Task launch intent committed but create/start reply lost after valid host handoff. | Reconcile the exact recorded task execution using inherited launch correlation. No second dispatch because a reply or local map is absent; unknown remains held. Initial-preparation authority cannot mutate handed-off resources. |

Include a connected positive path with finished host writers, durable completion,
identity revalidation and exactly one task launch. Zero launches on a held path
is necessary but is not success-path proof. Exercise DB-1 instrumentation at
filesystem and engine boundaries with an independent coordination connection to
show external I/O does not hold database transactions. Inspect actual exposed
paths and assert sibling isolation, not merely destination naming. Credentials,
authority stores and unrelated roots must not enter an execution's writable scope.

## Maintenance obligations that remain

These apply to operations still governed by maintenance containers; do not insert
a maintenance launch into ordinary host preparation to satisfy these rows.

| ID | Retained check | Evidence treatment |
| --- | --- | --- |
| MC1 | Normal transfer and expiry/revocation require exact bound runtime termination and exclusion of associated writers before settlement/return/replacement or conflicting task admission. | Reuse unchanged G1 and accepted W285463 proofs; connect any remaining recovery caller gap. A sent stop or expired deadline is not cessation. |
| MC2 | Engine outage, uncertain create/start and delayed replies preserve revocation/unknown holds; actual recovery reaches reconciliation after availability returns without duplicate effects. | Retain useful original C1–C6/C9 schedules where relevant to the accepted maintenance operation. Correlate late runtime evidence exactly; never clean up by guessed name or assert absence from missing local state. |
| MC3 | Durable maintenance settlement and fresh-handle replay bind exact operation/resource/result; changed identity refuses. | Retain applicable C7/C10 evidence and current accepted receipt contract. Cover transfer ordering only for actual governed operations; do not invent an API or rerun all historical probes. |

## Finite integrated acceptance record

For each HP1–HP8 and MC1–MC3 row record: applicable operation; exact cut and proof
it fired; durable state before/after; observed writer state; separate effect,
receipt, admission, create/start and dispatch counts; expected continue/refuse/hold
outcome; exact test selector, duration and evidence path. Subcuts of HP1 and HP4
must be individually distinguishable. Record unknowns and justified inherited
coverage rather than labeling unexecuted rows passed.

Inherited evidence is G1 acceptance and W285463's independently accepted facility
candidate/review, plus W285464 only once its revised host path is accepted.
Historical allocation-container reviews establish their then-applicable results,
not acceptance of the changed host-preparation contract. For each inherited row
pin the exact review/candidate and verify the relevant bytes and behavior remain
applicable; otherwise identify the focused missing proof. Remaining obligations
are connected host interruption/writer recovery and the integrated ordering,
isolation, replay and no-false-success checks above, to the extent not already
proved by the accepted predecessor.

Final independent review binds the actual candidate/path set and checks changed
expectations against the current contract. Preserve existing genuine defect
coverage and evidence; no broad stress, live Docker/model, cleanup campaign,
new graph gate, hold-clearing feature or W285465 closure is selected here.
The actual dependency on W285464 (edge285468) and existing route stay unchanged.
W286800 changes only this document, FINDING.md and PLAN.md in this dossier.
