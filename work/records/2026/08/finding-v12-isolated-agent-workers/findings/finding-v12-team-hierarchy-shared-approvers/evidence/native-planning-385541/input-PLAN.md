# Plan — v12 team hierarchy and shared approvers

1. [done] Record the confirmed need for shared principals, hierarchical team
   scopes, and one-to-one leaf approvers.
2. [done 2026-08-25] Define the principal, organizational node, membership, role
   grant, repository and route records without conflating their identities.
3. [done 2026-08-25] Rule inheritance, local binding, masking, alternatives and
   quorum semantics with concrete positive and ambiguous examples.
4. [done 2026-08-25] Define deterministic resolution, audit evidence, unified inbox,
   capacity and runtime projections.
5. [done 2026-08-25] Add conformance cases for shared subtree approval, leaf-local
   approval, absent principals, ambiguous grants and cross-scope isolation.
6. [deferred; clarified 2026-09-04] Design the Teams and Inbox views for
   hierarchy, inherited grants, and one cross-team manager identity before
   implementation. The UI and command surface must select an effective scope
   without manufacturing a separate participant identity per team.

## Reviewer design pass — 2026-08-25

1. [done] Revalidate the requirement against the current Python v12 authority:
   participant identity, global capabilities, opaque routes and actor-only
   receipts cannot represent scoped shared principals safely.
2. [done 2026-08-25] Rule a strict organizational forest, separate canonical
   principal/scope/membership/grant/mask/route/repository records, augmenting
   inheritance with explicit masks, and authority-derived effective scope.
3. [done 2026-08-25] Rule explicit one-of/all-of/threshold decision policy;
   freeze approval eligibility and threshold at the proposal policy generation.
4. [done 2026-08-25] Keep inbox, runtime and capacity principal-global while
   keeping availability operational and never authority-changing.
5. [implementation-gated] After W1431/W1433 ordering, decompose schema and
   resolver, assignment/receipt migration, scheduler/manager projections,
   conformance, and Teams/Inbox UX into independently reviewable M6 Jobs.
6. [verification-gated] Run the positive/negative/race/retry matrix pinned in
   `FINDING.md`; no production implementation is authorized by this design
   pass.

## Confirmed ordering — 2026-08-25

Slawomir approved the complete M6 baseline in T9901 message 10740. Design and
conformance specification are complete. Items 5-6 in the reviewer pass remain
gated behind W1431/W1433 and will be decomposed into new implementation Jobs;
W9901 does not authorize production edits while those gates remain.

## Ordering clarification — 2026-08-26

The final sentence above is superseded for compatibility work: W9901 still
does not authorize the full M6 hierarchy feature, but its approved model is a
binding constraint on M2-M5 foundations now. The W1431/W1433 identifiers are
pre-migration history; current full implementation remains ordered through W9
to W10.

1. [done 2026-08-26; W16793] Audit active v12 authority and Worker Manager
   foundations for irreversible flat `team.member`, actor-only receipt,
   route/scope and principal-locality assumptions.
2. [queued as W16821, W16823 and W16830] Correct only incompatibilities that
   would invalidate current work later. Authority principal/scope provenance,
   trusted-manager execution context and approval attestations are separate
   provider Work; approver obligation 16832 owns the serial dependency edges.
3. [still deferred to M6] Implement the complete hierarchy resolver, grants,
   masks, approval policy, projections and Teams/Inbox UX.

## Next planning action — owner clarification 2026-11-21

Capture complete; W9901 remains parked pending explicit scheduling, not executing. Revalidate existing principal/scope decisions and historical milestone references against current code and DESIGN. Map the confirmed multi-project/team operating model, cross-team filing and clarification dependencies, shared visibility, resource reuse and operator view to current capabilities; identify concrete gaps and update normative DESIGN before dependent implementation. Reuse W385331 rather than duplicate its clarification/discovery work. Prepare a read-only v11 migration inventory and bounded two-project pilot; no backlog copy, new authority, broad implementation, advanced scheduling or automatic launch selected. Current clarification proof remains the active priority.

## Selected next priority and decision gate — 2026-11-21

Supersedes the earlier unspecified scheduling: owner selects this as next PLANNING priority after acceptance/checkpoint of current clarification proof. Before dependent implementation, revalidate old milestones and DESIGN, produce concrete user workflows and gap/coverage map, and bring every unresolved product/UX ambiguity to the owner with scenarios/options/recommendation. Do not manufacture semantics or start a broad teams rewrite. Select the smallest two-project proof and coordinate with W385331 discovery/dependency work. Ledger activation/routing follows the current checkpoint; this note alone changes no graph gate.

## Owner priority supersession — full-suite failure, 2026-11-21

W385517 is now the current showstopper: resolve the ten full-suite failures and obtain clean owner-run acceptance before moving on. This supersedes immediate W9901 planning after the clarification checkpoint. Team/UX decisions remain valid; do not begin W9901 implementation or restart product planning while the blocker is unresolved.

## Planning release — 2026-11-21

The temporary W385517 full-suite stop above is satisfied: owner-run acceptance at 73506123 accounts for 11844 tests, 11842 passed and 2 optional skips, with zero failures/errors/unaccounted. Evidence is committed at 9fa0ec37 and W385517 is canonically closed. W9901 is now the selected planning assignment. This supersedes the temporary instruction not to restart planning; production implementation remains unselected.

Codexpc owns the bounded planning pass after routing, unpark and successful claim: revalidate current DESIGN, code and historical decisions; deliver concrete two-project operator workflows, a capability/gap map, an explicit unresolved-decision list, read-only migration inventory, and the smallest deterministic two-project proof plan. Coordinate with W385331 without transferring its implementation scope. Preserve confirmed decisions; propose specification deltas for owner review wherever semantics remain unsettled. No product edits, live runs, instance changes or migration in this pass. Return evidence and a concise decision packet in T9901, then pass to baton.decide and verify claim release.

## Native planning preparation — supersedes direct execution, 2026-11-21

The owner selects the complete workflow and v12 execution, as recorded in FINDING. M385538's direct planning default is superseded. Codexpc's immediate host assignment is bounded preparation: inspect existing supported native Job tools/templates and current installed instance readiness read-only; prepare the planning task and exact minimal kickoff commands, required inputs, routing, verification and retained-result consumer. Reuse existing tooling; no new bespoke launch helpers or extended qualification framework. Report any concrete blocker with the exact unsupported operation and smallest remedy. Do not use incomplete target functionality as a generic blocker or silently execute the substantive planning directly instead.

The native planning task must deliver the workflows, capability/gap map, decisions and bounded two-project proof plan above, with complete native workflow acceptance explicit. Planning proposals do not authorize product/spec changes. Existing no-live-run/no-instance-write boundary applies to this preparation: return the concrete launch packet to the coordinator for the supported operator execution sequence. Independent review and human Git checkpoint remain required; v11 retains the canonical coordination record until explicit cutover. No full-suite rerun is needed merely to prepare this task.
