# Progress

Implementation has not started. The assigned change author owns subsequent
implementation checkpoints; research and review remain in FINDING/PLAN.

## 2026-09-07 — baton.tuner, W106896 claim 106921

Prepared the owner-authorized eight-path initial-access candidate. Production
changes are restricted to workspaces.py, review_cycles.py and oci.py; three
existing test modules receive additions only, one initial-access engine module
is new, and the serial registry has only its appended member. Saved the seven
pre-edit files before implementation and preserved the eight exact candidate
files plus incremental patch and SHA-256 manifest under evidence/.

Initial provisioning holds no-follow descriptors through bounded preflight and
group/mode changes, preserving contents/inodes and leaving partial failure
materializing/ungranted for retry. Lifecycle publication/admission serialization
and durable launch resolution are in place; ordinary workspaces retain 02770.
Read-only admission/replay/launch never repairs a pre-existing line.

Verification: 251 focused tests, 250 pass and one explicit live-engine skip.
The engine fixture is prepared but not run; dedicated group, image and runner
authority remain required. Extra dependency/source-boundary/registry checks:
132 tests, one failure plus one error, three skips. Boundary ownership checks:
12 tests, three failures. See retained logs and comparative inventory output.
Required additional guard changes are precisely identified in
evidence/initial-access-scope-request.md; no unapproved guard edits were made.

Current state: candidate awaiting independent review and owner scope disposition
for the exact two additional test paths. Not ready to close W106896 or transfer
shared-path editing to custody. Full runtime/correction acceptance remains outside
this checkpoint. No source acquisition, concrete-worker, recipe, custody/intake,
job/integration, canonical Git or live coordination-store mutation was performed.

Operational notes: an optional guessed assignments.py source path was absent;
the same search located and read attempts.py:assignment_of. The added adapter
tests initially used fixture setUp/tearDown manually without invoking its
registered cleanup callbacks; that was corrected before final verification.
Any earlier disposable v12-w71917-* roots remain optional operator housekeeping;
no broad deletion was attempted. Source/test verification did not require
Docker, group setup, provider access or escalation.

## 2026-09-07 — baton.tuner, W106896 claim 107206

Completed M107203's owner-approved two-test-path guard extension. The exact
serial expected list and precise constructor/launch-proof ownership coverage
now match the reviewed initial implementation. Added executable invalid-capability,
unminted-root and two-live-line copied-metadata refusal witnesses.

Four focused checks pass. The saved-base AST preservation audit passes and all
eight original candidate hashes are unchanged. The broader 13-check guard sample
has nine passes and four unrelated baseline failures. Comparative source inventory
proves this checkpoint adds no unowned entry, orphan association or missing probe.
git diff --check passes. See evidence/initial-access-guard-focused-results.txt,
initial-access-guard-completed-checks.txt, initial-access-guard-preservation.json,
initial-access-guard-delta-completed.json and initial-access-guard-probe-delta.json.

Current state: exact two-path candidate awaiting baton.bug independent review,
then baton.ops disposition. evidence/initial-access-guard-manifest.json binds
base/candidate bytes and the incremental patch (19df2debd00d4a6fc07bd75fdf149e49f62475cfa651cfa8022bcf0ca95768e2).
Prior evidence and assertions remain intact. Shared-path ownership stays held
for checkpoint acceptance; no custody, runtime setup, live engine, production
creation-default or unrelated baseline repair was attempted.

## 2026-09-07 — baton.claude — revalidated; the live proof is blocked on one grant

Claimed W105706 after the owner transferred the remaining composed live proof.
Everything that does not depend on the missing grant is done; the proof itself
cannot start, and the PLAN's own instruction for that is one bounded operator
request rather than a choice made here.

**Revalidated.** `evidence/stable-access-source-hashes.json` still matches on
every path outside the accepted edit set — `checkpoint_profiles.py`,
`dogfood_entry.py` and `Dockerfile.claude` are byte-identical, so nothing
drifted outside the authorized eight. The three production paths and their
tests differ exactly as expected: that file records the PRE-implementation
baseline, and the accepted access code plus W105982's custody corrections have
landed since. The eighth path is in place — `test_private_line_access_engine`
is registered in `SERIAL_MODULES`. The scoped modules are 349 tests, passing,
with the engine module skipping for the reason below.

**What blocks the live proof.** The engine fixture opts in only on three
operator-supplied facts, and none is available to me:

