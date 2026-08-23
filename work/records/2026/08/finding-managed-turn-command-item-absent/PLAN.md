# Plan — Managed turns record no commandExecution item

1. [SUPERSEDED 2026-08-23] "The command runs and the turn record does not carry
   it" was measured correctly; the conclusion drawn from it was wrong. The
   command ran through a provider `custom_tool_call name=exec` wrapping
   `tools.exec_command`, never through the built-in shell, and the installed
   `ThreadItem` union has no `custom_tool_call` variant. Confirmed
   independently on the W7830 smoke turn as well as the nonce probe. A nonce
   proves execution; it does not prove which execution path.
2. [confirmed 2026-08-23] Neither W2845 nor W7830 can prove its live gate on
   this deployment, and neither gate is to be relaxed. `rawResponseItem`/
   `completed` can carry a `ResponseItem` and is the only identified in-turn
   candidate transport — NOT a proven oracle, because its input is
   model-generated JavaScript.
3. [approved 2026-08-23] `baton.ops` selected option (a): prove the live
   `rawResponseItem/completed` provider path, then implement a strict
   fail-closed custom-tool oracle under the pinned boundary. W2845 and W7830
   stay blocked until their independently reviewed live gates pass.
4. [confirmed 2026-08-23; separable, and reproducible with no model] The
   canonical CLI surfaces a sqlite open failure as an UNHANDLED PYTHON
   TRACEBACK, not the typed JSON error every other refusal on that path uses.

     deployed c529b28, unreadable work.sqlite3:
       sqlite3.OperationalError: unable to open database file
       (authority.py:830, via lifecycle.open_bound)
     current tree, src/baton_work/authority.py:978:
       the same, from `Authority(db)` directly

   Scope is wider than first recorded: ANY sqlite open failure takes it — an
   unreadable file, a missing directory, an inaccessible home — not only a
   read-only store. A caller cannot classify it, retry on it, or report it as
   anything but "the tool crashed". Sandbox authority is not to be broadened
   to avoid it.
5. [CLOSED AS A SCOPED MEASUREMENT 2026-08-23] Both capability declarations
   were measured for isolated BUILT-IN-SHELL turns. The opt-in repeat used the
   same denial, isolation, bounded-output and cleanup controls, differing from
   the pinned probe in one field. Neither run emitted
   `rawResponseItem/completed` or custom items. Neither configured or emitted
   the managed provider custom tool, so the approved target response path
   remains unmeasured. All three runs are preserved; none was rewritten.
6. [NOT UNLOCKED 2026-08-23] The wrapper contract remains gated on a measured
   matched `custom_tool_call` pair. The built-in-shell probes did not produce
   or test such a pair, so the oracle has no proven input and is not to be
   built. This is an inconclusive target-path measurement, not proof that the
   pair cannot occur on this build.
7. [measured 2026-08-23; needs an operator boundary] The evidence both gates
   require IS emitted live. `item/started` and `item/completed` carry a
   structured `commandExecution` ThreadItem with a shell-wrapped command,
   `source`,
   terminal `status`, `exitCode` and a correlatable id — and `thread/read`
   with `includeTurns` does not persist it. `reasoning` is dropped too, so the
   omission is not command-specific. The defect is PERSISTENCE, not recording
   and not the item family; both earlier diagnoses are superseded.
8. [open, and not an implementer's to decide] Adopting that transport also
   requires the managed stack to execute through the BUILT-IN SHELL. Both
   probes ran with no provider custom tool configured; the managed deployment
   runs `custom_tool_call name=exec`, and a gate reading `item/completed`
   would see nothing under it. The execution path is configuration-dependent,
   and that half is untested end to end. The observed item records
   `/bin/bash -lc 'date +%s%N'`, not the requested literal `date +%s%N`, so the
   current strict equality oracle would reject it; only a failed execution was
   observed. Shell-wrapper semantics and a successful positive path both need
   an explicit operator boundary and deterministic evidence. Neither gate is
   relaxed meanwhile.
9. [decided 2026-08-23] The operator selected option 3. Do not reconfigure the
   v11 managed execution path and do not wait for upstream persistence.
   Close W7989 satisfying as the diagnosis; close W7830 and W2845 cancelled
   with their strict live certification explicitly unmet. Deterministic
   safeguards may ship, but no live gate is represented as passing. V12's
   external Worker Manager owns the replacement evidence boundary.
