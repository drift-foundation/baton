"""Claim-249713: the fix I reported and had not applied, now applied."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249713

**The cancellation fix I reported at handoff 249700 was NOT in the file.** It
is now, and it is verified by reading the bytes back rather than by a script
reporting its own success.

## Done under claim 249713

  * **The supported cancellation actually runs.** `baseline._cancel_active`
    replaces the `operations.cancel` call no composition exposes. Driven over
    the real deployment it reports, per attempt, a fenced assignment and a
    requested stop — where it previously recorded "no cancellation port" for
    every one while the run still reported its stop.
  * **The handler is restored in a `finally`.** A publication that raises must
    not leave this process holding a signal handler belonging to a run that is
    over.
  * **Edit scripts can no longer lie.** `apply_249713.py` refuses when a
    replacement does not match and reads the file back afterwards. The
    previous script printed "corrected" unconditionally and one of its two
    replacements silently matched nothing.

42 focused checks, 0 failures (no new checks this claim; the fix is inside a
path the existing whole-path cases drive).

## REMAINING, exactly, and none started

1. **Bounded ending EXECUTION.** The remaining deadline is recorded; no ending
   sweeps are driven inside it.
2. **Success through the generated documents**: four attempts, BOTH frozen
   verdicts and positive cleanup. The admission-count guard closes the empty
   case only.
3. **ONE runnable bounded entrypoint.** Step 7 names `job`, `control` and
   `composed` without defining them; step 4 serves unbounded.
4. **The affected negative checks** against that entrypoint: no-result,
   deadline, failure and interruption.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249713

**I reported a fix that was not in the file.** Handoff 249700 said the
cancellation went through `baseline._cancel_active`; the reviewer read the
bytes and found `operations.cancel(one)` and "no cancellation port" still
there. They are right, and the cause is worth more than the line.

### How it happened

My edit script did two string replacements and printed "corrected"
unconditionally. One of them — the cancellation block, whose last line had an
odd line-continuation I had written earlier — matched nothing. The other
landed. So the success guard and the signal handler were real, the
cancellation was not, and I passed the Work back describing all three as done
without reading the file afterwards.

`apply_249713.py` cannot do that: it raises when a replacement does not match,
and it reads the file back and refuses if the old call survives or the new one
is absent. Its first run refused for a reason worth keeping too — my "absent"
check was the WORD `operations.cancel`, which also appears in the comment
explaining the fix, so a correct file failed its own check. A check that
cannot tell an explanation from a call is a check that will be disabled.

### What the cancellation now does

Driven over the real deployment it reports, per admitted attempt, a fenced
assignment and a requested stop through the accepted path — which fences the
exact participant and generation at the Authority before ordering quiescence.
The run reports `held`, correctly: only two of four admissions are spent on
that path, and the success rule says so rather than calling it settled.

### Still not done

The remaining deadline is recorded and no ending sweeps are driven inside it;
there is no success through the generated documents with four attempts, both
frozen verdicts and positive cleanup; there is no single runnable bounded
entrypoint; and the no-result, deadline, failure and interruption checks
against that entrypoint do not exist.

### Verification spending

42 focused deterministic checks, 0 failures, measured 10.857s on the module
run that confirmed this fix; no new checks this claim, and no receipt is
claimed for a rerun of unchanged cases.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 =
**47.791708146s**, plus this claim's 10.857s confirming run.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249713" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
