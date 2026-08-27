# Progress: run safe v12 tests across available cores

Implementer: `baton.claude`. Work `W9707`, claimed 2026-08-25.

## Current state — 2026-08-25

Plan items 1-5 are done. Item 6 is the handoff: passing to review with the
evidence below. **This is not a sign-off**, and the canonical `gate` recipe is
deliberately unchanged — replacing it is a separate recorded decision after
review, exactly as item 6 requires.

## Revalidation before implementing (AGENTS.md gate)

The reviewer's pinned inventory was re-checked against the current tree and one
correction was needed. It is recorded in `FINDING.md` under "Implementer
revalidation" and indexed in `PLAN.md`:

- `tests.manager.test_oci_engine` landed in `d36ca47` at 08:57, AFTER the 07:10
  inventory, and was named by neither pinned registry. It drives a real
  Docker/Podman daemon and pulls the pinned base into the shared image store,
  so it joins `tests.manager.test_worker_container` in the mandatory serial
  registry. The parallel-safe set of 28 is unchanged. Recorded as a dated
  CLARIFICATION, not a supersession: the pinned sentence was true of the tree
  it described.
- The pinned "no source test outside `test_worker_container` declares
  `setUpClass`/`tearDownClass`/`setUpModule`/`tearDownModule`" claim was
  re-checked verbatim and still holds, including for `test_oci_engine`.
- The lower-only jobs bound had two caps stated in one sentence; the order they
  compose in is now written down rather than left to the implementation.

## What was built

- `v12/python/tools/parallel_test.py` — standard-library only. Collector
  children report exact `unittest` ids so the PARENT NEVER IMPORTS A TEST
  MODULE; the parent partitions by concrete `TestCase` class with the two
  aggregate boundary-inventory scan classes split one method per shard;
  fresh-interpreter shards run up to a bounded worker count; every shard is a
  process-group leader so an interrupt reaps what the tests themselves started;
  results are structured JSON presented in sorted shard order, with durations
  confined to stderr so stdout stays comparable across worker counts.
- `v12/python/tools/__init__.py`, `v12/python/tests/tools/__init__.py` —
  packages so the tool's own regressions drive the real tool. `pyproject.toml`
  finds packages under `src/` only, so neither travels into the wheel.
- `v12/python/tests/tools/test_parallel_runner.py` — 31 regressions, registered
  in the parallel registry in the same edit so completeness never had a
  transitional exception.
- `v12/python/justfile` — `parallel-test JOBS=''` and `parallel-gate JOBS=''`.
  `gate`, `test`, `version` and `build` are untouched.

## Verification (item 5) — full results in `evidence/parallel-runner-2026-08-25.md`

- **Exact coverage.** 1120 parallel + 44 serial = 1164 collected ids; `unittest
  discover -s tests -t .` collects 1164; `diff` empty.
- **Speed.** Median of three runs each: jobs=1 444.34s at 99% CPU, default
  (32 workers) 117.19s at 460-490% CPU — **3.79x**.
- **The run is at its structural floor.** 118.00s wall against a 117.58s
  longest single shard; the scheduler costs ~0.4s. Six boundary-inventory scan
  methods are ~483s of ~557s total CPU. More cores CANNOT beat ~118s until one
  test method is decomposed, which belongs to the boundary-inventory work and
  was deliberately not attempted here.
- **Result parity.** All six runs: identical 203 shard verdict lines and
  identical 13 failing test ids.
- **Serial registry.** Alone (23.13s) and after the parallel phase (23.19s),
  identical results, one module at a time in registry order. Its 3 failures
  reproduce under the CANONICAL single-process runner, so they belong to W6632
  and W6633.
- **Cleanup.** No surviving containers, images, temp roots or processes.
- **Interrupt on the real tree.** 0 surviving processes, result root removed.
- **Locked installed layout.** `just build` unchanged: 1164 tests, 14 failures,
  2 errors, 5 skips — reconciling EXACTLY with this runner's 14/2/6 once
  `test_dependencies`' deliberate environment-conditional skip is accounted
  for. The new test module passes from site-packages too.
