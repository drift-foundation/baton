# Progress

## 2026-08-18 — `baton.claude` (implementer)

W10. Implementation of PLAN steps 3 and 4. No manifest or lifecycle-state
schema change.

### Revalidation against the live set

The pinned cause was re-derived from the running system rather than read from
the finding. `status` against `/home/sl/baton-v11` (read-only; nothing
signalled) still reports all four services `argv-mismatch`, and the recorded
snapshot against the live `/proc` shows exactly the exec chain the finding
names:

| service | recorded | live |
| --- | --- | --- |
| `codex-app-server` | `/usr/bin/env node …/codex app-server …` | `node …/codex app-server …` |
| `codex-dispatcher` | `/usr/bin/env node …/codex-event-bridge …` | `node …/codex-event-bridge …` |
| `codex-readiness` | `/usr/bin/env node …/codex-baton-bridge …` | `node …/codex-baton-bridge …` |
| `claude-acp` | `/usr/bin/env bash …/bin/acp-baton-bridge …` | `node …/lib/acp-baton-bridge/src/acp_baton_bridge.mjs …` |

**One correction to the finding, in the safe direction.** It records the
transition as dropping the `env` prefix. `claude-acp` is longer than that: a
`bash` wrapper execs node against a *different program path*, so the recorded
and live argv share no element at all. Any rule that tried to reconcile the two
by understanding interpreters would have to model that, which is the reason the
implementation understands nothing about them.

### The correction

`_settled_proc()` waits for the argv to stop changing and records what it
stopped at. It inspects only *whether* the argv changed, never what it
contains: no interpreter, launcher, or command shape is named anywhere.

`ARGV_SETTLE_SECONDS = 0.25` is deliberately not presented as a tuning knob.
An exec chain and a self-substituting process are the same event — same pid,
same session, same start ticks, new argv — distinguishable only by how soon it
happens. The interval **is** that boundary, so both sides of it are pinned by
tests: a chain that settles inside it is accepted, and a process that rewrites
its identity after it is still refused, which is what the ruling requires.

**Ownership across the new interval.** Settling opens a window in which the
process exists and, done naively, the state file would not — so a controller
interrupted inside it would orphan a service. The entry is therefore written
with the provisional snapshot *first*, carrying the pid and start ticks that
are the actual ownership record, and the argv is corrected after settling.
Crash ownership is strictly better than before this change, never worse.

### A defect the existing suite caught in my first attempt

`_settled_proc` initially returned a bare `None` for four different outcomes,
and `start` reported all of them as "never held a stable argv". W20's
`test_failed_readiness_rolls_back_only_this_invocations_children` went red:
its service *crashes* at 0.15s, inside the settle window, and was then
reported as one whose argv never stabilised. That is untrue, and it takes a
truthful diagnosis away from an operator reading a failed start — the same
defect class this Work exists to fix.

`_settled_proc` now names its reason (`settled` / `exited` / `pid-reused` /
`unstable`) the way `_identity` does, and `exited` deliberately falls through:
the process is gone and readiness is about to say so in the words it has always
used, so settling declines to invent a second story about one failure. No
existing assertion was edited.

### Regressions — `tests/work/test_w10_argv_identity.py`, 8 tests

A real three-stage chain (`/usr/bin/env sh` → `sh` → the interpreter), built by
the fixture rather than imitated. The launcher stage is 50 ms: long enough that
the old code's first read (~1 ms) reliably lands inside it, short enough to sit
well inside the 250 ms settle interval, so neither direction depends on winning
a race. Covered: immediate healthy status; the *recorded* snapshot being the
settled program, not merely self-consistent; all four services in one ordered
start, because the live failure was all four; a later substitution still
refused; `stop` still owning a settled service; PID reuse still fail-closed
after the re-read; ownership present before settling; and the named failure
causes.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Settling returns the first observation (the original defect) | 6 red |
| Settle, but never correct the recorded entry | 6 red |
| Drop the start-ticks reuse guard inside settling | 1 red |
| Write the ownership record only after settling | **green — then 1 red** |

The fourth is the one worth recording. My first ownership test asserted that
the entry appeared before `start` *returned* — which is true whichever order
the writes happen in, since the corrective write also precedes the return. It
proved nothing. It now asserts on *what was recorded the first time the file
names the service*: with ownership written first that snapshot is still the
transient launcher, and with it written last the very first record already
carries the settled argv. That discriminates, and the sweep reds.

(An earlier version of the same test read `tools/infra.py` and compared string
offsets. It broke on a line wrap in my own edit, which is the useful part: it
was never testing behaviour.)

### Gate

