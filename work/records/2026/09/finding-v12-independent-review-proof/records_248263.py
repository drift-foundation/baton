"""Claim-248263 dossier entries: the complete packet, and how it stays true."""
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
  * gate-state-at-cancellation and the exact outstanding identity
    (2026-09-23T13:10:01Z)
  * the reached deadline and the observed shutdown interruption
    (2026-09-23T13:15:08Z)
  * the successor snapshot and its bindings (2026-09-23T13:20:42Z)
  * the successor-only composition and the 106-file packet manifest
    (2026-09-23T13:25:28Z)
  * `main` actually invoked, bounded successor-source startup
    (2026-09-23T13:35:00Z)
  * the unallocated accounting correction and the actual six-tick stall
    (2026-09-23T13:52:06Z)
  * the origin-read interrupt correction; ITEM 3 COMPLETE
    (2026-09-23T13:57:49Z)

## Done under claim 248263 -- owner 247663 item 6, the last one

THE COMPLETE PACKET IS ASSEMBLED and every claim in it is checkable.

`OPERATOR-239533.md` is rewritten as the packet itself: what the packet
contains, the twelve unresolved operator-selected inputs with the three that
carry a refusal called out, steps 0-6 with the exact commands, the provider
question, and a limitations section a reader is sent to FIRST.

`EVIDENCE-239533.json` is the machine-readable half, DERIVED by the new
`packet.py` from the retained files at generation time -- digests, receipts,
the successor manifest, the subject, the bounds, and the two prose lists
`established` and `not_established`. `verify.py` regenerates it before each
run, so it cannot drift from the tree behind the page's back.

`test_packet.py` (25 checks) is the answer to the failure mode this Job has hit
twice: PROSE THAT WAS TRUE WHEN IT WAS WRITTEN. It asserts every shipped and
reused digest against disk; that no SHA256 on the page is one the evidence does
not know; that the page quotes no receipt name or check count of its own; that
the documented flags are the ones `review_bindings`, `review_supervisor`,
`packet` and `snapshot_247947` actually declare, read by `ast`; that the open
choices listed are exactly those the selections still ask for; and that the two
proofs stay distinguished.

**THE DISTINCTION, stated in both documents.** The `main` startup proof enters
the documented entry point and is HELD, because its composition starts nothing.
The real-coordination lifecycle settles with an attributed verdict but calls
`supervise` directly with an injected clock. No single run in this dossier both
enters `main` and settles, and none reached a live provider.

## Next executable milestone

None held by this implementer. The preparation is complete and returned for
independent review. What follows it is an owner decision: resolve the twelve
selected inputs and select the bounded live run that answers the provider
question.

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. Outside
the checkout: `/home/sl/baton-runs/independent-review-247947/manager-source`,
built once, read but never rewritten.

## Latest review, evidence and positions read

`review-2026-09-23T13-57-49Z.md`; receipt `verification-18.json`. Last
discussion position read: T239533 message 247805. Last event read: 248249.

## Blockers

None. NOT RUNNABLE until the preparation is independently accepted and the
twelve operator-selected inputs are resolved.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 248263

Review 2026-09-23T13:57:49Z accepted the origin-read correction and closed item
3. **This claim completes owner 247663 item 6, the last one: the complete
packet, exact commands, provider question and consolidated evidence.**

### The packet, and why it is two documents

`OPERATOR-239533.md` is now the packet rather than a note beside it. It opens
with what is in the packet, lists the TWELVE unresolved operator-selected
inputs by member -- calling out the three that carry a refusal rather than a
choice (`provider_network` where `none` is refused, the credential reference
where an expired token reproduces a known failure, and the evidence digest
where an all-zero sentinel is refused) -- then gives steps 0-6 with the exact
commands, the provider question with the three negative answers that are
evidence rather than bugs, and a limitations section.

`EVIDENCE-239533.json` is the machine-readable half, produced by the new
`packet.py`. Every digest, receipt, count and open choice in it is READ from a
retained file at generation time; the only written prose is `established`,
`not_established` and the provider question. `verify.py` regenerates it BEFORE
running the suite, so the checks compare a current document against the tree
rather than the previous run's -- which also means its `receipts` list stops one
run short of the receipt written afterwards, and the document says so.

### Prose that was true when it was written

That is the failure this Job has now hit twice -- a page claiming `main` had
run when it had not, and a page still advertising `verification-6.json` and "64
focused deterministic checks" at claim 248209. `test_packet.py` is the answer,
and its 25 checks are about the packet's honesty rather than the supervisor:

every shipped and reused digest against the file on disk; no SHA256 on the page
that the evidence does not know; NO receipt name or check count quoted in prose
at all, so there is nothing left to go stale; the documented `--flags` compared
against what `review_bindings`, `review_supervisor`, `packet` and
`snapshot_247947` actually declare, read out of the source by `ast` rather than
by running them; the open choices exactly those the selections still ask for,
with the count the page states; and the two proofs kept distinct.

I probed three of those assertions against deliberately corrupted inputs before
trusting them -- a stale baseline digest on the page, a blurred lifecycle entry
point, and a wrong document digest -- and each failed as it should.

### What the packet does NOT claim

The `main` startup proof enters the documented entry point with two seams
supplied, and its outcome is `held` because a composition that starts nothing
answers nothing about the reviewer. The real-coordination lifecycle settles
with an attributed verdict over real stores, a real attachment and a real
frozen output, but it calls `supervise` directly with an injected clock and
does not enter `main`. **No single run here both enters `main` and settles, and
no run reached a live provider.** Both documents say so in those words, and a
check asserts they keep saying it.

Verification: 138 focused deterministic checks, 0 failures, measured
36.4567306980025s, receipt `verification-18.json` with `verification-18.log`;
25 are new.

Cumulative MEASURED (suite receipts only) for W239533: 343.269261891 +
36.456730698 = **379.725992589s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032. Unmeasured ad-hoc driving
remains UNKNOWN and is not estimated; the retained receipts now sum to
183.515042473s in `EVIDENCE-239533.json`, and the difference between that and
the cumulative figure is superseded within-claim runs, which were not
individually receipted.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s, 4.183597788s, 2.115041870s, 2.201875895s, 13.059195031s) are
theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 248263 -- the packet assembled

Edited in this dossier: `OPERATOR-239533.md` (rewritten as the packet),
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added: `packet.py`,
`test_packet.py`, `EVIDENCE-239533.json`, `records_248263.py`,
`verification-18.json/.log`.

**No file under `v12/` was edited under this claim, no test of the supervisor
or the composer was changed, and the successor snapshot was not modified.** The
product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` is unchanged at
`f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5`, its
producer snapshot is unchanged, both images are unchanged, no deployed store
was opened, the disclosed `control.sqlite3-shm` and zero-length
`control.sqlite3-wal` are preserved, and every reviewer file in this dossier is
append-only history that was not modified.

`EVIDENCE-239533.json` is deliberately absent from `verify.py`'s `OWNED`
digests: a document regenerated by the same program that writes the receipt
cannot carry its own digest in it.
"""


def main():
    (HERE / "PLAN.md").write_text(CHECKPOINT, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 248263" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 248263" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