- **Recipes exercised.** `just parallel-test 8` gives jobs=8 and identical
  results; 99, 0, 8.5 and abc are each refused through the documented path.

## Stated limits — these are not covered, and should not be read as covered

1. **`just parallel-gate` was never run as one complete chain.** It cannot
   complete on this tree: the source phase has 13 real failures and the recipe
   fail-fasts there by design. Its three stages were each run individually.
2. **Cross-context Docker exclusion does not exist.** The serial registry
   serializes the two engine-owning modules WITHIN ONE INVOCATION. It cannot
   serialize two invocations, two processes, or two agent contexts sharing one
   daemon. Raised on T6633 and T6632.
3. **Concurrent memory footprint is unmeasured.** `/usr/bin/time`'s maxrss is
   the largest SINGLE process, so the near-identical ~195MB in both columns
   does not mean parallel costs no extra memory.
4. **Killed shards leave test-owned temp directories.** Runner-owned state is
   clean; the tests' own `TemporaryDirectory` finalizers do not run on
   termination. Verified that the canonical gate leaks the same way.

## Discovered and filed, not worked around

`W10265` (kind `bug`, routed to review): the currently-failing v12 assertions
interpolate unordered `set` objects into their failure messages, so their text
reorders every run. Proved against the CANONICAL single-process runner — one
test, two runs, two different md5s — so it is not caused by parallelism, and
those assertions were not touched. It is why the parity evidence compares shard
verdicts and failing ids rather than whole stdout.

## Observed while measuring

Another context modified `tests/manager/test_oci.py` (+39) and
`test_oci_engine.py` (+33) at 09:07, with a new W6632 review at 09:09. Every
measurement was taken after that against ONE tree state whose content hash was
recorded before the matrix and re-verified unchanged after all of it
(`9abe4053ce80b1c3422160cbf5594ac7d1fcd8729ed10f6254bdaba5fe779f7c`). This Work
modified no file owned by another context. Two of the failures in these runs are
that reviewer's new red tests; reported on T6632 as corroboration.

Two corrections to my own measurement method, recorded rather than quietly
fixed: a `pgrep` pattern self-matched its own command line and falsely reported
one surviving shard (walking `/proc` showed zero), and default run 1 predates a
stderr-only duration-logging change, so the six benchmark runs were not all
produced by byte-identical source.

After the benchmark matrix the only source change was removing an unused
`self.stopping` attribute — set, never read, therefore inert. The 31
regressions were re-run afterwards and pass in 3.1s.

## Response to review-2026-08-25T16-21-40Z (changes requested)

### R1 — High: interrupt cleanup could abandon a live shard descendant

**Accepted in full. The review is right, and the reasoning is right.**

Reproduced before touching anything, using the reviewer's own added
regression:

    AssertionError: True is not false : the TERM-ignoring descendant 3327090
    survived the interrupt

The defect was mine and the diagnosis is exact. `Run.shutdown()` popped a shard
from `self.live` as soon as its LEADER exited, and the SIGKILL pass iterated
only what was still in `self.live` — so a descendant that ignores SIGTERM
outlived the runner whenever its leader took the signal first, and the entry
naming its process group had already been discarded. My original interrupt test
used a descendant with the DEFAULT SIGTERM action, which dies on the first
signal, so the test could never reach the ordering that breaks. A leader's death
says nothing about what the tests it started are still doing, and the old code
assumed it did.

**Correction, matching the required shape:**

1. Process-group ids are now recorded at spawn in `Run.groups`, kept beside
   `Run.live` rather than derived from it, so escalation never depends on a
   leader still being alive and never re-derives an id from a process that has
   exited.
2. The SIGKILL pass visits EVERY recorded group, including those whose leader
   already exited.
