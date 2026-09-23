"""Claim-247159 dossier entries: the selected local specialization, delivered."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

FINDING = """
## 2026-09-23 -- the local specialization, and my framing was too narrow

Review 2026-09-23T05:08:49Z proposed a third option and owner reroute 247154
selected it. It is better than either of the two I named, and the record should
say why my framing was wrong rather than quietly adopting the better answer.

I presented the choice as a ~2000-line derived copy or a refactor of a closed
Work's accepted file. Both premises were measured and both were true; the
inference was not. Because `baseline._supervise` exposes no seam, I concluded
that the whole of `baseline.py` had to move -- but only the ORCHESTRATION BODY
is implementation-shaped. `Termination`, `AdmissionGate`, `survey`, `_guarded`,
`_attempts_of`, `_refresh`, `_terminal`, `_observation`, `_cleanups`,
`_cancel_active`, `_origin`, `_publish`, `_turn_ceiling`,
`verify_imported_sources`, `verify_worker_image` and `_compose` are all
importable as they stand, and I had already measured that they were
kind-agnostic. A local specialization imports every one of them and writes only
what a review differs in. I had the measurement and drew the wrong conclusion
from it.

WHAT `review_supervisor.py` IS: the orchestration body, `review`-shaped; a
packet validator for this Job's schema, bounds and subject; and
`_verdict_evidence` in place of `_workload_evidence`. Everything else is
W239528's accepted bytes, bound by digest
`f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5` and refused
before anything opens if the imported file is not those bytes. No global of
`baseline` is assigned and no attribute of it replaced; that is held by parsing
this program rather than by asserting it.

## 2026-09-23 -- what "no correction on changes-requested" actually means

The phrase is broader than the thing that can honestly be promised, and the
packet says so. `StageComposition.routed` opens the next round in the Job store
itself when a verdict answers `correction`. That is the ACCEPTED COMPOSITION'S
OWN ACT, and a supervisor that suppressed it would be weakening the composition
to make its own report tidier -- which is the shape review
2026-09-23T05:08:49Z explicitly refused in advance.

So the guarantee is narrower and exact: the admission gate's only cap is
`review`, so no correction CONTAINER can start; and the outcome reports the
opened ROUND as a fact, under `correction_rounds_opened`, because the Job store
really does hold one and it belongs to W236087's separately selected
correction. `correction_containers_started` is the outcome's own statement that
none started, and a non-empty one holds the run.

All three dispositions are successful reviews. The shortfall is a run that
produced no attributed verdict at all, which is why `_verdict_evidence` reads
the reviewer's FROZEN OUTPUT rather than a process exit status.
"""

PLAN = """# Current action -- the packet awaits owner selection

1. DONE. W239528's retained proposal and cleanup are independently accepted;
   W239528 is canonically closed satisfying.
2. DONE, accepted 2026-09-23T04:50:12Z. The attachment arrangement:
   `attachment.py` reads through `ControlStore.open_readonly`, one coherent
   `snapshot()` and the public readers, with the missing public lookups
   recorded in `attachment.GAPS`.
3. DONE, accepted 2026-09-23T05:08:49Z. The two P2 fixture corrections.
4. DONE. `review_supervisor.py` -- the local specialization the review
   proposed and reroute 247154 selected. It imports W239528's kind-agnostic
   machinery unchanged, binds it by digest, monkeypatches nothing, and writes
   only the review orchestration, packet validation and checkpoint-bound
   verdict collection.
5. DONE. The documented command driven through `write` and
   `stage_execution.held_configuration` on disposable supported stores, and
   the packet it writes handed to `review_supervisor.held_packet`.
6. DONE. `SELECTIONS-239533.json` and `OPERATOR-239533.md`: digest-bound
   operands, the exact commands, and the provider-specific question with the
   three answers that would each settle it negatively.
7. AWAITING OWNER SELECTION -- the live run. Nothing here authorizes it.
8. Then accept only a valid attributed verdict, stopped execution and positive
   cleanup. Pass the retained result to W236087; do not run correction here.

## Not in scope

No deployed-store access, live execution, provider, container, recovery,
implementation rerun or resume. No closure of W239533 or W236087.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247159

Owner reroute 247154, selecting the local specialization review
2026-09-23T05:08:49Z proposed. Read canonical state, the complete work-events,
thread T239533 in full (2 messages, no pagination remaining), the review, and
this dossier. **R2 is delivered.**

**No file under `v12/` was edited and no deployed store was opened.** The only
stores this claim opened are the disposable ones the tests build.

### The selection, recorded -- and my own framing corrected

The reviewer was right and my two options were a false choice. I had already
measured that `baseline`'s termination, admission, discovery, cancellation,
cleanup and publication parts are kind-agnostic, and then concluded that the
whole file had to move because `_supervise` has no seam. Only the
ORCHESTRATION BODY is implementation-shaped. `FINDING.md` records the
correction rather than adopting the better answer silently.

