# Progress — baton.claude, W183883 claim183891

The persistent v12 stack lifecycle, delivered through `v12/justfile`.

## What an operator can now do

```sh
cd v12
just start      # the scheduler and its snapshot publisher
just status     # process health, snapshot freshness, observed Jobs, config gaps
just monitor    # the read-only view; Ctrl-C to leave it
just stop       # only the processes this stack owns
```

One-time setup, the four required operands and every reported state are in
`v12/STACK.md`. Existing recipes — `default`, `install`, `test`,
`test-authority`, `proof`, `state`, `state-clean` — are untouched.

## Exact changed paths

| Path | Change |
| --- | --- |
| `v12/python/tools/stack.py` | new — the lifecycle helper |
| `v12/justfile` | four recipes appended |
| `v12/python/tests/tools/test_stack.py` | new — 32 focused lifecycle checks |
| `v12/python/tools/parallel_test.py` | one registry entry, justified in PLAN |
| `v12/STACK.md` | new — the operator runbook |

## The two decisions worth stating

**Two owned processes, not one.** `start` runs `job_manager serve` *and* a
snapshot publisher, because `JOB-VIEWER.md` requires **atomic** publication and
the viewer reads a document rather than a store. Publication belongs to `start`
rather than to `monitor`, which is what makes "quitting the monitor does not stop
scheduling" true: the monitor only ever reads a file.

**Ownership is proved, not assumed.** A pid file is a claim and pids are reused,
so every record carries the process's own start time from `/proc`, and a process
is signalled only when the pid *and* that start time both match. A recorded pid
that now belongs to something else — including v11's — is reported stale and
never signalled. There is a test for exactly that.

Nothing here is a stand-in scheduler: the manager runs the accepted
`tools.stage_execution:factory` over the operator's own stores. A missing
configuration **refuses** rather than reporting a comfortable idle, and an empty
*configured* stack is reported as the valid idle state it is.

## Verification

**32 focused lifecycle checks, OK, ~1.19 s** — deterministic local processes the
test owns; no scheduler, provider, engine, Docker, network or v11 service, and
the one real `job_manager` invocation is injected. They cover first start,
repeated start, stale-record replacement, stop, repeated stop, restart, an
unrelated process left untouched, pid reuse in both directions, atomic
publication, a failed publish leaving the previous snapshot, and the
absent/running/stale/unreadable distinctions.

**And I ran the recipes**, against a disposable state root: unconfigured `start`
refuses naming all four operands at once; `monitor` without a snapshot refuses
with what to run first; `start`/`status`/`stop` and their repeats behave as
documented.

## Two defects, both found by running rather than reading

**`alive()` called a zombie running.** A terminated-but-unreaped process keeps
its `/proc/<pid>/stat` entry with its original start time, so an identity match
alone reported a corpse as healthy — and `stop` then sat out its entire grace
period waiting for it. The lifecycle test caught it; state `Z` is now the
difference between still running and not yet reaped.

**The publisher argv was rejected by its own parser.** `--root` is a top-level
operand and I put it after the subcommand, so the publisher exited immediately.
Every unit test called `publish()` directly, so nothing exercised the argv
`start` actually builds — only running the recipes did. A regression now parses
the argv `start` produces, in both orders.

## One pre-existing condition, reported rather than fixed

`tools/parallel_test.py`'s registry **already refuses**: five test modules belong
to no registry — `tests.manager.test_claude_context`,
`tests.manager.test_provider_context`,
`tests.manager.test_provider_context_delivery`,
`tests.tools.test_correction_restart` and `tests.tools.test_managed_apply`. All
five have mtimes from 14–15 September, before this claim began, and
`tests.tools.test_stack` is **not** among them — my entry works. They belong to
other in-flight Works and the PLAN forbids unrelated cleanup, so they are named
here rather than quietly adopted.

## Not done

No v11 service, store or configuration edit; no Git operation; no backlog
migration; no Job submitted; no live provider or engine call; no disposable proof
run; no rich TUI; no distributed scheduling; optional session reuse W177936 stays
parked. Starting the stack selects no work.

## claim183998 — R1-R4 corrected, re-verified, and the idle stack actually run

Read the complete handoff (183958 claim, 183986 changes-requested pass, 183992
bug triage, 183994 forward to impl) and the bound review. Revalidated the five
candidate hashes in `EVIDENCE-183891.json` against the working tree before
editing: all five still matched, so the review was made against exactly what is
there. All four findings are real and all four are mine. Correction decisions
were pinned in `PLAN.md` before any edit.

**R1, lifecycle admission.** `start` was read-decide-spawn-record with nothing
covering the gap, and sequential repeat-start coverage could not see it. There
is now one exclusive `flock` on `<root>/lifecycle.lock` held across the WHOLE
ownership transition, taken by `stop` as well so the two cannot interleave. A
kernel lock rather than a lock file, so killing a start releases it. `_spawn`
also stops and reaps its own child when the record write fails, which was the
other way an admitted process could end up owned by nobody.

**R2, unknown ownership.** `read_record` already told unreadable from absent and
then `start` fed the answer into a liveness test, where False licensed a
replacement. Ownership is now four-state — `absent` / `live` / `gone` /
`unknown` — and `gone` is POSITIVE: no `/proc` entry, a start time that
disagrees, or state `Z`. A denied `/proc` read is `unknown`, not absence.
`start` refuses on `unknown`, retains the record, names the recovery and
signals nothing; `stop` retains it and returns non-success.

**R3, the runtime prerequisite and readiness.** The recipes ran a bare
`python3`, so the manager died on `ModuleNotFoundError: No module named
'baton_v12'` — and `monitor` could not have started either, for the identical
reason, which the review named and I had not checked. `child_environment` now
builds `PYTHONPATH` ABSOLUTELY from this distribution's `src` and `.` for the
manager, the publisher and the publisher's own `job_manager status`
subprocess; all four recipes name it too. `start` then waits, bounded, for
POSITIVE acknowledgement: every owned process still live AND a snapshot
published DURING this start, compared against a mark taken before spawning so a
previous run's document cannot be mistaken for this one's. Failure carries the
child's own last words out of its log, unwinds, and clears a record only for a
process it positively stopped.

**R3, composition — built rather than reported.** Before writing anything I
composed the literal `tools.stage_execution:factory` against a relocated real
deployment. It passed document validation, the Authority open, the five
sessions and their receipt capability grants, the pool generation compare and
all three `worker_preflight`s with no Docker and no provider, failing only on a
five-day-old fixture's integration-store schema. So an empty idle stack CAN
run, and reporting a missing deployment input would have been the easier answer
rather than the true one. `ValidIdleComposition` now reuses the accepted
`ServingCase` deployment fixture on a disk-backed root OUTSIDE the checkout,
creates an EMPTY Job store, and drives the REAL `tools.stack` children and the
REAL `job_viewer`. Nothing is substituted, because a separate child process is
exactly a composer that cannot inject. Its counterexample runs the same
machinery over a document the child refuses and gets a non-zero start carrying
that refusal.

**R4, honest stop.** Non-success for any unresolved owned process, whose record
is retained. And every `stop` and `status` prints a runtime boundary read from
the last snapshot — open episodes and recorded runtimes — or `unknown` when
that snapshot is absent, unreadable or stale. Supervisor exit is never read as
work completion, and a stale document is not read as a current one.

**Verification.** 63 focused checks, up from 32, returncode 0 in 23.368s.
Nineteen reversal probes in an isolated copy of `v12/`, one guard reverted per
probe; every one FAILED as required, 128.540s, and the restored copy hashes
identically to the working tree. One probe's first form was malformed and
failed on a SyntaxError — that proves nothing, so it was re-run well-formed and
recorded as such rather than counted. The four recipes were exercised for real:
`just status` and `just start` unconfigured, `just monitor` with and without a
snapshot. The monitor rendered a real status document; before this correction
that recipe could not import at all.

**What I did not do.** No live provider, no engine run, no Job submitted, no
v11 path, service, store or configuration touched, no version-control
operation. `tools/parallel_test.py` was not touched again this claim. Its
fail-closed registry still refuses the whole runner over five unregistered
modules belonging to other in-flight Work, all with mtimes of 14-15 Sep that
predate this claim; `tests.tools.test_stack` is registered. Preserved as an
operational finding, not adopted. The probe tree copy and the relocated
deployment probe — including a copied fixture credential file — were removed
after use, and every child this claim started was reaped.

`EVIDENCE-183998.json` carries the candidate hashes, the per-finding check
lists, the probe results and the cumulative verification spending, which is
reported per actor rather than summed: this claim 151.908s (23.368s tests plus
128.540s probes), author claim183891 1.195s, reviewer claim183958
1.5529989219503477s including its own test subprocess, and the earlier recipe
execution duration still unknown rather than erased.

## claim184239 — C1-C4 corrected, and one line added outside my five paths

Read the complete handoff (184197 claim, 184237 changes-requested pass) and the
bound review. Revalidated the five candidate hashes in `EVIDENCE-183998.json`
against the working tree before editing: all five matched. All four findings
reproduce and all four are mine. Decisions pinned in `PLAN.md` before any edit,
including the one path outside the five this Work owns.

**C1, visibility lost during cleanup.** My last round fixed ownership that was
unknown when `start` first looked, and left both cleanup paths waiting on `LIVE`
and clearing the record for every other answer. So a process whose `/proc`
stopped answering AFTER it was signalled was announced `stopped`, its record
deleted, and `stop` returned 0 — while it was still running. Both paths now
require a POSITIVE `gone` before clearing a record or announcing anything; the
process keeps its record and the stop is not a success. This is the same
mistake as the original R2, one step further along the path, which is the third
time review has caught me fixing the case rather than the class.

**C2, only a refusal unwound.** `_spawn` raises `OSError` from opening the log,
from `Popen` and from writing the record, and `_start_admitted` caught
`StackRefusal` alone — so a publisher that failed after the manager had been
admitted escaped with the manager running. It now catches `BaseException`,
unwinds what this start admitted, and re-raises the ORIGINAL error unchanged:
a cleanup problem must not replace the failure that caused it, which is the
rule `job_manager` already keeps for its own releases.

**C3, readiness was bound to the wrong process.** `observation_from` builds a
reader out of a held configuration and composes nothing; `operations_from` opens
the Authority, mints and authorizes five sessions, runs three worker preflights,
opens the integration store and activates the pool. A published snapshot is
therefore evidence about the OBSERVER, which is why a `SIGSTOP`ped manager
passed my gate. Nothing this Work owns can acknowledge an initialization that
happens inside another process, so — pinned in PLAN first, as the review
required — `tools/job_manager.py:_serve` gained ONE line on stderr after
`_operations_from` returns. `start` now requires that line, naming THIS start's
incarnation, at an offset after this start opened the log. Incarnations are
unique per start, which `DEPLOYMENT.md` already required for its own reason.
Observer publication is retained as the separate observation check and
tightened: the document must also be valid and fresh by its own `observed_at`.

