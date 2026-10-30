# The vehicle, revision 7 — what it enforces, what it still gets wrong

Recorded by `baton.claude`, claim339421 and carried forward at claim339628 and
claim339868,
read-only against this packet's base
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. The vehicle is **unchanged across
all three claims** — same controller, same supervisor baseline, same helper,
same base — so this document is carried with one correction: the attribution of
the two ceiling measurements below.

Read `SHUTDOWN.md` beside this: it covers the ending. This document covers the
vehicle, the composer defect, the lease, and the two measured ceilings.

## The start is not selected

Every input gate this Work had is closed:

| prerequisite | closed | checkpoint |
| --- | --- | --- |
| W333735 authoring expiry enforcement | owner close334628 | `a9f4fa4d` |
| W334910 single-manager guard | owner close337414 | `fb487979` |
| W338305 bounded shutdown and final reports | closed satisfying339412 | **`bc925cf5`** |
| W337955 finalization assessment (scheduling edge) | `remove_dependency`339410 as fulfilled | — |

`wake`339414 and the successful claim339421 confirm no remaining executable
input gate. **That is not a start.** Nobody has selected this run. Independent
preparation review comes first, then an exact execution selection by the owner.
`prepare.py stage` therefore refuses without `--acknowledge-unselected-start`,
and `PROVENANCE.json` carries both `start_authorized: false` and
`start_selected: false` — two different claims, because an earlier revision of
this program checked only the first and a probe caught it.

**Both temporary direct-implementation exceptions expired at acceptance, and
neither ever covered diagnostics.** W338305's disposable-workspace exception
expired when its candidate was independently accepted. Nothing in this packet
revives either one.

A disclosure about where that rule is written: `AGENTS.md` at this base still
carries the older *"Temporary W321689 completion exception"* section, because
the host's replacement of it with *"Recording bounded owner exceptions"* is an
uncommitted working-tree edit. The turn reads the **base** copy from its private
checkout, so it will see the superseded wording. It does not matter for scope —
the W321689 exception is expired either way and this packet's own documents are
the current authority on what is permitted here — but a reader should not be
surprised by it.

## Do not use `commands.json`'s `start`

`baseline_bindings.py` is **unchanged at this base** —
`09fbf3c59820231b7199e24aa1cf64eee93f6ea2e60f3477fed5ca909e5fc379`,
re-measured this claim — and its line 721 still composes:

```python
"start": [sys.executable, "-B", packet["supervisor"]["path"],
          "--packet", places["PACKET.json"], "--incarnation", packet["run_id"]],
```

That is `baseline.py` directly, whose `serve` call carries no reclaim argument:
the **unenforced** vehicle both prerequisites existed to replace. So a packet
composed by the accepted composer tells an operator to start exactly the wrong
thing, and **every later authoring packet inherits that** until the composer is
corrected.

**This is reported for classification, not patched.** Correcting
`baseline_bindings.py` is host product work this Work does not own, and the
sibling renewal and the authoring campaign both touch that surface. The
mitigation is local and explicit:

- `bind` writes `<root>/packet/AUTHORING-COMMAND.json` with the enforced
  invocation, the staged controller's path and digest, and the staged shutdown
  helper's path and digest;
- `PREPARED.json` carries `composer_start_is_unenforced: true`;
- `COMMANDS.md` and `OPERATOR.md` both say which command to use and which not
  to;
- the generated `commands.json` is left exactly as the accepted composer wrote
  it. Nothing in the composed packet is edited after composition.

The enforced invocation, for reference — `COMMANDS.md` has it with the real
paths and no placeholders:

```
python3 -m tools.authoring_enforcement --packet <root>/packet/PACKET.json
```

run from `<root>/code/v12/python` with the staged `src`, the staged source and
the staged `supervisor` directory on `PYTHONPATH`, and
`BATON_V12_STAGE_EXECUTION_CONFIG` pointing at `<root>/packet/deployment.json`.
`--status-path`, `--child-of` and `--lock-fd` are internal: the outer watchdog
passes them to the child.

Measured in preparation, read-only, starting nothing: the corrected
controller's own `verify_controller` **accepts** this packet's composed
documents when imported from the staged source and **refuses** them when
imported from the host checkout — *"authoring controller is outside the pinned
manager source"*. A packet pinning the **superseded** controller digest is
refused before any root is created, at the cross-check between
`authoring_controller.sha256` and the pinned manager source.

## The lease is enforced, not extended

`tokens.LIFETIME_SECONDS` is **still 900** at this base
(`worker_manager/tokens.py:37`, re-measured this claim) and production renewal
is still W333485's unfinished Work, separately allocated to `baton.codx`.

- W333735 made that initial lease **actually enforced** rather than ignored.
- W338305 made the **ending** bounded and its reports deadline-aware.
- **Neither extends the lease.**

So the composed `3600` provider ceiling and `4800` total are **requested
bounds, not a promised run length**. Expect enforced expiry at **900 seconds**,
with cessation ordered, the reserved cleanup window entered, partial output
retained and a **held** outcome. `TASK.md` requires the turn to report the
actual expiry, cleanup, retained-output and recovery behaviour it observes —
that is evidence for this Work, not a failure to hide. `TASK.md` also permits a
bounded first milestone that fits 900 seconds, with the remaining work stated
explicitly and no weakening of final acceptance.