- `BATON_V12_INITIAL_ACCESS_ENGINE=1` — unset.
- `BATON_V12_PRIVATE_LINE_IMAGE` — must be an exact installed image ID, and
  the plan reserves "exact installed image/runner authority" to the owner. The
  engine is reachable (Docker server 29.1.3) and local images exist, so this is
  a choice rather than a capability gap.
- `BATON_V12_WORKSPACE_GROUP` — a DEDICATED group. This is the one that cannot
  be resolved here at all. The runner is `uid=1000(sl) gid=1000(sl)` with
  supplementary `65534(nogroup)` and nothing else, and
  `check_workspace_group` refuses a gid this manager does not hold. Of the two
  it does hold, 1000 is a user's LOGIN group and 65534 is the overflow gid —
  and the accepted design refuses exactly those: a login group was measured and
  rejected once already, and "a group inherited from a service directory is not
  a workspace grant". Picking either would manufacture the defect this Work
  exists to remove, and would make a green run evidence of nothing.

So this is not a case where an assumption can be stated and the work continued:
the group IS the subject of the proof. One directed request is on the ledger
and this Work is blocked on it rather than parked, per the PLAN.

Nothing was executed, edited or set up for the runtime. No production or test
path changed under this claim.

## 2026-09-07 — baton.claude — grant verified; one exact operator command needed

The approved setup is real and checks out. What is left is the one thing
Slawomir anticipated in M107856, and his instruction for it is to return an
exact command rather than escalate or ask another design question.

**Verified, before attempting anything.**

- `getent group baton-workspace` → `baton-workspace:x:1001:sl`. The group
  exists and `sl` is a member.
- The image passes the fixture's own compatibility checks:
  `docker image inspect` returns `Id` exactly
  `sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f`,
  `Config.Volumes` is null so it adds no writable volume alias, `Config.User`
  is the pinned `65532:65532`, and the entrypoint is `dogfood_entry.py` —
  whose bytes the baseline hash file still matches. Tag
  `baton-w85497-dogfood:candidate4`. No build and no pull.

**The blocker, exactly as M107856 predicted.** Account membership does not
update existing processes, and this turn's process was started before the group
was created: `id -G` answers `1000 65534 …` with no `1001`. Re-acquiring the
group inside this session is refused by the managed policy —
`sg baton-workspace -c 'id -G'` fails with `sg: setgid() failed: Invalid
argument`. I did not retry it in another form, and I am not asking for an
escalation or a different design.

**The exact operator command**, from a session that can acquire the group — a
fresh login for `sl` after the group add, or `sg` from an unrestricted shell:

```sh
cd /home/sl/src/baton/v12/python && sg baton-workspace -c '
  BATON_V12_INITIAL_ACCESS_ENGINE=1 \
  BATON_V12_WORKSPACE_GROUP=1001 \
  BATON_V12_PRIVATE_LINE_IMAGE=sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f \
  PYTHONPATH=src python3 -m unittest tests.manager.test_private_line_access_engine -v'
```

Please confirm `id -G` inside that shell lists `1001` before the run, and
return the full output. With it I complete the evidence account — launched,
consumed, retained and cleaned paths, plus the image and group observations —
and return through independent review.

Nothing was executed, set up or edited under this claim: no runtime started, no
group or mode changed, no environment written, no production or test path
touched. The scoped modules remain at the 349 passing tests recorded above,
with the engine module still skipping for the opt-in it has not been given.

## 2026-09-07 — baton.claude — the harness now explains a failure before it destroys it

The first live run produced a verdict and destroyed its own explanation: the
exit code was asserted before anything read the container, cleanup then removed
it, and the read-only sweep afterwards found nothing left to inspect. That is a
harness defect rather than a finding about the runtime, and it is the only thing
corrected here.

One path changed, `tests/manager/test_private_line_access_engine.py`
(`9e3d79c26ac5820040272da55f4e4d050ae30eb92a01b244736050af9460acfc`), additively:

- `docker wait` is captured into `ended`, and the existing
  `assertEqual(..., "0")` is unchanged except that it now carries a message.
- `why_it_ended` gathers that message while the container still exists: three
  READ-ONLY reads of this run's own container — `State`, `logs`, `Mounts` —
  and nothing else. No engine mutation, no second run, no repair, no group or
  image substitution.