**C4, the document was walked before it was validated.** `runtime_boundary`
guarded the parse and then traversed jobs, stages and episodes outside that
guard, so `{"jobs": [null]}` raised `AttributeError` out of a `stop` that had
already signalled. One local validator now answers for `_jobs`,
`runtime_boundary` and freshness — schema, canonical, a readable `observed_at`,
and the nested shape — before anything traverses. Age comes from the document's
own `observed_at` with the file's write time beside it, so a document copied
into place reads as freshly written and stalely observed, which is what it is.
`STATUS_SCHEMA` is pinned locally to keep this helper standard-library-only, and
a check holds the copy equal to the package's own.

**Verification.** 86 focused checks, up from 63, returncode 0 in 25.008s. The
168 existing checks nearest the `job_manager` delta pass unchanged in 6.339s.
Fifteen reversal probes in an isolated copy; the restored copy hashes
identically to the working tree. TWO PROBES PASSED FIRST TIME AND SO PROVED
NOTHING. One named a check that never reaches the branch it reverted, and was
re-run against the check that does. The other found that no check held the
log-offset half of the acknowledgement — the incarnation alone was deciding
every case — so I ADDED a check for it rather than quietly dropping the guard,
and it then failed as required. Both are recorded as such rather than counted
as clean.

**The two composition cases the reviewer could not run, ran here** — their
`/tmp` is tmpfs and `/var/tmp` was outside that authority — and they now also
assert the acknowledgement end to end: a real line, from the real serving loop,
naming the incarnation this start gave it.

**A second pre-existing condition, reported not adopted.**
`tests/tools/test_stage_execution.py` has 12 errors —
`AttributeError: 'types.SimpleNamespace' object has no attribute 'reconciles'`
— in two integration-port classes. I proved they predate my change by reverting
the `job_manager` line in place, re-running, and restoring the file to its exact
prior digest. They belong to the integration-port Work of 14-15 September. The
five unregistered `parallel_test.py` modules are unchanged and still reported.

**What I did not do.** No live provider, no engine run, no Job submitted, no v11
path, service, store or configuration touched, no version-control operation.
`v12/justfile` and `tools/parallel_test.py` were not touched this claim. The
probe tree copy and the recipe state root were removed, and every child this
claim started was reaped.

`EVIDENCE-184239.json` carries the candidate hashes, the per-finding check
lists, the probe results including both probes that proved nothing, and the
cumulative spending reported per actor rather than summed: this claim 127.816s,
claim183998 151.908s, claim183891 1.195s, reviewer claim184197
12.840890395978931s, reviewer claim183958 1.5529989219503477s, earliest recipe
duration still unknown.

## claim184442 — D1 and D2, and a defect of my own that a new check caught

Read the handoff (184403 claim, 184436 pass) and the bound review. Revalidated
the six candidate hashes in `EVIDENCE-184239.json` against the tree before
editing: all six matched. C1 and C4 are verified; D1 and D2 are the remainders
of my own C2 and C3, and both reproduce. Decisions pinned in `PLAN.md` first.

**D1, the fallible second write is gone rather than guarded.** `_spawn` wrote
the record, `_start_admitted` wrote it AGAIN to add the incarnation, and only
then registered it for rollback — so a failure in that second write escaped with
the manager live and outside the unwind it had been promised. The review offered
two remedies and I took the stronger one: `_spawn` publishes the whole identity
in one owned transaction. The other post-spawn write went too — the
`serving_acknowledged` flag was a CACHE of what the manager's own log already
says, which is both a write that can fail and a second place the truth can live.
`acknowledged()` reads that log directly, so no record write happens after
`_spawn` at all. `_unwind` now also contains failure per process, so one that
cannot be taken back never stops the others being accounted for.

**D2, liveness is not readiness for an inherited manager either.** I wrote last
round that "a manager that was already running is not this start's to
acknowledge; the start that admitted it proved it." That is false after an
interrupted start, and false after an unwind that deliberately retained a live
process it could not stop — and in both cases `start` returned 0 while `status`
said, at the same moment, unacknowledged. A live manager is now reused only when
`acknowledged` holds for that identity NOW; otherwise it enters the same bounded
wait a fresh one does and the start refuses. It is never killed and never
duplicated — this start did not admit it — so the refusal names it and the
recovery. An already acknowledged manager is never asked to initialize again.

**A defect this claim introduced, caught by one of this claim's own checks.** I
first signalled the repeated-start path with `mark is None`, which is also true
on a genuine FIRST start with no previous snapshot — so a first start would have
skipped the observation check entirely. The containment case stopped raising and
showed it. It is now an explicit `require_snapshot` operand, and a probe holds
the wrong spelling out.

**Verification.** 96 focused checks, up from 86, returncode 0 in 26.132s; the
168 adjacent checks still pass in 6.318s. Nine reversal probes, 31.082s, restored
copy hashing identically to the working tree. ONE PROBE PASSED FIRST TIME: the
check I had written for the one-write transaction substituted `_spawn`, so it
could not see the real one's write count at all. I rewrote it against the real
`_spawn` and added a second check for `start`'s own writes; the probe then failed
as required. Recorded rather than counted.

**What I did not do.** `job_manager.py`, the justfile and `parallel_test.py` were
not touched again. No live provider, engine run, Job submitted, v11 operation or
version-control operation. Both preserved operational findings are unchanged and
still reported. Scratch removed; every child reaped.

`EVIDENCE-184442.json` carries the hashes, per-finding check lists, probe results
including the one that proved nothing, and spending reported per actor: this
claim 63.532s, claim184239 127.816s, claim183998 151.908s, claim183891 1.195s,
reviewer claim184403 20.8455910270568s, reviewer claim184197
12.840890395978931s plus its separate 0.002758326008915901s, reviewer
claim183958 1.5529989219503477s, earliest recipe duration still unknown.

## claim185653 — `just setup` delivered; the deployment bootstrap is NOT

Read the handoff (184537 review resolving D1/D2, the return to ops at 184558,
the owner reroute at 185651) and both new thread messages. Revalidated the six
candidate hashes against the tree first: all six match, and the owner's own
ValidIdleComposition run is recorded in OWNER-COMPOSITION-20260916.log. The
owner's new scope has two parts and **I completed one of them**.

**Part A, delivered: `just setup` and the prepared environment.** A separate
recipe, as the owner asked — start/stop/status/monitor use the environment it
prepares and install nothing, because a command that installs as a side effect
of starting a scheduler is one an operator cannot reason about. It creates a
dedicated venv outside the checkout, holds the interpreter to the minimum
`pyproject.toml` declares (read from that file rather than restated), and
installs `requirements.lock` with `--require-hashes`. Every recipe resolves the
interpreter's absolute path and runs it directly, so nothing is activated and
`tools/stack.py` spawns its children under the same interpreter. Repeat setup
re-verifies and leaves a prepared environment alone; a foreign, incompatible or
broken one is refused with its path named and **is never deleted**. A refused
install returns the exact pip command rather than an escalation.

It runs: the prepared environment resolves `jsonschema` **4.26.0**, the version
the lock pins, where the ambient interpreter on this machine has 4.19.2 — which
is exactly the drift `v12/python/justfile` already records catching in its own
source stage. All four recipes were run before setup (each refused, exit 2,
naming `just setup`) and after it.

**Part B, NOT delivered: the deployment bootstrap.** The owner also asked to
finish original PLAN step 3 — a concrete bootstrap producing a usable
deployment. I did the read-only discovery the PLAN asks for and wrote it up as
`DEPLOYMENT-INPUTS-185653.md`: what a bootstrap can derive over the Authority's
public API, and the nine classes of input only the owner can supply — image
digest, adapter identity, profile and policy digests, credential slots and
profile, per-Job workload material, target repository and line, workspace gid,
retention policy digest, and the nine participant endpoints. It also states the
real worker capacity the accepted schemas serve, because `/1` serves exactly one
worker per role and `/2` changes only the pool.

**The bootstrap helper itself is not written**, and I am not claiming it is.
That is why this Work returns through baton.bug rather than passing for review
as complete.

**One correction to existing work.** My justfile body parser — in both test
modules — attached column-0 comments to the preceding recipe, so a recipe check
could be satisfied by prose three recipes away. A new check caught it. Corrected
in both.

**Verification.** 125 focused checks (29 new), returncode 0 in 26.249s. Thirteen
reversal probes, 0.691s, restored copy hashing identically to the working tree.
One probe took three attempts: its first anchor did not apply, its second
reverted only prose and PASSED — proving nothing — so it was re-anchored on the
command construction the check actually reads, and then failed as required.
Recorded rather than counted.

**Secrets.** A `baton.user-credential-sources/1` registry exists at
`/home/sl/.baton/credential-sources.json`, mode 0600. Its contents were not read
and appear in nothing this claim wrote.

**What I did not do.** `tools/stack.py` and `tools/job_manager.py` are unchanged.
No live provider, engine run, Job submitted, v11 operation or version-control
operation. Both preserved operational findings are unchanged. The probe tree
copy, the demonstration venv and its stack root were removed; every child reaped.

## claim185774 — E1, E2, and the bootstrap written

Read the 185739 triage review. Revalidated all eight candidate hashes first:
all match. Both setup defects reproduce, and the reviewer is right that my nine
input classes were not nine blockers.

**E1, the documented remedy was not one.** I recommended
`just setup PY=/usr/bin/python3.13` in the recipe comment, the runbook and two
refusals. `PY` is a recipe ARGUMENT, not a named option: real `just` expansion
forwards the whole `PY=...` string as the interpreter path, so the operator
whose default Python was too old got a broken remedy. I reproduced it with
`just --dry-run` before changing anything, checked whether the sibling
justfile's `PY := ` convention would rescue it (`just --dry-run version PY=...`
is refused as an unknown recipe, so no), and made the override **positional**
everywhere. The new checks RUN `just` — reading the recipe is exactly what let
the wrong spelling survive.

**E2, a failed first install could not resume.** Ownership was published only
after a successful install, so a first install that failed left a directory this
tool had created and could no longer recognise: the next setup called its own
partial environment *foreign* and told the operator to delete it, and running
the printed pip command by hand could not write the missing marker either. The
marker is now written BEFORE the install and records `installed`; that state is
`incomplete` — ours, resumable, and not admitted as ready — while a genuinely
foreign or incompatible directory is still refused and still never deleted.

**B1, the bootstrap is written.** The reviewer was right that the missing
production choices do not block the helper. `tools/bootstrap.py` takes one
`baton.v12.stack-bootstrap/1` document of the operator's selections and:
validates every input, naming every missing one at once, before anything
durable; refuses a relative or inside-the-checkout state root, a malformed
Authority uuid, a missing or unknown stage, duplicate identifiers, a Job naming
an unconfigured producer, and — before anything is opened — an implementation
and review that share a participant; composes the Authority with principals
**derived** rather than configured, each Job's Work, the three route handlers
and the four grants in each Work's own scope; lays out the external state; emits
`/1` or `/2` with `job_bindings`; reports configured capacity; and prints the
four exports. It selects nothing, submits no Job and executes nothing. Repeating
it preserves state and refuses a conflicting binding *before the Authority is
even opened*.

