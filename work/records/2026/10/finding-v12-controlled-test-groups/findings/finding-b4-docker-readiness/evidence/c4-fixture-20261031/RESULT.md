# W384944 C4 fixture result — 2026-10-31

Author baton.codxpc / impl, claim E384955, episode384954; allocation M384952,
review-2026-10-31T02-24-00Z.md. Affected logical group: manager-pure.

Bounded delivery-fixture correction is ready for independent review. The complete
module is NOT green: final 83 collected/started, 81 passed, two unchanged
pre-existing failures, zero errors/skips/unaccounted ids. No B4 or joined-tree
acceptance is claimed.

## Candidate and behavior

Only v12/python/tests/manager/test_integration_worker.py changed. WorldCase now
calls integration.runtime.materialize_delivery with the already configured group
from its composed producer world, instead of creating ancestor/leaf namespaces
with ambient modes. The product establishes and checks its own delivery posture;
no product code, mode refusal, expected outcome or assertion was changed.

Reaching the intended paths also exposed silently failed fixture disposal:
published bundles are read-only, and shutil.rmtree(ignore_errors=True) left them
behind. The case now registers each exact root for cleanup, makes only that
case's own directories writable after the test, and removes them without hiding
errors. os.walk does not follow directory symlinks; linked destinations are not
thawed. Registering the root value matters because two existing tests call setUp
repeatedly within subtests. The intermediate version captured self.root, which
removed the last root repeatedly; that error was corrected before transfer.

All existing test bodies/assertions remain unchanged. The 60 cases formerly
blocked during setup now pass, including actual addition/edit/deletion imports,
mode preservation, whole-path validation, read-only-target refusal, and held
endings for unsuccessful or incomplete provider/verification results. The final
ledger names each result; no real model or Docker execution is involved.

Base SHA256: 7f6664dc2e1668660fb517cfdb7a42e686b58666f706a5346c6f7ba81e71b1cd.
Candidate SHA256: f5a443a9437992daaa7971209748c6f1edb0adb8982246216d99256614bb2a50.
Exact retained bytes: test_integration_worker.base.py and
 test_integration_worker.candidate.py; patch: candidate.diff; transfer: candidate.json.

## Verification and limitations

Verified all 1133 files in coordinator snapshot manifest from owner checkpoint
a8cbc9745d1eff51bcfb04d2fe4bb96a5ea3b12d before work. Only the allocated test file
changed in that snapshot. Every run verified all manifested source bytes before
and after, with no drift. Shared-tree original bytes still matched the allocated
base immediately before final same-file transfer; resulting bytes and file mode
were checked. K-owned files were neither copied back nor tested while changing.
Joined current-tree acceptance remains required after K stabilizes.

Command for each run, from snapshot v12:
`just test-one tests.manager.test_integration_worker`.
Prepared Python resolved through the recipe. run-focused.py records the interpreter,
argv, root, collection and source manifests; each run has its own /var/tmp root,
300s execution ceiling and 30s termination allowance. No timeout occurred.

| Run | Collected / started | Passed / failed / errors | Measured command wall seconds | Cleanup |
| --- | --- | --- | --- | --- |
| baseline | 83 / 83 | 21 / 2 / 60 | 13.1775 | Empty root removed |
| owner-delivery | 83 / 83 | 81 / 2 / 0 | 18.4340 | 937 paths left by old silent cleanup |
| final (intermediate cleanup attempt) | 83 / 83 unique | 79 / 2 / 2 unique errored ids, 6 error events | 18.4324 | 370 paths left; mutable-root callback defect |
| corrected-cleanup (actual final candidate) | 83 / 83 | 81 / 2 / 0 | 18.4328 | Empty root removed |

Measured command wall total about68.477s; collection/hash/orchestration time is
separate and not included in that total. unittest body durations appear in logs.
No full-suite or group run was made.

Accounting corrections are explicit: initial baseline summary parsing required
ellipsis on the first line, missing tests whose verbose output prints a docstring.
baseline.ledger.json corrects this from the retained log without rerunning.
The intermediate cleanup failure prints some test names again for cleanup error
events; its summary's duplicate_started=4 is a parser artifact, not repeated test
execution. The retained log says Ran83, with six cleanup error events on two ids.
Final corrected-cleanup ledger has 83 distinct starts and no such ambiguity.
Logs, collection lists, summaries, corrected ledgers and full source hashes are
retained together. Original failed-attempt summaries have not been rewritten.

Intermediate disposable roots remain for exact operator cleanup, not evidence:
- /var/tmp/baton-w384944-c4-owner-delivery-5qnsbglr — intermediate-leftovers.json
- /var/tmp/baton-w384944-c4-final-2n4qnheh — cleanup-attempt-leftovers.json

They contain this task's test fixtures, no containers or live executions. No broad
resource deletion was attempted. Durable evidence is here, not in those roots.
Future runs now clean their own exact roots successfully; historical leftover
cleanup can be selected separately without changing the candidate or test outcome.

## Two remaining failures, outside the released delivery-mode repair

1. EveryIntegrationRefusalSAYSWHY.test_a_generation_this_runtime_cannot_read_SAYS_SO
   constructs schema baton.worker-launch/5 in the legacy flat shape. The current
   reader recognizes /5 as an envelope and refuses missing payload/wire_profile,
   so the diagnostic does not name the purported unsupported generation. Fixture
   at test_integration_worker.py:1641ff (line shifts in candidate). Required follow-up:
   exercise an actually unsupported generation/shape without weakening diagnostic
   coverage. No worker launch reader change is justified by this fixture alone.
2. TheWrapperTakesTheAdaptersOwnProviderTurn.test_a_clean_turn_answers_the_closed_document
   at line118 expects four keys; the provider wrapper additionally returns
   seconds_bound and seconds_bound_source. Required follow-up: validate the accepted
   timeout-result contract and its values, preserving the closed-member assertion.
   Do not simply discard these keys or accept arbitrary output.

Both fail identically before and after this correction. Neither prevents the 60
C4 cases from reaching their intended result. They were deliberately not folded
into the explicitly released delivery-fixture-only milestone. Coordinator can
allocate that same-file follow-up routinely; no specification decision is asserted.

Handoff to baton.decide for independent assessment of exact candidate and bounded
result. Parent Stage C/B4/B5/final-accounting and owner Git checkpoint gates remain.
