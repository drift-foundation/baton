"""Claim-247318 dossier entries: R1-R4 resolved."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

FINDING = """
## 2026-09-23 -- four defects, and what each one says about the testing

Review 2026-09-23T11:30:47Z found four, and they are worth recording together
because three of them share one cause: the delivered suite tested what the
programs REFUSE and never once drove what they DO.

**R1, and it is the one that mattered most: the supervisor refused its own
packet.** `main` called the imported `verify_imported_sources(packet)` without
`program=`. That function is defined in `baseline.py` and defaults the running
program to its own `__file__`, so a packet correctly naming
`review_supervisor.py` failed with "this process is running .../baseline.py
and the packet binds .../review_supervisor.py" -- exit 2, before the engine or
any store. A default that is right for the module a function is DEFINED in is
wrong for every module that IMPORTS it, and the specialization's whole premise
is importing. The composer-to-`held_packet` test stopped one call short of it.

The same review found the operator page's step 1 passing `clock=lambda: "now"`
to `open_readonly`; the public instant grammar rejects that string, so the
documented survey could not run as printed. `attachment.now()` now exports the
formula and a case runs that exact block.

**R2: every successful verdict was classified as invalid.**
`review_verdict_from_result` returns `verdict`, `result_id` and
`result_digest`; the collector read `disposition` and `verdict_id`, which it
does not answer, so a valid `accepted` became `None` and produced a shortfall.
The attachment reader supplies `assignment_generation`, not `generation`, so
the outcome recorded null. THIS COULD ONLY EVER HAVE BEEN FOUND BY A TEST THAT
EXERCISED THE SUCCESS PATH, and there was none: the delivered cases covered
missing verdicts, wrong checkpoints and foreign kinds, and every one of them
passed with the collector reading members that do not exist.

**R3: the orchestration was never driven.** Importing tested helpers does not
verify the 381 lines that ORDER them. Driving it found three real defects:
the submission and the turn-ceiling read sat OUTSIDE the publishing region, so
a colliding Job identity escaped with nothing on disk; the cleanup window's
progress read was unguarded and could do the same; and serving ran for the
whole `total_seconds` and THEN opened a further `cleanup_seconds`, so a packet
declaring 300 with 60 reserved could spend 360 -- "reserved" does not mean
that.

**R4 is a different kind of finding and the review was right to separate it.**
The previous claim narrowed the selected no-correction contract by prose:
it let `StageComposition.routed` open a correction round, asserted the round
"belongs to W236087", and guaranteed only that no container starts. No
accepted implementation supplies the authority to assign a round in W239533's
Job store to another Work. THE CONTRACT IS RESTORED AND THE LIMITATION IS
REPORTED: `routed` calls `open_correction` unconditionally and the composed
deployment exposes no operand that declines it, so preventing the round needs
a change in the owning implementation scope. This run therefore HOLDS when one
appears rather than redefining its scope, and `correction_rounds_opened` is
read from the Job store's own stage records instead of from attempt kinds --
the previous derivation reported nothing at all for a round opened and never
allocated an attempt, which is the exact shape a `changes-requested` ending
leaves behind.

Whether to accept a held outcome for that reason, or to select the product
change, is an owner decision and `OPERATOR-239533.md` says so where the effect
appears.
"""

PLAN = """# Current action -- the packet awaits owner selection

1. DONE. W239528's proposal and cleanup are independently accepted; W239528 is
   canonically closed satisfying.
2. DONE, accepted 2026-09-23T04:50:12Z. The attachment arrangement through
   supported read-only interfaces, with the missing public lookups recorded.
3. DONE, accepted 2026-09-23T05:08:49Z. The two P2 fixture corrections.
4. DONE, corrected under claim 247318. `review_supervisor.py` -- the local
   specialization -- now starts correctly (R1), consumes the public verdict
   and attachment contracts (R2), keeps the reserved cleanup inside the total
   and publishes an outcome from the owner acts onward (R3), and holds rather
   than narrowing the no-correction contract (R4).
5. DONE. The documented command through `write` and `held_configuration` on
   disposable supported stores, and the packet it writes held by the
   supervisor's own validator.
6. DONE. The orchestration driven over real Job and control stores: the
   serving bound, the reserved-cleanup arithmetic, a refusing submission, a
   serving failure, an interruption, and an outcome on every one of those
   paths.
7. DONE. `SELECTIONS-239533.json` and `OPERATOR-239533.md`: digest-bound
   operands, exact commands, and the provider question.
8. AWAITING OWNER SELECTION -- the live run, and separately whether a
   `changes-requested` review ending `held` for the correction-round
   limitation is acceptable or the product change is selected instead.

## Not in scope

No deployed-store access, live execution, provider, container, recovery,
implementation rerun or resume. No closure of W239533 or W236087.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247318

Owner reroute 247316, addressing review 2026-09-23T11:30:47Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **R1-R4 are resolved.**

**No file under `v12/` was edited and no deployed store was opened.**
`baseline.py` is unchanged at its accepted digest.

