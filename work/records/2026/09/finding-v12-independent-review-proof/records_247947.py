"""Claim-247947 dossier entries: item 4's successor source; item 6 remains."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CHECKPOINT = """# Checkpoint -- W239533

Concise per AGENTS.md "Delivery continuity and bounded context". FINDING keeps
the history.

## Accepted

  * the attachment arrangement and its supported read-only survey
  * the `review_supervisor` specialization's source and the R1/R2 fixes
  * the `correction_policy` product change's source branch; item 5
  * owner 247663 ITEMS 1 AND 2 (2026-09-23T13:04:00Z)
  * the gate-state-at-cancellation observation and the exact outstanding
    identity (2026-09-23T13:10:01Z)
  * the reached deadline and the observed shutdown interruption
    (2026-09-23T13:15:08Z)

## Done under claim 247947 -- owner 247663 item 4

`snapshot_247947.py` builds and verifies THIS Job's own manager-source
snapshot at `/home/sl/baton-runs/independent-review-247947/manager-source`:
106 files, carrying `tools/stage_execution.py` at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, bound by
`MANAGER-SOURCE-independent-review-247947.json`. `--verify` holds. The
producer's snapshot is verified UNCHANGED against its own manifest as part of
every build and is never written to; a build refuses if it has drifted, if the
destination or the manifest exists, or if the copy does not carry the change.
`SELECTIONS-239533.json` and `OPERATOR-239533.md` are repointed at it, and the
page carries the `--verify` command.

## Next executable milestone

1. THE ADMITTED NO-PROGRESS CASE, still outstanding. Measured again this
   claim: the adapter's own `unable` path leaves cleanup OUTSTANDING
   (`no committed cleanup`), which correctly suppresses the detector, so that
   route does not reach it. The state the detector needs is positive cleanup
   COMMITTED under a stage still short of terminal, held at its real
   transition boundary.
2. Owner 247663 item 6: the complete packet, exact commands, provider
   question and execution evidence, over the successor source now bound. The
   documented preparation and startup have not yet been executed against those
   exact successor bytes on disposable fixtures.

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. Outside
the checkout, NEW and never replacing anything:
`/home/sl/baton-runs/independent-review-247947/manager-source`.

## Latest review, evidence and positions read

`review-2026-09-23T13-15-08Z.md`; receipt `verification-11.json`. Last
discussion position read: T239533 message 247805. Last event read: 247942.

## Blockers

None. NOT RUNNABLE until the remaining items are done and the whole
preparation is independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247947

Review 2026-09-23T13:15:08Z accepted the deadline and shutdown corrections.
**Item 4 is done. Item 6 and the admitted no-progress case remain.**

### Item 4 -- this Job's own manager source

The selections bound `single-implementation-242687/manager-source`, which is
W239528's producer snapshot and PREDATES the `correction_policy` change. A run
bound to it would have no boundary to decline the correction round with, and
`held_packet` would refuse the packet composed from it -- so the binding was
not merely stale, it was unusable.

`snapshot_247947.py` builds the successor: 106 files at
`/home/sl/baton-runs/independent-review-247947/manager-source`, carrying
`tools/stage_execution.py` at `6a212c3a...ab5801`, bound by
`MANAGER-SOURCE-independent-review-247947.json`. `--verify` holds with no
drift, nothing missing and nothing extra.

W239528'S SNAPSHOT_242687.PY WAS NOT USED, and the reason is ownership rather
than capability. It supports `--rebuild-into` and `--claim` for exactly this,
and its refusals are the ones this follows -- never replace a tree, never
replace a manifest, a successor states its own claim. But its `manifest_for`
writes into ITS OWN dossier, and W239528 is a closed Work whose dossier is
read-only here; writing a W239533 manifest into it would be this Job filing its
evidence in somebody else's record. The rules are reused; the destination is
this dossier's.

THE PREDECESSOR IS VERIFIED UNCHANGED AS PART OF EVERY BUILD, against its own
recorded manifest, and the build refuses if it has drifted. A successor whose
build could not say the predecessor survived would be asserting the one thing
the arrangement exists to guarantee.

`SELECTIONS-239533.json` and `OPERATOR-239533.md` are repointed, and the page
now carries the `--verify` command and says why the binding moved.

### The no-progress case, measured again

The adapter's own `unable` path was tried as a route to it: a malformed report
makes the turn `unable`, the stage stays `answering` and the run stops on its
bound -- but cleanup is OUTSTANDING (`no committed cleanup`), which correctly
suppresses the detector. So that route does not reach it. The state the
detector needs is positive cleanup COMMITTED under a stage still short of
terminal, held at its real transition boundary, and that is recorded in the
checkpoint as the next milestone rather than approximated.

Verification: 106 focused deterministic checks, 0 failures, measured
12.45698677400651s, receipt `verification-11.json` with `verification-11.log`.
No case was added this claim -- the work was the snapshot and the bindings --
and the receipt now also binds `snapshot_247947.py` and its manifest.

Cumulative MEASURED for W239533: 193.422196539 + 12.456986774 =
**205.879183313s**. Unmeasured ad-hoc driving remains UNKNOWN and is not
estimated. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s,
3.324525589s, 4.056475030s, 8.306612300s, 4.491119177s) are theirs and are
preserved separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 247947 -- the successor manager source

Added: `snapshot_247947.py`,
`MANAGER-SOURCE-independent-review-247947.json`, `records_247947.py`,
`verification-11.json/.log`.

Edited in this dossier: `SELECTIONS-239533.json`, `OPERATOR-239533.md`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file.

OUTSIDE THE CHECKOUT, NEW and replacing nothing:

    /home/sl/baton-runs/independent-review-247947/manager-source
        106 files, carrying the correction_policy change

PRESERVED and verified as part of the build:

    /home/sl/baton-runs/single-implementation-242687/manager-source
        W239528's producer snapshot, byte-identical to its own manifest

**No file under `v12/` was edited under this claim.** The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. W239528's
dossier was READ ONLY -- `MANAGER-SOURCE-242687.json` was opened to verify the
predecessor and nothing was written into that dossier. Both images are
unchanged, no deployed store was opened, the disclosed `control.sqlite3-shm`
and zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.
"""


def main():
    (HERE / "PLAN.md").write_text(CHECKPOINT, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247947" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247947" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