3. **Nothing is reaped until after the kill pass.** This is the part that keeps
   the signal boundary honest: an unreaped leader is a zombie, and a zombie's
   pid stays reserved, so a group id cannot be recycled onto an unrelated
   group in the window between TERM and KILL. Reaping first is what would make
   the escalation dangerous to processes the runner never created.
4. The bounded grace is a named `GRACE_SECONDS = 3.0`, spent only when there
   are groups to signal — a normal successful run does not pay it.

Accepted cost, stated rather than hidden: an abort always spends the grace
period instead of exiting the moment its leaders die. A zombie leader remains a
member of its own group, so "is this group empty?" cannot be answered by
signalling it; the only early exit available is a `/proc` scan, and that buys a
couple of seconds on a path that only runs when a run is being abandoned.

**Verification after the fix:**

- The reviewer's regression passes, and so does the original cooperative-
  descendant one: `AnInterruptLeavesNothingBehind` 2 tests, OK.
- The complete runner-test module: **32 tests, OK** (was 31 passing + 1
  failing).
- Real-tree re-run: 117.05s at 498% CPU, 203 shards, same 11 failures + 2
  errors + 1 skip, and the failing-id set is byte-identical to the pre-fix run.
- Coverage parity re-proved on the changed tree: runner 1121 parallel + 44
  serial = **1165**, `unittest discover` **1165**, diff empty. The counts moved
  from 1164 because this review added one test, not because anything was lost.
- No orphaned processes and no leftover runner temp roots afterwards.
- `git diff --check` clean.

The reviewer's regression was left exactly as written; I did not weaken or
reword it.

## Response to review-2026-08-25T16-30-55Z (R1 signed off, R2 changes requested)

### R2 — High: an ordinarily exiting failed shard could still orphan descendants

**Accepted in full.** Reproduced with the reviewer's added regression before
changing anything:

    AssertionError: True is not false : the failed shard's descendant … survived the run

This is the same class of mistake as R1 and my R1 fix did not close it. R1 made
`shutdown()` correct; R2 is about the ORDINARY completion path, which never
reaches `shutdown()`. `Run.drive()` dropped a completed leader's group from
`self.groups` as soon as `poll()` reported it, so by the time the phase verdict
existed there was no record of the group at all. A test can start a process,
fail an assertion, and let its worker exit 1 perfectly normally — the runner
reported that failure correctly and left the process running.

**The trap the review named, and how the fix avoids it.** The obvious repair —
keep the PGID, reap the leader, signal the group later — is exactly what the
review warned against, because reaping releases the pid and a released pid
takes its group id with it; a later signal could land on whatever inherits the
number. So the fix does not retain a bare PGID at all. It changes WHEN the
leader is reaped:

1. `Run.has_exited()` replaces `poll()` and asks `os.waitid(..., WNOWAIT)`,
   which reports the exit and LEAVES THE LEADER A ZOMBIE. `poll()` could not
   be used for this question because it reaps.
2. `Run.retire()` then, with the leader still unreaped and its group id
   therefore still provably this runner's, SIGKILLs the group.
3. Only then is the leader reaped and its ownership identity released.

**Cleanup is unconditional rather than verdict-conditioned.** The review asked
that verdict and cleanup both be resolved before ownership is released; always
cleaning up is simpler than that and strictly stronger, because it does not
depend on computing the verdict first — and a passing shard has no more right
to leave a process running than a failing one.

**SIGKILL with no grace, deliberately.** This shard is over; its descendants
are already orphans, not workers being asked to wind down. The graceful
TERM-then-grace path stays in `shutdown()`, where a run is abandoned while
shards are still legitimately working. The two paths now mean different things
on purpose.

**Verification after the fix:**

- `AFailingRunAlsoLeavesNothingBehind` 3 tests OK; full module **33 tests OK**
  (was 32 passing + 1 failing).
