# W337955 implementation checkpoint

## 2026-10-20 — baton.codxpc, claim338031

Incomplete diagnostic; returned for execution-boundary resolution. Read canonical
detail, complete W337955 events through338031 (no continuation), and T337955
through337955 (no continuation). Read bound FINDING/PLAN and owner parent event
337938 directly, plus parent events through337958. No product/test edits, fixture
execution, provider/engine invocation, retained-instance mutation or Git mutation.

### Revalidation and concrete boundary

AGENTS.md's October18 execution rule requires executable work in isolated v12
Jobs with no general host fallback. Owner337938 says “Assessment and preparation
only; no provider invocation, recovery, rerun, product implementation or integration
authorized.” Child handoff337971 selects real local deterministic process fixtures
but explicitly grants no execution exception; neither bound file supplies a
selected v12 diagnostic Job/adapter/packet. The exact unresolved operation is
starting the diagnostic subprocess composition directly on the host. No denied
command or engine failure is claimed. Before that launch, reconcile the handoff
with the owner boundary: select an isolated non-live v12 diagnostic execution
vehicle, or obtain an explicit bounded direct-diagnostic exception. Existing
exceptions must not be revived. This is not a request for test-path approval.

### Static preparation findings (not dynamic acceptance)

Current source hashes:

- `v12/python/tools/authoring_enforcement.py`: SHA256
  `bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f`.
- `work/records/2026/09/finding-v12-single-implementation-proof/baseline.py`:
  SHA256 `c1b0a10e609503df0ba7ebdc7455cc8518c9175882edd185b65f20c342c4bd2f`.

Confirmed by reading current code:

1. `child_main` installs handlers that set `guard.stopping` (line445), calls
   baseline.main (457), and reaches guard.stop/final publication only in its
   finally (459–464). Guard._run polls shutdown, not stopping (191);
   Guard.stop sets shutdown and joins (213).
2. Crucial refinement to the dossier's inference: baseline.supervise installs
   `Termination` (1057), whose install replaces SIGTERM/SIGINT handlers (271).
   While serving, its handler raises KeyboardInterrupt (294–300); the serving
   wrapper catches BaseException (1216), closes admission and calls defer
   (1230). During cleanup, later signals are recorded without raising.
   Thus signal behavior depends on phase; it is NOT established that the
   child_main stopping-only handler remains active throughout baseline.main.
3. Outer supervise_process terminates once, reserves a tail, then kills/reaps
   the child before RemoteGuard.stop reads final status (258–306).
   RemoteGuard.stop ignores its timeout and performs one refresh (412–418).
   Missing finished snapshot yields held even with an absent-runtime observation.
   This conservative result is not itself proof of a physical cessation failure.

No exact historical blocking stage is established. No source-only claim of a
deadlock, successful finalization, or correction acceptance is made. An initial
read of shortened dossier locations `tools/authoring_enforcement.py` and
`tools/baseline.py` failed with ENOENT; actual repository paths above were found
and read. This was a locator-prefix issue, not unreadable required evidence.

### Prepared diagnostic acceptance packet

Use fresh writable disposable stores and exact hashed committed source; retain
the real controller/manager process topology, manager lock ownership, baseline
Termination and guard thread. Substitute provider/engine only at their normal
boundaries. Inject short lease and cleanup timings; do not replay900 wall seconds.
Trace monotonic event times and PID for signal installation/delivery, serving
return, cleanup entry/return, guard shutdown/finished, snapshot replacement,
outer terminate/kill/reap and workload report publication.

Required comparisons: normal completion; expiry while sweep is blocked;
simulated exact writer absence with baseline still in cleanup; final snapshot
delayed around the outer kill boundary; unknown engine cessation. Split signal
delivery across pre-supervision, serving, and deferred-cleanup phases. Bound each
case and confirm every fixture process reaped. Preserve unknown holds and one
manager/admission semantics; absence supplied by the fake is simulation only.

Remaining: execution selection, concrete fixture implementation, all five
dynamic comparisons, measured run/cleanup evidence, retained-input revalidation,
digest-bound diagnosis and smallest justified correction recommendation for
independent review. Do not recommend a product change based solely on the
stopping-only hypothesis. Reviewer owns FINDING/PLAN updates; this checkpoint
does not silently supersede them.

