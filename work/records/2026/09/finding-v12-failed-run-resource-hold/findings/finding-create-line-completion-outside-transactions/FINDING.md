# W301404 — create_line completion outside database transactions

## 2026-09-29T02-18-18Z — owner-selected bounded correction

Created301404 under W257624, reviewer parent claim301403; owner301348/301398/301399. This child isolates the existing create_line DB-1 residual; it does not duplicate or close unrelated parent debt. Binding is this permanent dossier. Parent events read through301403/T257624 through270917; consumer events301399/T257627 through292130.

Confirmed: review_cycles.create_line commits initial reservation and materializes outside the lock, but its completion callback calls _object, workspaces.prove_line_integrity and establish_line_access inside ControlStore.transact. The connected positive Job succeeds despite this violation. Independent consumer review-2026-09-28T22-22-49Z.md and evidence/db1-review299834.json record46 lstat plus1 fchmod with in_transaction=true; author recorded62+1. Counts depend on traversal; zero forbidden external I/O is the invariant. Baseline probe1FAIL0.238s; useful packet1PASS5.730s are separately measured historical evidence, not current child acceptance.

Reproduction: work/records/2026/09/finding-v12-startup-failure-fresh-packet/probe_create_line_299768.py observes real filesystem calls and the disposable fixture connection, exercising TheFreshPacket connected positive. Keep its required zero-I/O assertion. No direct canonical-store access or live engine/provider. Exact source entry: v12/python/src/baton_v12/worker_manager/review_cycles.py:create_line. Existing source inspections and manifests are in consumer candidate299768 and REACHED-DB1-299768.md; revalidate current bytes before edits.

Selected outcome: filesystem inspection and access changes outside all DB transactions, while preserving exclusive preparation, exact object/operand identity, atomic conditional completion, interruption/replay safety and competing/stale completion exclusion. Implementer chooses necessary files and focused commands. Do not remove required integrity checks, publish early, or move checks outside without protecting their lifetime. Use current DESIGN DB-1 and initial-host-preparation lifecycle; no restoration of maintenance containers.

Required evidence: connected no-I/O-under-transaction regression; positive creation and no-effect replay; conflicting operands/object refusal; safe competing and stale completion; interrupted preparation/access effect retains honest recoverable state; unrelated DB progress during paused filesystem work where relevant. Fake/replay providers and disposable stores/processes only. Existing G2/packet/restoration acceptance remains bounded and preserved; no broader audit or historical acceptance transfer to reconstructed bytes.

Ownership: baton.claude via baton.impl implements selected correction and owns child PROGRESS. Reviewer owns FINDING/PLAN and append-only reviews. Before edits implementer records chosen source/test paths and coordinates any actual overlap; owner intentionally delegates necessary file/selector choice. Consumer Tuner keeps its existing four baseline paths; no consumer file takeover. Parent provenance/residue inventories and unknown historical delta remain unchanged.

Graph selection: W257627 must wait on this exact W301404 correction, not all unrelated W257624 debt. After independent acceptance and satisfying disposition, consumer resumes baton.tune for runtime hash rebind, DB-1/useful-packet rerun and final qualification. Parent W257624 returns baton.decide after decomposition and remains open with this child. No live run, build, deployment, Git mutation, broad R3/R4/R5 reopening or final packet acceptance.


## 2026-09-29T02-32-53Z — partial DB-1 correction; exclusive preparation not established

Reviewer301510 independently confirms connected no-I/O passes but root replacement publishes idle before refusal (focused4tests3PASS1FAIL0.232s). New review_late_preparation_301510.py1FAIL0.007s: competitor completes/admit writer after outer early replay, then stale creator performs actual access change while line writing. This explicitly refutes current PROGRESS claim that materializing plus conditional completion protects the external lifetime. Preserve candidate and all partial evidence; routine continuation baton.impl under existing owner authority, not forced A/B waiver selection. Full findings/limits: review-2026-09-29T02-32-53Z.md. Consumer gate remains; no graph/product changes.


## 2026-09-29T02-43-58Z — adjacent read is not effect exclusion; active refusal is allowed

Reviewer301591 four focused casesPASS0.234s, new syscall-boundary probeFAIL0.007s after _settled_elsewhere: admitted competitor/writer followed by stale actual fchmod. This explicitly refutes PROGRESS closure and all-in-process-schedules claim; _PREPARING is unused for exclusion. Prior probe assumed successful competitor to expose defect, not to require unsafe admission; correct active refusal may require revised implementation-owned test, with historical probe preserved. Recovery after interruption differs from concurrent live entry. Root withdrawal exact schedules pass; no whole-child acceptance. Routine impl correction under existing authority, no new scope/owner gate. See review-2026-09-29T02-43-58Z.md.


## 2026-09-29T02-49-10Z — guarded act still has unprotected preparation and handle bypass

Reviewer301624 four retained casesPASS0.234s; new hold-scope2FAIL0.011s confirms materialize before exclusion and second same-process handle bypass. Explicitly narrows author claim that the hold spans external acts: it begins after materialization and is keyed to Python store identity rather than shared resource. Safe refusal remains accepted; whole child not accepted. Existing scope covers correction without owner renewal; review review-2026-09-29T02-49-10Z.md.


## 2026-09-29T02-56-46Z — bounded create_line correction independently accepted

Reviewer301685 verifies owning167 tests plus4 DB-1/hold/boundary checks171PASS1.852s; new real threaded second-handle/independent-line/replay proof1PASS0.008s. Prior preparation-order/handle-identity/race failures explicitly superseded for current digest-bound candidate. Supported single-Host scope and historical probe/exception-death limits preserved. Full review review-2026-09-29T02-56-46Z.md. Accepted delivery to owner; child/parent/consumer graph not closed or altered by review.
