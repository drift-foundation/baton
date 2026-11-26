# Owner-paced MANUAL Jobs — W386295

2026-11-25. Child of W385263, created E386295 and claimed E386296. Slawomir approved M386287. Each assignment has a stable phase name, immutable inputs, explicit start and retained findings. Independent ready selections may overlap. Closed dependencies refuse start. The Job stays open on the operator to-do list after its last phase settles until explicit owner closure.

The Job wall budget charges elapsed time while any selected phase is outstanding, including capacity waits. Overlapping intervals count once. Idle gaps consume zero, including across manager restarts. A restart cannot grant a selection, duplicate an admission or reset charged time. Execution, provider and verification limits continue to apply.

## Owner ruling on M386315 U1 — recorded phase end and MANUAL budget

Charge from accepted selection, including capacity waits, through the verifiable frozen result timestamp for that attempt. A later manager settlement or owner decision adds no time. A held result can still need disposition after its budget interval ends. Charge overlapping active selections once; when none remain outstanding for budget purposes, the unused budget is preserved even if the owner returns a year later. This supersedes using the later settlement timestamp for that case.

## Owner ruling on M386315 U2 — closed MANUAL Job display

After explicit owner closure, show MANUAL · CLOSED with a phase-outcome summary, for example 1 finished · 1 failed · 2 never selected. Keep the individual phase rows and results readable. Remove the closed Job from the open to-do list.

## Owner ruling on M386315 R1 — owner finishes a held phase

A finished phase is frozen. When attribution is uncertain and the phase is still held, Slawomir may inspect its retained evidence and finish it with his chosen outcome, including success or failure. Record Slawomir as the principal responsible for that final decision. Preserve the original worker evidence and unresolved attribution. A subsequent request must not revise a finished outcome or replace its signer. The budget stops at the previously ruled recorded phase end even if the owner finishes it later.

2026-11-26, owner decision on K’s M386315. Supersedes the earlier use of manager settlement time when an attempt has a verifiable frozen result. End that selection’s charged interval at the bound frozen-result instant, including when a held result awaits an owner. Count overlap once. The authenticated owner can finish a held phase by visible Job and phase, selecting success or failure. Retain worker evidence and the owner identity and decision separately. Exact retries replay; conflicting decisions refuse. Explicit closure shows MANUAL · CLOSED and phase outcome counts.

## Owner ruling on M386325 U3 — personal confirmation

A finish-phase receipt naming Slawomir as the decider must mean he personally confirmed that decision. Authentication solely by the shared installation UID and configured participant does not meet this requirement. The mechanism has not been selected.

## Owner ruling on M386325 R2 — automatic worker release

After the owner finishes a held phase and Baton confirms the runtime has stopped, Baton automatically releases the worker for later assignments. Retain the frozen evidence and final owner decision. No separate operator release is needed.

## Owner ruling — pending phase decisions across sessions

When a Job is waiting for Slawomir, he must be able to find the pending decision and personally answer it from any supported operator interface, at any later time. Closing the originating terminal or restarting the manager must not lose the request. Bind the confirmation to the specific Job, phase and held result. The shared Unix account alone is insufficient. The choice of authentication and transport remains open.

## Owner clarification — interface-independent decision API

The required capability is an API through which an operator client can retrieve a pending decision and submit the owner’s personal confirmation for its exact Job, phase, held result and chosen outcome. CLI, TUI and web are possible clients. They use the same authority checks and durable decision. The owner did not select a transport, a particular confirmation UI, or implementation of all three clients.

## Owner clarification — trusted deployment, no personal signing key

Slawomir rejected a personal signing key for this trusted environment. Do not proceed with a signer, device enrollment or signature qualification on the basis of the U3 proposal. Keep the interface-independent explicit owner decision, bound outcome, retained evidence and frozen receipt. Local UID authentication identifies the shared account; the remaining distinction is whether personal confirmation is accepted as a trusted operator declaration.

2026-11-26, owner selection during claim E386327. This supersedes the earlier open authentication choice and the requirement for independent proof that a particular human operated the shared account. Use the trusted local installation-owner context and an explicit finish-phase decision through the shared API. Bind the identity, exact frozen result and chosen outcome; record the actual local authentication basis. Agents must leave owner decisions to Slawomir. The account is shared; this procedure attributes an explicit local-owner action and cannot distinguish humans from other processes running under the same UID. The owner declined a signing key. Discovery and confirmation can occur in separate sessions.

## Owner ruling — use the existing trust model for MANUAL decisions

Slawomir declined a phase-specific security, signing or logging project. This supersedes the earlier U3 requirement for technical proof of personal presence. An explicit owner action through the existing trusted operator API suffices; agents leave that action to the operator. The stored decision identifies the configured owner under the existing trust model and preserves the chosen outcome and held-result binding for restart and replay. No new authentication mechanism or audit subsystem is required for this Work.

2026-11-26, final U3 disposition from the owner in E386327. Keep M386318’s existing trusted-owner implementation. The implementation and test delta is R2 only. No additional authentication, presence check, API or audit logging is selected. This supersedes the preceding implementation proposal. Agents leave real owner decisions to Slawomir.
