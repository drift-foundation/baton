
## Review round — log containment (2026-08-18, `baton.claude`)

The P1 finding is correct and is fixed. I hold this Work as implementer; the
prior implementation was `baton.tune`'s, and I changed only `_open_log` and the
tests around it.

### Reproduced first

Before touching anything: a symlink at `MAILBOX/log/<service>.log` pointing at
a writable 0600 regular file is FOLLOWED by the open, passes both descriptor
checks — same type, same mode, different file — and the controller appends its
launch boundary and the child's output into the target, then starts the service
successfully. Measured directly, with the target's contents afterwards showing
the appended text.

### The fix, and why it belongs at the open

`O_NOFOLLOW`. Validating the descriptor afterwards cannot help: by then the
open has already followed the link, and every remaining property matches. The
open is the last moment the distinction between "the mailbox's log" and
"somebody else's file" still exists.

The descriptor checks stay, as the review requires. They answer a different
question — is this the KIND of file a private log may be — and had no coverage
at all, which the sweeps below made visible.

### Two more holes in the same function

Both are the reviewed defect through a different primitive, and I judged them
in scope because the ruling's boundary is mailbox-local log OWNERSHIP rather
than the symlink mechanism specifically. Flagging them explicitly so the
reviewer can disagree.

**A hard link.** `O_NOFOLLOW` cannot see one, and the descriptor is a private
regular file by every measure — it is simply also somebody else's file. Left
open, the outcome is identical to the symlink case: the controller appends into
an unrelated file and starts the service. The mailbox's own logs have exactly
one name, including across restarts, so refusing `st_nlink != 1` costs nothing
legitimate — and a test proves that, rather than my asserting it.

**A FIFO could not be refused at all — it HUNG.** Opening a FIFO for writing
waits for a reader, and that wait happens before any descriptor check runs, so
`start` sat there indefinitely with no diagnostic. This surfaced as a timeout
in my own FIFO test, whose docstring had predicted the refusal, not the hang.
The open is now non-blocking, which turns it into an immediate `ENXIO`, and the
flag is cleared with `F_SETFL` before the descriptor is used so the one the
child inherits is an ordinary blocking descriptor exactly as before.

### Regressions

Six added beside the review's own, all in
`tests/work/test_w20_infrastructure_lifecycle.py`: a hard-linked log; a symlink
to a directory; a DANGLING symlink (the dangerous case in waiting — with
`O_CREAT` and no `O_NOFOLLOW` the open CREATES the target, so the test also
asserts the target was not created); a group-readable log; a FIFO; and one
positive test that an ordinary run's log is a single-named private regular file
and stays one across a restart that appends to it, so the link guard is proved
to cost nothing.

Every refusal case also asserts the service did NOT launch, via the fake
service's own event file.

### Break-sweeps

| Removed guard | Result |
| --- | --- |
| `O_NOFOLLOW` | 2 red |
| `st_nlink != 1` | 1 red |
| `O_NONBLOCK` | 1 red (a 20s timeout, not an assertion) |
| The private-regular-file descriptor check | 1 red |

All four are load-bearing, which was not true before: the descriptor check the
review told me to RETAIN was passing vacuously, and I only learned that by
sweeping it.

### Gate

`just test-v11`: **1473 passed**, serial **36 passed**, ACP **41/41**, Codex
bridge **44/44**. `py_compile` and `just --list` clean; the three recipes are
present.

This is the first fully green gate in several turns — the failure that had been
red throughout was this Work's own containment regression.

### Still outstanding, and not mine to do

The acceptance-pinned live four-service smoke. It is operator-owned, and the
review's condition for running it (the containment regression green) is now
met. I did not run it and should not: stopping the live set would terminate the
ACP bridge session this participant is running inside, and the manifest names
the deployment's real release, thread and policy paths. It needs a human at a
terminal that does not depend on the services being stopped.

## Review round — socket readiness is a connection (2026-08-18)