- It never raises. A diagnostic that can fail replaces the failure it was meant
  to explain, so every read is guarded and its own error becomes part of the
  account rather than the verdict.

**No permissions conclusion is drawn.** Whether a denial explains exit `1` is a
reader's judgement over evidence nobody has yet; manufacturing that judgement
now is exactly the unproven diagnosis the handoff ruled out. The state, the
streams and the mount table are what the next run will finally show.

Every existing assertion is preserved, the cleanup path is byte-identical, and
the fixture still skips without the explicit opt-in. Nothing was executed under
this claim.

**One focused operator rerun**, same command as before:

```sh
cd /home/sl/src/baton/v12/python && sg baton-workspace -c '
  BATON_V12_INITIAL_ACCESS_ENGINE=1 \
  BATON_V12_WORKSPACE_GROUP=1001 \
  BATON_V12_PRIVATE_LINE_IMAGE=sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f \
  PYTHONPATH=src python3 -m unittest tests.manager.test_private_line_access_engine -v'
```

Exactly one test. If it passes, that is the proof. If it fails again, the
failure message now carries the container's own account and I can act on it.

## 2026-09-07 — baton.claude — the cause is a missing program, and one image has it

The diagnostic did its job. `FileNotFoundError` errno 2 at the first
version-control `add` is an executable-resolution failure, and the group-write
question is untouched by it — the payload append, the nested file creation and
the execute script all completed first.

**Cause, from the approved image's own metadata.** `sha256:979f11d5…`
(`baton-w85497-dogfood:candidate4`, built 2026-09-04) carries the standard
`PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`, and its
only apt layer installs `ca-certificates python3`. The version-control program
is simply not in that image. Nothing about PATH is wrong, and this is exactly
the operator's point that the current `Dockerfile.claude` says nothing about an
older digest's contents.

**One installed candidate carries it and passes every check the fixture makes.**

| Fact | Value |
| --- | --- |
| Id | `sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4` |
| Tag | `baton-w71917-provider-gate:20260905` |
| apt layer | `apt-get install --no-install-recommends -y ca-certificates git python3` |
| `Config.User` | `65532:65532` — the pinned runtime identity |
| `Config.Volumes` | null — adds no writable volume alias |
| Entrypoint | `python3 /opt/baton/dogfood_entry.py`, as the approved image |
| PATH | the same standard PATH |

It is the ONLY local image that both installs that program and satisfies the
fixture's user and volume assertions.

**I am not substituting it.** Selecting the exact image is the owner's
authority and the handoff forbids automatic substitution, so this is a proposal
with its evidence attached. Nothing was built, pulled, run or changed.

**One honest limit on this evidence.** The program is proved INSTALLED from the
image's build history, not by executing anything inside it. That is the
strongest read-only proof available here, and running a probe container would
be a runtime act this handoff did not authorize me to perform. If you want it
confirmed before the rerun, that probe is one command against the candidate
image with `--entrypoint=/usr/bin/git` and `--version`.

**With the image approved, the rerun is the previous command with one value
changed** — `BATON_V12_PRIVATE_LINE_IMAGE=sha256:0697b6595aff0af2a39a81d4922`
`23bf33cf69877426ec859fe1abb90abd617e4` — and everything else identical:
group `1001`, the opt-in, `PYTHONPATH=src`, exactly one test module.

No permission was weakened, no version-control check removed, no fixture
assertion changed, and no path was edited under this claim.

## 2026-09-07 — baton.claude — the initial access proof PASSED, live

Operator ran the approved command with group `1001` and image
`sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4`:
exactly 1 test, 0.236s, **OK**. The fixture hash at that run was
`9e3d79c26ac5820040272da55f4e4d050ae30eb92a01b244736050af9460acfc`, which is the
diagnostic candidate above and is unchanged since.

What that establishes, against a real engine and a real fixed-identity runtime
rather than a host fixture: the initially provisioned line is writable by uid
65532 with the dedicated group in its supplementary set; the version-control
program resolves and its commands run; the nominated source stays read-only;
created entries carry the configured gid with `0664` files under `02775`
directories; and the runtime ends cleanly with the container settled.

Two things this cost, and both are worth keeping:

- The first run failed and destroyed its own explanation, because the exit
  assertion preceded every read and cleanup then removed the container. The
  harness now gathers the container's own account before the assertion. That
  correction is what turned a second opaque failure into a one-line diagnosis.
