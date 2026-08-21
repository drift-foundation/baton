# Finding: recover cleanly from lifecycle state left by a machine restart

## Observed — 2026-08-21

After a forced machine restart, `just start /home/sl/baton-v11` refused:

```text
existing lifecycle state is not a complete healthy configured set; refusing
to adopt, replace, or kill it
```

Every configured service was reported `stopped`, with its pre-reboot PID still
present only in `run/infra-state.json`. `just status` therefore truthfully
reported `partial-or-stale`, but the ordinary start path could not recover
without a separate operator cleanup step.

## Confirmed cause

`tools/infra.py:_start_guarded()` refuses every persisted state document that
is not a complete healthy set. It does not distinguish contradictory or partly
live state from the safe terminal case in which every recorded service
identity is definitively `stopped`. The existing `stop()` path already handles
that terminal case safely: `_terminate()` observes each PID as absent, removes
the dead entries, and removes lifecycle state without signalling anything.

This is not an ownership failure and must not weaken the existing fail-closed
rules for PID reuse, argv mismatch, configuration changes, partly live sets,
or an identity that cannot be proven.

## Proposed correction

Under the mailbox lifecycle lock, `start` may discard persisted lifecycle and
rendered-context state and continue only when every recorded service is
provably `stopped`. This is the same dead-state cleanup already performed by
`stop`, not adoption, replacement, or termination.

Any live, reused, mismatched, provisional-but-present, configuration-changed,
unhealthy, state-only, or otherwise ambiguous entry continues to refuse and
requires explicit operator inspection and bounded `stop`.

The current safe workaround is explicit and temporary:

```text
just stop MAILBOX
just start MAILBOX
```

When every recorded process is already stopped, the first command only removes
the stale lifecycle record. It sends no signal.

## Acceptance boundary

- A full start, simulated host reboot/process disappearance, then start again
  succeeds without an intermediate operator command and creates one fresh
  configured service set.
- Recovery removes the prior start's rendered contexts and mints fresh ones;
  no previous agent session or locator is reused.
- A mixed live/stopped set, PID reuse, argv mismatch, configuration change,
  unhealthy owned process, malformed state, or uncertain identity still
  refuses without signalling or deleting evidence.
- Explicit `stop` remains idempotent and continues to clean an all-stopped
  state safely.
- Focused tests prove both the automatic dead-state recovery and every
  fail-closed inversion above.

## Reviewer revalidation — 2026-08-21

**Observed.** A two-service focused reproduction starts a healthy set, sends
`SIGKILL` to both recorded PIDs to model the process-disappearance half of a
host reboot, waits until both are absent, and invokes `start` again. The
second invocation exits 2. Its two rows are both `stopped`, but its error is
still `existing lifecycle state is not a complete healthy configured set;
refusing to adopt, replace, or kill it`. The prospective recovery assertion
therefore fails before a second service set is launched.

**Confirmed.** The current implementation has exactly one unconditional
branch responsible for that result: `tools/infra.py:_start_guarded()` returns
success only for a complete healthy persisted set and returns 2 for every
other loaded state. Both `start` and `stop` run inside the same
`MailboxLock` acquired by `run()`. `stop()` already reaches the safe terminal
case without signalling: `_terminate()` returns `stopped` for an absent PID,
the entry is removed, and the last entry removes `infra-state.json`.

**Confirmed.** The shared terminal cleanup is incomplete today. Startup
rollback clears `run/context/` before removing the state document, while the
last successful `stop()` removal deletes only `infra-state.json`. A recovered
start would clear the old context files later, before minting, but the cleaner
and testable boundary is one terminal cleanup operation used by rollback,
explicit stop, and dead-state recovery: clear controller-owned rendered
context files, then remove lifecycle state. This does not delete the external
per-start ACP selection directories; those remain history under the W459
decision.

**Confirmed safety constraint.** `_proc()` returns `None` for process absence
*and* for permission, I/O, and parse failures. `_identity()` consequently
maps every such `None` to `stopped`. That label is adequate for the existing
status presentation but is not, by itself, proof strong enough to authorize
automatic evidence deletion. Recovery must not treat an unreadable or
otherwise uncertain live PID as absent.