- Real-tree re-run: 116.36s at 476%, 203 shards, same 11 failures + 2 errors +
  1 skip. Failing-id set byte-identical to the post-R1 run; the ONLY shard
  verdict line that moved is `AFailingRunAlsoLeavesNothingBehind` going from 2
  tests to 3, which is this review's added regression.
- Serial/Docker phase unchanged: 23.21s, same 3 failures and 5 skips, image
  count 2, no suite containers surviving.
- Coverage parity re-proved on the changed tree: runner 1122 + 44 = **1166**,
  `unittest discover` **1166**, diff empty.
- 0 surviving shard processes, no leftover runner temp roots.

The reviewer's regression was left exactly as written.

## Response to review-2026-08-25T16-39-27Z (R1/R2 accepted, R3 changes requested)

### R3 — High: retirement deleted both cleanup handles before signalling

**Accepted in full**, and implemented exactly as prescribed. Reproduced first:

    AssertionError: True is not false : the descendant … survived an interrupt during retirement

The rule the review states — *the state mutation must follow the cleanup side
effect, not precede it* — is the correct general statement of what R1, R2 and
R3 all are. `retire()` now uses `groups.get()`, issues the SIGKILL while the
group is still registered, releases the group entry only afterwards, then reaps
and only then does `drive()` release the `live` entry. There is no instant at
which a descendant is alive and untracked:

    groups[child] still set    -> shutdown() TERM/grace/KILLs the group
    signal issued, entry gone  -> group already dead, later handler is a no-op
    live[child] still set      -> shutdown() still reaps the leader

**Verified:** `AnInterruptLeavesNothingBehind` 3 tests OK; full module **34
tests OK**. Real tree 115.06s at 461%, 203 shards, same 11 failures + 2 errors
+ 1 skip, failing-id set byte-identical to post-R2. Coverage parity re-proved:
runner 1123 + 44 = **1167**, `unittest discover` **1167**, diff empty.

### R4 — found by me while auditing for more of this class, NOT yet fixed

Since this is the third finding of one family, I probed the remaining
state/side-effect transitions myself instead of waiting. **There is a fourth
instance, on the SPAWN side, and it is demonstrated rather than suspected.**

In `Run.drive()`:

    child = self.suite.spawn(item["argv"], item["err"])   # process exists, owns a group
    self.live[child] = item                               # <- window
    self.groups[child] = self.group_of(child)             # <- window

A signal delivered between `spawn()` returning and those two registrations
finds `shutdown()` blind, exactly as in R3. Demonstrated with the reviewer's
own injection technique — wrapping `Suite.spawn` to raise SIGINT inside the
window, after the shard's descendant has published its pid:

    runner exit=130
    [runner] signal 2; terminating 0 live shards
    ORPHANS after the runner exited: 2
       the shard leader itself, and its TERM-ignoring descendant

A first attempt at this probe reported 0 orphans and I did not report that as a
pass: the shard had died incidentally because `shutdown()` removed the result
root containing its plan file before it could read it. That is luck, not
cleanup, and widening the window showed the real behaviour.

**Why it is not fixed in this round.** Unlike R1-R3 this one cannot be closed
by ordering, because the registration cannot precede the `Popen` that produces
the object being registered. It needs one of:

1. **Deferred signal handling** (preferred). The handler records the signal and
   returns; the scheduler loop checks the flag at a safe point and raises. Every
   state transition then becomes atomic with respect to cleanup, which closes
   this whole family rather than its fourth instance. All paths return to the
   loop within the bounded `child.wait(timeout=5)`, so response stays prompt.
   Cost: a second Ctrl-C no longer short-circuits, and cleanup runs microseconds
   later than it does today.
2. `pthread_sigmask` around the critical section — REJECTED on inspection.
   CPython restores the parent's pre-`Popen` mask in the child, so shards would
   inherit blocked SIGINT/SIGTERM and stop honouring the TERM phase. Avoiding
   that needs `preexec_fn`, which is thread-unsafe and discouraged.
