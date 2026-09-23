# Owner changes v12 delivery target — 2026-09-23

Slawomir confirms: "yes we need reuse (changed target) because it shows that
work progresses too slowly". The selected target is independent parallel
development Jobs with context reuse, followed by v13 refactoring, consolidation,
robustness and hardening.

This supersedes the optional-production-reuse minimum-release classification
in OWNER-FRESH-ATTEMPT-RECOVERY-20260916.md and older plan text treating reuse
as nonblocking. It extends the September 22 adoption sequencing into an explicit
delivery requirement. Accepted fresh-attempt recovery and historical readiness
evidence remain valid for their original scope; they do not establish this
expanded target. Preserve Work identities and all earlier evidence.

Current bounded sequence: W239528's accepted implementation baseline, W239533's
separate independent reviewer proof, then W236087's resume/correction proof.
Use these results to establish the selected independent parallel development
workflow with working reuse. Isolated proofs alone must not be called production
readiness; identify any concrete remaining wiring gap without inventing a broad
qualification campaign. No particular historical Work is reopened by this ruling.

Do not pause delivery for a broad supervisor refactor or consolidate historical
harnesses now. Necessary fixes to execution correctness, isolation, cancellation,
cleanup, attribution and honest result collection remain v12 requirements.
Broader refactoring and hardening belong to v13. Human-plus-agent integration
remains the default; automated integration is not restored as a release gate.

This decision changes the target, not live-run budgets, active claims or route
authority. Existing bounded execution selection and independent acceptance remain
applicable. No new live execution or deployment change is performed by this record.


## 2026-09-23 — later owner clarification: adopt v12 before reuse completes

Slawomir confirms initial v12 adoption may proceed before reuse is complete,
with reuse among the first Jobs performed using v12. Context reuse remains a
v12 deliverable before moving to v13; it is not an initial-adoption gate.

This explicitly supersedes the September 22 wait-for-restoration adoption gate
in OWNER-SERIOUS-WORK-GATE-20260922.md and the earlier September 23 wording
in this record insofar as it makes reuse block initial adoption. Preserve both
original decisions as history. Fresh-context independent parallel Jobs may be
selected once their own execution prerequisites are satisfied. This is not a
claim that parallel readiness has already been proved.

Continue existing bounded review/reuse Work; do not silently remove dependencies
or interrupt claims. Select reuse as an early v12 Job through an explicit
handoff once the execution surface is ready. No specific live run or deployment
change is authorized here. Broad refactoring/consolidation stays in v13.


## 2026-09-23 — owner confirms adoption path and execution evidence

Owner confirms: finish W239533 independent-review proof, then verify the
concrete independent parallel-Job setup and begin bounded development in v12
on fresh contexts. Reuse is among the first v12 Jobs, not an adoption gate.
Keep delivery on target; no broad supervisor refactor before adoption.

Readiness is demonstrated by the actual operator command through the real
manager, coordination, runtime and result/cleanup path. Focused deterministic
provider-boundary coverage prepares and diagnoses that path; test counts or
passing helpers do not establish end-to-end readiness. Use accepted evidence
and target concrete remaining gaps instead of growing broad suites. Keep
necessary failure, interruption, isolation and false-success coverage; do not
remove genuine defect coverage to accelerate signoff. Live provider execution
remains selected for a specific provider question, not every test iteration.

For W239533 the evidence must connect the accepted producer proposal to a
distinct reviewer, a valid attributed verdict, stopped execution and positive
cleanup, with no unintended implementation/correction admission. Then verify
the concrete parallel setup using separate Jobs with correctly isolated and
attributed results. Report exactly what each execution proves and what remains.
No new live invocation, claim change or dependency mutation is performed here.
