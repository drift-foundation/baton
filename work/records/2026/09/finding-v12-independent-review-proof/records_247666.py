"""Claim-247666 dossier entries: item 5 done; items 1-4 outstanding."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action -- the admitted-reviewer lifecycle, and what waits on it

Owner reroute 247663 numbers the remaining scope 1-6 and says to work it in
that order. Claim 247666 delivered item 5 and did NOT reach items 1-4.

1. OUTSTANDING -- a deterministic fixture that actually ADMITS one reviewer
   through supported real coordination and frozen results. The current
   `Serving` fixture defers every admission and does not qualify; the reviewer
   and the owner are both right about that.
2. OUTSTANDING -- drive the actual supervisor through an attributed verdict,
   stopped execution and positive cleanup, and prove `changes-requested` is a
   valid outcome with zero correction rounds and zero implementation
   admission. Waits on 1.
3. OUTSTANDING -- failure, interruption, no-progress and cleanup uncertainty
   with an OUTSTANDING ADMITTED attempt; admission closing before cancellation
   and cleanup staying inside the total, measured with one. Waits on 1.
4. OUTSTANDING -- a distinct digest-bound manager-source artifact containing
   the reviewed `correction_policy` change, with the producer snapshot
   preserved, and the documented preparation and startup executed against
   those exact successor bytes. The selections still name
   `single-implementation-242687/manager-source`, which predates the change.
5. DONE under claim 247666. The malformed policy is exercised through
   `held_configuration`, and the twelve product errors are corroborated
   focally rather than by count.
6. OUTSTANDING -- the complete packet, commands, provider question and
   execution evidence. Waits on 1-4.

**The packet is NOT runnable and is not labelled ready.** `OPERATOR-239533.md`
says so at the top and `review_supervisor.held_packet` enforces the
no-correction boundary as a precondition.

## Not in scope

No broad refactor, deployed-store access, live execution, image rebuild,
recovery, implementation rerun or resume. No closure of W239533 or W236087.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247666

Owner reroute 247663, addressing review 2026-09-23T12:20:24Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **Item 5 is done. Items
1-4 and 6 are not, and this claim did not reach them.** That is partial
progress, not readiness, and the packet stays marked NOT RUNNABLE.

**No deployed store was opened.** The one product file remains the one the
owner selected.

### Item 5, done

**The malformed policy goes through the validator.**
`test_a_malformed_correction_policy_is_refused_by_the_validator` composes a
real deployment and hands `held_configuration` five unreadable values --
`"Decline"`, `"off"`, `""`, `None`, `1` -- and requires each to be refused by
name. An unreadable policy would otherwise be discovered by `routed`, which
runs after a verdict has been recorded: the wrong moment to learn that a
deployment cannot say what it meant.

**The twelve are corroborated focally rather than counted.**
`preexisting_errors.py` runs them BY NAME and records where each one fails.
All twelve fail inside `Integration._run`'s producer-proposal read, through
`_authority_read`, and NO traceback among them names `correction_policy`,
`CORRECTION_POLICIES`, `DECLINE_CORRECTION`, `routed` or
`correction_declined`. A change that is never reached did not cause them.
`PREEXISTING-ERRORS-247666.json` records the selectors, the failing frames and
that result.

Exact prior evidence is quoted beside it -- W239528's
`review-2026-09-22T23-53-34Z.md`, dated the day BEFORE the product change --
**with that reviewer's own caveat kept**: "I did not rerun that broader suite
or independently establish their provenance." Quoting the report without the
caveat would have been citing my own claim back as if somebody else had
checked it, which is why the focused comparison exists rather than the quote
standing alone.

**A comment repair, and it is the only reason the product digest moved.** A
shell backtick had eaten the word `routed` from one comment line when claim
247423's edit was applied, leaving "# IS the deployment's own method". No
behaviour changed. `PRODUCT-CHANGE-247423.json` records the new after digest
`6a212c3a...` and says exactly that.

### Items 1-4, not reached, and the honest reason

I did not run out of interface or authority -- I ran out of turn. The path is
known and the reviewer named it: `BaselineCase` in W239528's
`test_baseline.py` already drives a real composition through
`stage_execution.operations_from` with a deterministic provider, real stores
and `baseline.prepare` in place of the owner acts, and `stores(incarnation)`
opens fixed paths so a second phase can share one control store with the
first. The shape is: run the accepted implementation phase to leave a frozen
review-ready checkpoint, then compose and drive the REVIEW packet over those
same stores with `review_supervisor.supervise`.

WHAT I EXPECT TO HAVE TO SOLVE THERE, recorded so the next claim starts from
it rather than from scratch:

  * `baseline.prepare` mints the qualification grant bound to
    `packet["context"]["job_id"]` for a CONTEXTUAL worker. The review worker
    is not contextual (`single_worker.CONFIG_SCHEMA`, not the context one), so
    whether a review run needs that preparation at all, and what it needs
    instead, is the first thing to establish.
  * the review packet's `context` member is currently composed with null
    profile members for the same reason, and `held_packet` accepts that; a
    driven run will say whether the composition agrees.
  * the second phase's Job identity must differ from the first's while the
    control store is shared, which is the arrangement `attachment.py` already
    describes and `survey` already refuses collisions for.

Item 4 is smaller and also unreached: a distinct digest-bound manager-source
snapshot carrying the `correction_policy` change, built the way
W239528's `snapshot_242687.py` builds one and leaving the producer's snapshot
untouched, then `SELECTIONS-239533.json` pointing at it instead of
`single-implementation-242687/manager-source`, which predates the change.

Verification: 88 focused deterministic checks, 0 failures, measured
1.2950563630001852s, receipt `verification-7.json` with `verification-7.log`;
2 are new. Separately, `preexisting_errors.py` ran the twelve named product
cases.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 + 1.295056363 =
**166.489882279s**. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s) are theirs and are
preserved separately.

State: returned for independent review with items 1-4 and 6 outstanding and
the packet not runnable.
"""

OWNERSHIP = """
## Claim 247666 -- item 5, and a comment repair

Added: `preexisting_errors.py`, `PREEXISTING-ERRORS-247666.json`,
`records_247666.py`, `verification-7.json/.log`.

Edited in this dossier: `test_review_bindings.py`, `PRODUCT-CHANGE-247423.json`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file.

PRODUCT PATH: `v12/python/tools/stage_execution.py` moved from
`318e9a4bdf111cb3b93bddbe63c6d6fe6911702023db7196c507fbae54d18d11` to
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801` for a
COMMENT REPAIR ONLY -- a shell backtick had eaten the word `routed` from one
comment line. No behaviour changed and no test moved with it.

**Nothing else under `v12/` was edited** and no product test was weakened.
W239528's `baseline.py` is unchanged at its accepted digest, both images are
unchanged, no deployed store was opened, the disclosed `control.sqlite3-shm`
and zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247666" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247666" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
