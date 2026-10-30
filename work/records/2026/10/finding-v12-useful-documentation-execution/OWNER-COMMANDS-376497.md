# Proposed native non-satisfying disposition — not selected or executed

Only the human owner acts as baton.slaw. These preserve the already reviewed W370560/W371320 request exactly; no new operation identity or changed rationale. Do not infer owner capability from reviewer's pending result.

First revalidate current capability and exact native assignment:

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack disposition pending --authority-store /home/sl/baton-instances/useful-template-job-w366962/db/authority.sqlite3 --authority-uuid 6dcb60dce5cd485b8bf03c24bc4afc82 --work 6dcb60dc-W1 --participant baton.slaw
```

Require holds.close=true, no unexpected close/receipt/proposal change, same authority/Work, active baton.reviewer-w366962 generation2. Guard file must retain56836ce3ba5c484ff2e39e3304d11ed58b6d739f7cde4d416bae2337fab3a1ca:

```sh
sha256sum /home/sl/src/baton/work/records/2026/10/finding-v12-documentation-review-startup-fault/evidence/research-370686/expected-assignment.json
```

If owner selects this non-satisfying disposition and checks match:

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack disposition close --authority-store /home/sl/baton-instances/useful-template-job-w366962/db/authority.sqlite3 --authority-uuid 6dcb60dce5cd485b8bf03c24bc4afc82 --participant baton.slaw --work 6dcb60dc-W1 --operation-id w370560-nonsatisfying-close-370686 --outcome non-satisfying --rationale 'Implementation candidate retained; review assignment faulted under incompatible output declarations; no independent verdict or accepted useful Job outcome. Preserve all evidence and unresolved cleanup.' --expect-assignment /home/sl/src/baton/work/records/2026/10/finding-v12-documentation-review-startup-fault/evidence/research-370686/expected-assignment.json
```

Repeat the pending command afterward. Require recorded non-satisfying ending, ended assignment, preserved proposal and no invented acceptance receipts. On mismatch/refusal/uncertain response preserve output, re-read pending, and reconcile the same operation rather than choosing new identity or dropping the guard. This is authority disposition only, not execution settlement, cleanup, review acceptance, integration, retry or supervisor-stop permission.

Changed-runtime assessment: fresh review inspection finds exact review container absent, not exited/present; recorded expiry reclamation explains earlier absence, but no fresh cleanup settlement is established. The old procedure's positive exited-container preflight is superseded for this assessment. Authority close does not require claiming successful cleanup; owner must explicitly accept preserved unresolved cleanup responsibility. Former supervisor PIDs are absent at current ps; no cause, replacement-process absence or supported stop success inferred. No stop/removal command is selected here. Keep original evidence and all safety preconditions for any later separately selected operational action.
