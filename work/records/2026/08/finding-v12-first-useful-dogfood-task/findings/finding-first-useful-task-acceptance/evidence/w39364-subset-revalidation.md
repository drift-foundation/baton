# The frozen delivered subset does not carry the task's own verification

`baton.claude`, 2026-08-30, W39364 PLAN item 1 ("revalidate the accepted
operator command and parent frozen-task evidence"). Measured, not read.

## What was measured

The parent's `evidence/first-task.md` freezes a "Delivered source subset" of
three repository-relative paths and a verification command run "from the
delivered source root":

    v12/spike/ping-pong/preflight.py
    v12/spike/ping-pong/trial.py
    v12/spike/ping-pong/test_harness.py

    python3 v12/spike/ping-pong/test_harness.py

Staged exactly that subset into a clean root and ran exactly that command:

    $ mkdir -p /tmp/w39364/subset/v12/spike/ping-pong
    $ cp <three paths> /tmp/w39364/subset/v12/spike/ping-pong/
    $ cd /tmp/w39364/subset && python3 v12/spike/ping-pong/test_harness.py
    Ran 26 tests -- FAILED (errors=11), exit 1

    FileNotFoundError: [Errno 2] No such file or directory:
      '/tmp/w39364/subset/v12/spike/ping-pong/trial.mjs'

Eleven of the twenty-six cases -- the whole
`AWriteDeniedSomewhereIsNotAWriteDeniedHere` class -- error before the worker
contributes anything. `test_harness.py:402` reads a FOURTH file:

    source = (HERE / "trial.mjs").read_text(encoding="utf-8")

That class tests the JS trial's write-denial classifier, so it lifts the
classifier out of `trial.mjs` and evaluates it with `node`. The two Python
modules in the subset are loaded by path at `test_harness.py:38-39` and are
correctly named; `trial.mjs` is the omission.

Adding the one missing path makes the command pass on the delivered subset:

    $ cp v12/spike/ping-pong/trial.mjs /tmp/w39364/subset/v12/spike/ping-pong/
    $ cd /tmp/w39364/subset && python3 v12/spike/ping-pong/test_harness.py
    Ran 26 tests -- OK, exit 0

## The second precondition, named because it is not obvious

The same eleven cases need `node` ON PATH, not just `trial.mjs` on disk:

    $ cd /tmp/w39364/subset && env PATH=/usr/bin:/bin python3 \
        v12/spike/ping-pong/test_harness.py
    Ran 26 tests -- FAILED (errors=11)

This one is SATISFIED on both sides and is recorded so nobody has to
rediscover it. The dogfood image is `FROM node:22-bookworm-slim`
(`v12/worker/Dockerfile.claude`), so the worker's in-container verification has
node; the operator's independent rerun host has node v24.14.0. A future image
whose base loses node would break this task's verification without touching
the task.

## Why this blocks rather than being fixed here

`evidence/first-task.md` is the PARENT's frozen artefact and W39364's own
FINDING says to use it VERBATIM. An implementer amending the frozen subset
would be selecting the delivery the milestone is supposed to measure. Two
consequences follow from the measurement, and both are the parent's to rule
on:

1. The worker's `proposal/verification.txt` would report exit 1 for a reason
   the worker did not cause, on a task whose stated objective it may have
   completed correctly.
2. W39364's acceptance requires "a reviewer independently ... runs
   `python3 v12/spike/ping-pong/test_harness.py` outside the worker". On the
   frozen subset that command cannot pass, so the criterion is unsatisfiable
   as written.

The narrowest correction consistent with the task's stated objective is to add
`v12/spike/ping-pong/trial.mjs` to the delivered subset -- a fourth read-only
path, no change to the objective, the required behaviour, the prohibitions or
the verification command. Whether to take it is the parent's call.
