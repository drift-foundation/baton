"""Claim-249845: the provenance nothing recorded, now recorded at the launch."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249845

## Done under claim 249845

  * **The gate records the provenance a verdict read needs.** `generations`
    and `stage_of` were read through `getattr` DEFAULTS and nothing ever wrote
    them, so the public attachment reader was handed `generation=None` and
    refused, and `job_of` answered None. A reader with a default for a fact
    nobody records answers "unknown" quietly. `launch` now records the stage
    and the assignment generation AT THE CALL, before delegating — the same
    discipline the inherited gate uses for the launch itself — and both are
    real attributes rather than defaulted lookups.
  * A focused case drives `admit` then `launch` on the gate and asserts
    `generations`, `stage_of`, `job_of` and the recorded kind.

44 focused checks, 0 failures, measured 11.682510098995408s,
`verification-11.json`; 1 is new.

## REMAINING — still one coherent piece

The generated-document success and the negatives that contrast against it:

1. A **worker-turn seam** so review stages can complete inside a supervised
   run; the accepted fixture drives its deterministic turn OUTSIDE `serve`.
2. A **disposable credential provider and registry** at the normal boundary.
3. The success case (four attempts, both frozen verdicts, positive cleanup),
   then `main`'s no-result, deadline, failure and interruption checks.
4. **Operator steps 4 and 7**, replaced by the one tested bounded command,
   and this module's own docstring, which still says it "does not run
   anything" — it does now.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249845

### A reader with a default for a fact nobody records

`TwoJobGate.generations` and `stage_of` were `getattr(self, "_generations", {})`
and `getattr(self, "_stage_of", {})`, and no code ever assigned either. So the
public attachment reader received `generation=None` and refused, `job_of`
answered None, and `verdicts_of` quietly derived nothing — with the refusal
landing in `uncertainty` rather than anywhere a reader would look first. I
wrote the readers and the consumer in the same claim and never wrote the
producer.

`launch` now records the stage identity and the assignment generation AT THE
CALL, before delegating — the same discipline the inherited gate uses for the
launch itself, and for the same reason: a fact reconstructed from a projection
between ticks can be lost. Both are real slots now, so a future read of an
unrecorded fact is an `AttributeError` rather than a silent empty map.

A focused case drives `admit` then `launch` and asserts all four answers.

### What is still one piece of work

The generated-document success needs the worker-turn seam and a disposable
credential provider; the four `main` negatives contrast against it; and then
operator steps 4 and 7 — plus this module's own docstring, which still says it
"does not run anything" and no longer should.

### Verification spending

44 focused deterministic checks, 0 failures, measured 11.682510098995408s,
receipt `verification-11.json` with `verification-11.log`; 1 is new.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 + 11.520278754 + 11.597300884 +
11.682510099 = **115.767964242s**. The reviewer's 0.203372271s diagnostic is
theirs and stays in their evidence.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249845" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