- The diagnosis was NOT the permission story everyone expected. It was errno 2:
  the approved image's only apt layer installs `ca-certificates python3` and
  simply had no version-control program. Guessing "denied" from a failing
  access proof would have been wrong, and would have sent the next turn looking
  at modes and groups that were fine all along.

**Remaining approved scope**, per M108016: the composed proof — confirmed-stop
custody, the read-only reviewer mount, and the same-line correction round. That
is a further extension of this same engine module, and it is now unblocked
because W105982's custody composition is implemented. I am NOT starting it in
this turn: it is a multi-case fixture extension that needs its own room to be
written and checked, and beginning it here would produce something I could not
verify before handing over. The next claim starts from this recorded state.

No path was edited under this claim, and no broad suite or checkpoint was
repeated.

## 2026-09-07 — baton.claude — the composed proof is written; one operator run left

Wrote the remaining approved scope into the same engine module — confirmed-stop
custody consumption, the read-only reviewer mount, and the same-line correction
round. One path changed,
`tests/manager/test_private_line_access_engine.py`
(`d94bf33b42ab347af6ca1d57a4fdd0d06889e8f42bd0970fad40c5664843c3a6`), which is
path 7 of the approved eight. Nothing else was touched.

**The first case is preserved exactly.** Its setup moved into a
`composed_writer` helper so the new case continues the SAME live line instead of
describing a second one; every assertion it made still runs, in the same order,
under the same test name. The passing run recorded above therefore still stands
for what it proved.

**What the new case adds, and why each step needs a real runtime.** The worker
wrote as uid 65532 under its own creation mask, so:

- **Consumption.** `prove_line_consumable` runs after the confirmed stop and
  the recorded disposition, over genuinely foreign-owned bytes. It must resolve
  this attempt's line, match the recorded pin, place the retained sibling
  OUTSIDE the writer's mount, and — the part no host fixture can establish —
  actually open what another uid created. It is then asserted to have repaired
  nothing: `nested/new` is still `0664` and the root still `02775`.
- **Checkpoint.** `freeze` runs the real `GitCheckpointProfile` over the
  runtime's own commit: the evidence head must equal the head the container
  produced, the base must be the declared one, `nested/new` must be in the
  reviewed path set, and the retained reference must resolve to that head.
- **Reviewer.** `review_boundary` must hand back ORDINARY roots — `_line` false
  and a workspace that is not the line — with the line's mode untouched.
- **Correction.** After a `changes-requested` verdict, a second writer attaches
  to the same line: same device and inode, same mode, the runtime's bytes still
  present, HEAD still the runtime's commit, and revision one still resolvable
  from its retained reference.

**Static state.** The module now reports 2 tests, both skipping without the
opt-in, and the scoped modules are 350 tests passing. `review_boundary` and
`OciAdapter.prove_line_consumable` are both importable, so the new case's
symbols exist. That is all a run without the grant can establish — the case
itself is only proved by the operator run below.

**One operator rerun**, same grant, now two tests:

```sh
cd /home/sl/src/baton/v12/python && sg baton-workspace -c '
  BATON_V12_INITIAL_ACCESS_ENGINE=1 \
  BATON_V12_WORKSPACE_GROUP=1001 \
  BATON_V12_PRIVATE_LINE_IMAGE=sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4 \
  PYTHONPATH=src python3 -m unittest tests.manager.test_private_line_access_engine -v'
```

If the new case fails, the diagnostic added earlier still reports the
container's own account before cleanup removes it. No permission was weakened,
no assertion removed, no production path edited, and no runtime was started
under this claim.

## 2026-09-07 — baton.claude — the last two runtime stages are written

The composed case PASSED live (1 test, 0.235s, OK, at digest `d94bf33b…`), and
the operator correctly named what it did NOT cover: it validated the host-side
custody, checkpoint, review-boundary and correction admission, but no reviewer
or correction CONTAINER ran in it. Those two stages are now written.

One path changed, `tests/manager/test_private_line_access_engine.py`
(`09d99499ebe811de16320fa930fadf30744c8b372625c7d6e794061187d5cbad`), path 7 of
the approved eight. Nothing else was touched.