**I corrected my own discovery record rather than extending it.** Three claims
in it were wrong, and the review was right about all three: `/2` is not
pool-only (`_held_bindings` requires a nonempty `job_bindings` list); the
implementation and review Work IDs are **equal within a binding**, so creating
two Works would produce a deployment whose review could never attach; and there
is no fixed count of nine endpoints — three receipt participants are configured
and the integrator and publisher are derived, so a one-Job deployment selects
six. Capacity is now per-Job affinity rather than a producer count.

**What the probe run itself found.** Two things, neither of them a product
defect, both recorded: my harness copied only `python/` and the justfile, so a
check reading `STACK.md` errored in the restored tree; and a reversal that
removed the inside-the-checkout guard made that guard's own test **create a
directory in the checkout and leave it there**. A case that dirties the tree it
asserts about is a real hygiene defect, so it now cleans up unconditionally.

**Verification.** 163 focused checks, 38 new, returncode 0 in 26.299s.
Seventeen reversal probes, 0.957s, restored copy hashing identically to the
working tree. One probe anchor did not apply on its first form because the text
had already been reworded; re-anchored and it failed as required.

**What is still the owner's.** Only the production selections, by exact field
name, in the corrected `DEPLOYMENT-INPUTS-185653.md`. The helper refuses each by
name and does not wait on them.

**What I did not do.** `stack.py`, `job_manager.py` and `test_stack.py` are
unchanged. No live provider, engine run, Job submitted, v11 operation or
version-control operation, and no dependency download this claim. The credential
registry was not read. Both preserved operational findings are unchanged; the
two new test modules are registered. Scratch removed; every child reaped.

## claim185884 — F1, F2, F3

Read the 185857 review; all ten candidate hashes revalidated first. E1 and E2
are verified. All three new findings are real and all three are mine.

**F1, I wrote a configuration without validating it.** The nested worker
`deployment` merely had to be nonempty, so a document missing twenty-two
required worker members was written out and an Authority composed for it, and
the refusal arrived from `held_configuration` afterwards with durable state
already made. It now goes to that same accepted validator — called, not
reimplemented — *before* anything durable. That is possible because principals
turn out to be derivable without building anything: `principal_of` is documented
as a read that writes nothing, and an Authority that does not yet exist has no
bindings to ask about, so the package's own `principal_for_endpoint` is the
answer. The derived identities now go into the document that is validated rather
than being grafted on after composition — previously what was written was not
what had been checked. And the schema is chosen from pool shape as well as Job
count, because `/1` permits exactly one worker per role.

**F2, a repeat could silently replace bindings.** Comparison read the *emitted*
configuration, where a `/1` document has no Job identifiers at all — so a `/2`
deployment repeated as `/1` compared `None` against the previous keys, matched
nothing, dropped a Job and rebound the other one, reporting success. The helper
now keeps its own record in one shape whichever variant is emitted. A changed
binding, a changed Authority and a **removed Job** are refused; a corrupt
record, a configuration with no record, and a record of another schema are
refused as *uncertain* rather than overwritten. All of it is settled before the
Authority is opened — otherwise the Authority's own refusal arrived instead of
mine. Both documents are published atomically.

**F3, selections could be silently discarded.** `integration_preparation: true`
was accepted and then left out of the configuration, so the serving deployment
defaulted it to false and the operator's requested managed preparation was
quietly disabled. The input document is now closed, nested wrappers included: a
member nothing reads is refused by name, and every supported optional selection
is carried through.

**The test module is restructured, and that is the real repair.** Every success
path used to run on wrapper dictionaries, which is how F1 survived. There are
now two fixtures: incomplete wrappers for what is refused before a deployment is
built, and a `ValidFixture` over the accepted `ServingCase` so every success path
runs against a deployment `held_configuration` really accepts.

**Verification.** 181 focused checks, returncode 0 in 26.718s; the bootstrap
module alone went from 28 to 46. Thirteen reversal probes, 6.581s, restored copy
hashing identically to the working tree. ONE PROBE PASSED FIRST TIME and so
proved nothing: my new fixture supplied the *same* principal the helper derives,
making "the helper derives it" unfalsifiable. The fixture now carries a
deliberately stale one — which additionally proves the input's own value is
discarded — and the probe then failed as required. Recorded rather than counted.

**What I did not do.** `environment.py`, the justfile, `parallel_test.py`,
`stack.py`, `job_manager.py` and `test_stack.py` are unchanged. No live
provider, engine run, Job submitted, v11 operation, version-control operation or
dependency download. The credential registry was not read. Both preserved
operational findings are unchanged. Scratch removed; every child reaped.

## claim185976 — G1 and G2

Read the 185945 review; all ten candidate hashes revalidated first. Both
remaining findings are real and both are mine.

**G1, my custody record was not evidence.** I validated its schema label and
nothing else, and `conflicts` compared only the members a binding happened to
carry — so a recognizable record whose binding was `{}` said nothing about that
Job's prior Work, base, target or producer, and authorized all of them to be
replaced. A non-dict binding would have reached an uncaught `.items()`. And the
document the record describes was never read at all, so a corrupt
`deployment.json` beside a complete record produced no conflict and was
rewritten after composition.

The record's whole shape is now validated, every member is compared, and the
emitted configuration is RELATED to the record across both representations —
missing, unreadable, not a document, another Authority, a different Job count or
any disagreeing member all make the state unknown. Every refusal case also
asserts that no Authority composition was attempted and that the documents the
case did not itself rewrite are byte-identical.

**G2, an explicit null was still dropped.** Carrying a selection only when it
was non-null confused an absent option with an explicitly supplied invalid one:
`integration_preparation: null` was dropped, the consumer defaulted it to false,
and an invalid request of the operator's became a different valid one that the
accepted validator never got to see. Present now means present, so the null
reaches `held_configuration` and is refused in the consumer's own words.

I also removed a test of my own that tested nothing —
`test_every_supported_optional_selection_is_carried` asserted each member of
`OPTIONAL` was in `OPTIONAL`. It is replaced by absent/true/false/null behaviour
checks, and by a case that records where each optional member is actually
validated: two by the preflight, five by the consumer at composition. That limit
is now stated rather than implied.

**Verification.** 196 focused checks, returncode 0 in 26.971s; the bootstrap
module went from 46 to 61. Nine reversal probes, 5.69s, restored copy hashing
identically to the working tree.

ONE PROBE PASSED FIRST TIME and so proved nothing: reverting the `_BINDING` loop
bound alone restored an *equivalent* form, because the new shape validation
already guarantees all four members — the two are one guarantee, not two. I
replaced it with a combined reversal of both, which failed as required, and kept
the `_BINDING` bound rather than deleting it, because depending on the record's
own key set is precisely the shape the defect exploited. Recorded rather than
counted.

**Still outstanding, and not mine to supply.** The ValidFixture success and
repeat cases have never been run by an independent reviewer — their `/tmp` is
tmpfs and `/var/tmp` is outside their write roots. The exact bounded command is
in the review and in `EVIDENCE-185976.json`. The owner's earlier two-case run
covers the unchanged launcher, not this bootstrap code, and I am not offering it
as though it did.

**What I did not do.** `environment.py`, the justfile, `parallel_test.py`,
`stack.py`, `job_manager.py` and `test_stack.py` are unchanged. No live
provider, engine run, Job submitted, v11 operation, version-control operation or
dependency download. Both preserved operational findings are unchanged. Scratch
removed; every child reaped.

## claim186044 — H1

Read the 186022 review; all ten candidate hashes revalidated first. G2 is
verified and the G1 incomplete-record and corrupt-JSON controls now refuse. The
one remaining finding is real and it is mine.

**H1, I grew the second validator I had promised not to grow.** `_drifted` read
the emitted configuration through `_emitted_bindings` — a partial projection of
my own that chose its representation from the truthiness of `job_bindings`
rather than from the schema, dropped the review Work in both variants, and had
no `source_worker_id` at all for `/1`. So a changed review Work, an unsupported
schema and a renamed sole producer all passed the repeat preflight.

That projection is deleted. The existing document is now validated through
`stage_execution.held_configuration` and its **normalized** `job_bindings` is
what gets compared. The accepted validator already resolves both variants
through `_held_bindings`, already requires the implementation and review Works
to match, and already derives `/1`'s producer from its sole implementation
worker — so reusing it is both less code and the only way the comparison means
what it says.

**Two probes passed first time, and they meant different things.**

The first said comparing `review_work_id` proves nothing: `held_configuration`
has already refused any document whose two Works differ, so after validation
that comparison is `job_work_id` compared twice. A **redundant guard** — removed,
not counted. The mutation is still caught, by the validator, and its case still
holds that.

The second said nothing held the multi-Job key-set comparison: the `/1`
Job-count case existed but had no `/2` counterpart, and the removed-Job case is
caught earlier by `conflicts`. A **test gap** — closed with a case for a `/2`
configuration edited to bind a different set of Jobs than its record. Both
probes then failed as required.

**Verification.** 202 focused checks, returncode 0 in 27.251s; the bootstrap
module went from 61 to 67. Five reversal probes, 3.686s, restored copy hashing
identically to the working tree.

**Still outstanding, and not mine to supply.** The ValidFixture success and
repeat cases have still never been run by an independent reviewer. The exact
bounded command is in the review and in the evidence. The owner's two-case run
covers the unchanged launcher, not this bootstrap code.

**What I did not do.** `STACK.md`, `environment.py`, the justfile,
`parallel_test.py`, `stack.py`, `job_manager.py` and `test_stack.py` are
unchanged. No live provider, engine run, Job submitted, v11 operation,
version-control operation or dependency download. Both preserved operational
findings are unchanged. Scratch removed; every child reaped.

## claim186132 — the requested `just test-bootstrap`

Read the 186081 review, the return to ops, and the owner reroute. Revalidated
all ten candidate hashes first: all match, so the owner's 67-test pass in 0.938s
recorded in `OWNER-BOOTSTRAP-20260916.log` still describes this code. That
supplies the independent run three reviews had been waiting for.

This turn is small and stays small: the recipe the owner asked for, its
documentation, and the checks that hold it. `bootstrap.py`, `test_bootstrap.py`,
`environment.py`, `stack.py`, `job_manager.py`, `parallel_test.py` and
`test_stack.py` are untouched.

