# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-19

The defect is exactly as recorded. `bootstrapThread` in
`tools/codex-event-bridge/src/main.mjs` called `client.startThread`,
wrote the returned id to stdout, and disconnected in the same `finally`
that closed the connection. No turn, no re-read, no proof — so the
command's success meant only "the app-server accepted a thread/start",
which is not what an operator or a deployment reads it as.

The workaround in the finding is the shape of the fix: hold one
connection across `thread/start` and a first turn. What the command was
missing is that plus a check that anybody ELSE can resume the result.

## What changed

`bootstrapThread` now does three things in order and reports success
only at the end of them:

1. **Create** the thread with the accepted role instructions, exactly
   as before.
2. **Persist** it with one turn — `BOOTSTRAP_PROMPT`, deliberately a
   no-tool instruction. The turn exists to write a rollout, not to do
   work; a bootstrap that ran a command would be acting in a workspace
   nobody has checked yet. A turn that fails to start, or ends in any
   status other than `completed`, fails the command.
3. **Prove** it on a SECOND connection: connect again, `thread/resume`,
   disconnect. This is the exact call that failed in production, and
   the exact thing the old command could not have known — a thread the
   creating client can read says nothing about whether the dispatcher
   can resume it.

Only then is the locator written, and the write itself moved behind an
injectable `out` so the ordering is testable rather than asserted.
Every failure path throws with the thread id in the message, so an
operator can find and clean up the half-made thread, and nothing
reaches stdout.

`bootstrapThread` is exported now, with `clientFactory`, `read` and
`out` seams — the same injection shape the dispatcher and the readiness
producer already use in this package.

## Plan item 3, decided

The plan asks whether target-level dispatcher health belongs in this
correction. **It does not**, and it is filed rather than dropped:
**W482 — "Dispatcher readiness proves a socket, not a loadable
target"**.

The reasoning: `tools/infra.py`'s `unix_socket` readiness proves a
connection to the dispatcher socket, which is already better than
blessing an inode and is documented there as such. But a dispatcher
accepts connections from the moment it listens, before any target has
resumed and forever after even if every target is dark. The dispatcher
already knows the answer — `{"control": "status"}` returns per-target
`connected`/`loaded` and an overall `ready` — and nothing reads it.

What makes it a separate Work is not size. It needs rulings this Work
has no mandate to make: whether readiness gains a probe kind that
speaks a control protocol, what an unhealthy TARGET means for a service
with several of them, and whether a target still resuming should hold
the whole service unready at startup. Those are policy decisions with
operational consequences.

W424 does not depend on W482. This Work stops the bootstrap producing
an unloadable target; W482 is about noticing one that exists for any
other reason.

## An adjacent risk I did not fix

**W484 — "waitForTurnCompletion can miss a completion that arrives
first"**, filed as suspected rather than confirmed.

`CodexClient.waitForTurnCompletion` is a pure listener with no timeout,
and every caller attaches it AFTER `startTurn` resolves. A completion
delivered before that continuation runs is never seen and the promise
never settles. I have not observed it; I filed it because this Work
adds a second dependence on the pattern, in a command an operator runs
interactively where a hang is indistinguishable from a slow model.

I did not fix it here because the fix is in `codex_client.mjs`, shared
with the dispatcher, whose tests pin the current event flow — and
because W424 owns the bootstrap command, not the client. The test fake
in this Work had to record the completion rather than emit it to be
deterministic, which is itself the shape of the eventual fix and is
commented as such.

## Verification

- `tools/codex-event-bridge/test/bootstrap_thread.test.mjs` — new,
  **12 passed**. Its fake app-server models the ONE property this Work
  is about: a thread becomes resumable only once it holds a completed
  turn, so `persistOnTurn: false` reproduces the production failure
  exactly — `no rollout found for thread id …` on the second
  connection. Covered: the first turn is recorded and is the no-tool
  prompt; two connections are used and both are closed; the locator
  carries the resolved identity and generation; role instructions
  still reach `thread/start`; an unresumable thread, a turn that ends
  `failed`, and a turn that cannot start each refuse with the thread
  id named and NOTHING on stdout; a failed bootstrap still closes its
  connection; a missing operand refuses before any connection is
  opened; and an unresolvable role refuses before a thread exists.
- The Codex bridge suite — **115 passed**.
- `tools/codex-event-bridge/README.md` and
  `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md` describe the new
  order and say plainly why it is that order.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2467 passed** (parallel), **40 passed** (serial), both bridge
  suites green. (Re-run after the review round: this round changed no
  code, and the count moved only because W321 landed beside it.)

## Response to the review — the boundary is narrower than I wrote

**P1 accepted.** I implemented the same-start handoff and then described it
against the ORIGINAL cross-restart contract, in the finding, in both user
documents, and in my own note below. Slawomir's clarification (thread
message 456) had already narrowed the requirement and asked for it to be
promoted before anything relied on it. I did not do that, so the durable
specification still said one thing while the code and the tests meant
another — and discussion is evidence, not specification.

Corrected:

- `FINDING.md` keeps its original Expected paragraph, marked as narrowed,
  and gains a dated **Clarification — 2026-08-19, approved by Slawomir**
  section plus a re-headed acceptance boundary. The superseded sentence is
  named explicitly ("and after an app-server restart") rather than deleted,
  with the reason it changed — the reasoning still holds for the defect, only
  the SPAN it must hold over moved — and managed-restart behaviour points at
  `finding-fresh-agent-context-per-start/` (W459).
- `tools/codex-event-bridge/README.md` no longer claims a restarted
  app-server can resume the locator; it says what is guaranteed — the
  handoff within one app-server lifetime — and that a bootstrapped id belongs
  to the start that produced it.
- `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md` says to record the id as
  dispatcher configuration FOR THIS START, and to bootstrap again rather than
  carry an id across a restart.
- Promoted through `revise work=W424 message=456 expect=0` — the Work now
  carries revision 1, so the contract is in the authority.

**The code did not change, and did not need to.** What the implementation
already proves is exactly the narrowed contract: one completed turn, then a
resume on a SECOND CONNECTION before any locator is printed. My earlier note
called that "the property restart-resumability depends on"; under the
narrowed boundary it is not a proxy for anything — it IS the requirement,
and the suite tests it directly rather than approximating a restart it never
exercised.

The paragraph I had written admitting the suite could not reach an
app-server restart is therefore gone rather than reworded. It was defending a
gap in a requirement that no longer exists, and leaving it would have implied
this Work still owes something it does not.
