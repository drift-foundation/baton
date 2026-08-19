# Finding: managed infrastructure reports immediate argv mismatch

## Observed — 2026-08-18

The first live `just start /home/sl/baton-v11` against release `7bea055`
spawned all four configured services but returned unhealthy. Both `start` and
`status` reported `argv-mismatch` for every freshly recorded PID:

- `codex-app-server`;
- `codex-dispatcher`;
- `codex-readiness`; and
- `claude-acp`.

The controller itself created these processes, so an immediate identity
mismatch across every command shape indicates a lifecycle identity defect or
an invalid manifest assumption, not a stale pre-existing service.

No process will be signalled until the recorded state, configured argv, and
live `/proc` argv have been compared. Directly killing the reported PIDs would
work around the ownership defect and is forbidden until the cause is pinned.

## Confirmed cause — 2026-08-18

The state and live process table prove one race shared by all four services.
`_wait_for_proc()` returns the first non-empty `/proc/PID/cmdline`, before the
shebang interpreter chain has settled. The stored values begin with transient
launchers:

```text
/usr/bin/env node …
/usr/bin/env bash …
```

The same PIDs and start ticks then run their stable interpreters:

```text
node …/codex …
node …/codex-event-bridge …
node …/codex-baton-bridge …
node …/acp_baton_bridge.mjs …
```

The PID, session, and process-group identities remain exactly those created by
the controller. Only the argv snapshot changes while `env`/the shebang execs
the actual runtime. `_identity()` is therefore correct to reject the stored
snapshot; launch recorded it too early.

## Pinned correction

Do not relax status or stop identity matching and do not special-case Node,
Bash, `env`, or these four commands. Launch must record an argv identity only
after the exec chain has stabilized, while preserving crash/interruption
ownership and fail-closed PID-reuse behavior. The focused test must exercise
a real shebang/`env` transition and prove both immediate healthy status and
continued refusal after later argv substitution.

## Acceptance boundary

- Record configured, stored, and observed process identity without weakening
  PID-reuse or ownership checks.
- Explain why scripts, shebangs, interpreters, or runtime argv rewriting do or
  do not account for each mismatch.
- Make a freshly started owned set pass `status` while stale, reused, or
  substituted processes still fail closed.
- Cover every affected command shape with focused regressions.
- Recover the partial live set only through a reviewed bounded path, then
  complete the real `start/status/stop/restart` smoke.

## Live-smoke correction — 2026-08-18

The first restart against the reviewed quiet-window implementation disproved
its boundary. Three services were healthy, but `codex-readiness` was recorded
as `/usr/bin/env node ...` and later observed as `node ...`, producing the same
`argv-mismatch` W10 exists to remove. A process may remain in one launcher argv
longer than 250 ms while the kernel/runtime loads the next executable; a quiet
interval therefore does not prove that an exec chain is complete.

This supersedes the earlier correction's fixed quiet-window mechanism. The
generic lifecycle boundary is configured readiness:

1. immediately record a **provisional** owned launch using PID, start ticks,
   session, process group, configured argv, and the first observed argv;
2. while provisional, argv transitions are expected startup behavior and do
   not finalize identity;
3. once configured readiness succeeds, atomically capture the current argv
   and mark the entry **ready/final**;
4. every later status and ordinary stop requires the exact final argv, so a
   post-readiness substitution still fails closed;
5. an interrupted/crashed provisional launch remains distinguishable from a
   ready service and may only be rolled back through its recorded immutable
   PID/start-tick/session/process-group ownership. It is never adopted or
   reported healthy.

No interpreter, launcher, wrapper, Node path, or command shape is special.
Readiness is already the manifest's declaration that startup completed; argv
identity must be finalized at that same authority boundary, not by a second
competing timer.

## Version-1 recovery ruling — approved 2026-08-19

Slawomir approved interpreting lifecycle-state version 1 as provisional for
the bounded transition to version 2. A v1 `observedArgv` was captured before a
declared readiness boundary and therefore cannot honestly be certified as
final. It is never healthy or adopted by a new start, but `stop` may recover
it using the recorded PID, start ticks, session, and process-group ownership.

Every newly written version-2 entry is provisional only until configured
readiness succeeds; its final state then resumes exact argv enforcement. This
ruling does not weaken final identity matching or permit process discovery or
adoption.
