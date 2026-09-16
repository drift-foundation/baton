## 2026-09-15 — owner defers reported pre-existing suite failures until post-v12

After W61599 implementation handoff178359, Slawomir directed: "the so called 'preexisting' failures need to be addressed in post-v12 era, where we have speedy access to parallel work. I don't want to burn time on them now".

Record the baseline failure backlog under W165786 for bounded parallel work after v12 readiness. W61599's ACTIVITY-IMPLEMENTATION-177898.md reports baseline7259 tests/89 failures-errors and candidate7333 tests/88 failures-errors, with the remaining set reported unchanged from baseline. These are author-reported classifications, not an independent certification or a green suite. Preserve the existing results, failure identifiers/log locators where already available, and the exact baseline/candidate context. Do not spend current release time repairing those baseline failures, reconstructing broad suite history, or repeating full suites merely to investigate them.

The active W61599 reviewer should use existing evidence and focused checks of the changed behavior and any concrete suspected introduced regression. Candidate acceptance does not require fixing unrelated baseline failures. Report a concretely demonstrated defect in selected v12 execution separately; do not call a new regression pre-existing to waive it, or use speculative classification concerns to launch a baseline cleanup campaign. This ruling narrows current verification/repair scope, not truthful result reporting or independent acceptance.

After readiness, W165786 will decompose surviving failures into small Jobs with explicit file ownership, prioritization and acceptance, reusing v12 parallel execution. Reuse existing defect Works when identified; no new implementation/backlog copies or release-gate edges are created now. The downstream consumer must revalidate the surviving failures then rather than treating this snapshot as current indefinitely.

Evidence: baton:work/records/2026/09/finding-live-worker-log-observability/ACTIVITY-IMPLEMENTATION-177898.md, section8; PROGRESS.md claim177898; W61599 pass178359. This explicit post-v12 repair selection supersedes any interpretation that the baseline suite must be made green before W61599/W2 can proceed. W161234 and the already-selected required v12 outcomes remain independently accountable.

