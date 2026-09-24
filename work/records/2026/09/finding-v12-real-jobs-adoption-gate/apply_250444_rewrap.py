"""Claim-250444: rewrap the lines the re-indent pushed past 79 columns.

Moving the serving-to-accounting block inside the outer `try` shifted it four
columns, and twelve lines that fitted before no longer do. This rewraps exactly
those, changing no behaviour: line 332 was already over before this claim and
is left alone so the diff stays about the lifetime correction.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "two_job_supervisor.py"

SWAPS = (
    ("""        # ADMISSION IS CLOSED BEFORE ANYTHING IS CANCELLED. That is what makes the
        # cleanup window unable to start a runtime while it settles the ones this
        # run already has.""",
     """        # ADMISSION IS CLOSED BEFORE ANYTHING IS CANCELLED. That is
        # what makes the cleanup window unable to start a runtime while it
        # settles the ones this run already has."""),
    ("""        # started. Both are the accepted helpers; neither is reimplemented here.""",
     """        # started. Both are the accepted helpers; neither is
        # reimplemented here."""),
    ("""        # THE ACCEPTED CANCELLATION PATH. This called `operations.cancel`, which""",
     """        # THE ACCEPTED CANCELLATION PATH. This called
        # `operations.cancel`, which"""),
    ("""                dict(gate.launched), dict(held.get("states") or {}), uncertainty,
                reason=measured["stopped"], launched=set(gate.launched),""",
     """                dict(gate.launched), dict(held.get("states") or {}),
                uncertainty, reason=measured["stopped"],
                launched=set(gate.launched),"""),
    ("""        # `_cleanups` asks the journal about a destroy bound to THIS deployment's""",
     """        # `_cleanups` asks the journal about a destroy bound to THIS
        # deployment's"""),
    ("""        # with admission closed it can finish endings without being able to admit
        # anything. Each pass is inside what is left of the TOTAL, so the reserve
        # is a window rather than an extension.""",
     """        # with admission closed it can finish endings without being able
        # to admit anything. Each pass is inside what is left of the TOTAL,
        # so the reserve is a window rather than an extension."""),
    ("""                    f"Job {one} produced no attributed verdict; a two-Job review "
                    f"run that collected fewer than two has not done its work")""",
     """                    f"Job {one} produced no attributed verdict; a "
                    f"two-Job review run that collected fewer than two has "
                    f"not done its work")"""),
    ("""                "no runtime was ever launched, so there is nothing this run can "
                "claim to have stopped or cleaned up")""",
     """                "no runtime was ever launched, so there is nothing "
                "this run can claim to have stopped or cleaned up")"""),
)

CLEANUP_LINE = ('        measured["cleanup"] = {} if settled is None '
                'else settled.get("cleanup", {})')
CLEANUP_WRAPPED = ('        measured["cleanup"] = ({} if settled is None\n'
                   '                               '
                   'else settled.get("cleanup", {}))')


def main():
    body = PLACE.read_text(encoding="utf-8")
    for old, new in SWAPS:
        if body.count(old) != 1:
            raise SystemExit(
                f"REFUSED: a block appears {body.count(old)} times, not once:"
                f"\n{old}")
        body = body.replace(old, new, 1)
    if body.count(CLEANUP_LINE) != 2:
        raise SystemExit(
            f"REFUSED: the cleanup line appears {body.count(CLEANUP_LINE)} "
            f"times, not twice")
    body = body.replace(CLEANUP_LINE, CLEANUP_WRAPPED)
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    over = [(number, line) for number, line
            in enumerate(written.splitlines(), 1) if len(line) > 79]
    # LINE 332 WAS ALREADY OVER before this claim and is not this correction's
    # business; anything else is.
    unexpected = [one for one in over
                  if "termination = baseline.Termination()" not in one[1]]
    if unexpected:
        raise SystemExit(f"REFUSED: still over 79 columns: {unexpected}")
    compile(written, str(PLACE), "exec")
    print(f"rewrapped; {len(over)} line(s) remain over 79 and each predates "
          f"this claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
