# W361910 — resolver contract correction

Candidate361943 manifest834e88af1eb98106adbfe4799baac83de1b31d56a8f84502d93dd455c85a7277
is not accepted. Latest review: review-2026-10-26T17-46-15Z.md.

Next milestone: correct R1 stable resolved limits/consumer boundary, R2 mutable
public template lookup and R3 separation of selected work scope from test scope.
Keep manager admission/CLI implementation in W361912; the resolver must supply
an honest usable contract to it. See review for outcome-based verification.
137 focused checks pass; counterexample evidence is evidence/review-362222/.

Implementer owns new isolated candidate, tests and attributable PROGRESS. Reviewer
owns FINDING/PLAN/reviews and independent evidence. Choose necessary files within
accepted scope; coordinate actual overlap and preserve canonical dirty files.
Complete corrections and focused deterministic verification, then return exact
candidate/base/path hashes and evidence to baton.bug. No live provider/engine,
deployment, migration, Git mutation or additional permission round.

W361912 stays gated; W321608 retains joined acceptance. One coupled resolver
milestone needs no further split. Human checkpoint follows independently accepted
product delivery: feat(v12): resolve versioned Job templates. Earlier planning
checkpoint remains pending unless separately observed. Prior plan preserved in
PLAN-HISTORY-362222.md. Read events362222/full handoff362220 and thread361910;
no new discussion at snapshot362232. Reviewer claim362222.
