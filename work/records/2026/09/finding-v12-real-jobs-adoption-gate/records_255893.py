"""Claim-255893: the resumed old declaration recovers; a deleted case is back."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255893; RETURNED INCOMPLETE

Review 2026-09-24T10:11:35Z raised a P1 against my first cut of Correction A
and it was right. It is corrected, with the positive outcome the owner
selected rather than another characterization.

## The P1 — declaration-first cancellation stranded recovery

My first cut chose the declaration's signed fence operand from the world AS IT
STANDS NOW. So an abandonment interrupted after `_abandon_intent` committed
under `own_fence`, and cancelled afterwards, had its next identical request
compose a DIFFERENT operand at the same `attempt.abandon:` identity and refuse
at §4.2 with the cleanup still absent. I had called that closed "by the
journal's own rule"; the reviewer's reply is exact — "keeping the identity
derivation function unchanged does not preserve its selected operand when the
call site now chooses a different identity."

**The record decides the operand; the world decides the fence.** Two separate
facts, and they are now separated:

  * **`_declared_fence_identity`** reads a COMMITTED declaration's own operand
    back and hands it to `_abandon_intent`, which then signs and validates
    exactly what was written. Only a declaration that does not exist yet is
    free to choose. Nothing is overwritten and no signature check is weakened
    — every other member of that record is still compared against the live
    attempt, and a resumed call naming a different REASON still refuses.
  * **The fence** is chosen from the separately validated cancellation record:
    when one exists, the generation is fenced by REPLAYING that Authority
    operation with its own reason. `port.cancel` is still called and
    `_abandoned_fence` still owns the answer, so nothing is inferred from a
    record.

So a declaration committed before any cancellation — including one interrupted
and resumed long afterwards — keeps its bytes and still ends.

## And I deleted a case, then put it back

An edit this claim sliced from one case name to the next and took
`test_the_preserved_runs_shape_now_has_exactly_one_door` with it. The suite
still passed at 19, which is exactly how a silent coverage loss looks. It is
restored, with a note in its own docstring saying why it went missing.

## Evidence — 28 focused cases, all passing

`test_abandonment.py` (20) and `test_routed_abandonment.py` (8), **1.677s**,
clean under `-W error::ResourceWarning`. New this claim:

  * **the older persisted shape** — a declaration committed under `own_fence`
    by a call that never reached the fence, then a cancellation, then a retry:
    it settles `retained` with `state: absent`, discharges its gate, and the
    old journal record's RESULT BYTES AND SIGNATURE ARE BYTE-IDENTICAL before
    and after. A repeat replays with identical effect counts;
  * **a resumed declaration naming another reason still refuses** at §4.2 with
    nothing changed;
  * **the routed prior-cancellation recovery** — the same history through the
    pooled router and the stage's own mounts.

Accepted suites over the changed file: `test_abandoned_attempt_engine`,
`test_intake`, `test_attempts`, `test_refused_session_cleanup`,
`test_failed_start_destroy`, `test_runtime_deadlines` and
`tests.tools.test_single_worker` — **899 tests, OK, 19.828s**.

## REMAINING

  1. first-call crash and launch-absent alternate recovery;
  2. the unpooled altered-context gap, which cannot close the way the routed
     one did because no allocation record exists there;
  3. the supervisor's explicit shutdown declaration;
  4. the two operator grants documents with validation and readback;
  5. the executed-image fault diagnosis;
  6. a new digest-bound manager snapshot, then exact recovery and fresh-run
     commands.

## Standing constraints

No deployed mutation, live rerun or cleanup execution. The preserved instance
and the pinned snapshot are read-only. Recovery of the preserved run is
PREPARED, not performed.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py` and
`src/baton_v12/worker_manager/intake.py`. `attempts.py`, `deadlines.py` and
`authority/` were not edited and no new shared reader was added.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255893

### You were right and my "already closed" was wrong

I claimed the declaration-first-then-cancelled interleaving was closed by the
journal's own §4.2 rule. It was closed the way a locked door closes a corridor:
the cleanup stayed absent and the attempt stayed stuck. Your sentence is the
one that landed — keeping the derivation unchanged does not preserve its
selected operand when the call site now chooses a different identity.

The fix separates two facts I had let merge. The RECORD decides the fence
operand a declaration signed: `_declared_fence_identity` reads a committed
declaration's own operand back, so a resumed call signs exactly what was
written and old bytes are reused rather than recomposed. The WORLD decides the
fence: when a validated cancellation exists, the generation is fenced by
replaying that Authority operation with its own reason. Neither infers
anything — `port.cancel` is still called and `_abandoned_fence` still owns the
answer.

The test proves the bytes: the declaration's journalled result and signature
are compared before the cancellation and after the ending, and they are
identical.

### I deleted a test and did not notice

An edit sliced from one case name to the next and took
`test_the_preserved_runs_shape_now_has_exactly_one_door` with it. The suite
went on passing at 19, which is exactly what a silent coverage loss looks like;
I only saw it because I listed the case names. It is restored and says so in
its own docstring. That is the second time a name-to-name slice has cost me
something — the first broke a product file three claims ago.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 28 cases, all passing,
**1.677s**, clean under `-W error::ResourceWarning`; intermediates this claim
1.057s, 1.557s, and routed-only 0.606s.
The accepted suites over the changed file, together — **899 tests, OK,
19.828s** (`test_abandoned_attempt_engine`, `test_intake`, `test_attempts`,
`test_refused_session_cleanup`, `test_failed_start_destroy`,
`test_runtime_deadlines`, `tests.tools.test_single_worker`).

The 424-case stage-execution suite was NOT repeated. Everything prior stands:
159.910s plus its untimed repeat, 0.966s, 1.170s, 10.041s, 9.966s, 0.348s,
0.130s, 9.308s, 10.337s, the combined 1.090s / 1.334s / 1.536s, the focused
0.632/0.701/0.371/0.772/0.800/0.803/0.904/0.917/0.937/1.118/1.364/1.378/1.424/
0.480s runs, the earlier focused and product-suite times, the untimed probes
and diagnostic reads, the unmeasured ~120s command-timeout run and the earlier
unknowns, alongside named **1047.869180986s**.

State: returned INCOMPLETE through baton.bug with the P1 corrected positively,
the deleted case restored, and the non-abandonment packet still open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255893" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
