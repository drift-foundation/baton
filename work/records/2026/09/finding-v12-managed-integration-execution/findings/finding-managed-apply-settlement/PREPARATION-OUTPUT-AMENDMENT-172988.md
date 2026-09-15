# Exact preparation-output amendment requested — W170385 claim172988

**Proposed, not selected.** Preserve W170385 and its partial candidate. This is a
concrete missing producer boundary discovered in the selected materializer/
judgment composition, not a request for an expanded v13 coverage campaign.

## Measured blocker

`test_managed_apply.ThePreparationHandoffNeedsItsGitObjects.test_the_current_output_omits_the_derived_commit_and_executable_mode`
runs the real preparation producer and PreparationAgent against disposable Git
history with one executable file. Supervised runs04/05 establish:

- The derived commit exists only in the preparation scratch object store. Its
  tree records `tool.sh` as100755.
- Declared output contains candidate file bytes and report/report.json only,
  with no object bundle or .git. The emitted tool.sh has no execute bit.
- The sealed report's content measurement contains path/digest/length only.
  Its derived_candidate includes revision/tree/source IDs, but no exact commit
  object bytes or Git tree inventory carrying modes.
- A new repository importing the ordinary input objects.bundle cannot resolve
  the reported derived commit. That bundle was produced before the merge.

The current `_copy_tree` explicitly excludes .git and chmods copied files0600.
The generic custody layer cannot retain objects the workload never declared.
Once scratch is gone, the selected target materializer cannot import the exact
reported derived commit/tree from this handoff. Inventing a replacement commit,
recovering private scratch or recomputing a coordinator merge would change the
selected identity/custody/execution boundary. No such workaround was attempted.
This does not revoke group2's reduced-scope acceptance; it is a missing group3
producer input exposed when consuming its retained artifact.

## Minimal requested scope

Add two preparation source paths to the selected fifteen-source upper bound:

| Additional source | Bounded change |
| --- | --- |
| v12/worker/reconciliation_task.py | Export the exact derived Git commit/tree and reachable object closure from the existing private preparation object store into a portable bundle; preserve executable modes in the Git tree and verify the emitted candidate bytes against that tree. No new merge or harness run. |
| v12/worker/reconciliation_entry.py | Emit that bundle as a separate ordinary declared `prepared-objects` output, alongside existing candidate/report outputs. Report its exact derived identity without replacing ordinary worker measurement/collection. |

The source objects remain in the worker until ordinary output measurement;
manager-side adoption uses accepted intake/retained custody, not a path into
scratch. The actual selected stage/bundle/reconciliation owners can declare and
adopt the extra artifact within their existing scope, keeping collection digest,
object-bundle artifact digest, candidate content and commit/tree IDs distinct.
All four must bind the same preparation/result before derived publication and
judgment. The judgment/apply materializer verifies the retained bundle and exact
revision/tree; executable permissions come from its Git tree, not custody modes.
Untrusted or mismatching output refuses, never repairs itself by a host merge.

No schema/migration/Authority/generic Worker Manager/OCI/scheduler/image change
is requested. The two files are already copied by the existing preparation
recipe; no image build or certification is selected. Tests remain inside the
already selected test_managed_apply.py and test_managed_preparation.py. Replace
the explicitly labelled blocker observation with positive exact-object/mode
retention/adoption evidence after amendment; retain the observed pre-fix log.
Standing test authority applies, with no separate test approval request.

Focused validation: one real producer/worker exact-object/mode export, ordinary
retained adoption after execution roots disappear, then resume the originally
selected ordinary preparation→independent judgments→apply→target transaction→
final settlement path and its existing bounded acceptance. No Cartesian failure,
partial-delivery protocol or shutdown campaign is added.

## Partial work preserved

The selected Git profile now offers atomic target-ref CAS plus receipt-ref
creation in one transaction, and exact receipt reading. The local target owner
binds publication, configured repository/ref, result/phase accounts, execution,
authorization and entry/grant to that receipt, rechecks the grant after receipt
object work, and recovers through the receipt. The production Git runner accepts
optional stdin for this transaction. These changes are not yet wired into the
ordinary managed Job flow.

Seven component tests cover atomic publication, stale target, receipt collision,
late grant check, lost-reply receipt recovery and composition with the existing
placement interface. Placement composition uses actual local target receipts;
its surrounding materializer/authorization/exclusion remain labelled fixtures.
One further test records the missing preparation handoff described above.
Final run05:71 tests pass (8 new module +63 existing placement tests),2.182261254s.
This is partial component evidence, not complete managed apply acceptance.

Resume after recorded amendment at the preparation export/adoption boundary,
then parent continuation and managed lifecycle/proposal/judgment/apply/final
outcome composition. Do not seek independent acceptance of only these helpers.
Return the complete later candidate to baton.feat with set-next=baton.feat as
owner selection172982 requires. Group4/parent/dependent gates stay closed.

Additional-path current baseline:

- `baton:v12/worker/reconciliation_task.py` SHA256 `69860bdfdc63e5144db973ddd70c7b101bde707ba97c8c99779b3ae6ce992eb6`.
- `baton:v12/worker/reconciliation_entry.py` SHA256 `5b9abe961c1551b2754c173611f5b3d1815dee32e7bf0881630e0ec4b05f7075`.
