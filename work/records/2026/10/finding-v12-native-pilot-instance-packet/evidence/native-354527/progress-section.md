
## 2026-10-22 — baton.claude, claim354527 — THE PROOF NOW GOES THROUGH THE REAL PATH, AND DISCONNECTION FAILS IT

Claimed at snapshot354527 after reading canonical state (queued, unclaimed,
routed `baton.impl`, `last_change_seq 354523`, zero open blockers), the
complete handoff through `work-events` (79 events, no pagination remaining) and
thread T325959 in full (5 messages, `last_seq 329708`, unchanged). Read
`review-2026-10-22T19-32-18Z.md` and `REVIEW-INPUTS-354510.json`.

### The blocker was real and it was the defect in my cases

The reviewer found that `test_native_permission` built a governance and then
called `tokens.acquire` **directly**, so no case drove `factory`, the lifetime
callback or `reserve` — and a disconnected wiring path would have evaded the
coverage entirely. That is correct: the old cases proved the arithmetic, not
the connection.

**Rewritten so every case goes through the real act** — `reserve` for the
acquisition, `operations_from`/`_SingleWorker` for the composition, and
`stage_execution.factory` for the entry point. Eleven cases, and the acquired
value is read back from the **stored token** rather than from anything the case
computed.

### A disconnected path now fails the proof, on two independent arms

- **Arm A**, `factory` stops supplying the policy: 11 tests, **1 failure**.
- **Arm B**, `reserve` stops forwarding `seconds` to `acquire`: 11 tests,
  **3 failures** — the real-policy case, the survives-past-900 case, and the
  seconds-beside-permission refusal.
- **Connected**: 11 tests, **OK**.

So each link is load-bearing and independently shown to be. Unwiring either end
is caught.

### What the cases now cover

The real policy feeding the real `reserve` with the stored token carrying the
value; **without** the policy the same real `reserve` still takes 900, which
reproduces the recorded pilot defect through the real act; the token surviving
past 900 and still being bounded, with expiry not release; expiry making it
reclaimable through `tokens.workspace_governance().overdue` — the owner
`_reclaiming` actually consults; **replay** returning the same generation with
the same `expires_at`, so timing is durable with no reset and no duplicate
generation; the 3600/900 ceilings unchanged; a lifetime beside a permission
refused; the policy refusing a resolution its owner would not produce;
the policy answering `None` when there is nothing to resolve; `factory`
supplying a callable policy; and the composition retaining it, with
`lifetime_policy` present in every forwarding signature and `seconds` in
`prepared_workspace_governance`.

### The policy inputs, clarified as the review required

The three checkout steps, the 900-second per-step allowance and the
120-second cleanup reserve are **selected native policy inputs** — taken from
this build's own `CHECKOUT_SECONDS` and three-step version-control plan and
from the pilot's own `cleanup_observation_seconds`. They are **not** a
universal elapsed-time proof, and the module docstring says so in those words.
What follows from the Job rather than from a selection is the pair of
invocation boundaries, resolved through their owner and never re-derived.

### Verification

- **Focused: 11 tests, OK.**
- **Affected modules only: 6 modules, 695 tests, 5.385s, OK** — the review
  directed no routine repeat of the 2175-test/288s sweep, so this is the set my
  five paths actually touch.
- The prior 2175-test run and its three-arm attribution of the single
  pre-existing baseline failure remain author evidence from claim354424.

**No product defect was exposed by the rewritten proof, so the four product
paths are unchanged from claim354424** — `execution_limits` `24f27d77…`,
`workspaces` `7db36ee6…`, `single_worker` `70cc0806…`, `stage_execution`
`765c1567…`. Only the test file changed, to `a94903fe…`.

### Still owed

Both native stages **end to end through the serving loop**: composition and
acquisition are proved per attempt and forwarding is proved for every
signature, but no case yet drives an implementation stage *and* a review stage
through `serve()` to their own acquisitions. Exact host **cancel** — expiry and
reclaim are proved through the real owner, cancellation is not. Cleanup and
unknown holds beyond the expiry-is-not-release and resource-stays-held
assertions. And the joined owner-produced cause through durable capture, `/7`
status and the packaged secret-free report.

### Cost and boundaries

Measured: focused 0.062s, the two disconnection arms 0.063s and 0.065s,
affected modules 5.385s, plus unmeasured reading. No live instance, engine,
provider or credential; no deployment, recovery, migration or shared import; no
version-control mutation — reads only. The disconnection arms are throwaway
copies under `/tmp` and are not candidates. Prior spending retained:
claim354424 288.769s joined-plus-seams, claim354259 14.254s + 0.213s,
claim354165 14.213s, claim354320 and claim354357 none.
