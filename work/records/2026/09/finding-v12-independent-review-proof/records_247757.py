"""Claim-247757 dossier entries: item 1 substantially advanced, not finished."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action -- one reviewer, admitted; the turn still answers `unable`

Owner reroute 247747: start with item 1, prioritize the executable path over
further helper tests, and state the exact next unfinished operation if a turn
ends. Claim 247757 advanced item 1 a long way and did not finish it.

1. IN PROGRESS -- `test_review_lifecycle.py` now ADMITS one reviewer through
   supported real coordination. Phase one is W239528's accepted
   `baseline.supervise` run, leaving a real `review-ready` line with a frozen
   checkpoint; phase two composes a review deployment over THOSE SAME STORES
   with its own Job identity and drives `review_supervisor.supervise`. The
   stage reaches `answering`, the turn runs, and the manager freezes a real
   result.

   **THE EXACT NEXT UNFINISHED OPERATION**: that frozen result is `unable`, so
   `review_verdict_from_result` refuses with "review attempt ... froze an
   'unable' result; a review that did not complete decided nothing". The next
   step is to find why `claude_agent._review` answers `unable` for this turn
   and supply what it is missing -- the report bytes now travel through the
   provider's own cwd, which is what `_review_report(room)` reads, so the
   remaining gap is inside that branch rather than in the manager.
2. OUTSTANDING -- the attributed verdict, stopped runtime and positive
   cleanup, and `changes-requested` with zero correction rounds and zero
   implementation admission. Waits on 1 reaching a completed result.
3. OUTSTANDING -- failure, interruption, no-progress and cleanup uncertainty
   with an OUTSTANDING ADMITTED attempt. The fixture that makes them reachable
   now exists; the cases do not.
4. OUTSTANDING -- the distinct digest-bound successor manager-source artifact
   carrying the `correction_policy` change, and the documented preparation and
   startup executed against those exact bytes. The selections still name
   `single-implementation-242687/manager-source`, which predates the change.
5. ACCEPTED at review 2026-09-23T12:45:47Z. Not repeated.
6. OUTSTANDING -- the complete packet, commands, provider question and
   execution evidence. Waits on 1-4.

**The packet is NOT runnable and is not labelled ready.**

## Not in scope

No broad refactor, deployed-store access, live execution, image rebuild,
recovery, implementation rerun or resume. No closure of W239533 or W236087.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247757

Owner reroute 247747. Read canonical state, the complete work-events, thread
T239533 in full (2 messages, no pagination remaining), the review, and this
dossier. Item 5 is accepted and was not repeated. **Item 1 is substantially
advanced and NOT finished; items 2-4 and 6 are untouched.**

**No deployed store was opened and no product byte changed under this claim.**

### What now works, and it is the thing three reviews have asked for

`test_review_lifecycle.py` admits ONE REVIEWER through supported real
coordination. Two phases over ONE control store:

  * PHASE ONE is W239528's accepted `baseline.supervise` run, driven
    unmodified, so what phase two reviews is a checkpoint that Job's own
    accepted program actually made -- a real line, a real writer, a real
    frozen checkpoint, `review-ready`.
  * PHASE TWO composes a review deployment carrying
    `correction_policy: "decline"`, submits a review-only Job with its OWN
    identity, and drives `review_supervisor.supervise` over the same stores.

The outcome now reports `admissions: {"review": 1}` and the stage reaches
`answering`: the reviewer is admitted, the turn runs, and the manager freezes
a real result. The subject is read back from the control store rather than
declared.

### Four real defects the drive found, each fixed

Every one of them was invisible to a fixture that defers admission, which is
exactly why the reviewer refused that fixture.

  * **The review Job's input digest was the fixture constant.** The stage sat
    `queued` for a whole run and the deferral said why: "no worker this
    deployment configures for the 'review' stage can serve Job ...:
    {'review-worker': ['the submitted input']}". It is now
    `job_input_identity(self.manifest)` -- the worker's own manifest.
  * **`composed_for` answered phase one's composition.** The fixture's `turn`
    reaches it for the prepared attempt's boundary, so the review turn raised
    `KeyError` for the attempt that had just been admitted. Phase two now sets
    `self._composed`.
  * **The report had no way to travel.** `claude_agent._review_report(room)`
    reads `review-report.json` from the PROVIDER'S OWN cwd, which the
    fixture's `edits` seam writes; a `report=` operand the turn does not take
    did nothing.
  * **The producer's stores were not carried forward.** `supervised` keeps
    `_job` but not `_control`, so the subject could not be read.

### THE EXACT NEXT UNFINISHED OPERATION

The frozen result is `unable`, so `review_verdict_from_result` refuses:

    review attempt 'attempt-27aae1ed...' froze an 'unable' result;
    a review that did not complete decided nothing

So the manager side is reached and correct -- it froze a result and refused to
read a verdict out of a turn that did not complete. What remains is to find why
`claude_agent._review` answers `unable` for this turn and supply what it is
missing. The report bytes now travel the way a real reviewer's would, so the
gap is inside that branch rather than in the manager or the supervisor.
`_review` re-reads the mounted source after the turn and refuses if it moved,
refuses an inherited report destination, and requires the provider to answer
`ok` -- each is a candidate and none has been eliminated yet.

Items 2 and 3 are one step behind that: the fixture that makes an attributed
verdict, a stopped runtime, positive cleanup and an outstanding-attempt
failure/interruption reachable now EXISTS, and the cases do not.

Verification: the dossier's receipt is unchanged from claim 247666
(`verification-7.json`, 88 checks) because this claim added no passing case --
`test_review_lifecycle.py` carries the fixture and no test method yet, and
`load_tests` keeps `BaselineCase`'s own cases from being counted here. Saying
"88" twice is more honest than inventing a number for work in progress.

Cumulative measured for W239533 is therefore unchanged at **166.489882279s**.
The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s) are theirs and are
preserved separately.

State: returned for independent review with item 1 in progress at the exact
operation named above, and the packet not runnable.
"""

OWNERSHIP = """
## Claim 247757 -- the admitted-reviewer fixture

Added: `test_review_lifecycle.py`, `records_247757.py`.

Edited in this dossier: `PLAN.md`, `PROGRESS.md`, this file.

**No file under `v12/` was edited under this claim** -- the product path stays
at `6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, the
digest claim 247666 recorded. W239528's `baseline.py` is unchanged at its
accepted digest and is SUBCLASSED for its fixture, not modified. No deployed
store was opened, both images are unchanged, the disclosed
`control.sqlite3-shm` and zero-length `control.sqlite3-wal` are preserved, and
every reviewer file in this dossier is append-only history that was not
modified.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247757" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247757" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
