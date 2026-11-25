

## 2026-11-25 — owner-selected credential lifecycle correction (baton.codxpc, E386081)

Owner instruction following M386079 selects automatic first initialization only, source-independent restart preserving refresh, explicit recovery for lost credentials, and automatic copying in qualification launchers. Supersedes seed-if-absent and manual per-Job staging prospectively; old packets/evidence remain immutable. Ruling and acceptance are pinned in [RULING-AND-PLAN](evidence/credential-lifecycle-386081/RULING-AND-PLAN.md), prepared before candidate implementation. Candidate/report: [REPORT](evidence/credential-lifecycle-386081/REPORT.md). This selects no real credential access, source, model, build, engine/provider call, native-use qualification or resume implementation.

The first seed now runs during host preparation, under durable initialization intent outside the worker mount. Both host and worker receipts bind the credential path; retained restarts inspect metadata only and never resolve the original source. Missing/corrupt/incomplete state requires explicit recovery, including crash after copy before final receipt. No automatic migration of unmarked seeded homes. Legacy delivered Claude credentials retain their prior behavior. Product lifecycle/helper and successor launcher are synthetic-verified draft bytes, awaiting independent review and coordinated exact import.

Observed human build-context checkpoint: c1727ad68ffa0f5015b07f27202a66be00848143. No protected Git mutation by codxpc. W386048/W386057 remain separate.
