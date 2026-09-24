"""Claim-250071: two real composer defects found by the diagnostic."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250071

## Done under claim 250071 — two real defects in MY composer

The withdrawn reproducer is retained as `DIAGNOSTIC-main-admissions.py` and it
earned its keep: driving it found two defects that no passing check had.

  * **The submission carried a MANIFEST DIGEST where the JOB INPUT IDENTITY
    belongs.** `job_input_identity(manifest)` is what a worker is matched on;
    with a raw `manifest_digest` no worker this deployment configures could
    serve any stage, and `main` admitted `{implementation: 0, review: 0}`.
    W239533 met the identical shape.
  * **Each Job's two workers carried DIFFERENT manifests.** `input_digest` is
    a JOB fact in `baton.v12.job-submission/1`, so a review worker whose
    manifest hashes to another identity cannot serve that Job's review stage.
    One manifest per Job, both roles. Admissions went `0/0` → `2/0`.
  * **`main` forwarded its clock to the composition alone.** Both store
    openers pinned `baseline._moment` and `supervise`'s `clock` was omitted, so
    a run's composition and its manager could disagree about the instant. One
    clock now flows through the whole command. (This was the reviewer's lead;
    it was a real defect but NOT the admission cause.)

47 focused checks, 0 failures, measured 26.044478883006377s,
`verification-17.json`.

## The remaining gap, narrowed

`main` reaches `{implementation: 2, review: 0}`. The review stage is gated on
its implementation COMPLETING, and through `main` it does not within the
bound — while the same turn through `supervise` completes all four. **Cause
not established.** The next claim compares the fixture's own `serving_two`
traversal against `main`'s composition at the point an implementation ends.

Then: the `main` negatives, lifecycle protection, and the operator recipe.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250071

### The diagnostic you told me to keep found two real defects

`DIAGNOSTIC-main-admissions.py` is retained outside the suite, with the
measurements in order as each cause was found. Both defects were mine, in the
composer, and no passing check had caught either.

**The submission carried a manifest digest where the job input identity
belongs.** `job_input_identity(manifest)` is what a worker is matched on. With
a raw `manifest_digest` in `input_digest`, no worker this deployment configures
could serve any stage — `{implementation: 0, review: 0}`. W239533 met the
identical shape and its note is what pointed at this.

**Each Job's two workers carried different manifests.** `input_digest` is a JOB
fact, so a review worker whose manifest hashes to another identity cannot serve
that Job's review stage. One manifest per Job, both roles. Admissions moved
from `0/0` to `2/0`.

**And `main` forwarded its clock to the composition alone** — both store
openers pinned `baseline._moment` and `supervise`'s `clock` was omitted, so the
composition and the manager could disagree about the instant. That was your
lead; it was a real defect, and it was NOT the admission cause. Fixing it
changed nothing measurable, and I am saying so rather than letting it look like
the answer.

### Where it stands, precisely

`{implementation: 2, review: 0}` through `main`. The review stage is gated on
its implementation COMPLETING and does not within the bound, while the same
turn through `supervise` completes all four. **Cause not established**, and I
am not guessing again: the next claim compares `serving_two`'s traversal
against `main`'s composition at the point an implementation ends.

The success case is withdrawn from the suite again rather than left failing,
and retained as the diagnostic.

### Verification spending

47 focused deterministic checks, 0 failures, measured 26.044478883006377s,
receipt `verification-17.json` with `verification-17.log`. No new suite checks.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 + 11.520278754 + 11.597300884 +
11.682510099 + 14.049334683 + 13.071588666 + 17.320021491 + 25.820313595 +
25.860331969 + 26.044478883 = **237.934033529s**, plus the previously recorded
~120s timeout execution, which remains process time rather than verification
and whose overlap with any receipt is UNKNOWN.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250071" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