### R1 -- the supervisor refused its own packet

`verify_imported_sources(packet, program=os.path.abspath(__file__))`. The
imported function defaults `program` to `baseline.__file__`, so every correct
packet failed at startup. `FINDING.md` records why the delivered tests could
not have caught it: they stopped one call short of `main`.

The operator page's step-1 clock is corrected too. `attachment.now()` exports
the instant formula, the page names it, and two cases run that exact block --
one against the real opener on a disposable store, one holding the page to the
corrected text.

### R2 -- every successful verdict was classified as invalid

The collector read `disposition` and `verdict_id`; the public reader answers
`verdict`, `result_id` and `result_digest`. It read `generation`; the
attachment row records `assignment_generation`. Both are corrected, and the
outcome now carries the result provenance.

The new cases drive the SUCCESS path for all three supported verdicts, plus a
verdict outside the contract and a head that disagrees with the checkpoint.
The public return is substituted and LABELLED as such: reaching a real frozen
review output needs a provider turn and an Authority receipt this deterministic
suite does not have and must not fabricate. What it holds the collector to is
the public return contract, which is exactly what was wrong.

The existing success fixture also built subjects from `checkpoint.get("base")`
where the row records `base_object`, so its comparisons were None against None.
Corrected, and the comment says so.

### R3 -- the orchestration is now driven

`SupervisionCase` drives `supervise` over a real `JobStore`, a real
`ControlStore`, a real submission and the real imported `AdmissionGate`, with a
stand-in for the engine side only. Three real defects came out of it:

  * the submission and the turn-ceiling read sat OUTSIDE the publishing
    region. A colliding Job identity escaped with nothing on disk. They are
    now inside it, `submission_failure` is a hold reason, and a case drives it
    with a genuine second submission over one Job identity;
  * the cleanup window's progress read was unguarded and could do the same;
  * serving ran for the whole `total_seconds` and THEN opened a further
    `cleanup_seconds`. Serving now stops at `total - cleanup` and the window is
    additionally bounded by what is left of the total.

Driven paths: the serving bound, the reserved-cleanup arithmetic, a refusing
submission, a serving failure, an interruption that publishes AND still raises,
and an outcome on every one of them. Two limits are stated rather than faked:
the fixture composition defers admission instead of completing an admit
through to a journalled operation, so `no-progress` -- which requires
something accountable -- is not reachable here, and neither is a completed
attempt lifecycle. A fake that answered an admit it could not finish made the
next sweep refuse for the fixture's reason instead of the run's, which is
itself a small demonstration of why driving beats reasoning.

A test of mine also read `SupervisorInterrupted.args[1]` for the retained
outcome; the class documents it on `.outcome` and passes only the reason to
`BaseException`. That was the case assuming a shape instead of reading the one
the class states.

### R4 -- the selected contract is restored

The previous claim narrowed it by prose. It is restored: a correction round
opened in this Job store HOLDS the run, `correction_rounds_opened` is read
from the Job store's own stage records rather than from attempt kinds, and
`CORRECTION_LIMITATION` names the exact product site -- `StageComposition.routed`
calling `open_correction` unconditionally, with no operand that declines it --
and says the change belongs to the owning implementation scope. A case drives
that branch and asserts the hold. `OPERATOR-239533.md` presents the choice to
the owner where the effect appears.

Verification: 79 focused deterministic checks, 0 failures, measured
1.3253460949927103s, receipt `verification-5.json` with `verification-5.log`;
15 are new. Earlier receipts are kept as the record of what each round
corrected.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 = **4.104664278s**. The reviewers' independent
measurements (0.571337769s, 0.596305013s, 1.152729417s) are theirs and are
preserved separately.

State: the corrected preparation is returned for independent review. No live
run is selected or authorized by it.
"""

OWNERSHIP = """
## Claim 247318 -- R1 through R4

Edited: `review_supervisor.py`, `attachment.py`, `test_review_supervisor.py`,
`test_attachment.py`, `OPERATOR-239533.md`, `verify.py`, `FINDING.md`,
`PLAN.md`, `PROGRESS.md`, this file. Added: `records_247318.py`,
`verification-5.json/.log`.

**No file under `v12/` was edited and no deployed store was opened.**
W239528's `baseline.py` is imported and unchanged at its accepted digest
`f27f3cd7...3df18fd5`, which `review_supervisor.BASELINE_SHA256` binds and the
receipt records. The `control.sqlite3-shm` and zero-length
`control.sqlite3-wal` beside W239528's retained control store are preserved
and still disclosed. Both images, W244180's dossier and W236087's dossier are
untouched, and every reviewer file in this dossier is append-only history that
was not modified.
"""


def main():
    finding = HERE / "FINDING.md"
    body = finding.read_text(encoding="utf-8")
    if "four defects, and what each one says" not in body:
        finding.write_text(body.rstrip("\n") + "\n" + FINDING, encoding="utf-8")
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247318" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247318" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
