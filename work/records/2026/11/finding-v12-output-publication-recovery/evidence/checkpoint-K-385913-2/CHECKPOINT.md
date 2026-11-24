# W385695 — internal checkpoint 2 under COMPLETION-PLAN-385909, with one design decision

**This is a recoverable progress checkpoint, not the complete candidate.** The connected path now runs from the installed commands and a real pooled producer through publication, custody and hand-off, with the ordinary reviewer admitted. It stops before the reviewer runs, on the decision in section 3.
Author: baton.prompt (K), owner-selected interactive continuation (M385913), no claim.
No host import, protected Git mutation, image build, engine or container operation, live call or credential read.

## 1. Identity

| | |
| --- | --- |
| Base | `6079ad78345aa87b7148db302d48fb9b1867f940` |
| Previous checkpoint (preserved) | manifest `485488c05e311c40bb058e308aa3a6059940c6d3e2effd2691792bbb8b404620`, `evidence/checkpoint-K-385911-1/` |
| Last reviewed candidate (preserved) | manifest `69b9328cfa8104dadb818af9d186818b6c70a9d5328e2a1bea06cc5650bebe75`, `evidence/continuation-K-385904/` |
| This checkpoint | `candidate-manifest.json` here; sha256 in `packet.sha256` and in the Baton message |
| Scratch repository | `work/scratch/w385695-K-385897/repo`, head `b5abcd8adc9f672e3addaa49df40d2978ca04534` |

`delta.patch` is over the last reviewed candidate `69b9328c`, so a reviewer has one delta to read; `delta-from-checkpoint-1.patch` is over checkpoint 1.

## 2. What is done since checkpoint 1

### Option A (M385913) — the declared base from the line's recorded source

- The host owner's answer for a line-layout original now names the line's own recorded source repository, its persisted `device:inode`, the base the line was declared on, and whether the object there is still the recorded one.
- The Git-aware port imports the base from that source **only** when: the owner reported it verified; the object's identity is proved again immediately before use; it is a real directory and not a link; the requested base is one full object name; and it equals the line's declared base. Then it imports the candidate from the retained bundle.
- No fallback: no branch tip, no caller path, no producer-writable line home. A missing, replaced, linked or mismatched source holds the inspection.
- An attempt-layout original has no line record and keeps the bundle-only read unchanged.

Proved with the real Git consumer in the connected cases, positive and negative.

### The connected path, through the installed commands

`TheConnectedRecoveryFromARealPooledProducer`. Nothing on the positive path is fixture-written:

1. The publisher is composed by the installer's own `pool.composed` and installed by the bootstrap repeat. The fixture then points its three state roots at the fixture pool's, because one instance has one workspace root.
2. The Job is created by the installed `create` command.
3. The pool's own implementation worker runs the real adapter with real version control; its candidate overflows the declared ceiling; the ordinary worker refuses it.
4. The failed attempt is ended by the composition's supported fourth ending.
5. Installed `publication-inspect`, default ports: **eligible, no holds**. The real Git consumer corresponds candidate, base and path set.
6. Installed `publication-decide --approve`: decision recorded and the recovery **admitted**, with `review` servable by the pool's ordinary reviewer.
7. A restarted manager serves the amended configuration; the installed publisher adopts the original; custody and hand-off follow; the gate opens.
8. The published proposal is the producer's own four files at the declared path, byte for byte; zero provider and verifier invocations; one implementation container ever; the original Job row and output unchanged.
9. Installed `publication-status` reports original, recovery, custody and gate separately.

The doubles are the engine and the provider, at their normal boundaries.

### Ordinary reviewer servability — the typed publication edge

- The recovery Job is now submitted under the **original Job's** input identity. That is what the Work's ordinarily configured reviewer serves, so no reviewer is reconfigured and no declaration is copied into the review lane.
- The **publication stage** is held to its own identity (the installed publisher's declarations bound to this recovery's Work and original task), recorded on the reservation and read through one rule, `publication_recovery.stage_job`, by the scheduler's offer binding, the deployment selector and the publication capacity.
- No comparison is relaxed. The publication identity selects no reviewer, and the Job's identity selects no publisher; both are asserted.

This reverses one sentence of accepted checkpoint-1 code ("the input digest is NOT carried forward"). That sentence stays true of the publication stage. I read contract section 5 ("the /4 binding adds exact recovery input and publication worker/profile") as supporting the split; flagged for review.

### Other corrections found on the way

- **Pooled cancellation could not reach a publication runtime.** The pooled manager routes a stop to the allocated worker's `cancel_attempt`, and the publication capacity did not define one. It now routes `cancel_attempt` and `fence_unstarted_attempt` to the operands the attempt was started under. Covered in the pooled composition.
- **A deployment with a publisher is the multi-Job document.** With one Job and one worker per role, bootstrap emitted the one-Job document, which cannot name the second Job a recovery adds; creation then refused. `bootstrap.variant` now answers multi-Job whenever a publication worker is configured.
- **Failure before launch** is covered: a recovery cancelled before its worker ever started delivers one owner item, with no runtime to settle.

