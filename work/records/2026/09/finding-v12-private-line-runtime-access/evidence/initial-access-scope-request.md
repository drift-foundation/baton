# Exact additional guard scope for review and owner disposition

W106896, claim 106921. The authorized eight-path candidate is prepared and
preserved with pre-edit bytes, incremental patch and SHA-256 manifest. No guard
listed below has been edited. The accepted PLAN requires returning additional
existing-test paths and expected-behavior changes for scope review.

## Requested additions

1. v12/python/tests/tools/test_parallel_runner.py:
   In TheRealRegistryDescribesTheRealTree.test_the_serial_modules_are_the_ones_that_own_an_engine,
   append exactly tests.manager.test_private_line_access_engine to the expected
   SERIAL_MODULES tuple. Preserve its existing members/order, exact equality,
   and disjointness assertions. This is the expected-list counterpart of the
   already authorized production test-registry addition, not a weaker assertion.

2. v12/python/tests/manager/test_boundary_inventory.py:
   Add precise ownership and executable witness coverage for the two new caller
   entries (workspaces.py:AllocatedRoots.__init__, _line) and
   (workspaces.py:AllocatedRoots.__init__, _line_proof). The constructor's mint
   gate owns internal metadata; the marker selects policy but cannot authorize
   a host path. The lifecycle proof resolves current assignment and durable roots
   at launch. Associate the capability validation at workspaces.py:_granted_roots
   with the exact line-proof crossing, label "a development-line launch proof".
   Use the existing ownership/delegation and witness machinery; preserve all
   discovery, orphan, completeness and witness assertions. Do not add a wildcard
   exclusion, exclude the constructor or silently mark the crossing unowned.
   Witnesses must cover refusal without the manager mint and copied/cross-wired
   metadata failing the durable path/assignment proof. Exact table/witness bytes
   require independent review under the owner's additional path authority.

No new production path or behavior is requested. No repair of the wider baseline
inventory or unrelated registry omissions is included in this request.

## Evidence separating this change from the current tree

The 251-test focused source sweep passes with one explicitly disabled live
engine test. The extra 132-test dependency/source-boundary/registry sweep reports
one failure and one error (three existing skips): the expected serial tuple is
missing our one new member; completeness also names two pre-existing unregistered
modules, tests.integration.test_driver and tests.job_manager.test_review_driver.

The 12 boundary-ownership checks report three failures. The read-only comparative
AST probe holds all other current source/guard bytes fixed and replaces only the
three scoped production modules with saved pre-edit bytes. It finds baseline
172 unowned entries/55 orphan calls versus candidate 174/56; the exact added set
is only the two constructor inputs and one capability label above. Existing
column-tracking failure names operation_id and settled_at. No removal was found.

This comparison is a local differential, not a claim that the entire current
working tree or baseline is signed off. Full logs, the reproducible comparative
script and JSON output are retained alongside this request.

## Disposition

Independently review the eight-path candidate and this bounded two-test-path
request, then return to the owner for exact scope disposition. W106896 is not
ready to close while its required guard additions remain unauthorized/unverified.
The custody provider must continue to wait for the independently accepted initial
checkpoint; the overall runtime/correction proof remains with W105706.
