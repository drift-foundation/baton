# Per-Job task delivery prerequisite

Work W363066, created E363066 and routed to baton.impl. Parent dependency is
installed before parent execution can resume.
Current review: review-2026-10-26T20-10-02Z.md. Candidate363069 is partial, not accepted.
104 focused cases pass; actual input/context delivery is the remaining blocker.
Continue through the known owning seam; no renewed owner approval is needed.

One milestone: requested Job task reaches the owning stage/context boundary with
validated matching inputs on a reused worker pool. Read FINDING and parent R3.

1. Revalidate the existing task composition, manifest/input identity, selector and
   workspace/context boundaries against DESIGN; choose a bounded internal seam.
2. Implement and run focused deterministic positive, mismatch, two-Job isolation
   and restart verification. No operator-authored packets or digest-check bypass.
3. Return immutable candidate/base/inherited-overlay digests, actual paths and
   measured evidence to baton.bug for independent review. Preserve parent candidates.

Parent W361912 stays gated and performs joined creation acceptance after delivery.
No owner decision is pending merely for selecting storage or necessary code paths.

Current review supersession: review-2026-10-26T20-28-59Z.md. Candidate363241 is changes-requested.
Priority: consistent per-stage manifest across _matches, attempt record, assignment,
input publication/proof, launch/context and adapter. Drive connected preparation
with fake boundary providers/engine; do not stop at direct task-file helper tests.
147 focused tests pass but independent probe fails actual match and input pairing.

Current review supersession: review-2026-10-26T20-45-45Z.md. Candidate363375 corrects prior
match/input-pair counterexamples; 130 focused cases pass. Remaining milestone is
consistent adapter identity for recovery callers lacking stage, and verification
through actual runtime preparation/recovery entrypoints with fake boundaries.
Root-derived identity must remain bound to durable attempt/assignment provenance.
Do not transfer this child restart requirement to the parent or add an owner gate.

Current review supersession: review-2026-10-26T21-26-14Z.md. Candidate363492 recovery code
passes 137 focused cases. Finish original finite acceptance: two Jobs through one
loop, actual review-role delivery, crash/restart adoption. Establish genuinely
self-consistent substituted-root refusal against durable attempt and correct old
coverage claims. Preserve mismatch coverage. No broad rerun needed solely because
of handoff; complete these scenarios and fix any concrete failures they expose.

Current review supersession: review-2026-10-26T21-47-24Z.md. Candidate363763 adds verified
whole-pair refusal and six named crash/restart proofs; 150 focused cases pass.
Remaining: supported pool delivers two distinct Jobs, and review runtime consumes
requested task with upstream checkpoint. Use deterministic non-Git-mutating seams;
bootstrap second-Job waiting is not delivery evidence. Preserve earlier proofs.

Current review supersession: review-2026-10-26T22-08-43Z.md. 158 cases pass. Continue from
independently composed real pool with checkpoint_profile injection and matching
document name (evidence/review-364036/pool_profile_probe.py). Two-Job serving and
review runtime remain pending; mounts alone do not fulfill them. No new broad suite
or lower-level helper-only completion handoff. Preserve all accepted partial evidence.

Current review supersession: review-2026-10-26T22-34-25Z.md. 165 focused passes; /1 pool
task guard corrected. Two-Job runtime proof independently succeeds with existing
_ConcurrentEngine (evidence/review-364216/concurrent_probe.py). Incorporate durable
concurrent success regression and finish the single review-runtime scenario through
serving loop. No missing-engine owner gate. Prior proof remains valid.

Current review supersession: review-2026-10-26T22-48-40Z.md. Concurrent regression satisfied;
166 focused passes. Finish review-runtime proof by matching upstream deterministic
output/publication fixture contract, using labelled synthetic boundary inputs as
needed. Existing authority covers bounded fixture/seam changes; no Git permission
gate. Real review claim/activation/preparation/launch and attribution remain required.

Current review supersession: review-2026-10-26T23-06-29Z.md. Bounded child acceptance satisfied
by candidate-364329 (169 focused passes). Await owner disposition via baton.decide;
W361912 remains the joined acceptance consumer. This supersedes prior pending
review-runtime instructions above, not parent acceptance or integration gates.
