"""Claim-250210: the single-runtime fake, and a success that did NOT reproduce."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250210

## Done under claim 250210

  * **The witness used a SINGLE-RUNTIME fake for a concurrent run.** Review
    2026-09-23T18:56:28Z: `tests/tools/test_single_worker.Engine` answers
    `runtime-single-1` for EVERY run and overwrites its one labels/mounts
    record, and `main` was handed ONE instance — so two concurrent launches
    collided and one delivery went missing. That is the incompatible boundary,
    and it is in my witness.
  * It now supplies the ACCEPTED two-Job fixture's own engine, which models
    SEVERAL live containers. **No runtime identity is weakened anywhere**; the
    single-runtime fake is simply the wrong instrument for two.

## THE HONEST RESULT: a success observed ONCE, which did NOT reproduce

With the multi-runtime engine, the diagnostic printed
`DIAGNOSTIC-250210-SUCCESS.log`:

    admissions {implementation: 2, review: 2}
    verdicts   [job-a, job-b]
    state      settled

**Three subsequent runs of the identical command reported
`{implementation: 2, review: 0}`, `state: held`** —
`DIAGNOSTIC-250210-SECOND.log`. The suite case written against the success also
failed at `2/0` and was withdrawn again rather than left failing.

So the engine was a real defect and its correction changed the behaviour, but
**the result is not stable and I am not claiming the success.** Something
between runs differs — the shared disposable root accumulates state across
runs, which is the first thing to rule out, and I have not.

## REMAINING

Reproducibility first: make the diagnostic's root fresh per run and see which
result is the real one. Then the `main` success as a suite case, its
negatives, lifecycle protection, the generation regression through `main`, the
operator recipe, and the diagnostic's import pinning and `status(None)` gaps.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250210

### The wrong instrument for two runtimes

`test_single_worker.Engine` answers `runtime-single-1` for every run and
overwrites its single labels/mounts record. `main` was handed ONE instance, so
two concurrent launches collided on one runtime identity and one delivery never
materialised — the missing directory from last claim. The reviewer found it by
reading the fake; I had been reading the manager.

The witness now supplies the accepted two-Job fixture's own engine, which
models several live containers. No runtime identity is weakened; the
single-runtime fake was simply the wrong instrument.

### A success I am NOT claiming

The first run with that engine settled: four admissions, both verdicts,
`state: settled`, retained as `DIAGNOSTIC-250210-SUCCESS.log`. It looked like
the end of this thread.

**Three further runs of the identical command reported `2/0` and `held`**
(`DIAGNOSTIC-250210-SECOND.log`), and the suite case written against the
success failed the same way and was withdrawn rather than left failing.

One passing observation out of four is not a proof; it is a non-deterministic
witness. The engine correction was real and changed the behaviour, and that is
all I will say about it. The obvious first suspect is the shared disposable
root accumulating state between runs — the diagnostic reuses
`/var/tmp/baton-w247941` — and ruling that out is the next claim's first act,
before any success is claimed again.

### Verification spending

Suite green at 26.174s on the confirming run; no new receipt.
`verification-17.json` (47 checks, 0 failures) stands.

Cumulative MEASURED for W247941, adopting the reviewer's arithmetic:
**315.986033529s**, plus the identified diagnostics (1.586s, 1.592s) and this
claim's runs, plus the earlier ~120s timeout execution whose overlap remains
UNKNOWN.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250210" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
