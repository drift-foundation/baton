# v12 system architecture and maintainability review

Authoritative Work: W386228; thread T386228; root baton.

## 2026-11-25 — owner request

Owner requests a whole-system review of whether v12 is organized efficiently, with duplication, unclear functions and leftovers identified. Repeated qualification failures and manual handoffs motivate an assessment beyond individual accepted patches. Scope is evidence-based assessment, not a broad rewrite or a presumption that old code should be deleted.

Selected sequencing: after W385830 native-provider qualification, without interrupting it. Created on baton.codx for codexpc. Coordinator attempted block W386228 on W385830; canonical operation refused because baton.prompt is not a handler of baton.codx. No dependency is claimed installed. Codexpc must install and read back this edge before execution; until then the owner instruction still prohibits early execution.

2026-11-25 owner sequencing supersession. E386229 installed the original edge. The owner then assigned qualification to K and selected concurrent assessment of the committed source. E386230 removed the edge, E386231 woke this Work and E386232 records baton.codxpc's claim. Qualification evidence is an input when available. It is no longer a scheduling prerequisite.

## Owner ruling — sequential role changes and independent review, 2026-11-25

Implementation and review are assignments. Within a Job, a worker may change roles between sequential assignments and retain its Job/worker home. Each assignment supplies its own instructions and permissions. Independent review starts a fresh conversation with the task, acceptance criteria, exact candidate and verification evidence. Eligibility is evaluated against the producer of that candidate. A new conversation cannot turn the producing worker's self-check into an independent review. Distinct workers may use the same model. A fresh conversation does not establish filesystem isolation. These are design decisions for subsequent work; the two-worker Q4 proof did not exercise a role change.

## Owner ruling — provider adapter independence, 2026-11-25

Baton owns the assignment lifecycle, workspace, verification and artifact custody. Each vendor adapter owns its CLI invocation, provider-specific home and environment settings, model selection and interpretation of provider output. Containment takes priority over reuse across adapters. A vendor adapter must be able to evolve independently of another vendor's implementation. One vendor adapter inheriting from another conflicts with this goal. Similar code may remain local where the two providers can change for different reasons. Common utilities are appropriate for stable mechanisms with an independent contract. This ruling establishes a design target for separately scoped implementation.

## Owner ruling — committed recovery journal reads, 2026-11-25

The Job store owns retrieval of committed operation results, their ordering and JSON decoding. Each recovery workflow selects its event kinds, owns required fields and interprets the records under its domain rules. Preserve existing ordering, integrity refusals and reopen behavior across all three consumers. Scope implementation separately.

## Owner ruling — instance startup, 2026-11-25

Keep one operator-facing startup call. Separate validation of worker, store and Authority bindings from activation at the first durable change. Invalid bindings must refuse before mutation. During activation the component opening a resource owns its cleanup on partial failure. Preserve the existing lifecycle and recovery guarantees for effects already committed. Check both a mismatched configuration and a failure partway through activation.

## Owner ruling — retiring old code, 2026-11-25

Trace suspected leftovers through supported callers, CLI entry points, build and packaging recipes, and recovery paths for existing instances. Name any current dependency. When the only use was a retired pilot, remove the obsolete code and its entry points together. Preserve implementation history in Git and the supporting evidence in the permanent dossier. An inconclusive caller search leaves the item open for investigation. This rule does not select a particular deletion.

## Owner ruling — verification of refactors, 2026-11-25

Exercise the boundary whose behavior must survive the change. For adapter separation, drive the real Baton assignment loop with simulated provider CLIs. Check each invocation and its environment, and verify that changing only the provider selection preserves the verifier's environment for the same Job layout. A vendor-specific change should leave the other adapter and its tests untouched and passing. Use a real container for mount and permission behavior and a live provider when the question depends on actual provider behavior. Select those executions under the existing execution rules.
