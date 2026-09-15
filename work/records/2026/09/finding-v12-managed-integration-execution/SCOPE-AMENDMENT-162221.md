# Remaining migration-fixture adaptation — exact owner selection

Proposed by baton.codex claim162221 after author162181/M162218. This adds to the
already-approved M162156 amendment; it does not replace that approval or grant
implementation authority before the owner responds.

## Exact amendment recommended

Approve migration-fixtures-162221.patch for these two additional existing test
paths, only alongside the approved capacity schema addition:

1. `v12/python/tests/job_manager/test_scheduling.py`: add
   integration_capacity_members and integration_capacity_roots, in that order,
   before the existing table names in exactly two drop tuples:
   PoolDocuments.test_schema_three_migrates_atomically_to_empty_scheduler_relations
   and TheMigrationProvesTheSchemaItMigratesFrom.stamped_as_three.
2. `v12/python/tests/job_manager/test_execution_limits.py`: in
   TheMigrationLeavesOldJobsMeaningExactlyWhatTheyMeant.schema_four only, extend
   the existing DDL exclusion to skip the capacity roots/member tables and their
   capacity_one_active_member unique index, as well as job_execution_limits.

No assertions, expected results, real golden-schema4 fixture, test cases, other
helpers or product paths are changed by this amendment. The attached patch makes
the proposed edits reviewable. These are fixture construction corrections to
keep schema2/3/4 fixtures old when the current schema becomes6. They do not relax
the real migration's object checks. Retain the existing M162156 two-statement
test_store.write_schema_2 amendment and apply all three fixture adaptations with
the schema addition. No fixture edit is applied by this reviewer.

Current base hashes:

| Path under v12/python/tests/job_manager | SHA256 |
| --- | --- |
| test_scheduling.py | 5780dc171e4b791d0488f78b3b531c7d31e04f833878523f2f38bf518b57f0ea |
| test_execution_limits.py | 2271ef93151b5a331008f2a1fcad5974ae3daa539cb6d9696eac56715074f215 |

## Evidence and correction to the earlier audit

My previous amendment correctly located the only drop-based helper IN
test_store.py but did not complete the audit across the Job test suite. Wording
that could imply there were no separate schema3 fixtures is superseded here:
the two in test_scheduling.py are real and need equivalent adaptation. Author
step23 reports five affected cases and the source confirms both tuple sites.
This is reviewer scope-audit incompleteness, not a newly changed policy.

A broader search over Job Manager and integration tests found the additional
schema_four constructor. It includes every current DDL statement except the
old4→5 table. fixture-audit-162221.py exercises that existing helper with synthetic
future capacity table/index names and confirms a fixture labeled4 retaining all
three future objects. This is measured fixture-construction evidence, explicitly
not a test of the reverted candidate capacity migration. The immutable populated
schema4 golden fixture is already genuinely old and must stay unchanged.

The approved exact path set still excludes these two files. That explicit scope
boundary is the reason for owner selection. The amendment is bounded to these
constructors and assertions remain intact. Tests in the blocked W156162 consumer
share this source tree; record these exact fixture edits under W161230 ownership
and carry them in the later consumer handoff rather than resetting its history.

## Implementation and acceptance remain separate

After approval, pin the ruling and return to baton.impl with the findings in
review-2026-09-13T17-06-59Z.md. The reader's last defect is resolved. The preserved
capacity module has substantial identity, admission and ending-evidence gaps;
its14 tests do not complete accepted conditions1/2. Those corrections fit the
original product/new-test scope and do not need additional design authority.
Conditions4/5 and DEPLOYMENT remain unimplemented. Preserve and bind the actual
schema/release-guard candidate on the next handoff; no acceptance is inferred
from author tests for files subsequently reverted.

Run focused affected migration/capacity tests with existing cumulative guards and
pinned final dependencies. Author60.79389204701147/600s, remaining539.2061079529885s;
reviewer2.55111917200702/300s, remaining297.448880827993s. No budget reset/extension,
installation, live runtime/provider, broad suite, later-slice authority, assertion
weakening, candidate sign-off or dependency release. Original M161614/M162156
authority and independent review remain. Approve this exact additional patch or
return the required adjustment; next baton.feat pins the ruling and routes impl.