3. A `/proc` sweep for the runner's own children in `shutdown()` — narrows the
   runner from POSIX to Linux and widens the signal boundary from "groups I
   recorded" to "processes that look like mine", which cuts against the rule
   this review has been holding me to.

I am proposing (1) but have NOT implemented it, because it changes the signal
architecture the reviewer is actively mid-review on, and because R3's prescribed
correction should be reviewable on its own. Say the word and it is a small
change. Sitting on a demonstrated defect would be worse than either, which is
why it is written down here.

## Response to review-2026-08-25T16-49-30Z (R1-R3 signed off, R4 approved)

R4 was independently confirmed and deferred signal handling approved as the
in-scope correction. Implemented.

**The handler now records and nothing else.** `Run.record_signal()` sets
`pending_signal` and returns; it reads and mutates no scheduler state, because
it can run between any two bytecodes — including the two that register a
freshly spawned shard. `Run.checkpoint()` raises `Interrupted` only where
`live` and `groups` describe every process the runner has actually created.

**Safe points cover the family, not the injected line.** Registration of a
spawned child is never interruptible work: a signal landing anywhere inside it
is merely recorded, both lines complete, and the checkpoint that follows sees
the real picture. There is a second checkpoint after the retirement batch, so
no group is half-released and no leader half-reaped when cleanup runs. The
idle scheduler is covered by the same first checkpoint, because the sleep path
returns straight to it.

**Both revalidation requirements were proved, not assumed.**

*Signal during final cleanup, on a run that otherwise SUCCEEDED* — probed by
wrapping `Run.shutdown` to raise SIGINT on entry:

    [summary] parallel source: 1 tests, 0 failed, 0 skipped | … -> OK
    [runner] interrupted by signal 2 during cleanup
    exit=130          (not 0)
    TMPDIR empty      (bounded cleanup still completed)

Writing that probe found a second-order bug in my own first attempt: I had
restored the original handlers BEFORE `run.shutdown()`, so a SIGINT during
cleanup would take the caller's default disposition and raise KeyboardInterrupt
through the middle of the bounded cleanup — abandoning the kill pass and the
result root. The `finally` now runs `shutdown()` with recording still armed and
restores handlers afterwards in a nested `finally`. That is what makes "a
second signal need not bypass the bounded cleanup" true rather than intended.

*Signal never reached by a checkpoint* — the post-cleanup check converts a
still-pending signal into `128 + number`. A run that already FAILED keeps its
own code: the failures are the more informative answer, and 1 is not a success
being papered over.

*Idle scheduler* — covered by the existing R1 regression, which interrupts
while a shard sleeps.

**Verified:** `AnInterruptLeavesNothingBehind` 4 tests OK; full module **35
tests OK**. Real tree 115.66s at 461%, 203 shards, same 11 failures + 2 errors
+ 1 skip, failing-id set byte-identical to post-R3. Serial/Docker phase
unchanged: 44 tests, 3 failures, 5 skips, image count 2, no suite containers.
Coverage parity re-proved: runner 1124 + 44 = **1168**, `unittest discover`
**1168**, diff empty. 0 surviving shard processes, no leftover temp roots.

## Review state

**R1, R2 and R3 signed off. R4 addressed, awaiting re-review.** Passing back to
`baton.feat` (rview). Not closed by the implementer.

The four "Stated limits" above still stand unchanged — `just parallel-gate` is
still unproved as one complete chain, cross-context Docker exclusion still does
not exist, concurrent memory is still unmeasured, and killed shards still leave
test-owned temp directories as the canonical gate does.

Everything in "Stated limits" above still stands unchanged — in particular
`just parallel-gate` is still unproved as one complete chain, and cross-context
Docker exclusion still does not exist.

One portability note now worth recording: `os.waitid` and `WNOWAIT` make the
runner explicitly POSIX-only. It already was in practice — `os.killpg`,
`os.getpgid` and `start_new_session` are all POSIX — but this is the first
place that dependency is load-bearing rather than incidental.
