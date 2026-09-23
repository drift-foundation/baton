"""Claim-244759 dossier entries: R1 corrected, R2 still open."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

FINDING = """
## 2026-09-23 -- the survey reads through supported interfaces (R1)

Review 2026-09-23T04:40:30Z refused the first `attachment.py` as a P1 and was
right. It opened the control store with `sqlite3.connect` and issued its own
`SELECT`s against `review_lines`, `line_checkpoints`, `line_writers` and
`review_attachments`. AGENTS.md does not qualify the rule: "Never read it
directly either: if a question about the coordination state can only be
answered by opening the store, that inability is the finding." `mode=ro` does
not exempt raw SQL from it.

The premise I built it on was true but incomplete. `ControlStore.open` can
initialize or migrate -- but `ControlStore.open_readonly` already existed, in
the current tree and in the selected `manager-source-242687` snapshot, and it
recognizes the schema and refuses an empty or unsupported store WITHOUT
migrating it. I did not look for it, and a correct premise led to a wrong
conclusion because of what I did not check.

WHAT THE SUPPORTED VERSION READS: `ControlStore.open_readonly`, one
`snapshot()` spanning the whole account, and `line_of`, `checkpoint_of` and
`writer_of`. The reviewer's second point was also right -- separate reads with
no explicit snapshot are not a coherent line/checkpoint/writer account, and
sequential test cases do not demonstrate one. The snapshot is now measured
rather than asserted.

THREE PUBLIC LOOKUPS DO NOT EXIST, and `attachment.GAPS` records each with the
supported alternative used in its place rather than routing around it:

  * No public function answers "the line for this Authority and Work" without
    creating one. So the packet NAMES `line_id` and `line_of` PROVES that line
    carries the expected Authority and Work. An operator reads the identity
    from the producer's retained `outcome.json`, which is a file.
  * No public reader lists a line's checkpoints. `checkpoint_of` answers one
    checkpoint's own line and revision, which is exactly what separates a
    superseded revision of this line from a checkpoint of another line. The
    listing was never needed for the decision.
  * No public reader lists a line's writers or attachments. `line_of` answers
    the state, and `review-ready` / `writing` / `reviewing` is the signal the
    validator itself acts on.

THE DISCLOSED PRODUCER ARTIFACTS ARE PRESERVED. The earlier raw-SQL survey
created `control.sqlite3-shm` and a zero-length `control.sqlite3-wal` beside
W239528's retained control store. They are still there, still disclosed, and
were not cleaned up or relabelled. `open_readonly`'s own docstring records the
same SQLite-owned behaviour, so using the supported opener does not make that
read retrospectively clean -- it makes the next one supported.
"""

PLAN = """# Current action -- the review Job's own composition

1. DONE. W239528's retained proposal and cleanup are independently accepted
   (review-2026-09-23T04-15-56Z.md), and W239528 is now canonically closed
   satisfying. See FINDING for what that acceptance covers and what it does
   not.
2. DONE, AND CORRECTED UNDER R1. The attachment arrangement: `attachment.py`
   and `test_attachment.py`, now reading through `ControlStore.open_readonly`,
   one coherent `snapshot()` and the public `line_of`/`checkpoint_of`/
   `writer_of` readers. Producer/reviewer independence and wrong, stale and
   foreign checkpoint rejection are each driven through the real
   `review_cycles.attach_review` against a real `ControlStore`, and the
   preflight's account is required to agree with the validator's. The missing
   public lookups are recorded in `attachment.GAPS`.
3. DONE AS COMPOSITION ONLY -- not as executable readiness, and review
   2026-09-23T04:40:30Z is right that the two must not be confused.
   `review_bindings.py` and `test_review_bindings.py` compose one review
   stage against a real line. `review_bindings.write` has NOT been held
   against `stage_execution.held_configuration` on a disposable Authority.
4. OUTSTANDING -- the bounded review-only supervisor.
5. OUTSTANDING -- `write` through `held_configuration` on disposable supported
   stores, driven by the actual documented command.
6. OUTSTANDING -- digest-bound selections, exact commands and the
   provider-specific question. They wait on 4: `PACKET.json` names its
   supervisor and its digest.
7. Then accept only a valid attributed verdict, stopped execution and positive
   cleanup. Pass the retained result to W236087; do not run correction here.

## Not in scope

No deployed-store access, live execution, provider, container, recovery,
implementation rerun or resume. No closure of W239533 or W236087.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 244759

Owner reroute 244755, addressing review 2026-09-23T04:40:30Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **R1 is fully addressed.
R2 is not, and it is returned again with exact scope.**

**No file under `v12/` was edited and no deployed store was opened under this
claim.** The only store this claim opened was the disposable one the tests
build; the producer's retained store was not read at all this turn.

### R1 -- the survey now reads through supported interfaces

`attachment.py` was rewritten onto `ControlStore.open_readonly`, one
`snapshot()` spanning the whole account, and the public `line_of`,
`checkpoint_of` and `writer_of` readers. `FINDING.md` records why the first
version was wrong, and `attachment.GAPS` records the three public lookups that
do not exist together with the supported alternative used in place of each.