The P1 is correct and was already repaired before this review reached me: I hit
the reviewer's regression on the shared gate during W48, fixed it, and reported
it on T20. This round covers the parts the reviewer's single test does not
reach, and one of those exposed two tests of mine that passed for the wrong
reason.

### The defect

`_ready` treated a Unix service as ready when `os.stat` said the pathname was a
socket. That proves the inode TYPE, not that anything is listening — while the
http probe beside it makes a real request. So the two readiness kinds disagreed
about what readiness means, and an owned process outliving its listener
reported the whole set healthy with exit zero.

It connects now, bounded at 0.25s, and closes immediately. That is the same kind
of contact the http probe already makes against a live service.

### Expected refusals versus being unable to ask

The review asks that `ENOENT` and `ECONNREFUSED` be not-ready and that
"unexpected errors should remain a clear non-ready/refusal", pointing at the
event bridge's own handling. That bridge distinguishes the two; my first repair
did not — it swallowed every `OSError` as not-ready.

The distinction matters and now exists. Connection-refused and no-such-file are
ANSWERS: nothing is listening, or there is no path. Anything else is the
controller unable to ASK, and reporting `unhealthy` for that would assert a
state it has not proved — the same defect as blessing an inode, one layer up. It
refuses by name with the errno instead, so the operator can tell "the service is
down" from "I could not look".

### Two of my own tests passed for the wrong reason

My first startup-half tests pre-created an inert socket inode before `start`.
Both passed — and kept passing under a sweep that restored the `stat` probe,
which should have been impossible. Investigating: a pre-existing inode trips the
SEPARATE refusal-to-adopt-pre-existing-readiness guard, so `start` refused
either way and the assertions matched both messages. The tests proved the
controller refuses something, not that the probe works.

The reachable construction is a service that binds without listening — which is
also the realistic shape, a dispatcher whose listener died while the process
lives. The fake service gained a `--bind-only` flag for it, and both tests now
assert WHY the refusal happened (`failed readiness`) and prove the service
actually launched, so a build that blessed the inode cannot pass them.

One smaller error in the same tests: I asserted `"ready" in error`, which is
false for the message "failed readiness" — there is no `y` in `readiness`. A
substring assertion that cannot match is a test that only ever fails for its own
reasons.

### Regressions

Five added beside the review's own: startup refuses a bind-without-listen
service; a DEPENDENT service never starts behind one, which is the consequence
the review names; a live listener stays ready across four repeated `status`
probes, so the connect-and-close does not itself break health; an unprobeable
path refuses by name rather than reporting unhealthy; and the reviewer's status
case is retained.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| `stat` the inode again | 4 red (status, startup, dependent, unprobeable) |
| Swallow every error as not-ready | 1 red |

The first sweep red only 2 tests before the startup tests were rewritten. That
gap is the whole reason this section exists.

### Gate

`just test-v11`: **1578 passed**, serial **36 passed**, ACP **41/41**.
`py_compile` clean.

### Still outstanding, and still not mine

The live four-service smoke. Both of this Work's health-truth regressions are
now green, which was the review's condition, so it is unblocked — but it
remains a human step: stopping that set would terminate the ACP bridge session
this participant runs inside.

## Review round — the lifecycle lock (2026-08-18)

The P1 is correct, and it is the same containment defect as the service log,
on a sibling I did not sweep when I fixed the log. That is the finding worth
recording, more than the repair itself: this Work has now had one defect
reported against two different files, one at a time.

### The repair

`MailboxLock.__enter__` opened `run/infra.lock` and checked only the mode, so a
symlink to any private regular file was followed and a hard link accepted — and
the controller then took its advisory lock on an inode the mailbox does not
own, where lifecycle commands could block behind or interfere with an unrelated
lock domain. It is now validated before `fdopen` or `flock`.

### One rule, stated once

Rather than a third copy of the four flags, `_open_owned()` states the
mailbox-owned-file discipline in one place and the lock, the logs and the
lifecycle-state read all go through it. Each part closes a hole the others do
not, and the docstring says which:

