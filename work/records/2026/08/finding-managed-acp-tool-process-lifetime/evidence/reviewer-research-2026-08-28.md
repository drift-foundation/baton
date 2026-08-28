# Reviewer research — 2026-08-28

## Live-process revalidation

**Observed:** the first reviewer snapshot revalidated all five process groups
named in the finding. They were descendants of Claude PID `1099234`, but they
were not members of the bridge's session or process group:

| PID/PGID | PPID | SID | age at snapshot | observation |
|---|---:|---:|---:|---|
| `1433251` | `1099234` | `1433251` | 132883s | session leader polling `pgrep -cf 'discover -s tests'` |
| `1433308` | `1099234` | `1433308` | 132883s | session leader polling `pgrep -cf EveryReceivingEntryHasOneOwner` |
| `1433501` | `1099234` | `1433501` | 132883s | session leader polling `pgrep -cf test_boundary_inventory` |
| `1433741` | `1099234` | `1433741` | 132883s | session leader polling a file with `grep -c` |
| `1460997` | `1460989` | `1460989` | 124512s | Python unittest using 99.9% CPU |

The bridge was PID/PGID/SID `1099205`; its configured launcher was bubblewrap
PID `1099219`, the ACP adapter was PID `1099222`, and Claude was PID `1099234`.
The four polling shells had each called `setsid`, so signalling process group
`1099205` could not reach them. The unittest pipeline also occupied a separate
session. This is kernel identity evidence, not a command-name inference.

**Observed later:** at `2026-08-28T04:09:37Z`, the same bridge, bubblewrap,
adapter, and Claude PIDs remained alive, but all five stale groups were absent.
The reviewer issued no signal or recovery command. Recovery therefore happened
externally; who performed it and by which mechanism are unknown. Their absence
does not prove settlement teardown because the still-running deployment is
unchanged.

## Exact code boundary

**Confirmed:** source and deployed
`tools/acp-baton-bridge/src/acp_agent_session.mjs` are byte-for-byte equal for
this boundary.

- `setup()` calls `spawn(command, args, ...)` without a detached group,
  namespace, cgroup, or other descendant-owning process domain.
- Setup RPCs race `setupTimeoutMs`, process exit, and spawn failure.
- `promptText()` deliberately has no work deadline. It races only the ACP
  prompt response against death of the direct configured child.
- `stop()` sends TERM and then KILL only through `this.child.kill(...)`; it
  waits only for that direct child's exit.
- `runBridge()` publishes `working` immediately before the prompt and `idle`
  after it returns. The runtime publisher renews the last state every 100s, so
  a live bridge keeps a silent prompt projected as `working` indefinitely.
- A successful prompt retains the same ACP agent process for later turns.
  Failure also leaves a still-alive session reusable. Only agent death,
  replacement setup, bridge abort, or final shutdown calls `stop()`.

**Confirmed:** the deployed Claude policy launcher runs bubblewrap with mount
bindings only. It does not pass `--unshare-pid` or `--die-with-parent`.
Bubblewrap's installed manual states that `--unshare-pid` creates a PID
namespace with a minimal PID 1 reaper, and that `--die-with-parent` kills the
bubblewrap sandbox process chain when bubblewrap or its parent dies. The manual
also states that PID 1 remains until no sandbox process remains. Combining a
PID namespace with forced launcher teardown is therefore the available kernel
boundary that `setsid` cannot escape.

**Operational limitation:** a probe from this managed reviewer sandbox was
refused with `No permissions to create new namespace`. A plain nested
bubblewrap probe was refused identically, while the already-running deployment
demonstrates that its outer launch context can create the current mount
namespace. The PID-namespace form must be preflighted from the actual service
launch context; this reviewer result neither proves nor disproves host support.

## Derived lifecycle model

**Confirmed:** ACP session continuity is distinct from agent-process
continuity. `AcpAgentSession` already persists one session id and, after a
process replacement, uses `loadSession` with the retained id. The bridge can
therefore make one agent process domain serve one delivered turn, destroy that
domain after settlement, and resume the same ACP session in a fresh domain for
the next delivery. No new ACP session-rotation rule is required.

