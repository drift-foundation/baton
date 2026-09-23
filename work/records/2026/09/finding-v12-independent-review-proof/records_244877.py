"""Claim-244877 dossier entries: P2 closed; the R2 ownership question."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

FINDING = """
## 2026-09-23 -- the R2 question the owner has to answer

W239533's remaining scope is a bounded review-only supervisor. Three claims
have now recorded it as outstanding, and the reason is not that it is merely
large. It is that there is no seam to build it on, and the only two ways to
get one are a decision this Job cannot take by itself.

WHAT WAS MEASURED, under claim 244877, reading W239528's accepted `baseline.py`
rather than guessing about it:

  * `AdmissionGate` is ALREADY kind-agnostic. It is constructed with
    `caps={kind: count}` and a `job_id`, and refuses by reading `self._caps`.
    A review Job passes `caps={"review": 1}` and nothing else changes. Its
    module-level `KINDS` constant is referenced nowhere but its own definition.
  * `Termination`, `_guarded`, `_attempts_of`, `_terminal`, `_observation`,
    `_cleanups`, `_refresh`, `_cancel_active`, `_runtime_facts`, `_origin`,
    `_publish`, `_turn_ceiling` and `survey` are all kind-agnostic too.
  * `_supervise` IS NOT. It is one ~400-line function that reads
    `bounds["implementer_invocations"]` directly, builds the caps dictionary
    inline, and calls `_workload_evidence`, which gathers proposals,
    attributions and provider-context evidence -- the implementation-shaped
    half. There is no parameter, no hook and no subclass point for a different
    stage kind or a different evidence shape.

SO THE REVIEW SUPERVISOR IS EITHER:

  (a) A DERIVED COPY of `baseline.py`, about 2000 lines, of which perhaps 60
      differ: the caps key, the bounds member, the outcome vocabulary, and
      `_workload_evidence` replaced by verdict collection through
      `review_driver.review_verdict_from_result`. Every ending, interruption
      and cleanup path in the copy then has to be driven deterministically
      again, because a copy nobody drove is not evidence.

  (b) A BOUNDED REFACTOR of `baseline.py` to expose the seam -- caps and
      workload evidence as operands -- after which this dossier's supervisor
      is a few hundred lines that IMPORT the accepted machinery, and W239528's
      own tests keep proving it.

(b) is better engineering and it is what "reuse accepted components" points
at. It also EDITS A FILE THIS JOB DOES NOT OWN: `baseline.py` belongs to
W239528, which is now canonically closed satisfying, and the owner's split
ruling deliberately separated the two dossiers so that neither Job's proof
moved when the other changed. Taking that decision quietly inside W239533
would be exactly the boundary violation the split exists to prevent.

THE QUESTION, in one line: may W239533 refactor W239528's accepted
`baseline.py` to expose a stage-kind and workload-evidence seam, or must it
carry a derived copy? Absent an answer this implementer will proceed with (a),
because it is the option that needs nobody's permission -- but it is the worse
one, and it should be chosen rather than defaulted into.
"""

PLAN = """# Current action -- the review Job's own composition

1. DONE. W239528's retained proposal and cleanup are independently accepted
   (review-2026-09-23T04-15-56Z.md); W239528 is canonically closed satisfying.
2. DONE, accepted at review 2026-09-23T04:50:12Z. The attachment arrangement:
   `attachment.py` reads through `ControlStore.open_readonly`, one coherent
   `snapshot()` and the public `line_of`/`checkpoint_of`/`writer_of` readers,
   with the missing public lookups recorded in `attachment.GAPS`.
3. DONE under claim 244877 -- the review's two P2 test items. The foreign
   attempt is now ADMITTED through `issue_offer`, `accept_offer`,
   `record_attempt`, `submit_claim` and `activate_assignment` against a
   session bound to the other Work, and the read-only boundary is measured
   through a supported mutator with operands that actually require a write.
   No private SQL remains anywhere in this dossier.
4. DONE AS COMPOSITION ONLY, and not as executable readiness.
   `review_bindings.py` composes one review stage against a real line;
   `write` has NOT been held against `stage_execution.held_configuration`.
5. OUTSTANDING AND BLOCKED ON AN OWNER DECISION -- the bounded review-only
   supervisor. See FINDING: `baseline._supervise` exposes no seam for a
   different stage kind, so this is either a ~2000-line derived copy or a
   bounded refactor of a closed Work's accepted file. The second needs
   authorization this Job does not hold.
6. OUTSTANDING -- `write` through `held_configuration` on disposable supported
   stores, driven by the actual documented command.
7. OUTSTANDING -- digest-bound selections, exact commands and the
   provider-specific question. They wait on 5: `PACKET.json` names its
   supervisor and its digest.
8. Then accept only a valid attributed verdict, stopped execution and positive
   cleanup. Pass the retained result to W236087; do not run correction here.

## Not in scope

No deployed-store access, live execution, provider, container, recovery,
implementation rerun or resume. No closure of W239533 or W236087.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 244877

Owner reroute 244875, addressing review 2026-09-23T04:50:12Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **Both P2 test items are
closed. R2 is not delivered, and the concrete blocker is named rather than
deferred again.**