`review_supervisor.py` imports sixteen names from W239528's accepted
`baseline.py` unchanged and binds that file by digest
(`f27f3cd7...3df18fd5`), refusing before anything opens if the imported bytes
are not the accepted ones -- reuse that cannot say WHICH bytes it reused is a
dependency, not reuse. It monkeypatches nothing, and
`test_it_monkeypatches_nothing_in_baseline` parses this program to hold it to
that rather than trusting the sentence.

### What it delivers

One review invocation, retry refused, finite turn/total/reserved-cleanup
bounds and a no-progress stop after six unchanged ticks; admission closed
BEFORE cancellation; cancellation through the composition's own port; a
cleanup window that settles endings and can admit nothing; every discovered
attempt classified and accounted; an outcome published on every path including
a serving failure and an interruption, with `SupervisorInterrupted` carrying
the retained outcome.

`_verdict_evidence` replaces the implementation's workload evidence: one review
attempt and no other kind, an attachment to the checkpoint the packet names,
and a verdict read from the reviewer's own frozen output through
`review_driver.review_verdict_from_result`, whose cross-binding is the point --
base, head and tree are checked against the reviewed checkpoint's own record.

### The correction guarantee, stated at its real width

`StageComposition.routed` opens a correction ROUND itself on a
`changes-requested` verdict. This supervisor does not suppress it: that is the
accepted composition's act, and suppressing it would be weakening the
composition to make this report tidier. What it guarantees is that no
correction CONTAINER starts -- the gate's only cap is `review` -- and the
outcome reports both facts separately. See `FINDING.md`.

### The command through write and held_configuration

`TheDocumentedCommandProducesAnAcceptedPacket` runs the operator page's command
as a subprocess: it composes, holds the deployment against
`stage_execution.held_configuration`, writes seven documents, and the
`PACKET.json` it wrote is then handed to `review_supervisor.held_packet`. A
refused composition writes no packet at all.

Two things that surfaced there are corrected in place rather than worked
around. `_document` is an EXACT member check, and holding the subject to one
refused the real composition for carrying the survey's full account -- the
line's path, device, inode, state and revision, the source, the reference name
and the path set. All of that belongs in a packet an operator reads, so the
subject check is now REQUIRED-members: a validator should not fail in the
direction of refusing evidence. And the second case first derived a checkout
from the state root, which put the deployment's mutable state inside the
checkout; it now reads the packet's own bound `code_boundary`, which is exactly
the disagreement W239528's composer carries that value to avoid.

### The packet

`SELECTIONS-239533.json` binds the subject, the image, the adapter, the manager
source and the 180/300/60 bounds, and leaves every choice this implementer may
not take as an explicit `<OWNER: ...>`. The subject values were read at claim
244629 and are reproduced rather than re-read, because this reroute forbids
deployed-store access; step 1 re-reads them and the composer refuses on drift.

`OPERATOR-239533.md` carries the six steps, and says plainly what the run is
not: the review APPENDS to W239528's retained control store and its boundary
lands under W239528's workspace storage, because those four things are the
line's identity and custody. It states the real-provider question with the
three outcomes that would each answer it negatively, and says that
`changes-requested` and `rejected` are not among them.

Verification: 64 focused deterministic checks, 0 failures, measured
1.1679170720017282s, receipt `verification-4.json` with `verification-4.log`;
26 are new. The supervisor's imported machinery is bound by digest and was
proved by W239528's own suite, not re-proved here, and the receipt says so.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 = **2.779318183s**. The reviewers' independent measurements
(0.571337769s at claim 244799, 0.596305013s at claim 244917) are theirs and are
preserved separately.

State: the complete preparation is returned for independent review. No live run
is selected or authorized by it.
"""

OWNERSHIP = """
## Claim 247159 -- the review supervisor and the packet

Added: `review_supervisor.py`, `test_review_supervisor.py`,
`SELECTIONS-239533.json`, `OPERATOR-239533.md`, `records_247159.py`,
`verification-4.json/.log`.

Edited: `test_review_bindings.py`, `verify.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file.

**No file under `v12/` was edited and no deployed store was opened.**
W239528's `baseline.py` is IMPORTED and its digest is bound in
`review_supervisor.BASELINE_SHA256` and in the receipt; it was not edited,
copied or monkeypatched. Earlier receipts are kept: each records what the
following round corrected. The `control.sqlite3-shm` and zero-length
`control.sqlite3-wal` that claim 244629's survey created beside W239528's
retained control store are preserved and still disclosed. Both images,
W244180's dossier and W236087's dossier are untouched, and every reviewer file
in this dossier is append-only history that was not modified.
"""


def main():
    finding = HERE / "FINDING.md"
    body = finding.read_text(encoding="utf-8")
    if "the local specialization, and my framing" not in body:
        finding.write_text(body.rstrip("\n") + "\n" + FINDING, encoding="utf-8")
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247159" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247159" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
