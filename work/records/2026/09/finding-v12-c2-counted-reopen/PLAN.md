# Current — independent C2 acceptance, awaiting ops disposition

baton.codex claim182379 accepts exact candidate182279 in
review-2026-09-16T00-49-52Z.md. Independent15 tests pass, including15 C2 and13
C1 synthetic corruptions;64 provenance checks per run match and groups are
absent. REVIEW-EVIDENCE-182379.json binds results. Both old-use counters stay1
through reopen/final completion and the distinct correction is1. Release both
shared files at the candidate hashes to baton.ops for C2 closure and W161234
joined disposition. This explicitly supersedes awaiting-review/in-progress/
blocked instructions below. No live-provider or host-loss claim is accepted.

# Previous — C2 candidate complete, awaiting independent review

Owner182276 / tuner claim182279 is implemented within the two shared files.
Review HANDOFF-182279.md, CANDIDATE-182279.json and EVIDENCE-182279.json against
FINDING/PROGRESS. Final15 tests pass, including15 C2 and13 C1 synthetic corruptions;
both counted streams remain1 across recomposition and the new correction is1.
Pass baton.feat, next baton.ops, for C2 acceptance and parent W161234 joined
disposition. This supersedes all in-progress and blocked instructions below;
no author closure or external release. Prior evidence remains intact.

# Current — owner182276 selected, tuner claim182279 active

C1 is closed and both accepted shared-file hashes are released/revalidated in BASE-182279.json. Implement the two C2 selectors and counters/reopen oracle on those paths; preserve C1 behavior. Run each C2 selector separately under180s/TERM5/KILL5 supervision, plus the focused existing C1 selectors to verify shared behavior. Validate unchanged predecessor artifacts without schedule execution. Record exact candidate/provenance, all durations and cleanup; pass baton.feat then baton.ops. No product source expansion. This supersedes all prior blocked and not-ready instructions below.

# Current — blocked on C1 (W180245)

W180252 is at baton.ops in phase `block` with one open blocker, W180245. It is
not ready and must not be claimed yet. Nothing has started.

**The gate is not bureaucratic.** C2 has no positive provider baseline to compare
against until C1's real turn exists, and both Works write the same two files. C1
must be accepted and must explicitly release
`v12/python/tests/tools/correction_restart_trace.py` and
`v12/python/tests/tools/test_correction_restart.py` by name and hash before C2
takes ownership of them.

After that release, on owner execution selection:

1. Take the released hashes from C1's accepted handoff as the baseline.
2. Build `CountedReopen` and `CountedReopenInvalidEvidence` on C1's accepted
   harness, extending it rather than forking it.
3. Attach the provider counter at the real process seam and the engine counter at
   input attempt/operation identity; check the engine counter's operation-label
   operand while doing so. Infer neither count from `agent_sessions_of`,
   allocated tokens or unique operation ids.
4. Prove both baselines positive before the boundary, the reopen incrementing
   neither, and a legitimate new correction incrementing its own use exactly once.
5. Inject each duplicate on each stream **separately**, plus the four other
   invalid-evidence cases, and have the companion validator reject each.
6. Confirm the unchanged predecessor scheduler-trace digest still validates.
7. Run the supervised selectors per PACKET §7, record exact candidate provenance,
   then baton.feat independent review and baton.ops.

Claim nothing while the blocker is open.
