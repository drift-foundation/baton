# Owner resume and selected corrections — 2026-11-17T19-36-36Z

Slawomir explicitly resumes development after hardware maintenance and selects BOTH recommendations from K's RENEWAL-DECISION.md and SETTLE-CLEANUP-DECISION.md (evidence/stage-c-2026-10-30). This supersedes the shutdown stop instruction for the bounded assignments below; it does not close either Work or accept pending evidence. Shutdown checkpoint6477a8db is committed; working tree was clean at recovery. Parent remains owner-held E384905; child was unclaimed at baton.decide. No new codexpc recovery message was present when inspected; new session must read canonical state and claim before execution.

## K: selected renewal option A

Keep renewal request identity, operands and lost-reply replay semantics. Write the self-signed renewal decision alongside the request result in the SAME transaction. Bind version/domain/generation/revision and both instants to the correct renewal; read through verified decision and refuse absent/mismatched/corrupted evidence. Existing renewals without the decision record fail closed; NO migration/adoption from unverifiable old result bytes selected. Use the existing operations schema, no DESIGN semantics adjustment selected. Pin clarification in the owning renewal record as needed without changing its Work state.

Acceptance includes honest renewal/expiry, exact lost-reply replay without extension, revision skip/collision refusal, corruption of request result or decision result, missing decision, wrong domain/generation/revision correlation and rollback leaving neither half committed. Verify all public read and replay paths, including direct renew retry, rather than protecting token_of alone. A changing current clock must not become part of retry request identity. Optional unrelated judgement hardening is not selected for this bounded correction.

## K: selected cleanup option1

Keep connection parameter and require it is this store's connection and is in an active transaction before writes. Continue journal writes through _record. Reject foreign connection and own connection outside a transaction before effects; verify the real ending path and atomic rollback/commit. in_transaction proves active transaction, not by itself that BEGIN IMMEDIATE acquired a particular lock; describe the guarantee accurately and rely on the accepted transact call path for its existing write-lock semantics. No atomicity/API/spec redesign selected.

K owns existing Stage C product/test paths and records affected paths/candidate hashes. No overlapping edits to codexpc's four allocated engine fixture files. Focused verification of selected corrections first; scans after the corrections and pending Stage C review findings are resolved, no full/B4/Docker/live runs. Report exact new candidate and any unresolved spec conflict; do not hold ordinary in-scope corrections for renewed permission.

## Coordinator and codexpc

Coordinator still independently reviews K M385024's trace/intake/provider_context corrections from immutable checkpoint6477a8db. Owner selection above is not acceptance of that candidate. K may implement the two selected corrections while coordinator reviews the committed bytes; report any overlap explicitly. Never review an unspecified moving candidate.

Codexpc custody M385019 is accepted by code/evidence review in child review-2026-11-17T19-36-36Z.md;12/12 historical tests. Next assignment: seven remaining historical engine IDs in four test modules, with post-maintenance prerequisite checks and isolated source, as specified in that review. No product/K paths or full suite.

Both streams return to independent review; then remaining pure/B5, joined current-tree verification, clean full-suite accounting and owner closure/check-in gate still apply before W383215.