`just test-v11`: **1742 passed**, serial **40 passed**, ACP **41/41**.
`tools/codex-event-bridge`: **44 passed**.

### Not done, and not mine to do — PLAN step 5

**The live partial set is untouched.** No process was signalled; only
read-only `status` and `/proc` reads were performed. Two things the reviewer
and the approver need before recovery:

1. **This fix cannot repair the running set.** The four entries were recorded
   with launcher argv and stay `argv-mismatch` until the services are
   restarted. Recovery is a restart, not a re-read.
2. **`claude-acp` (pid 1622937) is the ACP bridge currently driving this
   implementer session.** A `stop` or `restart` of the configured set
   terminates the agent performing it, mid-operation. That is not a reason to
   avoid it — it is a reason the operator should run it, from outside this
   session, rather than an agent running it on itself.

### Return blocked — 2026-08-18

The implementation above is complete and gated, but W10 could **not** be
returned to `baton.bug`. Every verb, including read-only `detail`, now refuses:

```
/home/sl/baton-v11/baton.json is edited but not accepted: its digest is
d28a5d256b21… and the accepted configuration is 3eb133eea348…
A modified config is a proposal; accept it or restore the file.
```

The file was edited at 16:52:45 local and was still an unaccepted proposal ten
minutes later. Accepting a configuration is the approver's, so this is not
something the implementer should route around, and no workaround was attempted.

**Current authority state:** W10 is `active`, claimed by `baton.claude`. That
is accurate — the work is done but not handed over — and the claim should be
left alone until the configuration is accepted or restored, at which point
`pass work=W10 to=baton.bug` is the only remaining step.

**Cleared — 2026-08-18.** The configuration was accepted by the approver. The
tree was revalidated before handing over rather than assumed unchanged across
the wait: `tools/infra.py` still carries the settling code, and the two focused
suites are green at 53 (`test_w10_argv_identity.py` 8, W20 45). W10 returned to
`baton.bug`.

## 2026-08-19 UTC — `baton.claude` (implementer)

W10 returned with changes requested (`review-2026-08-18T23-56-10Z.md`). PLAN
step 4: replace the disproved quiet-window mechanism with a provisional launch
identity finalized at configured readiness. Lifecycle-state schema change; no
manifest change.

### Revalidation against the current tree and the live set

Both re-derived rather than read from the record.

`tools/infra.py` still carried the reviewed quiet-window code
(`ARGV_SETTLE_SECONDS`, `_settled_proc`), so the tree matched what the review
rejected and nothing had moved underneath it.

The live set from the reviewer's smoke is still running and still shows the
disproof exactly as the review states — read-only `/proc` and state reads, no
process signalled:

| service | recorded | live | agrees |
| --- | --- | --- | --- |
| `codex-app-server` | `node …/codex app-server …` | same | yes |
| `codex-dispatcher` | `node …/codex-event-bridge …` | same | yes |
| `codex-readiness` | `/usr/bin/env node …/codex-baton-bridge …` | `node …/codex-baton-bridge …` | **no** |
| `claude-acp` | `node …/acp_baton_bridge.mjs …` | same | yes |

Three of four settled inside 250 ms and one did not. That is the shape of a
race, not of a threshold merely set too low, which is what the review concluded
and what the correction below is built on.

### The correction

Readiness is the boundary. `_finalize_identity()` runs immediately after
`_wait_ready()` succeeds: it re-reads `/proc`, refuses an exited process or a
reused pid, and in ONE atomic state write captures the current argv and marks
the entry final. There is no second timer, and nothing in the file reads what
an argv contains — no interpreter, launcher, wrapper, Node path, or command
shape is named anywhere in the implementation.

Lifecycle state is version 2 and each service entry carries
`argvIdentity: "provisional" | "final"`.

- **Provisional** is written the instant the pid exists, before readiness. It
  carries pid, start ticks, configured argv and the first observed argv. The
  pid and start ticks are the whole ownership record, so a controller killed
  anywhere in the launch interval leaves a service `stop` can still prove it
  owns rather than an orphan.
- `_identity()` returns `provisional` for such an entry — never `owned`, so it
  is never healthy and `start` refuses to adopt it.
- `_terminate()` accepts `owned` and `provisional`. A provisional rollback
  drops only the argv requirement, which was never certified; the pid, start
  ticks, session and process-group checks are unchanged, so a reused pid still
  refuses without signalling.
- **Final** keeps the previous exact-argv rule, so a post-readiness
  substitution still fails closed.

