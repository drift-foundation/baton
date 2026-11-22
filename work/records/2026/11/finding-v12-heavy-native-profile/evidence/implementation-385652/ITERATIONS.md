# Verification iterations

Preparation-only path mistake: first append targeted a root-relative path while cwd was the isolated python directory, so no test code was written. A subsequent loader invocation could not find TheHeavyNativeProfile; zero intended cases ran. No product defect inferred.

First real new-class run: 7 tests in0.300s (tool wall0.350s),6 passed and1 failed,0 errors/skips. Failure was reused test_the_original_deadlines_are_PRESERVED_by_a_continuation asserting the old literal native-handoff/1 while intentionally running the heavy profile. Added the explicit heavy-profile assertion and retained the same job-origin/deadline/continuation expectations. Existing test bytes unchanged; no product correction needed. Console failure was not captured to a file at the time; this exact diagnosis/accounting is preserved rather than pretending it was a passing run.

Final focused run: focused.log and run.json.85 tests passed,0 failures/errors/skips. Includes7 new cases and existing control, command, worker-bound and continuation coverage. New cases contain subtests; do not count them as extra independent tests. No full suite, build, package test, live provider or Docker campaign.