**Inferred:** one persistent process domain cannot prove that a child belongs
to an earlier versus later turn. The bridge observes ACP tool updates but does
not launch those tool subprocesses itself. A turn-scoped domain is the first
outer boundary it can correlate exactly with `(action_key, work, episode,
session)` and destroy without PID discovery.

**Confirmed:** an activity-reset watchdog would not close the defect. ACP
updates can be absent during legitimate tools, and a chatty infinite operation
could reset such a timer forever. The enforceable bound is a wall-clock turn
deadline owned by the bridge. Streamed updates may be diagnostic facts, but
must not extend that deadline or be treated as proof of progress.

## Proposed implementation boundary for ruling

1. Make a positive integer `turnTimeoutMs` mandatory in ACP bridge
   configuration and examples. It has no implicit default. Deployment chooses
   the operational duration; tests inject short values.
2. Require the configured agent launcher to create a descendant-owning process
   domain. For the shipped Claude deployment shape, add bubblewrap
   `--unshare-pid` and `--die-with-parent`, keep its PID 1 reaper, and preflight
   this exact launch in the service context. A direct executable or a
   mount-only bubblewrap command is not an accepted managed configuration.
3. Bind one fully initialized agent process domain to at most one delivered
   readiness turn. Retain ACP's session id, not its process. On prompt success,
   prompt failure, deadline, cancellation, session replacement, and bridge
   shutdown, stop the domain and positively await its outer owner before the
   attempt settles or another domain starts.
4. On deadline, teardown completes before publishing `failed` and before the
   readiness key can retry. Use the existing typed runtime shape
   `failed/cause=internal` with a bounded detail such as `configured ACP turn
   deadline exceeded`; keep `work`, `episode`, and `session` correlation. Do
   not add a second Work state or imply a claim. A separate `stalled` runtime
   state/cause is unnecessary unless the approver wants an operator-visible
   pre-deadline warning.
5. A teardown that cannot positively establish domain exit is itself a
   fail-closed delivery failure. It must not publish `idle`, mark the offer
   presented, or start the next agent process.
6. Preserve current session-selection rules: a fresh process loads the one
   retained session; lack of `loadSession` capability already fails closed.

## Focused regression matrix

- Configuration refuses missing, zero, negative, fractional, or non-integer
  `turnTimeoutMs`; templates name it explicitly.
- A never-returning fake prompt reaches its wall-clock deadline, destroys the
  process domain, publishes correlated `failed/internal`, and leaves readiness
  eligible for a later healthy attempt.
- A successful prompt also destroys the old domain before publishing `idle`;
  the next turn loads the same ACP session in a new process.
- A fake tool calls `setsid`, and another forks a CPU-bound descendant. Both
  are absent after success, failure, timeout, cancellation, bridge shutdown,
  and session replacement.
- A self-matching `pgrep -cf` watcher cannot survive the turn boundary.
- Teardown and timeout racing with prompt success settle once; no late prompt
  result overwrites `failed`, no duplicate agent starts, and no unhandled
  rejection remains.
- A failed or unverifiable domain teardown fences the lane and leaves an
  unrelated process outside the domain untouched.
- An agent-process replacement loads the retained session id; it never creates
  a replacement session or rewrites the create-only selection.
- Infrastructure stop proves no process remains in the ACP service's
  descendant domain even when a tool created a new session/process group.

## V12 carry-forward

The v12 equivalent is already located at W6636's owned destroy/settlement
crossing: an execution container is the attempt's process domain. Success,
failure, cancellation, deadline, restart reconciliation, or orphan recovery
must force-remove that exact container and observe positive absence before the
attempt settles cleanly, credentials are removed, or a replacement starts.
Container `exited` alone is insufficient if the runtime object still exists;
manager state must preserve `uncertain`/cleanup-required until adapter
observation proves absence. The container must not be able to launch host or
sibling-container processes outside its runtime boundary.

