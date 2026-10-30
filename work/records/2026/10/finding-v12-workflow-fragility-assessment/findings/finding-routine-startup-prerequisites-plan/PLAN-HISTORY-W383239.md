# Current milestone — deliver approved ordinary startup behavior

Owner E375491 approves JOINED-PROPOSAL eec22c06… with fresh-schema/no-migration/no-backward-compatibility amendment. FINDING pins exact ruling and supersession; DESIGN SCH-1a/OBS-0a now includes selected behavior. This supersedes pending-owner/planning-only next-action text; original proposal/reviews remain unchanged evidence.

| Work | Executable outcome | Route and required accepted inputs |
| --- | --- | --- |
| W375516 | Installer prerequisites, control-store initialization, read-only validation | baton.impl; ready, normal queue behind active work |
| W375517 | Shared direct/queue admission, immutable snapshot, retirement/recovery | baton.codx; W371295 role provenance/schema and W375516 installer |
| W375518 | Serving/create/wait/status/retire and instance observation | baton.codx; W375517 core and W375445 shared command-file ownership |
| W375519 | Joined installed startup/recovery and honest whole-path timing | baton.codx; W375516 and W375518 |

Child dossiers under baton:work/records/2026/10/ are finding-v12-startup-prerequisites, finding-v12-shared-creation-admission, finding-v12-serving-creation-commands and finding-v12-ordinary-startup-proof. Their FINDING/PLAN fix bounded scope/ownership and acceptance; product authors choose necessary files, coordinate actual overlap, record tests and exact candidate provenance. W371073 installer compatibility is not yet selected; coordinate if selected later. W371295 owns its Job schema first; queue uses the accepted version afterwards, no competing version meaning. Settlement W375445 first owns shared CLI/single_worker changes; source-serialization edge is documented, not a semantic startup dependency.

W371075 remains open, waiting on W375519 and retaining all children through integrated independent acceptance. W371076 remains dependent as originally recorded; W370747 rolls up broader workflow outcomes. Routine corrections pass directly to implementation. No additional owner approval for selected behavior; no live provider/engine, operational install/deployment, retained-store mutation or Git action authorized. Fresh temporary packaged fixtures and deterministic tests are authorized.

Checkpoint: E375494, owner handoff375491, thread through371453 (no newer message on resumed read), graph edges read back375547; evidence/allocation-375494/CHECKS.json. No product tests this allocation; prior evidence retained and historical wall total unknown. Reviewer owns parent decision/plan/review/evidence and the narrow selected DESIGN amendment; original PROGRESS/proposals/reviews preserved. Human checkpoint due: `docs: select and allocate ordinary startup delivery`; no commit observed.
