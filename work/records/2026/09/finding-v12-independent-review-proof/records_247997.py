"""Claim-247997 dossier entries: item 4 completed on the successor bytes."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CHECKPOINT = """# Checkpoint -- W239533

Concise per AGENTS.md "Delivery continuity and bounded context". FINDING keeps
the history.

## Accepted

  * the attachment arrangement and its supported read-only survey
  * the `review_supervisor` specialization's source and its interface fixes
  * the `correction_policy` product change's source branch; item 5
  * owner 247663 ITEMS 1 AND 2 (2026-09-23T13:04:00Z)
  * the gate-state-at-cancellation observation and the exact outstanding
    identity (2026-09-23T13:10:01Z)
  * the reached deadline and the observed shutdown interruption
    (2026-09-23T13:15:08Z)
  * the successor snapshot, its local manifest and the selections/operator
    path updates (2026-09-23T13:20:42Z)

## Done under claim 247997 -- item 4's remaining half

`TheDocumentedCommandsRunAgainstTheSUCCESSORSource` binds `PYTHONPATH` to
`/home/sl/baton-runs/independent-review-247947/manager-source` -- exactly what
`BOUND` names on the operator page, and nothing from the checkout's own
`v12/python` -- and runs the documented commands through it:

  * the documented COMPOSITION exits 0, and the `PACKET.json` it writes names
    that snapshot as its manager source and code boundary, with a file count
    and per-file digests equal to the manifest's;
  * the documented STARTUP holds the packet, resolves
    `verify_imported_sources` INSIDE the snapshot -- both `tools` and
    `baton_v12` are asserted to resolve under that path -- and passes the
    image check through `main`'s own `image_inspect` seam with a stub, so no
    container, image or engine is reached.

`OPERATOR-239533.md`'s opening note no longer repeats an older state: it lists
what is accepted, what is outstanding, and that the whole preparation is not
accepted so steps 2 and 4 are unauthorized.

## Next executable milestone

1. THE ADMITTED NO-PROGRESS CASE: positive cleanup COMMITTED under a stage
   still short of terminal, held at its real transition boundary, six
   unchanged observations, no false timeout attribution, no raw store edits
   and no fabricated receipts.
2. Owner 247663 item 6: the complete packet, exact commands, provider question
   and execution evidence.

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. Outside
the checkout: `/home/sl/baton-runs/independent-review-247947/manager-source`,
built once and never rewritten.

## Latest review, evidence and positions read

`review-2026-09-23T13-20-42Z.md`; receipt `verification-12.json`. Last
discussion position read: T239533 message 247805. Last event read: 247985.
Owner 247956's adoption dependency is noted; scope unchanged.

## Blockers

None. NOT RUNNABLE until the remaining items are done and the whole
preparation is independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247997

Review 2026-09-23T13:20:42Z accepted the successor snapshot and its bindings,
and corrected me on scope: **owner 247663 item 4 includes the exact-successor
documented preparation and startup, and I had deferred that into item 6 and
called item 4 done.** That was moving a requirement rather than meeting it, and
the correction is right. It is now executed.

### Item 4's remaining half

`TheDocumentedCommandsRunAgainstTheSUCCESSORSource` binds `PYTHONPATH` to the
successor snapshot -- exactly what `BOUND` names on the operator page, and
NOTHING from the checkout's own `v12/python`, because a path carrying both
would prove nothing about which bytes answered.

  * The documented COMPOSITION exits 0 against those bytes, and the
    `PACKET.json` it writes names the snapshot as its manager source and code
    boundary with a file count and per-file digests equal to the manifest's --
    so the packet is bound to the tree the manifest describes rather than to a
    path that happens to have the right name.
  * The documented STARTUP holds the packet and resolves
    `verify_imported_sources` INSIDE the snapshot; both `tools` and
    `baton_v12` are asserted to resolve under that path. The image check goes
    through `review_supervisor.main`'s own `image_inspect` seam with a stub,
    so no container, image or engine is reached -- the proof is about which
    bytes ran, not about a deployment.

One defect surfaced there and is fixed: the shared composition fixture binds
`attachment.py` as `supervisor_path`, so the startup refused with "this process
is running review_supervisor.py and the packet binds attachment.py". A startup
proof has to name the supervisor rather than inherit a composition fixture's
placeholder.

### The operator page's opening note

It still claimed the boundary "has not yet been accepted" and that R3b was
outstanding, both of which had moved. It now lists what IS accepted, what is
outstanding, and that the whole preparation is not accepted so steps 2 and 4
are unauthorized -- and it distinguishes "nothing has been executed against a
deployment" from "the documented commands have been executed on disposable
fixtures", which are different claims and were being blurred.

Verification: 108 focused deterministic checks, 0 failures, measured
13.294443416991271s, receipt `verification-12.json` with
`verification-12.log`; 2 are new.

Cumulative MEASURED for W239533: 205.879183313 + 13.294443417 =
**219.173626730s**. Unmeasured ad-hoc driving remains UNKNOWN and is not
estimated. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s,
3.324525589s, 4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s) are
theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 247997 -- the documented commands on the successor bytes

Edited in this dossier: `test_review_bindings.py`, `OPERATOR-239533.md`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added:
`records_247997.py`, `verification-12.json/.log`.

**No file under `v12/` was edited under this claim, and the successor snapshot
was not modified** -- it was READ, with `PYTHONPATH` bound to it, and its
manifest compared against the packet the documented command wrote. The product
path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` is unchanged at its accepted digest, its producer snapshot is
untouched, both images are unchanged, no deployed store was opened, the
disclosed `control.sqlite3-shm` and zero-length `control.sqlite3-wal` are
preserved, and every reviewer file in this dossier is append-only history that
was not modified.
"""


def main():
    (HERE / "PLAN.md").write_text(CHECKPOINT, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247997" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247997" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