**`just test-bootstrap [ROOT]`.** `ROOT` is positional, as `just setup`'s
interpreter is, and defaults to `/var/tmp` — these cases need real storage
*outside* the checkout, because `held_configuration` refuses a configured
mutable root inside the working tree and the workspace boundary refuses one on a
memory filesystem, which is exactly why the managed reviewer could never run
them. It resolves the prepared interpreter the way the other four recipes do,
sets `BATON_V12_STACK_TEST_ROOT` and `PYTHONPATH`, and runs
`timeout --kill-after=10s 180s` — the reviewed bounds. It `exec`s under
`set -euo pipefail` with no `|| true` anywhere, so its exit status means
something.

**Validated as a wrapper, not as a rerun.** Real `just --dry-run` expansion for
the default and for a named root; the recipe run once for real (67 tests,
0.968s, exit 0 — agreeing with the owner's); and the recipe's own failure path
exercised end to end by pointing `BATON_V12_VENV` at an absent environment,
which exits 2 naming `just setup`. Six reversal probes over the recipe body —
ambient interpreter, installing on the way through, an unbounded run, a
swallowed failure, an unforwarded root, and a root defaulting into a memory
filesystem — all failed as required, with the restored copy hashing identically.

I deliberately did **not** rerun the unchanged launcher, adjacent, stack or
bootstrap suites beyond that one wrapper run. The PLAN asks that the owner's
pass not be repeated merely for a handoff, and repeating it would have said
nothing new.

**What I did not do.** No source redesign, no new harness, no installation, no
live provider, engine run, Job submitted, v11 operation, version-control
operation or dependency download. Both preserved operational findings are
unchanged. Scratch removed; every child reaped. The production selections and
the external installation remain the owner's.

## claim186214 — I1, and the packaging slice returned rather than started

Read the 186175 review and both owner rulings. All ten candidate hashes
revalidated first: all match.

**I1 is real and it is mine.** The recipe declared `ROOT="/var/tmp"` and always
assigned from it, so an operator who had exported `BATON_V12_STACK_TEST_ROOT`
ran the checks on a different storage root and was never told. The precedence —
explicit operand, then the export, then `/var/tmp` — now lives in
`tools.environment test-root`, not in the recipe: a `just` default cannot read
the environment, so a recipe expressing that order would have had to reimplement
it in shell, and this is the same helper the recipes already ask for the
interpreter.

**Fixing the recipe alone would have fixed nothing.** I ran it to check:
`BATON_V12_STACK_TEST_ROOT=/srv/owner-selected just test-bootstrap` passed 67
tests — on `/var/tmp`. `_disk_root_outside_the_checkout` fell through to the next
candidate when the named root was unusable, so the operator's selection was
still silently replaced, one layer down. It now refuses by name, which is
`disk_roots`' own stated policy, and `test_stack.py` joined this claim's owned
paths for that reason alone.

**Verification.** 216 focused checks, returncode 0 in 27.146s, ten of them new.
Six reversal probes, 1.430s, restored copy hashing identically to the working
tree — including two over the resolver, since the recipe half alone would not
have held the behaviour.

**The packaging slice is NOT started, and I am not reporting it as done.** The
owner's PyInstaller ruling is a new deployment mechanism: a frozen entry point,
a bundled child dispatch replacing `sys.executable -m tools.X`, an
`instance.json` contract that replaces the four environment operands across
bootstrap, stack and every recipe, an external distro/db/repo layout, and a real
built-bundle smoke check. Beginning that at the end of a claim and handing it on
as finished is exactly the failure the last several reviews have been catching
in my work.

What I did do for it is the part that was due before any edit: I established
read-only that `pyinstaller==6.16.0` resolves here, so the slice is buildable on
this host, and I pinned every path it will create or edit in PLAN, together with
what the real-bundle check must actually prove. The owner explicitly sanctioned
finishing the small recipe and handing off the named slice, so that is what this
does.

**What I did not do.** `bootstrap.py`, `test_bootstrap.py`, `parallel_test.py`,
`stack.py` and `job_manager.py` are unchanged. No live provider, engine run, Job
submitted, v11 operation, version-control operation, or retained dependency
download. Both preserved operational findings are unchanged. Scratch removed;
every child reaped.

## claim186284 — J1, and the bundle actually built and ran

**J1 is mine and the reviewer is right.** `probes-186214.py` named
`TheRecipesUseIt.test_the_recipe_asks_the_helper_...` and that method lives in
`TheInterpreterOverrideIsExecutable`, so the probe errored with AttributeError on
PRISTINE code -- and my harness, which only asked whether the exit was non-zero,
counted the error as a mutation kill. It was not one. The original evidence
stands unchanged and `probes-186284-j1.py` is the attributable correction.

What actually needed fixing was the methodology, not the name. Every probe now
proves its named checks PASS on pristine code before the reversal is applied,
and requires the reversed run to fail on the INTENDED assertion rather than
merely to exit non-zero. The re-run gives: baseline passes, reversal fails on
the intended assertion, tree restored.

**The packaging slice: the risky half, built and run.** I took the build first
on purpose -- a contract written against a bundle that turns out not to build is
wasted work.

`tools/stack_command.py` is the one command a deployed stack is. Its reason for
existing is concrete: the children were `sys.executable -m tools.X`, and in a
frozen build `sys.executable` IS the application and `-m` means nothing to it,
so a deployed supervisor would have started copies of itself with operands it
could not parse. `bundled_argv` owns the single place the two forms differ, and
`stack.py` now dispatches the manager, the publisher and the publisher's own
status subprocess through it.

The spec names what PyInstaller cannot see by reading code: the
`module:attribute` factories this distribution resolves at run time, the frozen
JSON Schema assets, and rpds-py's native library. The build tool is pinned in
its own lock, with hashes measured from the artifacts, so a deployed
distribution can never acquire a packaging tool as a runtime dependency.

**And it was proved rather than assumed.** Built with both locks hash-enforced,
then run from /var/tmp under `env -i` -- no PYTHONPATH, no checkout on any path.
`identity` reports frozen, and reports the schema assets at 48212 and 51419
bytes (they are read at import time, so a bundle missing them fails rather than
quietly refusing every document later) and rpds imported from inside the bundle.

The child dispatch was proved by running it: the bundled `start`, given a
deliberately one-key deployment document, produced a manager traceback reading
`stack_command.py` then `_manager` then `tools/job_manager.py` then
`tools/stage_execution.py`, ending in the real `ContractRefusal` naming every
required member, with the PyInstaller bootloader reporting the failure. The
child was the bundled command reaching the accepted validator from bundled code,
and `start` refused with the child's own words and unwound.

**What I did not do, and am not claiming.** The `instance.json` contract and the
external destination layout -- which is the UX the owner actually asked for. It
changes how all four lifecycle commands are addressed, and its acceptance is a
real two-instance isolation run. Starting that now and handing it on as finished
is the failure the last several reviews have been catching in my work. The exact
remaining scope is in `EVIDENCE-186284.json` and on the PLAN path table.

220 focused checks pass; two Lifecycle expectations now read the corrected
dispatch. No live provider, engine run, Job submitted, v11 operation or
version-control operation. Scratch, the build environment and the built bundle
were removed; every child reaped.

## claim186381 -- the instance contract, and what running the bundle found

`tools/instance.py` is the one selector. Its identity binds EVERY file under
`distro/` rather than the executable's digest, because a one-folder bundle is a
directory: a distro whose native `rpds` library had been replaced, or whose
schema assets had been deleted, would satisfy an executable checksum and then
fail at import -- inside a child a supervisor had already started. `verify`
recomputes the whole manifest before anything is derived. A selector copied
elsewhere is refused, by name, because it names its own destination.

`bootstrap --destination --distro` prepares `destination/{distro,db,repo,logs,
state}`, copies the runtime in, asks the built command what it is, and publishes
`instance.json` atomically. An existing runtime is refused rather than replaced.
`stack --instance` reads it, verifies it, and derives the four operands and the
state root from it. I also reconciled the two layouts: bootstrap and instance
now derive byte-identical store paths under `db/`, and the stage deployment's
own mutable root is `deployment-state/` -- one path for two different things is
how they collide.

**The defect only the real bundle could find.** `stage_execution._checkout()`
walks three parents up from `__file__`; frozen, that is inside the bundle, so it
answered the INSTANCE DESTINATION and refused that destination's own `db/` for
being "inside the checkout". Frozen it now answers the bundle, which keeps the
rule exactly as strong -- a store inside `distro/` is still refused. This is
precisely the "avoid checkout-relative discovery" boundary the owner said to
validate rather than assume, and it was invisible from source.

**What the real external run established.** Built (80 files), installed TWO
instances each with their own stores, repo, logs, state and runtime copy, and
drove them through the bundled command from /var/tmp under `env -i`. `status`
and `stop` work through the selector and report this instance's own paths. A
COPIED selector is refused by name. B's own selector through A's command
succeeds -- and that is correct rather than a leak: two copies of one build are
byte-identical, so the executable is not the identity; the selector is.

**What I am not claiming.** `start` reached the real composition inside the
bundle and was refused: the production credential provider wants an absolute
credential registry, and my external-run fixture's workers carry none. That is a
fixture gap in the harness, not a product defect -- but it means a successful
external lifecycle with the manager, publisher and viewer actually running has
NOT been demonstrated, and the review named that as the acceptance bar. So this
returns rather than passing.

**A timing correction the review asked for.** I wrote "J1 1.291s, total 28.428s"
in prose while the JSON recorded 0.125s and 27.262s. The JSON is right: 1.291s
was the whole harness including its baseline and restore passes. And I described
the unmeasured frozen smoke runs as deployment cost rather than verification;
that was wrong, and they are now recorded as verification of unknown duration.

220 focused checks pass. `test_stage_execution` still shows the same 12
pre-existing errors after the `_checkout` change, re-measured. No live provider,
engine run, Job submitted, v11 operation or version-control operation. The build
environment, the bundle and both demonstration instances were removed.

## claim186468 -- K1 to K4, all four mine

**K1.** I compared only the destination, so a selector kept at A carrying A's
valid runtime but B's state, stores, configuration and logs passed -- and `stop`
went to B's state root. Every path an instance owns is DERIVED from its
destination, so every path is now compared against the layout rather than
believed. Verified against the real bundle: a forged selector naming B's state
is refused by name, exit 2.

**K2, two holes.** Verifying the instance's own folder said nothing about WHICH
command was running, so A's executable given B's selector verified B's folder
and went on dispatching children as A. The running command is now bound to the
instance's when frozen -- verified: exit 2, naming both. And the manifest
recorded only a symlink's TEXT, so an external link's target could change while
the manifest stayed identical; links pointing outside the bundle, broken links
and unsupported entries are refused, and safe internal links still recorded.

**K3.** `main` composed the Authority and wrote the configuration BEFORE
discovering there was no runtime to install, and `install` would overwrite an
existing corrupt selector. `admit` now settles every custody and runtime
admission first, and `install` calls it too so a direct caller cannot skip it.
The identity is validated meaningfully: exit 0 is not an identity, so a build
that is not frozen, or whose schema assets or native validator did not travel,
is refused.

**K4.** For a one-folder build `_MEIPASS` is `<distro>/_internal`, so my fix
protected the libraries and left `<distro>/` itself open -- a store beside the
executable passed. Frozen, `_checkout` now answers the distro ROOT.

**What is still outstanding, and the most important of it.** K1-K4 are verified
by RUNNING the real bundle, not by committed checks: `test_instance.py` and
`test_packaging.py` do not exist yet. A live demonstration against a bundle that
has since been removed is reproducible but is not a regression, and that is the
single most important thing left. Beyond it: the credential fixture for a
successful lifecycle, the recipes and STACK.md, the independent repo, and a
retained artifact manifest.

220 focused checks pass. No live provider, engine run, Job submitted, v11
operation or version-control operation. The build environment, the rebuilt
bundle and both demonstration instances were removed; every child reaped.

## claim186523 -- the K1-K3 remainders, and the coverage that holds them

**K1's subtler half was mine and I had half-fixed it.** Comparing RESOLVED paths
made `a/state` symlinked to `b/state` compare EQUAL to itself -- both sides
resolved to b -- so an unchanged selector still dispatched `stop` into another
instance. Equality is not containment. The comparison is now literal against the
derived layout AND the derived path must resolve inside the resolved
destination. A path that is not text is type-checked first, because `isabs` on
an integer raised TypeError out of the validator whose whole job is to turn a
bad document into a refusal.

**K2**: every link INSIDE the bundle was bound and the root was not, so a
`distro` that was a name for another tree digested that tree and called it this
one. A symlinked root is refused.

**K3**: the identity was asked of the INSTALLED command, so a digestible but
unsuitable runtime reached a composed Authority, a created destination and a
copied distro before being refused -- leaving all of it behind. It is asked of
the SOURCE command in `admit`, before any effect, and what lands is re-digested
against what was admitted. The identity itself now means something: the schema
assets must be exactly the two this distribution ships, and the native validator
must resolve inside the bundle rather than being the host's.

**The most important part of this claim is not a correction.** K1-K4 had been
verified by running bundles that were afterwards removed, and a refusal nothing
holds can be undone by the next edit without anybody noticing. There is now a
registered `test_instance.py` -- 24 checks covering every refusal above plus the
layout agreement with bootstrap and atomic publication -- and it runs in 0.011s
rather than needing a bundle rebuilt to be believed. I deliberately did not
build this claim; the reviewer was right that further partial builds do not
replace coverage.

244 focused checks pass. Still outstanding: `test_packaging.py` (the one thing
that genuinely needs a build), the credential fixture for a demonstrated
lifecycle, the recipes and docs, the independent repo, and a retained artifact
manifest. No live provider, engine run, Job submitted, v11 operation or
version-control operation.

## claim186583 -- the admission gates, held rather than demonstrated

The review was right twice over. The four corrections were real, and the module
I had just written covered the SELECTOR and nothing about `admit`, `install` or
the resource anchoring -- so every one of them was a live demonstration again.

**What I had actually done wrong.** Installing into a destination whose `state`
was a link out of it succeeded and published a selector `instance.read` rejected
on the very next read: a deployment that could never be started, left behind.
`exists` follows the final link, so a dangling `instance.json` link read as
absent and was then overwritten -- through the link, into wherever it pointed.
My first anchoring of the native validator used the identity's own reported
`resources`, which is the build describing itself: `resources: "/"` made every
path on the host qualify. And `main` admitted, threw the answer away, and let
`install` admit again, so a source changed while `prepare` was composing was
re-admitted and installed with exit 0 and a digest nobody had agreed to.

**Fix the case, not the class -- again.** The second and third of those are the
same mistake I have now been caught making several times: I corrected the
instance of the problem the reviewer showed me and left the general rule
un-narrowed. Anchoring to what the artifact SAYS instead of to what was
MEASURED is the shape to watch for.

**Six reversal probes, and two that first proved nothing.** K3-c and K3-e failed
on assertions other than the ones I had named -- reverted, the anchoring admits
the host path (so the intended failure is the refusal that never came), and
reverted, the drift is caught later by the copied-runtime comparison (so the
intended failure is that the refusal names the wrong thing, after a destination
has been created and a distro copied). I corrected the probes rather than
counting them. One arm genuinely is not independently reachable: containment
cannot fire without the link arm firing first, because every derived path is a
direct child of the destination. That is recorded as belt-and-braces rather than
as covered.

260 focused checks pass, 16 of them new. No build, no live provider, no engine
run, no Job submitted, no v11 operation, no version-control operation, no
credential registry read. Still outstanding: `test_packaging.py`, the credential
fixture for a demonstrated lifecycle, the recipes and docs, the independent
repo, and a retained artifact manifest.

## claim186672 -- the interval between admitting and installing

Carrying the admission fixed one half of K3 and opened the other, and the
reviewer found it with two scratch interleavings. An admission is a decision
about a RUNTIME. It cannot promise the destination still looks the way it did
while `prepare` was composing an Authority into it -- and `install(admitted=...)`
believed a layout it had not looked at since. A selector that appeared meanwhile
was overwritten. A state link that appeared meanwhile was accepted, and the
selector published for it was one `instance.read` rejects on the very next read.

**What I changed.** The owned-path preflight became `custody()`, a rule in its
own right, asked by `admit` before any effect and again by `install` under the
destination's lock. Publication became `instance.create`, which LINKS the
selector into place and fails if the name exists, because `os.replace` is atomic
for a replacement and a replacement is the one thing that must not happen here.
Cooperating attempts serialize on an owned, O_NOFOLLOW lock. A refusal after the
copy unwinds only what this attempt made.

**Two probes proved nothing, and that was the useful part.** Reverting the
exclusive publication and reverting the unwind both left my tests passing --
because the selector in those tests was already there before `install`, and
`custody` refuses that one first. Those two guards own only the interval
BETWEEN custody and publication, and I had written nothing that reached it. The
gap was real; it is covered now by a test that injects the appearance at the
step before publication, and the probes were re-pointed at it rather than
counted. That is the same lesson as J1 in a new place: a probe that does not
fail is telling me something about my tests.

**What I am not claiming.** These are deterministic interleavings, one of them
injected. Nothing here is a concurrency test and nothing here withstands
arbitrary hostile mutation of a destination -- which is exactly why the last
step refuses exclusively instead of relying on having looked.

270 focused checks pass, 10 of them new. No build, no live provider, no engine
run, no Job submitted, no v11 operation, no version-control operation, no
credential registry read. Still outstanding: `test_packaging.py`, the credential
fixture for a demonstrated lifecycle, the recipes and docs, the independent
repo, repeat/corrupt/mismatch preservation, and a retained artifact manifest.

## claim186742 -- owning the temporary, and then getting on with it

**The defect.** Publication wrote a fixed `instance.json.new`, so it wrote
through whatever was already at that name -- before the final name was ever
considered. A symlink there redirected the write into a foreign document and
published a symlink as the selector. A hardlink to an existing selector
destroyed its bytes while publication went on to refuse and say it had left them
exactly as they were. The no-clobber at the end was real and it was guarding the
wrong step.

`mkstemp` in the selector's own parent answers it: O_EXCL, a regular file, a
name nobody else holds, written through its own descriptor. Nothing checks an
unknown entry and then writes it -- a check before a write does not establish
ownership -- and nothing removes one, because an unknown entry is somebody
else's. I applied the same change to `publish`, which had the identical fixed
name; the review named only `create`, and fixing the case instead of the class
is my own recurring failure.

**And then the delivery.** The review said not to return another partial
demonstration if the implementation can continue, so this claim also does the
lifecycle slice: `just bootstrap INPUTS DESTINATION DISTRO` installs, and
`just start|stop|status|monitor <instance.json>` runs the deployment's OWN
command out of its own distro -- not this checkout's interpreter, not its
sources, which is the whole point of installing. `tools.instance command`
validates the selector and answers where that command is, so the layout is
derived once rather than rebuilt in shell. `tools.stack monitor` is the
installed monitor, deriving the snapshot from `snapshot_path` -- the same answer
`publish` and `status` use. STACK.md documents all of it, and the older
exported-operand form still works unchanged.

**One thing I had to correct in my own dispatch**: `stack_command._stack`
appended the verb to every operand, which is fine for verbs with no options of
their own and unparseable for `monitor --interval 5`. The instance selection is
split from the verb's own options now, and the four older verbs dispatching
exactly as before is its own check.

291 focused checks pass, 21 of them new. Ten reversal probes across two
harnesses, all valid kills with pristine baselines. No build, no live provider,
no engine run, no Job submitted, no v11 operation, no version-control operation,
no credential registry read. Still outstanding: `test_packaging.py` against a
real build, the credential fixture for a demonstrated running lifecycle, the
independent repo with repeat/corrupt/mismatch preservation, and a retained
artifact manifest.

## claim186838 -- a runtime cannot check its own bytes after it has run

The helper I added last claim asked `read` and stopped there. `read` validates
the SELECTOR -- members, derived layout, containment -- and says nothing about
the bytes at the end of those paths, and all four recipes execute what the
helper prints. So `just status <instance>` ran a changed launcher and exited 0,
while `verify(read(...))` would have refused it. The verifier that already
existed simply was not being asked, at the one moment it mattered.

**The lesson I keep re-learning, in a new shape.** Each correction I make gets
checked at the layer I was thinking about. Last claim I was thinking about
custody of FILES, so I never asked what the helper was handing to `exec`. The
reviewer's four-step reproduction is worth more than my four-step reasoning
because it ran the recipe.

So these regressions run the actual recipe -- `just start|stop|status|monitor`
against a printing stand-in, with an unchanged positive control that proves the
ordinary path still reaches the deployment's own command with the instance
named. The stand-in is not a bundle and I am not claiming it is; `test_packaging`
still owns real-build acceptance, and nothing here is a security framework.

STACK.md now leads with the installed instance as the normal way to run this,
says plainly that `just` needs the checkout to find the installed command while
the installed command needs nothing from here, qualifies the bootstrap lock as
coordinating cooperating bootstraps and nothing else, and documents that the
runtime is verified before it runs.

300 focused checks pass, 9 of them new. Four reversal probes, all valid kills
with pristine baselines; two intended assertions were misnamed and corrected
rather than counted -- reverted, the helper answers and the recipe exits 0, so
the intended failures are the exit that was zero, not the message a refusal
would have carried. No build, no live provider, no engine run, no Job, no v11
operation, no version-control operation, no credential registry read.

## claim186890 -- the first real installed deployment, and what it found

Everything before this was checked against stand-ins. The bundle exists now: it
was built, installed into two external destinations, started, watched, stopped
and re-verified, all from `/` with an environment of HOME and PATH only -- no
PYTHONPATH, no exported operands, no virtual environment, nothing from this
checkout. Two instances ran side by side with their own managers, publishers,
stores and state roots, and one command given the other's selector refused by
name.

**Two defects the stand-ins could not see.** The identity reported
`rpds.__file__`, which for a one-folder build is an `__init__.py` frozen into
the archive and absent from disk -- so my own guard refused the very first real
install, correctly and for a reason that was about the path rather than the
bundle. What must travel is the compiled extension. Then, frozen, `bootstrap`
computed its own "checkout" by walking three parents up from `__file__` and so
answered the INSTANCE DESTINATION, refusing a repeated install with "inside the
checkout at <that same destination>". I had fixed exactly this in
`stage_execution._checkout` for K4 and left two inline copies of the old rule in
`bootstrap` -- the class, again, after fixing the case. It asks the owner now.

**And one thing the operator would have hit first**: a composed install printed
"Now export these and run `just start` from v12/", which is advice for the
deployment they did not ask for.

**The credential fixture was not a formality.** The bundled manager refused to
serve without an absolute credential-sources registry -- a real contract refusal
from the real worker preflight that no stand-in reached. The registry this claim
composed names a fixture bearer file; the owner's registry was never read, no
provider was contacted, and nothing secret is in source or in the dossier.

`tests/tools/test_packaging.py` is registered and runs against a real bundle. It
skips, loudly and with the exact command, when there is no bundle -- and `just
test-packaging` builds first so there is a command that cannot skip. Its teeth
are proved by the one probe here that had to build: revert the identity line,
rebuild, and the check fails on the `__init__.py` it reports.

312 focused checks pass. Four reversal probes -- three source, one
build-and-revert -- all valid kills with pristine baselines. The mismatch case
is run with the instance STOPPED, because an earlier attempt rewrote a library
the running manager had mapped and killed it; the refusal was real and so was
the crash, and reporting them together would have been reporting my own doing as
a product property. No Job submitted, no provider, no engine, no v11 operation,
no version-control operation, no credential registry read.

Remaining: the independent repository from the selected immutable base. `repo/`
is created and empty; choosing and preparing that base is an owner selection.

## claim187015 -- two recipe gaps, and the repository the owner still owns

**The two gaps were both mine and both invisible to the checks I had written.**
The bootstrap recipe resolved the optional distro unconditionally, and
`realpath -m ""` is an error -- so `just bootstrap inputs.json`, the form that
installs nothing, died in the shell before the helper ran. My expansion checks
saw a correct expansion; the shell rejected it. And `just test-packaging`
inherited `BATON_V12_STACK_DISTRO` while building the default output, so the one
gate that cannot be stood in for could exit 0 with nine skips. Both now have
checks that RUN the thing: three that run the real recipe, four that run the
module under each environment.

**The repository.** `repo/` existed and was bound to nothing, which is the kind
of half-delivery that reads as done. The destination now owns its integration
workspace -- derived when absent, refused when it points outside -- while the
integration TARGET stays the owner's, because it is not deployment state and it
outlives any instance. `baton-v12-stack repository --instance ...` says what is
actually there, read-only, without running a repository tool; one of its checks
fails the test if it starts a process at all.

**What I did not do, and will not.** Creating or cloning a repository is a
version-control mutation. `OPERATOR-INDEPENDENT-REPOSITORY.md` gives the exact
commands, says which are reads and which is the one that creates, maps the input
members to add, and states plainly that the two installed instances carry no
target, reference or observer -- so their `repo/` is bound and empty, because an
empty configured stack schedules nothing.

The lifecycle harness is retained as a runnable file with every argv, cwd,
environment, timeout, elapsed time, its cleanup block and the fixture digest
mapping, beside the output it produced.

336 focused checks pass. Six reversal probes, all valid kills with pristine
baselines -- one first proved nothing because reverting the branch fell through
to a KeyError, which is an error rather than the assertion it was about; it is
re-anchored on the derivation, and the check now asks whether the member is
there before reading it.

## claim187142 -- the packet that would have failed late, and a harness that only worked when nothing went wrong

**The operator packet was worse than incomplete: it was confidently wrong.** It
cloned the external target and left the derived workspace an empty directory,
and `_prove_isolation` resolves the workspace's OWN repository identity before
anything is written -- comparing it against the target and every producer's
line and source, by common directory and by device/inode. An empty directory has
no identity to resolve. The owner would have followed my instructions, prepared
a deployment that looked right, and found out when a result was ready to import.
The packet now names three roles rather than two, gives the two clone commands
that create anything, and a fail-closed read-only block that exits non-zero on
the first thing that is wrong. And the deployment says it too: `repository
--instance` now reports what an unprepared workspace costs, so this is a
property of the product rather than a paragraph.

**The manifest drift was mine and the reviewer is right about what it means.**
Three bundle copies agreeing proves they are one artifact and says nothing about
which source built it. I edited `bootstrap.py`, `stack.py` and `STACK.md` after
generating the manifest and did not regenerate it, so the record described a
bundle built from earlier source -- and one of those edits added a subcommand,
which is executable behaviour the record did not describe. Rebuilt, re-gated,
reinstalled, re-recorded; the drift and its cause are in the new manifest, and
the old one is retained unedited.

**And the harness only worked when nothing went wrong.** A timeout after both
starts escaped with zero stops; the selector and the library were restored on
the normal path only. That is the same failure I have been correcting in product
code all week, in my own evidence tooling: the happy path proved, the failing
path assumed. Undos are registered before each mutation now and run in reverse
whatever happened, owned instances are stopped with a bound and what did not
settle is reported, and the process table is asked rather than assumed. Three
injected failures prove it rather than my saying so.

338 focused checks pass. Two reversal probes, both valid kills -- and only two,
because the rest of this claim is a document, a manifest and a harness, which
are checked by running them rather than by reverting a guard.

## claim187223 -- a harness that reported success it had not established

The reviewer drove my harness over mocked subprocesses and found four ways it
said "fine" without having established anything: a timed-out status recorded and
returned 0; non-zero stops with a survivor named, after which it tampered with a
library anyway; a FileNotFoundError in cleanup that skipped the second stop and
emitted no JSON at all; and "nothing owned is running" answered by a global
`pgrep` that knows nothing about the pids I started.

Every one of those is the same mistake in a different place: **recording an
outcome instead of checking it**. The harness now declares the exit each step is
supposed to have and fails on a mismatch, owns its children by pid and asks
`/proc` about those pids, refuses to touch the runtime unless they prove both
instances stopped, isolates each cleanup action, emits its JSON from a `finally`
so the run that went wrong is the one with the fullest record, and exits
non-zero when cleanup did not resolve. Six injected boundaries measure all of
that rather than my asserting it.

The packet was wrong in two ways that matter more than either. It mandated roots
OUTSIDE the destination -- an external target and workspace, worker storage
elsewhere -- which is the opposite of the owner's self-contained ruling I had
been quoting all week. And its check block compared command output without
checking the commands succeeded, so a workspace that could not be stat-ed
passed: a check that turns "I could not tell" into "it is fine". Both are
rewritten, and the block is now extracted from the document and driven through
nine scenarios, because a block an operator copies should be tested as the text
they copy.

I also had the manifest chronology wrong: I grouped `stack.py` with the genuine
187015 drift when its digest there was exactly what that claim passed. Corrected
against the retained candidate hashes rather than from memory.

338 focused checks pass and no product file changed. No probes this claim, and
that is the honest answer: nothing guarded changed, and a reversal over
unchanged code proves nothing.

## claim187303 -- deciding what you own from what a command happened to print

The harness asked `start` what it owned. A start against an ALREADY-RUNNING
instance prints no pid line, and a timed-out one prints nothing -- and an empty
pid map read as "nothing of ours is alive", so the run went on to corrupt a
library while somebody else's manager could have been serving, and then claimed
cleanup ownership over processes it had never started. The same shape as
everything else this week: absence of evidence read as evidence of absence,
this time in my own tooling, and the reviewer had to show it to me twice.

Ownership is now established BEFORE anything starts, using the deployment's own
four-state reader rather than a process manager invented in a harness: every
process must be positively `absent` or the run refuses the instance, starts
nothing and stops nothing. Identity must be COMPLETE -- a pid for every process,
confirmed by `status` -- or it is UNKNOWN, and unknown is never absence. Cleanup
stops only what was claimed. And the corruption step is simply gone: the
mismatch is already held against a real bundle in `LIFECYCLE-187142.json` and in
`test_packaging`, so there was never a reason to do it again under an identity
that might be empty.

Two smaller things, both the same failure to assert: the repeated bootstrap
recorded `selector_unchanged: false` and exited 0 -- a refusal that rewrote what
it refused to replace, reported as a pass -- and the previous evidence carried a
build field inherited from the claim before rather than measured. Both corrected.

And the packet ordered the work impossibly. I wrote that cloning after
`just bootstrap` was "simpler"; `nominate_source` proves each worker's source
with an `lstat` and an `O_DIRECTORY|O_NOFOLLOW` open, so an absent source is
refused before an Authority is composed. One order now, plus the two things that
check also requires that are easy to get wrong.

Nine injected boundaries measure the ownership rules; nine extracted scenarios
re-check the packet's block after the rewrite. No product file changed, no
suite re-run, no build -- and no probes, because there is nothing new to revert.

## claim187356 -- "did I claim anything?" is not the question

I had the ownership check and then asked it the wrong question. `if not owned:`
means "did I claim ANYTHING", and the demonstration reads and writes across BOTH
instances -- so with A fresh and B already running, it claimed A, refused B, and
then corrupted B's selector and called stop on B anyway. The cleanup filter I was
proud of was right; the normal path simply went around it.

Both sides with a complete identity, or no shared step at all. And every write
and every stop now goes through one gate rather than two paths with different
rules, because the way that defect existed was having the rule in one place and
the traffic in another.

Eleven controls, including both mixed orders and both one-side-unknown cases,
each showing nothing claimed on the refused side and nothing touched on either.
No product file changed, no suite re-run, no build, no probes.

## claim188434 -- the interface the owner actually wanted

The owner's direction was blunt and correct: two arguments to install, and then
nothing but the destination. What I had built took three operands and made every
lifecycle command carry a JSON path around -- technically complete, and nothing
anyone would want to operate.

So: `just bootstrap inputs.json /destination` builds its own distribution, and
the destination now carries its own justfile. `cd /destination && just start`
works; `just --justfile /destination/justfile status` from `/` means the same
deployment, because every path resolves from the justfile's own directory
rather than the caller's. The source-side wrappers take a destination and
dispatch to that file instead of reaching into the deployment. Beneath it,
nothing was loosened: every recipe still names the instance, so the command
still verifies the whole runtime and still refuses another instance's selector.

The two-argument operation also prepares the repositories the owner named --
target, workspace and one source per worker, each a separate clone -- and then
proves the isolation `_prove_isolation` will demand later: distinct repository
and directory identities, no borrowed objects, the declared bases and the import
reference present. I ran none of that: the repository tool goes through an
injectable runner and every check substitutes it, because this Work performs no
version-control mutation and the owner invokes the finished operation.

**One thing the change cost, and I am saying it rather than letting it pass.**
The old source recipe verified the runtime and only then exec'd it, so a changed
LAUNCHER never ran. A standalone deployment has nothing outside itself to ask,
so the launcher runs and then verifies everything else. I deleted the four
stand-in cases that used to "prove" the old property rather than leaving them
passing for the wrong reason, replaced them with a check that the command
refuses when verification fails, and wrote the limit into STACK.md.

349 focused checks pass, 20 of them new. Ten reversal probes, all valid kills.
The interface was exercised live: installed from two operands, started, watched,
stopped, and addressed from both `cd` and `--justfile`, with an environment of
HOME and PATH only.

## claim188582 -- four ways the new flow was not finished

R1 was the blocking one and it is the oldest mistake in this Work: I added
`repository_source` to the OPTIONAL list, which is the set carried into the
manager's CLOSED configuration schema. A valid input composed an Authority and
then exited 2 on the validator -- the installer's own operand refused by the
document it wrote. It is INSTALLER_ONLY now, and the coverage runs the real
validator and the whole command rather than a stub.

R2 was effects before checks, again: a source-only input cloned twice and then
refused for missing structure, and a worker_id of `x/../../../escape` planned a
clone outside the destination. Everything is proved first now -- the document,
the plan's agreement with the configuration, custody -- and the clones happen
under the destination's lock with the existence checks inside it. When a clone
fails part-way the earlier ones are NAMED and left: repository data this command
cannot re-derive is not something it deletes on the way out.

R3: custody refused a link at the deployed justfile and not a regular file, so
somebody else's justfile was overwritten and the selector published over it. It
refuses material there now and the write is exclusive.

R4: the plan was fixed under the destination while an explicitly named target
was preserved -- so one repository would be prepared and proved and a different
one configured. That is refused now, before any effect, naming both sides.

Two probes needed honesty rather than cleverness. V1 only reproduces with BOTH
guards reverted, so the harness now takes several edits per probe and says why.
V3 still refuses the escaping worker_id when the name check is reverted, because
containment catches it -- recorded as belt-and-braces rather than counted.

370 focused checks pass. And the count I put in the last handoff was wrong: I
said 349 where the evidence said 358, an arithmetic slip rather than a different
run.

## claim188671 -- three boundaries, and three probes that proved nothing first

R2's remainder is the oldest shape in this Work: I asked custody and then
WAITED. Everything it had established was about a destination that could be
taken while the attempt queued for the lock -- and it was, in the reviewer's
injection, and five clones went in anyway. The question worth asking is the one
asked immediately before the effects, so custody and the agreement check are
asked again under the lock.

R3's remainder was the same asymmetry I keep writing: the unwind removed the
runtime I had copied and left the justfile I had written, so a transient
publication failure blocked my own retry with my own leftover. Both are mine and
both go; anything foreign -- including a justfile that appears in the interval
custody cannot cover -- is refused and left untouched, which is now checked from
both sides.

R4's remainder: I put repositories under the destination and never looked at
where the workers' storage went. Derived when absent, refused when it leaves,
and deliberately quiet about two workers of one instance sharing a path inside
it. The credential registry stays the owner's and does not move.

Three probes proved nothing before they proved anything. W3's checks refused at
custody and never reached the unwind, so I wrote a case that reaches it and made
the check ask whether the file is there before reading it. W4 is covered in two
places, so it is a combined reversal now. W6 as first written duplicated W4; it
points at the positive property instead -- sharing inside the instance being
left alone -- which a refuse-everything reversal does kill.

379 focused checks pass. Six reversal probes, all valid kills. The live install
and lifecycle were re-run and this time the exact destination and transcript are
recorded, which the reviewer rightly noted was missing last time.

## claim188740 -- a path is not an identity

Two halves of one mistake. I set the ownership flag AFTER the write finished, so
a write that failed part-way left a file I had created and would not remove --
blocking my own retry with my own leftover, which is exactly the defect I had
just "fixed". And the unwind removed whatever was at the path, so a file
replaced between the create and the publication was deleted by me while the run
reported that nothing else had been touched.

Ownership is (device, inode) from the descriptor the exclusive create returns,
before a byte is written. Cleanup removes a path only while it is still that
identity; anything else is left and reported -- replaced, unreadable, or simply
gone -- and a removal that fails says so instead of being thrown over the
refusal that caused it.

X4 proved nothing at first: the uncertain branch is only reachable when the stat
fails with something other than absence, and nothing I had written produced
that. A case that does -- an unreadable justfile at cleanup -- is in the module
now.

384 focused checks pass. Four reversal probes, all valid kills. No build: this
correction is a failure path in bootstrap.py, and the retained live evidence
describes a deployment installed from the previous bootstrap.py, which is stated
in the record rather than left for a reader to notice.

## claim188783 -- the state was right and the answer was unreadable

The unwind was correct, the destination was left clean, and what an operator
actually saw was a Python traceback. `main` caught only `BootstrapRefusal`, so
an expected installation failure -- a selector publication that cannot write --
went past it. Correct behaviour reported incomprehensibly is still a defect, and
it is the kind I am least likely to notice because I read the code path rather
than the transcript.

`install` keeps raising the OSError, because its callers need the real thing.
The public command answers it: what failed, what was unwound (printed above),
and exit 2. Only OSError -- a TypeError is my bug and belongs in a traceback,
which the second check holds.

386 focused checks pass. Two reversal probes, both valid kills.

## claim188818 -- a promise where a report belonged

The sentence I added last claim to make a failure readable made it wrong in the
one case that matters: it asserted that anything this attempt made had been
unwound, and the cleanup immediately above it can say "could not remove ...: it
is still there". Two lines of output contradicting each other is worse than the
traceback I replaced, because this one reads as authoritative.

It points now -- see the cleanup messages above for what was removed and what
was retained -- and says only what it knows: what failed, and that nothing this
attempt did not make was touched. One regression drives the real command with
both the publication and the removal failing, and checks that the file is still
there, that the old sentence is gone and the pointer is present.

387 focused checks pass. One reversal probe: putting the blanket assertion back
fails the new check while the earlier one keeps passing, which is the shape of
the defect exactly.

## claim188860 -- the guide was describing a delivery that no longer existed

The implementation was accepted and the reviewer caught the thing I had stopped
looking at: the first screen of STACK.md was current, and everything below it
still described the older shape -- a separate build and a third operand, lifecycle
commands taking `instance.json`, and a repositories section saying the target is
never derived and must be cloned by hand, with `repository_source` appearing
nowhere at all. A guide that contradicts itself halfway down is worse than one
that is simply out of date, because the reader has no way to tell which half is
true.

It is one story now: two operands with the build folded in, the destination as
the interface, and the repositories the bootstrap prepares and proves -- with
what stays the owner's said plainly, and the no-source case described as the
idle state it is rather than something that sounds finished.

No code, no tests, no rebuild, no live run, and no probes: nothing guarded
changed. I re-ran only the suite that reads STACK.md, and verified the rewritten
sections by reading them against the accepted behaviour and the reviewer's owner
packet.

## claim189383 -- `baton 12.0.0 (3c0dd082, dirty)`

The owner asked for a version file so the command can say what it is, with the
commit as separate provenance and dirty builds allowed. The temptation in a
thing like this is to let the deployed command ask the repository at run time;
the ruling forbids exactly that, and it is right -- an installed build's
identity must not change because somebody edited the tree it came from. So the
stamp is captured while the bundle is being packaged and travels inside it, and
the packaged `--version` answers with an empty PATH, from `/`, with no checkout
in sight.

The parts I had to be careful about: unknown is unknown (no repository tool is
not a clean tree), ignored build output must not make every build dirty (the
packaging run creates `build/` itself), and the version must live in exactly one
place with the package metadata reading it rather than repeating a literal.

The source of the repositories is the checkout containing `v12/justfile`, found
from this distribution's own file rather than from wherever the operator is
standing -- which also means the input document no longer names it, and one that
still does is refused with the reason rather than ignored. That makes the
two-operand command prepare repositories by default. I did not run that form:
cloning is a version-control mutation and the owner invokes it. And a clone
carries commits, not uncommitted work, so a dirty checkout's edits do not reach
the prepared repositories -- named here and in the guide rather than quietly
changed.

412 focused checks pass, 23 of them new. Seven reversal probes, all valid kills
-- two proved nothing first: the checkout-discovery case passed reverted because
it ran INSIDE the checkout, which is exactly when a cwd answer looks right, and
one intended assertion was misnamed.

## claim189471 -- two assumptions and a command line

V1 and V2 were both me assuming what a tool does instead of asking it. I
believed `--porcelain` always reports untracked files -- it honours a config
setting that can switch them off, which would have made a dirty tree report
itself clean, the exact failure the stamp exists to prevent. And I wrote in a
comment that `build/out` was *ignored*; it is untracked, so the first build
dirtied every capture after it, and the stamp would have said `dirty` about its
own output. Both are now asked for explicitly: untracked observation forced, and
three exact paths excused only when they are untracked -- a tracked change under
`build/out` is still dirty, and so is any untracked source anywhere.

V3 is the kind of thing only a real run finds. I documented
`just bootstrap inputs dest --no-repositories`, and `just` binds that option as
the DISTRO operand: it never reaches the helper, and what the operator gets is a
usage error from `realpath` about a tool they never named. The recipe refuses an
option in a positional slot now and prints the form that works with the operand
they actually typed, the guide shows that form, and a check walks every
`just bootstrap` line in the guide so the documentation cannot drift back.

420 focused checks pass, 9 new. Four reversal probes, all valid kills; B4
proved nothing first because the reverted path fails in `realpath` rather than
in my refusal -- which is precisely the confusion the guard removes.

### claim189538 -- a test that paid for itself, and a path typed from the wrong place

Both returned things were mine, and the first one is the worse of the two. I
wrote a focused check for the documented two-operand bootstrap and gave it a
destination with an empty DISTRO, which is exactly the branch that runs
`just build`. That build -- pip, then PyInstaller -- happens before Python ever
opens the input document, so the absent input I relied on to keep the check
cheap could not prevent anything. The module header says DETERMINISTIC AND
OFFLINE. It built the distribution every time it ran.

It is two checks now. One names an existing directory as DISTRO, which takes
the branch that does not build and still proves the fourth operand reaches the
helper rather than the recipe. The other runs the actual recipe against a PATH
whose `just`, `python3` and prepared interpreter record what they were asked for
and whose pip, PyInstaller, npm and version-control tool refuse outright -- so
the argv the recipe forwards is visible, including that `--distro` is the path
`just build` produces, and nothing real is reached. A third case reaches one of
the refusing programs on purpose, because a recording that proves nothing is
worse than no recording. The whole class is 0.703s.

The second: the guide told an operator to `cd v12/python` and then pass
`--distro python/build/out/distro`, which from there means
`v12/python/python/build/out/distro`. The recipe's operand is right because the
recipe resolves it from `v12/`; I copied it into a context where it was not.
It is `build/out/distro` now, with the prepared interpreter rather than ambient
python3, and a check resolves every relative `--distro` in a `cd v12/python`
example against that directory.

Two things in the record are corrected rather than left to be found again. I
said claim189471 involved no rebuild; it did, and the proof is in the artifacts
-- the current bundle's stamp carries `excused_build_output` and the retained
claim189383 install's does not. How many builds ran and what each cost was never
measured and is not reconstructed. And the count was 421, not the 420 I wrote;
the evidence JSON was right and my arithmetic was not. It is 424 now, 3 new,
with four reversal probes, all valid kills.

### claim189719 -- a fresh install has zero Jobs, and where that stops being true

The owner's question was the right one: why is a fresh install asking for a Job?
It was, and it also asked for an Authority identity, which is not an operator's
selection either. Both are gone. `jobs` is deferred -- absent is the ordinary
install, present is held to every rule it ever was -- and a document that names
an `authority_uuid` is refused by name, because the instance mints its own once
and persists it at the destination before the Authority it names exists. Two
destinations are now two instances rather than two names for one.

The emitted configuration follows: an installation that binds nothing is the
multi-Job document with an EMPTY binding list and none of the four global Job
members, and the two forms cannot be mixed -- a global Work beside an empty
list is refused by the manager's own closed schema, which a probe found before
I did. Nothing is invented to get there: no placeholder Work, no seed Job, no
grant. A grant is made in a bound Work's own scope, and an instance with no
Work has no scope to grant anything in.

What I could not finish is worth more than what I did. A worker's `deployment`
carries an `input_manifest`, and that manifest is digest-sealed around a
`work_ref` naming an Authority and a Work. So a worker document can only be
written against an identity that already exists -- and the identity is now
minted during the same command. Installing into a genuinely fresh destination
with configured workers is therefore refused: *the bootstrap input manifest
names another Authority*. Leaving the pool out instead is not available either,
because `scheduler.own_pool` refuses an empty pool. The pool is not yet
instance configuration, and making it one means moving `input_manifest` and
`task_document` to the assignment and admitting an empty pool through the
manager's composition -- the scheduler expansion the ruling excludes.

I wrote that as two checks rather than a paragraph, so the remaining scope is a
fact about the build instead of a claim in a dossier. The consequence for the
owner is blunt: do not attempt a production run against this yet.

442 focused checks pass, 18 new. Nine reversal probes, all valid kills; two
proved nothing first -- F1 because the guard turned out to live one layer below
my assertion, and F6 because my expected token was written backwards.

### claim189861 -- the identity was not as owned as I said it was

F3 is the one that should not have got past me. I wrote "an instance owns what
is under its own destination" into a docstring and then read the identity
record with `Path.read_bytes`, which follows a symlink -- and the
`FileExistsError` fallback called the same reader, so `O_EXCL` was protecting
only the create. The reviewer reproduced the consequence exactly: two separate
destinations, each with a link at that name pointing at one external file, both
read the same identity, both report it already persisted, and both believe they
were installed independently. That is the isolation boundary the whole
generated-identity design exists for.

It is one safe read now -- `O_RDONLY|O_NOFOLLOW` and an `fstat` regular-file
check -- used by both paths, and the name is in the custody sweep so a link
there is refused before the reader is even reached. Foreign bytes and foreign
links are refused and left exactly as they are, which the checks assert
afterwards rather than assume.

F2 I overclaimed. I called the guide block a complete runnable example and
wrote a check that compares member NAMES; the block does not parse, because the
elided worker deployment is not JSON. The check is renamed and its docstring
says what it proves and what it does not, the block says about itself that it
is a shape, and the contradictory `authority_uuid` example is gone. A genuinely
runnable one waits on F1, and inventing a credential or a Work ID to make it
parse is exactly what must not happen.

F1: the reviewer is right and I was wrong. The ruling excludes a generic
scheduling project; it does not exclude the minimum empty-capacity handling the
selected outcome needs, and I read the exclusion too broadly. I am not
re-arguing it. What kept it out of this claim is budget, not scope, and the
remaining step is pinned seam by seam rather than as a category -- including
the one place I think a product decision may genuinely be needed, which is what
`_minted`/`_bound_scope` should answer for a deployment with no bound Work.

446 focused checks pass, 4 new. Thirteen reversal probes, all valid kills; G2
proved nothing first, and the reason is the point: without the regular-file
check the reverted code does not accept a directory, it raises
`IsADirectoryError` from the middle of `identity()`. The guard buys a sentence
instead of a traceback.

### claim189914 -- it starts

The thing I said was not reachable is reachable, and the reviewer was right
that the work to get there was inside the owner's scope rather than outside it.
A fresh installation naming no Job and no worker now installs, and `just start`
runs the real manager and the real publisher over it: the publisher writes a
canonical snapshot it actually observed, `status` reports `jobs 0 observed
(canonical=True)` and `serving acknowledged`, `monitor` refreshes, `stop` stops
both. Nothing about that is a dummy branch; the zeros come from store reads and
the check asserts the snapshot was written during that start.

What made it work was smaller than I feared, and most of it was deciding what
NOT to invent. `workers` joins `jobs` as deferred, because a worker is
configured with the Job it serves. `_serves_nothing` is the one predicate
everything branches on. With no bound Work there is no scope, so `_minted`
mints nothing -- no session, no per-Work grant, no deployment-scoped receipt
capability, which is exactly what the review told me not to invent and also the
only honest answer. The workspace group is not asked for, because it exists to
allocate an execution workspace and none is allocated; it is not inferred
either, which is the thing `configured_workspace_group` itself refuses to do.

The one change outside this module is one line in the scheduler:
`PooledManagerOperations` accepts an empty mapping. Nothing else is relaxed,
and that matters more than the change -- `_required_workers` already answers
nothing only when the store has no active generation and no live allocation, so
the existing comparison is what makes an empty attachment fail closed the
moment work exists. I proved that by weakening the comparison and watching it
stop refusing.

The guide's example is a real document now, and the acceptance parses it out of
STACK.md rather than keeping a copy, so it cannot drift into being unrunnable
again. The identity reader no longer blocks on a named pipe -- which it did,
forever -- and no longer takes the first 64 KiB of a longer file.

455 focused checks pass, 9 new. Nine reversal probes, all valid kills. Two
proved nothing first: H6 because my oversize document was cut mid-string so the
PARSER caught it and the bound proved nothing, and H7 because a weakened
comparison raises KeyError rather than accepting -- the guard still earns its
place, by turning that into a refusal that names the mismatch.

### claim190047 -- an empty report about work that exists

P1 was the one worth finding, and the reviewer found it with a real store and
public APIs rather than by reading my code. An instance with no capacity
attached no worker, so recovery looped over nothing: a genuine accepted control
offer sat in the store while the manager reported an ordinary idle tick. An
empty report about work that exists reads as "there is nothing here", which is
the one sentence it must never say.

The fix needed a question that did not exist: `recover_on_restart` answers
something close, and ACTS -- it expires overdue offers and abandons another
incarnation's issued ones. A deployment that called it merely to look would be
settling somebody else's durable state to decide whether it may start. So
`outstanding_offers` is that question without the actions, through the same
owned crossing, and `unconfigured_work` puts it beside the Job rows, the active
pool generation and the live allocations. It runs at startup and on every
resume, because the constructor comparison I had leaned on answers one moment
and says nothing about what arrives afterwards.

A probe made that honest. My first version of the read-only check seeded only an
accepted offer -- which recovery leaves alone -- so a reader that expired and
abandoned would have sailed through it. It now seeds a foreign ISSUED offer too,
the state recovery does abandon, and the reversal is visible.

P2: I called a source-run lifecycle an installation. It was not. The class is
renamed, the evidence correction is recorded rather than quietly fixed, and
there is now a real installation boundary beside it -- installer, selector,
deployed justfile, copied runtime, persisted identity, lifecycle through the
selector -- with its stand-in runtime and in-process execution named as
substitutions rather than implied to be a bundle.

And the guide had gone on saying things this build no longer does: that a
manager cannot serve without a pool, that a record needs a non-empty binding
set, that every member is required of every document. All three are superseded
in place, and the later-configuration path is now exact rather than gestured at:
stop, one-operand bootstrap with `state_root` pointing at the destination,
start. I ran that path and asserted what it preserves, and I ran the two-operand
command against an installed destination to show it refuses.

464 focused checks pass, 9 new. Eight reversal probes, all valid kills; K5
proved nothing first because the check could not see a mutation, and then
because my expected token named a state the reader no longer reports.

### claim190149 -- the tick I never looked at

P1 was mine twice over: the guard was in the wrong place, and I had asserted in
writing that it was in the right one. `manager.serve` calls `reconcile` once
and then `sweep` for every tick after it, so a check living in `recover` is
asked at startup and never again. It is asked from `drain` now as well --
`sweep`'s first pass is `_observe`, and `drain` is what `_observe` calls into
these operations, before anything that tick could observe, adopt, delegate,
launch or converse. What it is NOT is recovery every tick: recovery expires and
abandons, and settling durable state in order to observe it is the exact thing
this correction exists to prevent. The proof drives the real loop, with the
offer arriving inside the injected wait.

P2 was subtler and worse. My documented reconfiguration returned zero and
removed `integration_workspace` from the deployment -- the installation derives
it under the destination and the one-operand branch composes from the input
alone. Selector, runtime and identity all unchanged, and the deployment had
quietly stopped naming where integration works. My own preservation check
compared exactly the files that did not change, which is how it passed. It
compares the configuration now, and a repeat that would drop a derived
selection is refused by name with where to copy the values from. A copy step,
not a merge: a document that filled its own gaps from the previous
configuration would make "what this deployment selects" two files.

And the frozen lifecycle finally ran. The candidate built, installed with
`--no-repositories`, and answered for itself with nothing from this checkout on
PATH: `baton 12.0.0 (fb5d39d6, dirty)`, then start, status, a bounded monitor,
stop, status -- honest zeros from a canonical snapshot the publisher observed,
and the destination removed afterwards.

Two things about that run I would rather say than have found. The first attempt
hung: `just monitor` is unbounded by design, a harness cannot press Ctrl-C, and
it sat there for its whole 600s timeout and left live processes behind. I
stopped and removed them by hand, the watch is asked of the bundled command
with its own `--ticks` bound, and the stop runs in a `finally`. The second is
that the cold build's duration is gone with that attempt -- the 7.1s recorded
is a warm rebuild, and I am not presenting it as the cost of building from
nothing.

468 focused checks pass, 4 new. Five reversal probes, all valid kills; L3 and
L4 proved nothing first because both tokens were backwards -- the third time in
this line of work I have written an `assertEqual` token in the wrong operand
order, which is worth recording rather than quietly fixing.