**No file under `v12/` was edited and no deployed store was opened.**

### The two P2 items, closed

**The foreign attempt is admitted, not relabelled.** The case built the attempt
with this fixture's own Work and then ran
`UPDATE attempts SET work_id = ?` before granting a writer. The reviewer was
right that this asserts the foreign-checkpoint lifecycle rather than
establishing it. `admitted_attempt` now runs the authority half in order --
`issue_offer`, `accept_offer`, `record_attempt`, `submit_claim`,
`activate_assignment` -- against a `FakeSession` bound to the OTHER Work, using
the product suite's own admission fixture (`tests.manager.test_offers`,
`tests.manager.input_roots`). The coverage is unchanged in meaning: a real
frozen checkpoint of a real second line, refused as `WRONG` by both accounts.

Two refusals along the way were the lifecycle working and are followed rather
than worked around: an offer whose profile nothing certifies is refused, so the
case certifies it the way the product's own offer fixture does; and a claim
whose decision fences somebody else is refused, so the decision now names the
participant it is about.

**The read-only boundary is measured through a supported mutator.** The probe
ran `DELETE FROM review_lines` on the handle's private connection, which proves
SQLite refuses a write but not that the SUPPORTED interface cannot change the
store through that handle. It now calls `create_line` on the read-only handle.

THE FIRST DRAFT OF THAT REPLACEMENT PASSED THE EXISTING WORK AND NOTHING WAS
RAISED -- correctly, because that call is a pure replay and a replay writes
nothing. Measuring a read-only boundary with an operand that needs no write
measures nothing at all. The case now names a Work the store holds no line for,
so the mutator must insert, and the refusal is real. The draft is recorded in
the case rather than quietly replaced.

**No private SQL remains in this dossier.** `attachment.py`, `review_bindings.py`,
`test_attachment.py` and `test_review_bindings.py` contain no `sqlite3` import
and no `execute` call; the only occurrences of the word are in the prose that
records what was removed, and the bypass check parses the module rather than
searching its text for exactly that reason.

### R2 -- not delivered, and the concrete blocker

The owner asked for R2 complete or a concrete blocker rather than another
helper-only handoff. The blocker is real and it is an OWNERSHIP question, not a
size complaint. `FINDING.md` carries the measurement; in short:
`baseline.AdmissionGate` and every other machine part of W239528's accepted
supervisor are already kind-agnostic and importable, but `_supervise` itself is
one ~400-line function that reads `bounds["implementer_invocations"]` inline
and calls an implementation-shaped `_workload_evidence`, with no seam for a
different stage kind.

So the review supervisor is either a ~2000-line derived copy whose every
ending must be driven again, or a bounded refactor of `baseline.py` to expose
caps and workload evidence as operands. The refactor is the better engineering
and is what "reuse accepted components" points at -- and it edits a file
W239533 does not own, belonging to a Work that is now closed, across a boundary
the owner's split ruling drew deliberately.

**The question: may W239533 refactor W239528's accepted `baseline.py` to expose
that seam, or must it carry a derived copy?** Absent an answer this implementer
will proceed with the derived copy, because it needs nobody's permission -- but
it is the worse option and should be chosen rather than defaulted into.

Nothing else about R2 has changed: the supervisor, `write` through
`held_configuration` driven by the actual documented command, and the
digest-bound selections, commands and provider question remain as
claim 244759's entry records them.

Verification: 38 focused deterministic checks, 0 failures, measured
0.5885895419924054s, receipt `verification-3.json` with `verification-3.log`.
The receipt now also binds the product admission fixtures this claim reuses.
`verification-1.json` and `verification-2.json` are kept as the record of what
each round corrected.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 =
**1.611401111s**. The reviewer's independently measured 0.571337769s at claim
244799 is theirs and is preserved separately rather than added here.

State: returned for independent review with R2 outstanding and its blocker
named.
"""

OWNERSHIP = """
## Claim 244877 -- the two P2 test items

Edited: `test_attachment.py`, `verify.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_244877.py`,
`verification-3.json/.log`.

`verification-1.json/.log` and `verification-2.json/.log` are earlier claims'
receipts and are KEPT: each records what the following round corrected.

**No file under `v12/` was edited and no deployed store was opened.** The
product's own admission fixtures (`tests.manager.test_offers`,
`tests.manager.input_roots`) are imported read-only and their digests are
bound in the receipt. The `control.sqlite3-shm` and zero-length
`control.sqlite3-wal` that claim 244629's survey created beside W239528's
retained control store are preserved and still disclosed. Both images,
W244180's dossier and W236087's dossier are untouched.

The reviewer's files -- `review-2026-09-23T04-40-30Z.md`,
`review-2026-09-23T04-50-12Z.md`, `review-evidence-244729.json`,
`review-evidence-244799.json` and `review-tests-244799.log` -- are append-only
history and were not modified.
"""


def main():
    finding = HERE / "FINDING.md"
    body = finding.read_text(encoding="utf-8")
    if "the R2 question the owner has to answer" not in body:
        finding.write_text(body.rstrip("\n") + "\n" + FINDING, encoding="utf-8")
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 244877" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 244877" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
