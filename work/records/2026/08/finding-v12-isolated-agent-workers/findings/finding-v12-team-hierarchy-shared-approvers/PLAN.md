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
6. [deferred] Design the Teams and Inbox views for hierarchy and inherited
   grants before implementation.

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
