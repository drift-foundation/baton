# W337955 diagnostic result — awaiting independent review

Author: baton.codxpc, claim338073, owner exception338070. Product code unchanged.

## Confirmed mechanism

The committed controller and baseline allocate incompatible shutdown windows.
`authoring_enforcement.supervise_process` sends SIGTERM and sets its deadline to
at most `now + cleanup_seconds`. It reserves `min(12, cleanup_seconds / 2)` for
its own final steps, then unconditionally kills/reaps the manager before reading
the final enforcement snapshot. With the live60-second allowance this leaves
at most48 seconds for the manager to finish.

`baseline.supervise` replaces the child_main handler with Termination. SIGTERM
raises during serving, is caught, closes admission, and switches Termination to
deferred mode. Baseline then starts a NEW full cleanup_seconds window (line1293),
bounded only by its original total limit. In the early-token-expiry case that
total limit is much later. It waits while committed cleanup remains outstanding,
even after the separate enforcement thread observes exact runtime absence and
returns the token. Only after that window and final accounting does baseline
publish its workload outcome and return. Only then does child_main finally call
Guard.stop, set shutdown, join, and finish/publish the guard snapshot.

The real composition reproduces SIGKILL inside that cleanup window with no
baseline outcome and no finished guard snapshot. It requires no deadlock and no
unresponsive enforcement thread. A blocked serving sweep is interruptible in the
fixture and still reaches the same failing cleanup sequence.

For the shortened4-second cleanup fixture:

| Case | SIGTERM | Cleanup deadline | SIGKILL | Result |
| --- | ---: | ---: | ---: | --- |
| Blocked serving sweep | 3.753635s | 7.768618s | 5.753891s | Absent/returned token; no final reports |
| Absent writer, outstanding cleanup | 3.753671s | 7.769707s | 5.754001s | Absent/returned token; no final reports |

Times are monotonic offsets from each outer fixture entry, not token durations.
Guard.stop was never entered in these two cases. The extra deferred-mode SIGTERM
in the second case returned normally and was recorded twice in Termination's
received list; it did not interrupt cleanup.

## Five comparisons and phase controls

All assertions in `../analyze.py` pass over `comparisons2/analysis.json`.

| Comparison | Observed result |
| --- | --- |
| Ordinary supervisor return | Fake create refuses, baseline returns held with workload outcome and finished guard snapshot; child1; no SIGTERM. This is orderly failure completion, not a successful authored workload. |
| Expiry during blocked serving sweep | Real SIGTERM interrupts injected20-second sweep wait; cleanup starts; exact fake runtime absent/token returned; child-9 before cleanup deadline, both final reports missing. |
| Exact writer absent, cleanup still pending | Unmodified cleanup loop continues on its real outstanding cleanup journal; no artificial cleanup blockage needed; child-9 before baseline return. |
| Delayed final snapshot | Baseline workload outcome is already on disk; a6-second publication delay loses final guard snapshot at outer kill. A0.01-second control publishes it and exits130 before kill. |
| Unknown engine cessation | Explicit uncertain observation/reclaim/settlement, revoked token not returned, held result. Final reports can exist while cessation remains unknown; report presence does not establish cessation. |

A pre-supervision signal control delivers SIGTERM after Guard.start and before
baseline entry. The real child handler sets stopping; child_main takes its
no-admission path, never starts baseline or the author invocation, and publishes
the final guard report. Together with raising serving and deferred cleanup
observations this disproves the original phase-independent stopping-only theory.

The final snapshot comparison also identifies a separate failure location:
RemoteGuard.stop ignores its timeout and refreshes once, after manager kill/reap.
A missing finished snapshot is held conservatively. That is appropriate fail-closed
behavior; it is not proof that a previously observed exact runtime is still alive.

## Historical relationship and limits