Verification spending this claim: 0 test/fixture execution seconds. Prior failed
claim337974 has no retained execution evidence in this dossier; historical
spending is unknown, not assumed zero. No fixture processes were started by this
claim. Existing parent-run durations remain unchanged historical evidence.

## 2026-10-20 — baton.codxpc, claim338073, diagnostic execution in progress

Read events338051–338073 including exact owner338070 and T337955 unchanged;
read current FINDING/PLAN, EXECUTION-DECISION and review03-05-43. Pinned new owner
exception in FINDING and current milestone in PLAN before execution, as owner
expressly required. Earlier unselected execution checkpoint is superseded.

Own diagnose.py and evidence only. Fixture exports exact owner-selected commit
read-only, uses real controller/child_main, Guard/Lane, baseline.main/supervise,
Termination, public store APIs, real stage composition and workspace manager
guard. Provider/OCI is fake. Setup packet validation is replaced by fixture
construction plus exact source hashes; source materialization uses a named
deterministic checkpoint adapter (no checkpoint is frozen/accepted). This
additional setup seam prevents Git operations; it is not shutdown evidence.
Real process Popen is restricted to the fixture Python executable thereafter.

Preparation probes are retained, not acceptance: probe1 used old submission
schema and refused execution_limits; probe2 reached the inherited Git profile
which attempted and failed clone from a nonexistent fixture repository (no Git
repository/index created); probe3 refused tmpfs-backed workspace. This failed
Git attempt is an operational finding against this fixture, not a claimed Git
mutation or a product defect. The final fixture substitutes source materializer
and prohibits external executable dispatch. Cases now use dossier-owned disposable
disk-backed storage while source copies are read-only under /tmp. Failed optional
source-location reads were resolved with rg; required source remains readable.

Probe4 and comparisons1 reproduce absent/returned token with killed manager and
missing final reports. Real baseline cleanup begins on SIGTERM with its full
cleanup_seconds, whereas outer supervise_process kills after reserving its tail
from that same cleanup allowance. Comparisons also expose delayed final snapshot
as a separate missing-report mechanism. None establishes the historical live
blocking stack. Final adjusted controls and assertions remain in progress; do
not read exploratory exit codes as diagnostic acceptance.

### Completed diagnostic handoff, claim338073

Deliver `evidence/DIAGNOSIS.md`, `diagnose.py`, `analyze.py`, and digest-bound
`evidence/MANIFEST.json`. Five comparisons plus pre-supervision and short-snapshot
controls pass assertions over comparisons2. Every manager reaped, named PID absent
and real workspace guard reacquired; all293 exported source files unchanged.
No v12 Job/attempt is claimed: this is the explicitly selected direct diagnostic
exception, with real disposable manager attempts recorded in case evidence.

Confirmed reproducible mechanism: outer reserves a tail from cleanup_seconds,
but baseline begins a full cleanup_seconds window after the serving SIGTERM.
In blocked-sweep and absent-writer cases the manager is killed during its real
pending-cleanup loop before baseline outcome/Guard.stop/final snapshot. A separate
delayed-snapshot case loses the guard report AFTER workload publication. Unknown
engine observation retains its revoked token and held result. Ordinary return is
an orderly fake-start failure, not successful authoring. Pre-serving signal prevents
author invocation. No historical live stack or live cessation proof is invented.

All10 original retained report/partial hashes revalidated read-only. Both historic
durations match token expiry plus48-second outer slice within polling/start-time
offset; this is corroboration, not exact historic stack attribution. Required
smallest correction and acceptance are recommendations in DIAGNOSIS; implementation,
renewal completion, recovery and a third authoring run remain unauthorized.

Measured fixture subprocess spending99.374755971s cumulative this claim, including
40.351627708s final matrix and all exploratory runs. Setup/source extraction,
hashing/analysis overhead not measured; claim337974 historical total still unknown.
Analyzer first failed because it looked for uncertainty in the faults list; actual
typed uncertain observation/held settlement retained it, and the corrected assertion
checks that real contract. No production/test expectation was changed.

No product or accepted test files edited. Owner ruling pin necessitated append-only
FINDING and current PLAN clarification; reviewer continues to own substantive
FINDING/PLAN/review. Await independent diagnostic acceptance. Human checkpoint
after acceptance remains due; proposed message: `Record bounded authoring shutdown
deadline diagnostic and reproduction`. No commit has been made by this agent.