**Both passing cases are untouched.** Their bodies and assertions are exactly
as they were proved. The two additions are new methods plus two small enabling
changes: `self.containers` collects every container a case starts so a
three-container proof removes three, with the same per-container assertions
`cleanup_runtime` always made; and a `launched` helper composes a further
runtime over roots that an accepted lifecycle operation produced. The initial
writer's launch stays inline exactly as proved rather than being refactored
into that helper — a passing live case is not worth the risk of tidying.

**The reviewer stage** hands the runtime the line as its SOURCE and its own
attempt workspace as its output, then requires the same fixed identity that
could write this tree as the writer to be REFUSED as the reviewer: an append to
a tracked file, an append to `.git/HEAD`, and a new path in the checkpoint must
each fail with `EROFS`, and the private metadata is in that list deliberately —
it is where a reviewer could otherwise rewrite the history it is judging. It
must still read what it was given and write its own `findings`, and afterwards
the line must be unchanged in bytes, mode and HEAD.

**The correction stage** starts a second fixed-identity container on the same
line. What it must FIND is the first runtime's bytes, because the line was
never recloned — the mount is asserted to be the same device and inode before
the container starts. It appends, commits, and reports its head; the line's
HEAD must be that commit, its parent must be the first runtime's commit, and
the frozen reference the reviewer examined must still resolve to what was
reviewed.

**Static state**, which is all a run without the grant can establish: the module
reports 4 tests, all skipping without the opt-in; the scoped modules are 352
tests passing; and every symbol the new cases use imports. The stages themselves
are proved only by the operator run.

**One operator run**, same grant, four tests:

```sh
cd /home/sl/src/baton/v12/python && sg baton-workspace -c '
  BATON_V12_INITIAL_ACCESS_ENGINE=1 \
  BATON_V12_WORKSPACE_GROUP=1001 \
  BATON_V12_PRIVATE_LINE_IMAGE=sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4 \
  PYTHONPATH=src python3 -m unittest tests.manager.test_private_line_access_engine -v'
```

A failure still carries the container's own account. No permission was
weakened, no assertion removed, no production path edited, and no runtime was
started under this claim.

## 2026-09-07 — baton.claude — the correction round now finishes as a round

The review was right, and the gap is worth naming precisely: my correction case
ended at file, stat and revision checks over a stopped container. That proves
the RUNTIME wrote the line and leaves the LIFECYCLE half of the round untested
— a second turn that never records its disposition, never has its consumption
proved, and never produces a checkpoint is not a correction round, it is a
container that happened to write.

Completed inside the same case, over the same live line, with every existing
assertion kept:

- the second adapter is retained rather than discarded;
- `complete("writer-attempt-2")` records the disposition after the observed
  stop, in the same order the driver uses;
- `prove_line_consumable` is proved for assignment 2 at generation 2 — same
  line path, same recorded pin, and a custody sibling derived for THIS attempt
  rather than the first one's;
- a second checkpoint is frozen over the second runtime's own commit: evidence
  head equal to the head the container reported, the same declared base,
  `tracked` in the reviewed path set, a reference distinct from round one's,
  and that reference resolving to the new head;
- and the reviewed checkpoint is re-proved as audit evidence through
  `audit_checkpoint`, which is the API that owns that question, rather than by
  resolving a reference by hand. Its head and reference must still be round
  one's.

One path changed, `tests/manager/test_private_line_access_engine.py`
(`20981569e64054222404b4765d3114c4dbb7630c02aa70e81ac7ee0ec06ae2d7`). Both
previously passing cases remain byte-identical in body and assertions; the
reviewer case is unchanged from the reviewed candidate. Static state: 4 tests
skipping without the opt-in, scoped modules 352 passing, `audit_checkpoint`
imports.

**The final run is the two NEW methods only**, as the review asks — the two
already-passing cases need no repetition:

```sh
cd /home/sl/src/baton/v12/python && sg baton-workspace -c '
  BATON_V12_INITIAL_ACCESS_ENGINE=1 \
  BATON_V12_WORKSPACE_GROUP=1001 \
  BATON_V12_PRIVATE_LINE_IMAGE=sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4 \
  PYTHONPATH=src python3 -m unittest -v \
    tests.manager.test_private_line_access_engine.InitialPrivateLineEngine.test_a_reviewer_runtime_cannot_write_the_checkpoint_it_reads \
    tests.manager.test_private_line_access_engine.InitialPrivateLineEngine.test_a_correction_runtime_advances_the_same_line'
```

No production path was edited, no assertion removed, no permission weakened,
and no runtime started under this claim.
