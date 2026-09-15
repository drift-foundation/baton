# Progress

Not started. The run3 authority and recovery record remain disposable evidence;
W61984 continues only under a fresh authority and attempt identity.

## Claim 174231 — baton.claude, implementation

Unparked W63255 to `queued` at seq 174230 under the configured `baton.impl`
Handler, per poke 174223 and owner M174212, then claimed standalone at 174231.
Read the FINDING through the 2026-09-14 selection, the 2026-09-01 reviewer
revalidation, the approved 2026-09-02 direction, M174212's exact path list, and
`evidence/research-2026-09-01/README.md` in full — which my own W174050 pre-work
had flagged as unread.

### What was implemented

**`fence_pre_attach_abandonment(store, port, *, attempt_id, reason)`** in
`worker_manager/intake.py`, colocated with abandonment so it shares the private
intent and fence primitives, named as the research recommended rather than
widening `abandon_attempt` into two result shapes. It reuses `_abandon_intent`,
`_abandon_fence_operation_id` and `AuthorityPort.cancel`, and fences with the
**adopted record's own** operation id and reason so a resumed call reissues the
same authority act.

**`_no_start_declared`** is the eligibility body that closes the race. It runs
inside the declaration's own transaction: it requires `runtime_id is None` and
`execution_runtime == "not-started"`, calls the existing `_declared` for the
three attached checks rather than restating them, and moves the axis to
`cancel-requested` in the same transaction. That makes the two outcomes
exclusive — if a start won, this refuses and fences nothing; if this won,
`request_runtime_start` can no longer pass its own precondition.
`_abandon_intent` gained an optional `declare=` parameter defaulting to
`_declared`, so **attached abandonment commits exactly what it always did.**

**`_pre_attach_recovered`** now takes `port` and `reason` and calls the fence
**before** any resource account is taken, recording the exact answer in
`record["authority_fence"]`. A refused fence returns `_unresolved` naming it.

### Verification

- Step 10, both selected modules: `OK`, **780 checks**, supervisor 8.1 s.
- Supervised reversals, each restored:

| Reversal | Result |
| --- | --- |
| the fence answer is not recorded | **3 cases fail** (step 06) |
| the no-start guard removed | **1 case fails** (step 09) |

**Two earlier reversal attempts silently no-opped** — step 04 on an indentation
mismatch and step 08 on a string that occurs twice in the file — and both
"passed". I am recording them because a reversal that fails to apply looks
exactly like a reversal that proves nothing, and steps 06 and 09 are the real
evidence.

- Ledger `ledger-63255.json`: **10 rows, 65.024305 s**. No run timed out, none
  was signalled, every run proved its process group gone.

### Paths, against M174212's list

Changed: `worker_manager/intake.py`, `worker_manager/__init__.py` (export only),
`tools/dogfood_operator.py`, `tests/tools/test_dogfood_operator.py`.

**`tests/manager/test_attempts.py` was NOT changed** — no manager-side change
was needed, so there was nothing to cover there; the new operation's own race
case drives it directly from the operator module's fixture.
**`worker_manager/__init__.py` is not on M174212's list**; it carries only the
export line, without which the operation is unreachable. Flagging rather than
assuming it is covered.

### Scope held

`abandon_attempt`, `request_cancellation`, `AuthorityPort.cancel` and W61984's
finalizer are untouched. No output freeze, intake, retention, custody, review,
integration or Baton pass. No Git mutation, no engine, model or image.

Candidate `candidate-174231.json`.