`ARGV_SETTLE_SECONDS` and `_settled_proc()` are removed. The named-cause
machinery they carried went with them: a crash before certification is again
reported by readiness in the words readiness has always used, which is the
outcome that machinery existed to protect and which is now structural rather
than maintained.

### One decision I made and did not have — please rule on it

**A version-1 lifecycle document is read as provisional, not rejected and not
read as final.** This is not in the pinned correction; I chose it, and it is
the one part of this change a reviewer should look at first.

A version-1 `observedArgv` is by construction the first readable cmdline —
precisely the uncertified snapshot this Work proved wrong. Reading it as
`final` would certify the one value that was never verified. Rejecting the
document instead makes `_load_state` raise, which takes `status` and `stop`
away entirely at the moment they are needed.

Read as provisional it is true to what it is, and it has an operational
consequence worth stating plainly: **the deployed partial set becomes
recoverable through the controller.** `stop` will terminate all four on the
recorded pid and start ticks, which is a bounded reviewed path rather than the
hand-rolled kill the acceptance boundary was otherwise heading for. If the
reviewer would rather have an explicit refusal and a separate recovery
mechanism, this is a few lines and I will change it.

### The honest limit of this boundary

For `readiness.type == "process"` the manifest declares startup complete after
`stableMilliseconds` of a live pid. The exec chain is invisible to that probe,
so the certified argv is whatever is live when the operator's own declaration
says startup finished. In the deployed manifest `codex-readiness` declares
1000 ms against the 250 ms that failed — a four-fold margin, and derived from
the manifest instead of guessed by the controller — but it is a declaration,
not a proof.

I am stating this rather than papering over it. If a launcher ever outlives its
configured readiness the failure is still VISIBLE (`argv-mismatch`, fail
closed) and never a silently blessed wrong identity, and the remedy is that
service's `stableMilliseconds` or a stronger readiness probe. Adding a
controller-side interval to cover it is exactly the mechanism the live smoke
disproved, so I did not add one back under another name.

### Regressions — `tests/work/test_w10_argv_identity.py`, 12 tests

Rewritten against the new boundary, on the same real three-stage chain
(`/usr/bin/env sh` → `sh` → the interpreter) built by the fixture rather than
imitated. The launcher delay is now a fixture variable, because the disproved
mechanism was sensitive to it and this one must not be.

New for this correction:

- a launcher holding its own argv for **3× the disproved 250 ms interval** is
  still healthy and still recorded as the program that arrived — the field
  failure, reduced;
- the launch is owned and marked provisional before readiness, observed by
  watching the state file while `start` is still running;
- a SIGKILLed controller mid-launch: the service survives, `status` reports
  `provisional` and unhealthy, `start` refuses to adopt it without signalling
  it, and `stop` rolls it back on ownership alone;
- provisional rollback still refuses a tampered start-ticks field without
  signalling;
- a crash before readiness keeps the readiness diagnosis and mentions no argv;
- `_finalize_identity` refuses an exited process and a reused pid, and a
  refused finalization leaves the entry provisional;
- a version-1 document is read as provisional and is stoppable.

Retained: healthy immediately after start, the recorded snapshot being the
settled program rather than merely self-consistent, all four services in one
ordered start, post-readiness substitution refused, `stop` owning a finalized
service, and pid reuse fail-closed after finalization.

### Break-sweeps

Each defect reintroduced alone against W10 + W20 (57 tests).

| Reintroduced defect | Result |
| --- | --- |
| Never finalize — the launch snapshot is the identity (the original defect) | 24 red |
| Finalize, but never mark the launch provisional | 3 red |
| Provisional entries read as `owned` | 2 red |
| Finalization drops the start-ticks reuse guard | 1 red |
| Provisional rollback ignores the reuse guard | 2 red |
| Version-1 documents read as certified | 1 red |

### Gate

`just test-v11`: **1756 passed**, serial **40 passed**, ACP **41/41**.
`tools/codex-event-bridge`: **44 passed**. The three pre-W12 Held expectations
noted in `review-2026-08-18T23-12-09Z.md` are green; that review's full-gate
caveat is discharged.

### Not done, and not mine to do — PLAN step 5

**The live partial set is untouched.** Only read-only `status` and `/proc`
reads were performed; no process was signalled.

1. This fix cannot repair the running set. The four entries were recorded by
   the previous release and stay uncertified until the services are restarted.
   Recovery is a restart, not a re-read.
2. `claude-acp` (pid 1739112) is the ACP bridge driving this implementer
   session — confirmed by walking this process's ancestry, not assumed. A
   `stop` or `restart` of the configured set terminates the agent performing
   it, mid-operation. That is why the operator should run it from outside this
   session.