`cleanup_seconds: 60` is load-bearing twice over now: the outer watchdog
reserves that tail for kill and reap, and `authoring_shutdown.Shutdown` derives
the whole inner allowance from it. See `SHUTDOWN.md`.

## The two measured ceilings

### 1. The verification command gets 30 seconds, and this packet cannot change it

`baseline_bindings.py:345` composes `"verification_command_seconds": 900 if
contextual else 30`, and `:522` adds the same 30 for the non-contextual case.
`contextual` is `context_mode == "contextual"` — and the contextual branch
**ignores this packet's task and verification entirely**, substituting the
built-in `TASK_INSTRUCTIONS` and `["python3", "harness.py"]` (lines 363 and
367). A fresh-context packet is the only shape that can carry this task, so the
ceiling is **30 seconds** and is not this packet's to set.

Measured against a clean export of the declared base bytes, with a deliberately
useless ambient `PYTHONPATH`:

| | tests | seconds |
| --- | --- | --- |
| the ten existing gate modules | 1124, all passing, zero skips | **13.642** unittest / 14.007 wall |
| remaining for the two modules the turn must create | — | **≈16.36** |

**Attribution, corrected at claim339628.** Those seconds were obtained by
**direct host product test execution at claim339421, outside that claim's
preparation-only boundary** — `decisions/review-339623.md` item 3 is the
finding, `PROGRESS.md` the author's additive correction, `GATE-CHECK.json` the
full record. They were **not** re-measured at claim339628, which ran no product
test at all, because re-running them to tidy their own provenance would repeat
the mistake. The 30-second ceiling itself is a composition fact, re-read from
this claim's generated `policy.json`.

**That fit is UNPROVED.** `decisions/review-334776.md` was explicit about it
one revision ago and nothing has changed except that the margin moved slightly.
No coverage may be removed to force a pass; if the gate cannot be made to fit,
the turn reports it with the measured numbers.

Author evidence, not independent product acceptance.

### 2. Two real-process modules are excluded for that ceiling, not for coverage

| module | measured | why excluded | coverage carried by |
| --- | --- | --- | --- |
| `tests.manager.test_authoring_shutdown_deadline` | **51.333s / 4 tests** | exceeds the 30s ceiling **by itself** | `decisions/shutdown-review.md` — 44 tests, no skips, 72.891s unittest, authority338596, plus `decisions/shutdown-integration.json` |
| `tests.manager.test_authoring_manager_guard` | **19.888s / 7 tests** | with the ten gate modules it would put the sealed gate at 33.5s | `decisions/guard-integration-result.json` — 79 tests PASS, 15.278s, authority337376 |

Both are **reused, never re-run here** — and both of those measurements come
from the same out-of-boundary claim339421 execution, so **both exclusion
decisions rest on out-of-boundary measurements.** Stated, not laundered. The
condition on both exclusions is the same and is stated in `TASK.md`: this candidate edits neither
`tools/authoring_enforcement.py`, `tools/authoring_shutdown.py` nor the
supervisor baseline. If a turn ever does, it runs that module as a focused check
**outside** the sealed argv and says so.

`tests.manager.test_authoring_enforcement` **is** in the gate, because this
candidate edits `worker_manager/intake.py` and `worker_manager/attempts.py`,
which that module exercises through the enforcement lane cancellation path. It
needs `work/records/2026/09/finding-v12-single-implementation-proof` present at
the checkout root — it spawns a real supervisor. Measured both ways: 1 error
without it, all 33 passing with it. The private checkout carries it, and
`PREPARATION-PINS.json` lists it in `read_from_checkout_at_base` so nobody
rediscovers that inside a provider turn.

## Two excluded modules that already fail at base

Both are the author's **explicitly unverified baseline reports**, with no
cleanup, fix or weakening selected, and neither is attributable to this
candidate:

- `tests.manager.test_boundary_inventory` does not pass at base and would
  exceed the 30-second ceiling alone (328 tests, 28 failures, 1 error, 49.469s
  measured on an earlier base's bytes; not re-measured this claim and labelled
  as such). The turn still registers its own new boundary's entries and probes
  and reports what it registered.
- `tests.tools.test_packaging`'s subcommand case holds the **source**
  `stack_command.COMMANDS` table against the **installed** bundle, built at
  `1e576ff2` before `record` and `disposition` joined that table, so it fails on
  the host; inside a private checkout it SKIPs, which the sealed gate refuses.
  **A source-level case is not proof that a rebuilt bundle carries a new verb.**
  That deployment obligation stays explicit in the module the turn writes and in
  its report.

`tests.manager.test_dependencies` also fails at base for reasons that predate
this Work. Not this candidate's.

## What has never happened

**No authoring invocation has ever completed for this Work.** One was selected
and started; it died 0.506s into startup (`FAILURE.md`). Two corrections later,
one corrected startup refusal and one accepted shutdown correction are still not
a demonstration that a full provider-backed authoring invocation completes on
this vehicle. If this one does not either, the honest account of how far it got
— with the three final-result files `SHUTDOWN.md` names — is the deliverable.
