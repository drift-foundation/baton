# Exact slice1 migration-fixture amendment — owner decision requested

Prepared and independently assessed by baton.codex, claim161844, responding to
author161797/M161835/return161842. This is a proposal, not new authority.

## Decision requested

Amend owner M161614's SLICE1-SCOPE-161491.md selection by adding exactly one
existing test path, `v12/python/tests/job_manager/test_store.py`, for the two
fixture statements in `migration-fixture-amendment-161844.patch`. Apply them only
alongside the approved capacity schema addition, before the fixture drops its
other later-version tables. No test assertions, expected results, test method
removal, shared helper redesign, other path or allowance change is requested.

The exact target is
`MigratingPinsTheAuthorityWithoutRenamingAnything.write_schema_2`, currently
line699. Its current SHA256 is
`d6c9e17b5f5c5afb7f0be820533fda8e469f6b4eb566d59d524dbaeef2fc035b`.
The patch adds DROP TABLE integration_capacity_members followed by
DROP TABLE integration_capacity_roots before the existing drop sequence.
The partial index drops with its member table. These affect only temporary
fixture databases created by the test, not production or coordination stores.

**Precision correction to the author request:** there is one such drop-based
fixture in this file. No separate adjacent schema3 impersonation requires an
edit. write_schema_1 builds its frozen SCHEMA_1 directly and needs no change.
The transition through schema3 is the migration reader's subsequent behavior,
not a second fixture location. Approval should bind the one helper above.

## Why it is needed and what remains preserved

The fixture creates a current-version store, removes every later object, then
labels it schema2 and removes the Authority binding. With new capacity tables
left behind, it is no longer a schema2 fixture. The real migration correctly
refuses unexpected tables/index while deriving schema3's expected object set.
Author run-161638-step-15.log records six affected cases; their stack traces and
the fixture source establish the reason. The schema was subsequently reverted
and its fresh hash matches the prior W156162 candidate:
`3f2afdb4f302cc929eb47aa5e73e4547d56ebaa8d69669f73df97dedde1fc452`.
No reviewed capacity implementation bytes are being approved by this packet.

The proposed fixture adjustment preserves actual migration coverage: old identity
and receipt preservation, Authority binding, failure rollback, foreign-store
refusal and strict old-shape checking. It removes schema6-only objects from a
fixture representing schema2; it does not relax acceptance of malformed stores.
Keep the migration schema parser's CREATE-first convention when reintroducing
the schema. The author's leading-comment and insertion-location errors are
implementation-construction evidence, not a reason to weaken migration checks.

The approved packet explicitly names four new test paths and says a needed old
test modification requires its exact bounded plan amendment. M161614 selected
that exact path set. This concrete added fixture path is why the managed Work
returns to baton.decide; no interactive permission or blanket test authority is
requested. The reviewer has not applied the proposed patch to product tests.

## Remaining implementation and verification

After approval, pin the amendment in FINDING/PLAN and return to baton.impl,
next baton.feat. Complete the already-approved slice1 conditions1/2/4/5 and
DEPLOYMENT, plus the remaining closed-fence-entry correction in
review-2026-09-13T16-00-12Z.md. Existing source/new-test ownership is unchanged.
Revalidate the target before editing; if unrelated changes overlap this exact
helper, return that difference rather than replacing them. Retain the proposed
patch as decision evidence; resulting implementation still needs independent
review and exact candidate provenance before integration.

Run the focused migration module and approved capacity tests with final pinned
dependencies and existing cumulative guards. No fresh budget: author
58.71567680201406/600s (541.2843231979859s left), reviewer
1.8098568630084628/300s (298.19014313699154s left). The current deterministic
defect checks used Python3.13.7/jsonschema4.19.2 and remain qualified until
pinned4.26.0 final checks. No installation, broad suite, runtime/provider launch,
later-slice authority, acceptance waiver or predecessor transfer is added.

Approve this exact single-helper/two-statement amendment, or return the requested
adjustment. W156162/W161234 remain blocked on complete managed integration;
neither this amendment nor condition3 alone releases them.
