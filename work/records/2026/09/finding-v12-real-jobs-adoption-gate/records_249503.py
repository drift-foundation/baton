"""Claim-249503 entries: R1 closed by an actual roundtrip; R3/R4 still unstarted."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249503

**R1 is closed. R3's frozen verdicts and R4's supervisor are still unstarted,
and no work has begun on either.**

## Done under claim 249503

  * **The template and the composer now agree, and a ROUNDTRIP proves it.**
    `two_jobs.INSTANCE_OPERANDS` and `JOB_OPERANDS` name every operand the
    composition consumes; `compose` checks the document against them and
    refuses by name before building anything;
    `SELECTIONS-247941.json` carries all of them, including the
    `implementation_principal` the reviewer found missing, as owner choices.
  * **The submission is one the public reader accepts.** It was missing
    `test_scope` and `terminal_policy` and its stages carried no profile; it
    now carries all of them, and a case submits the WRITTEN document through
    `job_manager.submit`.
  * **`TheSHIPPEDTemplateComposesThroughTheACTUALCLI`** reads the shipped
    file, resolves every `<OWNER: ...>` with disposable fixture values, runs
    `two_jobs.py` as a subprocess exactly as step 3 prints it, and hands the
    written deployment to `held_configuration` and the written submission to
    `submit`. An unresolved template is refused by name and writes nothing.
  * **Pin validation is bound to composition.** `two_jobs.py` runs the pin
    check itself and refuses a drifted snapshot, so step 1 cannot be skipped
    by an operator who goes straight to step 3.

24 focused checks, 0 failures, measured 2.8681838100019377s,
`verification-3.json`.

## Still NOT started

  * **R3's rest — two FROZEN attributed verdicts.** Both reviewers are reached
    on distinct attempts; that is not two collected verdicts.
  * **R4 — the bounded four-admission supervisor**, its stop, positive cleanup
    for all four attempts and its published outcome.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md,
ASSESSMENT-EVIDENCE-249338.json, review-2026-09-23T17-12-02Z.md,
review-2026-09-23T17-17-50Z.md and every review-*.json/.log beside them.
baton.claude owns two_jobs.py, test_two_jobs.py, ADOPTION-247941.md,
CONTINUITY-247941.md, SELECTIONS-247941.json, verify_247941.py,
align_template.py, add_roundtrip.py, verification-*.json/.log, PROGRESS.md,
records_*.py and PLAN.md.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249503

Review 2026-09-23T17:17:50Z accepted the CLI globals, the decline/no-integration
witness and the manifest check, and found R1 still broken. It was right: I had
fixed the composer's SHAPE and never once run it against the file an operator
holds.

### What the roundtrip found that the unit checks could not

The shipped template lacked `implementation_principal` and a dozen other
operands `worker_document` consumes, so the composer would have raised a
`KeyError` on somebody's first real attempt. And the submission it generated
omitted `test_scope` and `terminal_policy` and gave its stages no profile, so
the public reader refused it.

Both are now closed the same way: `INSTANCE_OPERANDS` and `JOB_OPERANDS` name
every operand the composition consumes, `compose` checks the document against
them and refuses BY NAME before building anything, and the template carries all
of them as owner choices. `align_template.py` is the recorded act that brought
them into agreement.

`TheSHIPPEDTemplateComposesThroughTheACTUALCLI` is the proof: the shipped file,
every `<OWNER: ...>` resolved with disposable fixture values, `two_jobs.py` run
as a subprocess exactly as step 3 prints it, the written deployment handed to
`held_configuration` and the written submission handed to `job_manager.submit`.
An unresolved template is refused by name and writes nothing.

This is the third Work in a row where the defect was a document I shipped
without running. The pattern is not "the composer was wrong" -- it is that a
suite writing its own inputs cannot see a template defect at all.

### Pin validation bound to composition

The reviewer asked for it and it is one line of consequence: `two_jobs.py` runs
the pin check itself and refuses a drifted snapshot, so an operator who goes
straight to step 3 cannot compose against bytes nobody accepted.

### Verification spending

24 focused deterministic checks, 0 failures, measured 2.8681838100019377s,
receipt `verification-3.json` with `verification-3.log`; 5 are new.

Cumulative MEASURED for W247941, every retained invocation preserved rather
than superseded: 1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 =
**8.814818454s**. The pin checks are separate and their elapsed times were not
measured and are not estimated.

State: returned INCOMPLETE through baton.bug. R3's frozen verdicts and R4's
four-admission supervisor remain, with no work started on either.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249503" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