`retained-revalidation.json` verifies all10 original report/partial-source hashes
from review337693 and337905, without opening their stores or operating their
engines. Historical elapsed955.098994 and954.105032 seconds agree with each token
expiry plus the48-second outer slice:955 approximately vs954.935 predicted,
954.105 vs954.118 predicted. The comparisons use envelope start and recorded
token timestamps; outer timing starts slightly later and polling adds jitter.
They support this mechanism but do not reconstruct either live stack. The exact
historical blocking line remains unobserved. No live rerun is needed to establish
the reproduced deadline-composition defect.

The fake OCI engine owns no container. Its absent/uncertain observations are
simulation, never proof of live physical cessation. The ordinary-return control
does not prove successful provider output. Delayed snapshot is an injected
filesystem-publication stall, not a claim that the historical filesystem stalled.
No product fix, full renewal correctness, restart recovery, retained allocation
release, or authoring readiness is accepted by this diagnostic.

## Smallest correction recommendation (not implementation authority)

Select a coupled shutdown-deadline correction: give baseline cleanup a manager
deadline within the outer deadline, reserving time for workload accounting,
Guard.stop/join and final snapshot publication. Propagate the current bounded
shutdown allowance instead of starting a fresh full cleanup window on SIGTERM.
Preserve original total/provider/token limits and the outer hard stop. Simply
increasing token duration, weakening holds, or waiting longer without bounded
I/O does not address the observed composition.

All cleanup/ending steps on that path must honor the remaining deadline; a
deadline check only between unbounded sweeps is insufficient. When a step cannot
finish, retain a bounded honest partial/failure report identifying that step,
known runtime observation and outstanding accounting. Keep unknown runtime or
launch effects held. Do not infer workload success or release unresolved
ownership from a report filename, token expiry or manager death.

Acceptance for a separately selected correction: these same real-composition
expiry cases must publish honest workload/enforcement outcomes before the outer
cutoff when cleanup is cooperative; genuinely stalled finalization must remain
bounded with explicit partial/unknown evidence. Ordinary return and pre-serving
admission fence must remain correct; unknown cessation must retain the token.
Independently review the exact candidate under its own execution selection.
This diagnostic authorizes no third authoring run and no product patch.

## Provenance, reproduction and spending

Exact source base and hashes are in `comparisons2/source.json`; all293 exported
source files are checked unchanged in `source-unchanged.json` (the file's count
is authoritative). `HARNESS.json` binds the diagnostic and assertion scripts.
Stores, authority, stage composition, workspace guard, admission, tokens,
controller, baseline and signal handlers are real disposable instances. Only
external OCI/provider behavior, packet/image validation, setup source materializer,
timing and the named delay/block probes are substituted. The source materializer
creates a disposable directory and refuses freeze/validate; it manufactures no
accepted checkpoint. No credentials are read. Instrumentation logs real function
entry/exit and phase times without replacing shutdown control flow.

From repository root, choose a NEW absolute disk-backed dossier evidence path:

```sh
python3 -B work/records/2026/10/finding-v12-authoring-expiry-finalization/diagnose.py --repository "$PWD" --output "$PWD/work/records/2026/10/finding-v12-authoring-expiry-finalization/evidence/review-fresh"
python3 -B work/records/2026/10/finding-v12-authoring-expiry-finalization/analyze.py work/records/2026/10/finding-v12-authoring-expiry-finalization/evidence/review-fresh
```

All seven final fixture managers were reaped and their PIDs absent; manager
guards were reacquired after each. Each case has a30-second process timeout plus
5-second reap allowance. Final measured process time40.351628s; cumulative
measured fixture process time99.374756s including every exploratory run.
Source extraction, setup, hashing, analysis and read-only preparation overhead
were not stopwatch-accounted; no full-turn upper bound is asserted. Earlier
claim337974 spending remains unknown. Claim338031 ran no tests.

Exploratory schema/tmpfs/materializer failures and the first analyzer's incorrect
expectation that uncertainty must appear in `faults` are preserved in PROGRESS
and RUNS.json. The corrected assertion checks actual typed uncertain observation
and held settlement; genuine unknown coverage is retained. The inherited Git
materializer attempted an unsuccessful clone in probe2; no Git repository/index
was created. Final fixture processes prohibit external executables and use the
setup adapter. Product source, accepted tests and Git state were not modified.