Four things changed in substance rather than in wording:

  * **The line is named and proved, not searched for.** No public function
    answers "the line for this Authority and Work", so the packet names
    `line_id` and `subject()` refuses when that line carries a different
    Authority or Work. A named identity that is checked is better evidence
    than a search that could quietly find something else.
  * **`STALE` and `WRONG` come from the checkpoint's own record.**
    `checkpoint_of` answers its line and revision, which is the whole
    distinction; and a checkpoint the store does not hold is reported as
    absence rather than raised, because "no such checkpoint" IS the answer.
  * **The `ACTIVE WRITER` refusal is gone.** It existed only because of the
    raw `line_writers` scan. The line state is the supported signal and the
    reachable one -- `test_attachment` already established that
    `attach_review`'s writer-coexistence branch cannot be reached from
    `review-ready` -- so the `writing` refusal now says what that state means
    instead.
  * **`checkpoint_of` decodes `evidence` itself.** The raw-SQL version read
    stored text and called `json.loads` on it. That it had to is one more way
    that version was reading something other than what the supported interface
    answers.

Two cases hold the correction to more than its own wording: the snapshot depth
is MEASURED while the survey is inside the boundary, and the bypass is checked
by PARSING the module -- no `sqlite3` import, no `execute` call -- rather than
by searching its text, because the docstring names what was removed and a
substring search would be satisfied by the confession.

`review_bindings.compose` was moved onto the same handle and closes it; its
`COMPOSITION_INSTANT` is a constant so composing the same selections twice
produces the same documents byte for byte.

**The disclosed producer artifacts are preserved.** `control.sqlite3-shm` and
the zero-length `control.sqlite3-wal` beside W239528's retained control store
are still there and still disclosed. They were not cleaned up, and using the
supported opener does not make the earlier read retrospectively clean.

**A test of mine measured the wrong thing, and it is corrected in place.**
`test_the_command_takes_no_base_operand` ran the documented command WITHOUT the
bound import path, so its exit status was an import failure rather than the
argparse refusal it claimed to prove. It now runs through the same bound
environment as the accepting path.

### R2 -- still open, and this is the second claim it has been open

The owner asked for it at reroute 244627 and again at 244755. It is not
delivered, and saying so plainly is better than delivering a supervisor whose
endings I have not driven. Exact remaining scope:

1. **The bounded review-only supervisor.** `KINDS` closed over `review`; one
   admission and retry disabled; finite turn, total and reserved cleanup
   limits with an actionable no-progress rule; admission closed before
   cancellation; every discovered attempt accounted for; the ordinary ending
   and cleanup path driven; an outcome published on interruption and on
   failure; attributed verdict collection through
   `review_driver.review_verdict_from_result` with base/head/tree checked
   against the attached checkpoint; and an explicit refusal to open a
   correction on `changes-requested`.
2. **`review_bindings.write` through `stage_execution.held_configuration` on
   disposable supported stores, driven by the actual documented command.**
   `tests.manager.test_claude_context.ManagedSessionResume` is the fixture
   that supplies a disposable Authority, control store and configured
   workspace storage; reaching a frozen checkpoint there means producing one
   through a deterministic implementation turn the way W239528's
   `test_baseline` does.
3. **Digest-bound selections, the exact commands and the provider question.**
   They wait on 1 because `PACKET.json` names its supervisor and its digest.

Also outstanding and not this Job's: the `seconds_bound` 3600/180 metadata
discrepancy the accepted W239528 review retained for a bounded follow-up.

Verification: 38 focused deterministic checks, 0 failures, measured
0.5900577230058843s, receipt `verification-2.json` with `verification-2.log`.
`verification-1.json` is claim 244629's receipt and is kept beside it; its
checks exercised the refused direct-SQL implementation and it is retained as
history rather than as current evidence.

Cumulative measured for W239533: 0.432753846 (claim 244629) + 0.590057723
(claim 244759) = **1.022811569s**.

State: returned for independent review with R2 outstanding.
"""

OWNERSHIP = """
## Claim 244759 -- R1 corrected

Edited: `attachment.py`, `test_attachment.py`, `review_bindings.py`,
`test_review_bindings.py`, `verify.py`, `FINDING.md`, `PLAN.md`, `PROGRESS.md`,
this file. Added: `records_244759.py`, `verification-2.json/.log`.

`verification-1.json/.log` is claim 244629's receipt and is KEPT rather than
replaced: it measured the implementation R1 refused, and deleting it would
delete the evidence of what was corrected.

**No file under `v12/` was edited and NO DEPLOYED STORE WAS OPENED under this
claim.** The producer's retained control store was not read this turn at all;
the `control.sqlite3-shm` and zero-length `control.sqlite3-wal` that claim
244629's survey created beside it are preserved and disclosed, not cleaned up.
Both images, W244180's dossier and W236087's dossier are untouched. W239528 is
now canonically closed satisfying and its dossier remains read-only here.
"""


def main():
    finding = HERE / "FINDING.md"
    body = finding.read_text(encoding="utf-8")
    if "supported interfaces (R1)" not in body:
        finding.write_text(body.rstrip("\n") + "\n" + FINDING, encoding="utf-8")
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 244759" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 244759" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