## 3. DESIGN DECISION — how the reviewer is given the candidate

Observed in the connected run: after the hand-off the review stage is allocated to the Work's ordinary reviewer and its offer is issued, then its claim is refused and no reviewer container starts. Two things stand between the hand-off and a running reviewer.

**(a) Routine, mine to finish:** the publication ending releases the Work rather than handing it to the review route, and the reviewer is not yet delivered the publication hand-off document. The existing review machinery already carries a recovery hand-off document end to end (delivery, the reviewer's required digest claim, verdict collection); it needs to be handed the publication one.

**(b) Needs your decision.** An ordinary reviewer mounts a **frozen checkpoint of the development line**. For a recovered candidate the line owner offers `freeze_recovered_checkpoint`, and it requires the original writer to have been **released** — a committed release carrying a quiescent-finalization fence, which exists only when the producer answered with a no-candidate disposition. A producer whose publication failed never answered: its worker faulted, it has no disposition, and its writer grant is still on record as active. Neither supported ending of such an attempt releases the writer (`settle-stopped` mutates no Authority state; the fourth ending fences the assignment but not the writer). So the candidate of exactly the failure this Work exists for cannot become a reviewable checkpoint today.

Options:

- **R1 (recommended) — the line owner freezes a recovered checkpoint for a never-released writer, on host proof.** Required before the freeze: the attempt's runtime is positively absent with settled cleanup, read from the control store's own journal; no later writer on the line; the line is still at the checkpoint that writer was granted on; the frozen candidate's head equals the approved original's and its base equals the line's declared base. The writer is revoked in the same act. The checkpoint carries a new, separately typed recovery fence that checkpoint readers verify by its own kind. The Authority-side ending stays where it already is (the admission's prior-assignment ending, or the fourth ending).
- **R2 — give a failed-publication producer an ending that releases its writer the existing way.** The manager would record a no-candidate disposition for a faulted exchange and release the writer through the producer's own session. This changes the producer's failure lifecycle and the meaning of a disposition, and must also be applied to attempts that already failed.
- **R3 — do not use the line.** Deliver the reviewer a recovery-owned read-only export of the candidate and add a parallel attachment and verdict path. Largest change; departs from the existing review and verdict machinery.

R1 keeps the reviewer on the ordinary review path and confines the change to one owner, but it adds a second kind of evidence under which a line checkpoint may be frozen. That is a trust rule in an accepted owner, which is why I am not choosing it alone.

## 4. Verification on this checkpoint (`b5abcd8a`)

| Run | Result |
| --- | --- |
| Four required modules | 365 collected, 365 passed, 51.957 s |
| `job_manager` group (short scratch path) | 2267 collected, 2267 passed, accounting clean |
| Owner module, custody, intake, worker entry, packaging, installer, bootstrap, connected creation, retry lineage | 861 passed, 130.612 s |
| Whole `test_stage_execution` | 517 passed, 357.602 s |
| Reviewer probes, unmodified | 9 of 10 pass |

The tenth probe asserts the line-layout refusal, which no longer exists. `scans` was not rerun: it remains incomplete and unattributed, and `worker_manager/workspaces.py` — a file those scans inventory — has changed.

## 5. Plan outcomes against evidence

| Outcome | State | Evidence |
| --- | --- | --- |
| 1. Adoption fence, terminal race | Done | `ARecoveryThatDoesNotPublishIsFencedSettledAndReported` (window, replay, cancellation); reviewer `probe-window` |
| 2. Real pooled original, inspect → decide → admit → publish | Done | `APooledProducersFailedOutputIsReadThroughItsLine`; `TheConnectedRecoveryFromARealPooledProducer`; option A cases |
| 3. Settlement, unknown observation, owner item, status | Done | same settlement class (failure, expiry, restart, unreadable engine, before launch); pooled cancel case; reviewer `probe-failure` |
| 4. Ordinary reviewer admitted | Done | connected case; `test_the_review_stage_is_served_by_the_works_ordinary_reviewer` |
| 4. Reviewer delivered the candidate, runs, verdict collected | **Open** | section 3 |
| 4. Restart and lost-reply cuts at review; cancellation and expiry during review | Open | follows the above |
| Acceptance matrix, qualification commands | Open | final packet |

## 6. Not done or not proved

- The reviewer does not run (section 3). Everything in outcome 4 after admission.
- The connected case ends the failed producer with the fourth ending. The other supported ending, `settle-stopped`, leaves the Work held; that held-assignment path is covered only with fixture-built failed executions.
- A running manager still serves only the bindings it started with; the connected case restarts it after admission.
- No image build, container run or kernel confinement evidence.
- `scans` incomplete and unattributed.
