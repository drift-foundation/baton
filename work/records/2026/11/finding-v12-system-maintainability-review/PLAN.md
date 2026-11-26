# Plan

## Current state

W386228 created, routed baton.codx for codexpc, unclaimed. Dependency on W385830 requested but not installed: coordinator lacks handler authority. First action by codexpc is the supported block operation, then detail readback. Do not begin assessment while W385830 remains open. No product ownership transferred.

## Selected outcome

One whole-v12 architecture and maintainability assessment grounded in v12/DESIGN.md, actual source, supported commands and retained qualification failures. Begin with component responsibilities and execution/recovery/data-flow maps. Cover lifecycle/timeout/credential/custody/publication duplication; provider boundaries; oversized modules/functions; obsolete or temporary paths and compatibility obligations; verification isolation and over-mocked integration gaps; operator complexity, manual steps and diagnostics. Performance claims require evidence; no speculative speed or savings claims.

Deliver one report with a concise system map, prioritized findings and concrete file/symbol/evidence references. Separate confirmed defects, baseline limitations, design gaps and optional refactoring. For each proposed change state benefit, risk, scope/ownership, dependencies and acceptance checks. Identify existing authoritative Work before proposing new Work; do not duplicate known backlog. Recommend a small first batch of independently deliverable changes. State coverage and blind spots; do not promise absence of all duplication or dead code.

## Execution boundary

Assessment only. No product/spec edits, deletion, broad consolidation, protected Git changes, live models, builds, engine operations, credentials, deployment or full suite. Read current testing guide before selecting focused deterministic probes; use prepared interpreter and retain accounted evidence. Preserve permanent dossiers and required compatibility. Diagnose before recommending removal. Source snapshot must be recorded; ongoing unrelated edits remain untouched.

## Handoff

Codexpc performs the assessment after the dependency is satisfied, under ordinary claim protocol. Return one complete report for independent review, escalating only a concrete unresolved owner decision. Implementation follow-ups are separately scoped and selected. Avoid repeated partial preparation handoffs.

2026-11-25 current milestone supersedes original sequencing. W385830 edge removed E386230, readiness verified and W386228 claimed E386232. Assessment delivered in REPORT.md with reproducible source inventory. K's Q1/Q2 results incorporated through M386233. Combined Claude qualification remains pending. Next milestone is independent report review. Proposed changes require separate selection.

2026-11-25 owner clarification for independent report review. Assess the overall architecture, including code with no known defect. Trace representative operations from caller to driver and back. For each major responsibility ask what requirement and callers justify it, whether the same rule is implemented elsewhere, which layer owns it, and what implementation details callers must understand. Look for simpler interfaces, removable indirection and opportunities for reuse where semantics agree. Identify healthy abstractions worth preserving. For proposed changes, show how the caller and driver responsibilities would look afterwards and what complexity actually disappears. Record coverage and blind spots. The launcher delay is one example. Field qualification proceeds independently.

Independent owner-selected coordinator review completed: review-2026-11-25T17-23-19Z.md. Assessment accepted with architectural priority amendments. Proposed first slice: separate provider and verifier environment construction. Implementation awaits separate selection.

2026-11-25 — Owner-approved direction for the provider boundary. Scope the environment split as a first step toward independent adapters and a Baton-owned assignment loop. Assess changes by whether one vendor's CLI or environment behavior can change while the other vendor's invocation and verifier behavior stay stable. Cross-vendor line-count reduction is not an acceptance criterion. Reflect the ruling in the normative design before product implementation.

## 2026-11-25 — first refactor selected

Slawomir delegated the ordering decision. Start with separate provider and verifier environment construction. Keep the first change bounded to fresh Codex and Claude assignments, preserving existing legacy and contextual behavior. Trace callers before editing. The provider owns its home and CLI settings; the verifier owns its private roots and layout. Share low-level validation where the contract is common. Preserve independent launch-policy checks. Verify through the real assignment loop with simulated provider CLIs that changing only the provider changes its invocation and leaves the final verifier environment equivalent under the same layout. Keep W385263 field use moving, coordinating any shared file ownership. The three committed-journal readers are the next independently scoped cleanup.
