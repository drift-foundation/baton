# Unresolved v12 suite checks

Ledger Work W115824; reviewer claim115826, 2026-09-08.

Owner M115824 requests a complete accounting of the eleven failures and one
error in the W110774 review115739 canonical gate, current causes and existing
owners, exact repair paths and focused verification. Reuse W48697 for inventory
debt. Separate currently leaking containers from old leftovers using read-only
inspection. Enumerate existing-test changes for owner approval.

Authorized: diagnosis, durable evidence, focused verification and repair planning.
Not authorized: implementation/source/test changes, resource deletion or another
whole-suite run. Return the complete disposition to baton.ops before demonstration
advancement. This record will retain observations and the final repair map.

Source evidence:
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-integration-runtime-port/evidence/review-115739/gate.txt`.

## 2026-09-08 — complete reviewer disposition

**Confirmed.** All twelve check identities are accounted for in
`review-2026-09-08T03-46-00Z.md`. Eight focused non-engine checks reproduce the
retained seven failures and one error in 3.516 seconds. The four engine
diagnostics select old resources still present at read-only inspection; none
of the 32 matching containers was created by the September 8 gate. There is
no evidence here of a newly leaking W110774 container. Exited residue still
exists and is not waived by its age.

**Confirmed.** W48697 remains the existing global inventory owner, parked at
baton.ops. The fresh census is 61 missing probes, 11 probes without attributed
owners, 185 entries without attributed owners, 55 orphan validator calls, and
two missed column names. The old counts are history, not acceptance totals.
The writer-key probe fails before adoption; a separate diagnostic proves the
real reader rejects a malformed returned key at the required integrity/schema
boundary. The scanner also demonstrably drops adopted interrogation column
reads in `_view`. Neither observation justifies weakening aggregate assertions
or editing runtime validators to fit a scanner.

**Proposed.** Use the review's exact queue: additive catalog repair under this
Work; scanner/fixture repair and module-local completion under W48697;
separately approved operator disposition of old engine resources. W48697 needs
explicit activation and approval of expanded module coverage, not a duplicate
inventory Work. Its required module children before implementation remain in
force. W39666 is now closed; a surviving worker-entry delta needs a bounded
follow-up, not an assumption that the old Work is still executing.

**Operational observation.** Python's nested Docker subprocess and direct
`docker images --filter reference=baton-w6633-test --no-trunc --format ...`
were denied access to `/var/run/docker.sock`. Standalone `docker ps`,
`docker inspect`, and `docker image inspect` succeeded under installed policy.
No escalation, deletion, stronger command, or daemon mutation was attempted.
No exhaustive image-tag census is claimed; inspection confirms the exact
retained tag and two additional aliases. This is an execution-policy limitation,
not evidence of a Baton protocol defect. No Baton store was opened directly.

Evidence: `evidence/focused.txt`, `inventory.json`, `probe-analysis.json`,
`docker.json`, `hashes.json`, and the two narrow diagnostic scripts beside them.
No source, test, implementation PROGRESS entry, or engine resource was changed.