## Proposed implementation boundary — 2026-08-21

The reviewer recommends the following narrow recovery rule for approval:

1. Recovery is considered only after `_load_state()` has accepted the
   persisted document and while the existing mailbox lifecycle lock is held.
2. The recorded manifest digest must equal the current manifest digest; every
   recorded service must still belong to the current manifest; recorded
   launch order must remain the manifest-order-preserving subset that the
   controller can produce; recorded contexts must belong to the current
   manifest; and each recorded `configuredArgv` must equal the argv resolved
   from that persisted start. A state-only service, changed manifest, changed
   resolved argv, or structurally impossible record refuses and preserves
   evidence.
3. Every recorded PID must be *definitively stopped*. A failed
   `pidfd_open()` with `ProcessLookupError` proves absence. If a pidfd can be
   opened, only a readable zombie with the same recorded start ticks is a
   stopped identity. pidfd unavailability, an unreadable `/proc` record, a
   live process, reused PID, provisional-but-present process, argv mismatch,
   or any other uncertainty refuses. The start recovery path never calls
   `_terminate()` and never sends a signal.
4. A valid partial-start or partial-stop record is recoverable when all
   identities still recorded in it satisfy the rule above. An empty valid
   record is also recoverable: no process identity exists to adopt or kill,
   and any contexts it minted are abandoned runtime state.
5. On success, use one terminal cleanup helper to clear the old
   controller-owned `run/context/` files and remove `infra-state.json`, then
   continue through the ordinary fresh-start path. That path must mint a new
   `startId`, new context locators, new rendered files, and one new service
   set. Do not reuse any locator from the discarded state.

This boundary does not weaken status, stop, PID/argv ownership, readiness,
configuration, log-containment, or process-group rules. It adds no process
discovery and no force escalation.

## Regression matrix

**Positive.** Extend `tests/work/test_w20_infrastructure_lifecycle.py` with a
full two-service start, disappearance of every recorded process, and direct
second start. Assert success, a fresh `startId`, new PIDs, exactly two new
launch events, no controller termination event for the vanished set, and a
healthy final set. Add valid partial and empty persisted-state cases.

**Fresh-context positive.** Extend
`tests/work/test_w459_fresh_contexts.py` with the same no-intermediate-stop
restart. Assert that the context locator and rendered content change, the old
rendered file is removed/replaced rather than reused, and explicit `stop`
also removes controller-owned rendered context files.

**Fail-closed inversions.** In focused subprocess or helper-level cases,
prove that mixed live/stopped, unhealthy owned, PID-reused, argv-mismatched,
provisional-but-present, configuration-changed, state-only, malformed,
unreadable `/proc`, and pidfd-unavailable records all return refusal. For
each applicable live case, assert the process remains alive, no new launch or
termination event appears, and the lifecycle/context evidence remains.

**Race/retry.** Repeated `start` calls remain serialized by `MailboxLock`:
the first successful recovery writes the new state, and the next call observes
that complete healthy set as `already_running` rather than launching a rival.
If the recorded PID is absent at the definitive check and the number is later
reused, cleanup is still safe because recovery sends no signal and adopts no
process.

## Focused baseline — 2026-08-21

- The prospective reboot regression fails on the current tree exactly at the
  second-start assertion (`returncode` 2 instead of 0), with both rows
  `stopped`.
- Seven retained lifecycle/context cases pass in 2.02 seconds: stopped-child
  cleanup, partial-state refusal while live, PID reuse and argv mismatch stop
  refusals, provisional live-start refusal/rollback, fresh context across an
  explicit stop, and failed-start rendered-context cleanup.

## Deferred decision — 2026-08-21

Do not implement the proposed automatic v11 recovery yet. V12 is expected to
change worker lifecycle ownership, process isolation, and restart semantics;
adding the full pidfd-backed recovery boundary to v11 now risks throwaway
work. The explicit, safe operator sequence remains the accepted workaround:

```text
just stop MAILBOX
just start MAILBOX
```

Keep this record as evidence and reconsider it only if v11 remains deployed
long enough for the manual recovery burden to justify a v11-specific fix, or
when the v12 worker-manager lifecycle contract is concrete enough to absorb
the requirement.