- `O_NOFOLLOW` — validating afterwards cannot help; the open has already
  followed, and a link to another private regular file matches every remaining
  check;
- `O_NONBLOCK` — a FIFO's open waits for a peer BEFORE any check can refuse it,
  so without this the controller hangs with no diagnostic;
- type and mode — a directory or group-readable file is not a private file
  whatever its name;
- `st_nlink` — a hard link defeats `O_NOFOLLOW` entirely.

A future mailbox-owned file gets the contract by calling the helper rather than
by remembering four flags. `test_every_mailbox_owned_file_shares_one_containment_rule`
holds both halves: the rule keeps its four guards, and every owner goes through
it instead of opening for itself.

### The sibling I swept for, and what it actually was

I checked the lifecycle-state read expecting the same hole. It was not:
`_load_state` already `lstat`s the path and refuses a symlink and a
group-readable mode before reading. What it did not cover was a HARD link,
which `lstat` cannot see, and the window between that check and the open. Both
are closed now, and the `lstat` guard stays because it is reached first and
says plainly what is wrong.

I had written the code comment and the test claiming the symlink case was a
fresh hole. It was not, and reporting it that way would have been a false claim
about my own change — the test now says which half was already closed and which
was not.

### Break-sweeps

| Removed guard | Result |
| --- | --- |
| `O_NOFOLLOW` | 3 red |
| `st_nlink` | 3 red |
| `O_NONBLOCK` | 1 red (a 24s timeout, not an assertion) |
| type and mode | 4 red |

### Gate

`just test-v11`: **1666 passed**, serial **38 passed**, ACP **41/41**.
`py_compile` clean.

### Still outstanding, still not mine

The live four-service smoke. Its blocker — this containment regression — is
green, but it remains a human step: stopping that set terminates the session
this participant runs inside.

## Review round — the owned process group (2026-08-18)

The P1 is correct and is the sharpest finding on this Work so far, because the
controller was not merely missing a case: it was *accounting for one process in
a group it had created*, and reporting success on that basis.

### The defect

Every service launches with `start_new_session=True`, so the recorded pid leads
a session and process group that exist only because the controller made them.
`_terminate` signalled the leader through its pidfd and waited for that one
process. A managed service that spawns a child — which the deployed ACP bridge
does for its agent — left that child running while stop removed the service
from lifecycle state and reported success.

### The repair, and the boundary it keeps

Termination signals the GROUP, and only after the existing fail-closed identity
check passes. Two conditions gate the broadening, and both matter:

- the pidfd is opened FIRST and the recorded argv and start ticks rechecked
  through it, so a reused pid refuses before anything is signalled;
- the leader must really be its own group AND session leader — which is what
  `start_new_session` makes, and what distinguishes a group the controller
  created from one it merely joined. When it is not, only the recorded process
  is signalled. Broadening there would reach a group this controller does not
  own, which is worse than leaving a child behind.

This never enumerates or discovers processes. It asks the kernel about one
group id, and holding the pidfd is what stops that id being recycled underneath
the question.

After the leader exits, the group is waited on within the same bounded timeout
and the service stays in lifecycle state, reported as `group-did-not-exit`, if
anything remains. A service is not stopped while a child it started is running.

### The zombie, which cost the first attempt

The first repair broke rollback. On that path the services are still this
controller's own children, so the exited leader becomes a ZOMBIE — and a zombie
is a live member of its process group, so `killpg(pgid, 0)` never reported the
group drained and a correct rollback returned `group-did-not-exit` forever. The
leader is now reaped with `waitpid(WNOHANG)` when it is our child, guarded
because on the ordinary stop path it belongs to an earlier invocation.

### Regressions

