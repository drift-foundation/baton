
## 2026-10-22 — baton.claude, claim354566 — THE MIDDLE FORWARDING IS PROVED ON ACTUAL ACQUIRED TOKENS

Claimed at snapshot354566 after reading canonical state (queued, unclaimed,
routed `baton.impl`, `last_change_seq 354563`, zero open blockers), the
complete handoff through `work-events` (83 events, no pagination remaining) and
thread T325959 in full (5 messages, `last_seq 329708`, unchanged). Read
`review-2026-10-22T19-38-15Z.md` and `REVIEW-INPUTS-354560.json`.

### The blocker, accepted on every count

`NativeComposition` proved the middle with `inspect.signature`/`getsource`,
and the factory case **mocked** `operations_from`. Both are surrogates: a
source-text assertion passes while the value is dropped at runtime, and a
mocked composer never composes. The endpoint arms from last claim did not
establish **middle** forwarding. **The surrogate class is deleted, not
supplemented.**

Replaced by two real-composition cases that **observe the acquired token**:

- `single_worker.operations_from` composed for real with the native policy,
  driven through `self.commanded` to an actual dispatch, then
  `token['seconds']` read **out of the store the serving pass wrote** — equal
  to `task_token_seconds` for the Job's own selected limits, not
  `LIFETIME_SECONDS`, above 900, carrying no permission envelope, bound to the
  engine's runtime. Its negative: the same real serving **without** the policy
  acquires exactly 900 — the recorded pilot defect through the real
  composition.
- `stage_execution.factory` composing **real stage workers**, with both
  carrying the same `lifetime_policy` asserted by **object identity**.

### Every middle link is now load-bearing, proved by reversion

One-line reversion per link, same 12 cases:

| link unwired | result |
| --- | --- |
| `single_worker.operations_from` → `worker_operations` | **1 failure** (acquisition) |
| `worker_operations` → the worker composition | **2 failures** (acquisition + both stages) |
| `stage_execution.operations_from` → `worker_operations` | **1 failure** (both stages) |
| connected | **12 OK** |

With last claim's two endpoint arms — `factory` unwired (1 failure) and
`reserve` unwired (3 failures) — **all five links** are individually shown to
be load-bearing, and the proof now rests on actual acquired tokens rather than
on any source-text or signature surrogate.

### Verification

- **Focused: 12 tests, OK, 0.212s.**
- **Affected modules: 4 modules, 200 tests, 1.387s, OK.** Focused deterministic
  boundary proof only, as the review directed — no broad sweep, no live run.

**No product defect was exposed, so none was corrected**: all four product
paths are byte-unchanged (`24f27d77…`, `7db36ee6…`, `70cc0806…`,
`765c1567…`). Only the test file changed, to `6de86489…`.

### Still owed — the review named each and I am not softening them

**Exact stop/cancel**: I prove expiry through the real `overdue` owner, and the
review is right that overdue *selection* is not exact stop or cleanup;
cancellation is not proved at all. **Cleanup and unknown holds** beyond
expiry-is-not-release and resource-stays-held. **Persisted restart**: my replay
case reuses the same open store, and the review is right that same-store replay
is not restart — a reopened store proving durable original timing is still
owed. **The joined owner-produced failure** through durable capture, `/7`
status and the packaged secret-free report.

### Cost and boundaries

Measured: focused 0.212s, three middle arms 0.227s/0.220s/0.220s, affected
modules 1.387s, plus unmeasured reading. No live instance, engine, provider or
credential; no deployment, recovery, migration or shared import; no
version-control mutation. The three middle arms are throwaway `/tmp` copies and
are not candidates. Prior spending retained: claim354527 focused + two arms +
695 tests/5.385s; claim354424 2175 tests/288.769s; claim354259 14.254s +
0.213s; claim354165 14.213s; claim354320 and claim354357 none.
