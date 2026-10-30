
## 2026-10-22 — baton.claude, claim354424 — THE NATIVE CONNECTION IS IMPLEMENTED; THE LIFETIME IS COMMITTED

Claimed at snapshot354424 after reading canonical state (queued, unclaimed,
routed `baton.impl`, `last_change_seq 354404`, zero open blockers, child
W354389 now contained and open), the complete handoff through `work-events` (75
events, no pagination remaining) and thread T325959 in full (5 messages,
`last_seq 329708`, unchanged).

### Both unknowns closed by enumeration, not estimate

Every `*_SECONDS` constant in the worker adapter and the manager-side attempt
path was enumerated and classified by **where in the lifecycle it applies**.
**No additional bounded operation sits between acquisition and cessation.** The
two real candidates resolved against themselves: `workspaces.TOKEN_SECONDS`
(900) is the **removal** token family — *"how long a removal may hold the
roots"*, used only at `workspaces.py:4246` — not the attempt's task token; and
`custody.CUSTODY_SECONDS` (1800) bounds a custodian discard, which is
cleanup-side at or after cessation. `maintenance.PREPARE_SECONDS` and the
offer TTL are pre-acquisition; `oci` observe/list/remove and
`tokens.STOP_GRACE_SECONDS` are manager- or cleanup-side and are not work the
worker's permission must cover.

So the attempt's authorized in-workspace work is exactly **checkout + one
provider turn + one verification**.

### The lifetime, committed and composed from named bounds

`execution_limits.task_token_seconds(resolved)` =
`CHECKOUT_STEPS × CHECKOUT_SECONDS + provider_turn + ordinary_verification +
CLEANUP_RESERVE_SECONDS`. Each addend is named rather than estimated: 3 × 900
from `claude_agent.py:356` and the three-step version-control plan; the two
boundaries from **the Job's own resolution**, not constants; 120 from the
pilot's `cleanup_observation_seconds`. The pilot resolves to **7320**, and it
**follows the Job** — a Job selecting 120/45 resolves to 2985, proved by a
case. This is **not the floor accepted as a value**: the floor was addition,
this is a composition whose every term has an owner.

Classified **LIM-2**: derived per attempt, each attempt acquiring its own
token, so nothing accumulates across the Job's stages.

### The connection, implemented

- `prepared_workspace_governance` gains `seconds=None`; `reserve` passes it to
  `tokens.acquire` only when resolved, so `acquire`'s `seconds`/`permission`
  exclusivity holds and every pre-existing caller keeps the default.
- `single_worker` threads `lifetime_policy` through `operations_from` →
  `worker_operations` → `_Composition`, called beside the accepted
  `permission_policy` at the acquisition.
- `stage_execution.native_lifetime_policy` resolves the lifetime from the Job's
  admitted configuration **through its owner** — `owned_execution_limits` +
  `owned_generation` + `resolved`, refusing a document the owner would not
  produce — and **`factory` now supplies it**. That is the caller that did not
  exist.
- **No envelope.** Nothing native reads `stop_at`, so an envelope would record
  a deadline no native party enforces.

### Verification

- **Focused: `tests.job_manager.test_native_permission`, 7 tests, OK.**
- **Red before green:** the same cases with my four product edits reverted to
  baseline/supplier bytes give **7 tests, 5 errors**.
- **Joined plus affected seams: 18 modules, 2175 tests, 288.769s, 1 failure.**
  That failure —
  `test_single_worker…test_a_real_observing_status_run_mutates_no_durable_state`
  — fails **identically on three arms**: mine, the composed arm with my edits
  reverted, and the **pure pinned baseline `d6881d8a` with no supplier at
  all**. Pre-existing at the baseline, not introduced by either supplier nor by
  me, and not fixed by me.

### Still owed

My cases prove the composition, the acquisition accepting it, the exclusivity
refusal, and that a native-lifetime token survives past 900 yet still expires
and is **not released**. They do **not** yet drive both implementation and
review stages end to end through the serving loop; host stop/cancel governing
the exact runtime and cleanup/unknown holds are covered only by the
expiry-is-not-release assertion; replay/restart with durable original timing,
no revival and no duplicate effects is not proved; and the joined
owner-produced failure through durable capture, `/7` status and the packaged
report is not done.

### Cost and boundaries

Changed: four product files plus one new test file, all in the isolated root —
`execution_limits.py` → `24f27d77…`, `workspaces.py` → `7db36ee6…`,
`single_worker.py` → `70cc0806…`, `stage_execution.py` → `765c1567…`,
`test_native_permission.py` → `0468e72c…`. The 31-path composition is retained.
Measured: focused 0.008s, red arm 0.008s, joined-plus-seams 288.769s once, plus
unmeasured reading. No live instance, engine, provider or credential; no
deployment, recovery, migration or shared import; no version-control mutation —
reads only. Prior spending retained: claim354165 14.213s; claim354259 14.254s +
0.213s; claim354320 and claim354357 no product test.