Five beside the review's own: a GRANDCHILD in the owned session (the same shape
one level deeper, which signalling the group covers without walking any chain);
rollback terminating the whole group; stop staying truthful — refusal exit,
`group-did-not-exit`, and the service retained in state — when a child ignores
`SIGTERM`; a pid that matches nothing recorded not being signalled at all; and
the process reader exposing the group identity the guard needs.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Signal only the leader | 3 red |
| Report stopped without waiting for the group | 1 red |
| Broaden before the identity check | **not run to completion — see below** |

The third sweep was a mistake to attempt. Removing the identity gate lets
`_terminate` signal the group of whatever pid it is handed, and the test that
hands it this process's own pid then signals the suite's own group. The run's
output was disturbed and the sweep proves nothing beyond what it cost. That the
sweep is dangerous to perform is itself the argument for the guard, and the
guard's own test asserts the safe behaviour directly rather than by removal.

### Gate

`just test-v11`: **1703 passed**, serial **38 passed**, ACP **41/41**.
`py_compile` clean.

### One thing fixed outside this Work

The gate came up red on `test_the_row_never_truncates_a_large_obligation_selector`,
a new W228 regression. Real: a fixed four-cell `Do` column turned `@1000` into
`@100` — a different obligation, which is worse than hiding the cue. Worth
recording because W49 sized `Id` from the page for exactly that reason and I
wrote the sentence saying so, then gave the next selector column a constant.
Fixed, covered at every decimal boundary, and reported on T228; W228 stays with
its reviewer.

## R4 — 2026-08-18, `baton.claude`

One finding, and it was correct on both counts.
`test_a_service_that_is_not_its_own_session_leader_is_not_broadened` was
**environment-dependent** — it asserted the runner's own `sid`/`pgid` as a
precondition, and fails outright in a runner that *is* its own session leader,
which the reviewer's focused run was — and **vacuous**: it called `_proc()` and
asserted ids, never `_terminate`, so removing or inverting the guard it is
named for could not have reddened it. A test that cannot fail for the reason
in its own docstring is worse than no test, because it reads as coverage.

**The root cause is one I had already written down in this file.** The R3 entry
records that sweeping this branch by removal was unsafe, because `_terminate`
would then signal the suite's own group — and I concluded the guard's test
should "assert the safe behaviour directly rather than by removal." What I
actually wrote asserted the *runner's topology*, not the behaviour. The real
answer was available and one step further on: if the runner's group is unsafe
to sweep, do not use the runner's group — **build a topology the test owns.**

**The replacement.** The test now starts a leader with
`start_new_session=True` (the same call the controller makes) which spawns a
child inside that session. The child is alive, owned, and argv-matching, but
leads neither its group nor its session — precisely the guarded condition, and
constructed rather than assumed. `_identity` is asserted `owned` first, so a
refusal upstream cannot masquerade as a pass. Then `_terminate(entry)` runs.

The discriminating assertion is **what survives**: the leader sits in the group
`killpg` would have signalled, so it dies if the guard is removed or inverted
and lives if the single-process pidfd path was taken. That group belongs to
this test and was created by it, so an inverted guard damages nothing outside
the topology under test. This is what makes the sweep that was unsafe in R3
safe to actually perform now.

**Break-sweeps, both directions, run to completion:**

| Reintroduced defect | Result |
| --- | --- |
| Remove the guard (`own_group = True`, always `killpg`) | **1 red — this test alone** |
| Invert the guard (`own_group = not (…)`) | **5 red** — this test plus the four group cases |

The first is the sweep R3 recorded as dangerous and did not finish. It now
completes safely and isolates exactly the one test, which is the evidence the
old version could not produce.

**Gate.** Focused file: **45 passed** (was 44 passed, 1 failed).
`just test-v11`: **1734 passed**, serial **40 passed**, ACP **41/41**.

**Still blocked, unchanged:** the operator-owned live four-service smoke. It
needs the real Codex app-server, dispatcher, readiness and Claude ACP backends
and an operator's own mailbox; it is not something I can run from here, and I
have not claimed it as done anywhere in this file.
