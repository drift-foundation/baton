# Adoption packet — two independent parallel development Jobs

Prepared by baton.claude under claim 249364, answering ASSESSMENT-249338.md's
G1 and G2. **This is a preparation, not an authorization**: no deployment was
changed, nothing was started, no engine, image, network or credential was
reached, no deployed store was opened, and no old root was removed or reused.

## The recommendation, stated first

**NOT READY as a resolved current deployment; READY IN ARRANGEMENT.** The
arrangement is chosen, composed and deterministically witnessed, and what
remains is operand selection an owner makes, not a defect and not a missing
capability.

  * The two-Job arrangement is the **supported multi-Job composition**, not a
    new design: one manager, one pool, one
    `baton.v12.stage-execution-deployment/2` document with four stage workers
    and two `job_bindings`. `two_jobs.py` composes it and holds it against the
    product's own `stage_execution.held_configuration`.
  * The deterministic witness (`test_two_jobs.py`, 85 checks) drives **that
    composed document** through W130224's independently accepted two-Job
    fixture and observes both Jobs' implementations `waiting` at one instant,
    on their own allocated producers, writing their own lines, mounting their
    own workspaces, with Job B reaching its own reviewer — and then drives the
    whole step 4 command to four admissions, two frozen attributed verdicts,
    positive cleanup and `settled`.
  * **The operands are no longer owner questions.** Owner reroute 250730 asked
    for them to be derived from accepted configuration and supported APIs
    rather than asked for, and `prepare_two_jobs.py` does that: the
    participants, routes, capabilities, roots, credential reference, network,
    retention, profiles, task documents and input manifests are all derived,
    and the two Works are created through the Authority API. **Four operands
    remain, and none is derivable**: the fresh run root, the fixture
    repository, its base revision, and the uuid the instance bootstrap minted.
    [SELECTIONS-247941.json](SELECTIONS-247941.json) is kept as the template
    the composer's operand contract is checked against; the resolved document
    the preparation writes is what an operator composes from.

## The arrangement, and why this one

ONE manager serving both Jobs. Two isolated managers would prove that two
single-Job deployments still work — which W239528 and W239533 already
established one at a time — and would say nothing about shared capacity,
per-Job allocation or cross-Job isolation inside one pool, which are the three
things an adoption decision actually turns on.

| Part | This arrangement |
| --- | --- |
| Deployment document | `baton.v12.stage-execution-deployment/2` |
| Pool | 4 stage workers: `implementation-worker-a`, `review-worker-a`, `implementation-worker-b`, `review-worker-b` |
| Bindings | 2 `job_bindings`, each naming its own `source_worker_id`, Work, base and target |
| Integration | **None configured by this gate.** Human plus agent integrates; no integration stage is submitted, so no integration capacity is ever allocated |
| Corrections | `correction_policy: "decline"` — the W239533 product boundary, so a `changes-requested` verdict opens no round in this store |
| Limits | `two_jobs.LIMITS`: 2 Jobs, 2+2 admissions, 0 correction rounds, no retry, no session restoration, **180s per provider invocation and per verification command**, 600s total for the RUN including a 60s cleanup reserve |

**WHAT 180 SECONDS BOUNDS, exactly.** It is `execution_limits`:
one provider invocation (`provider_turn_seconds`) and one
verification command (`verification_command_seconds`). **It is not a
total attempt lifetime**, and this packet has no mechanism that
bounds one — review 2026-09-24T01:14:08Z corrected the earlier
"180s per attempt" wording, which claimed a guarantee these settings
do not give. What IS bounded in total is the RUN: 600 seconds
including the 60-second cleanup reserve, enforced by
`two_job_supervisor.supervise` and asserted on a controlled clock.

**What each Job owns alone** is `two_jobs.PER_JOB`: its Job identity, its Work,
its producer participant, its reviewer participant and its task document.

**What it does NOT own alone, and the packet says so rather than implying
otherwise.** The workspace storage, launch home and credential home are
INSTANCE members — one manager owns them and every attempt gets its own
directory beneath. And the source and the declared base MAY be shared: an
Authority holds one canonical revision, so two Jobs that both publish are two
development lines of one target. An arrangement that refused a shared source
would be refusing the supported shape; the first version of this one did, and
the accepted traversal could not compose under it.

Isolation that matters is therefore asserted on a RUN rather than declared in a
document: distinct lines, distinct allocated producers, distinct mounted
workspaces, distinct attempts, and each Job's own reviewer.

## Step 1 — check the pinned artifacts, changing nothing

```sh
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate
BOUND=/home/sl/baton-runs/independent-review-247947/manager-source
PY=/home/sl/.local/state/baton-v12-venv/bin/python

PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B "$DOSSIER/verify_247941.py" --pins
```

It re-reads the 106-file manager-source manifest, the runtime executable digest
and `tools/stage_execution.py`'s digest, and prints what it found beside what
ASSESSMENT-249338.md pinned. It starts nothing and writes nothing outside this
dossier.

### Running this dossier's own checks

```sh
mkdir -p /var/tmp/baton-w247941
BATON_V12_DISK_ROOT=/var/tmp/baton-w247941 \
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B "$DOSSIER/verify_247941.py"
```

**THE FIXTURE ROOT MATTERS, and the guard it satisfies is not weakened.**
`held_configuration` denies mutable deployment state inside "the checkout",
and the checkout it detects is derived from the source that imported it —
bound to the pinned snapshot under `/home/sl/baton-runs/...`, that makes
`/home/sl/baton-runs` the checkout. A disposable root under it is refused even
though it is nowhere near the repository. `verify_247941.py --pins` reports
`fixture_root` findings for exactly this reason.

## Step 2 — create the fresh instance

**The two acts only a human performs**, because this preparation performs no
Git operation and creates no repository for you:

```sh
# NOT under /home/sl/baton-runs. Bound to the pinned snapshot,
# `held_configuration` treats that directory as the checkout and refuses
# mutable deployment state inside it -- see below.
ROOT=/home/sl/baton-instances/two-jobs-<the fresh identity you choose>
SOURCE="$ROOT/fixture-source"

mkdir -p "$SOURCE"
#   ... create the fixture's files, then commit them ...
BASE="$(git -C "$SOURCE" rev-parse HEAD)"
```

**THE RUN ROOT MUST BE OUTSIDE THE CHECKOUT BOUNDARY, and this page had it
wrong.** Review 2026-09-23T20:34:15Z composed the shape printed here and the
product refused it by name:

> the configured integration_store at
> `/home/sl/baton-runs/two-jobs-.../db/integration.sqlite3` is inside the
> checkout at `/home/sl/baton-runs`; mutable deployment state belongs outside
> the working tree

`held_configuration` derives "the checkout" from the source that imported it,
so binding the pinned snapshot makes `/home/sl/baton-runs` one — the same rule
the fixture-root section above already documents, which I had applied to the
tests and not to the recipe. `prepare_two_jobs.BOUNDARIES` now refuses such a
root **before anything is written**, and the validator is not weakened.

**The run identity must also be fresh.** `prepare_two_jobs.CONSUMED` names
every root this campaign has spent — each holds other work and is preserved
evidence — and the refusal resolves symlinks first, because a fresh-named
alias pointing into a consumed root walked around the earlier lexical check.

Then bootstrap the instance. Its input document is **derived by the same step
that uses it**, so there is no separate configuration task:

```sh
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B "$DOSSIER/prepare_two_jobs.py" \
    --run-root "$ROOT" --source "$SOURCE" --base "$BASE" \
    --emit-bootstrap-inputs > "$ROOT/bootstrap-inputs.json"

PYTHONPATH="$BOUND" "$PY" -B -m tools.bootstrap \
    --inputs "$ROOT/bootstrap-inputs.json" \
    --destination "$ROOT" \
    --no-repositories \
    --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro
```

`--emit-bootstrap-inputs` runs before the instance exists, needs no record and
performs no act; it still refuses a root inside a checkout boundary or under a
consumed instance, because an operator who bootstraps into one has already
spent the effort. The document it prints carries only what
`tools.bootstrap.REQUIRED` names — the state root, the checkpoint profile, the
integration profile, the retention policy and disposition, the two generations
and the receipt participants — all from the same accepted configuration as the
rest of this packet.

**`--distro` is the one seam.** The tool refuses without a built runtime —
*"installing into … needs a built runtime; name it with `--distro`"* — and
copies the pinned distribution into `$ROOT/distro`. That copy is the only part
of step 2 this dossier's checks perform rather than reason about; no scheduler
is started and no repository is prepared (`--no-repositories`).

**A fresh install creates no Work**, which is why the preparation's two are
unambiguous. That is the tool's own account of itself, not an inference:

> `job   none; no Work, grant or placeholder was created`

It writes `$ROOT/bootstrap.json`, `$ROOT/authority-identity.json`,
`$ROOT/deployment.json` (the empty-capacity instance configuration) and the
four stores under `$ROOT/db/`. **The record is the identity** — the preparation
reads the uuid from it, and an `--authority-uuid` that disagrees is refused
rather than preferred:

```sh
AUTH="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["authority_uuid"])' "$ROOT/bootstrap.json")"
```

## Step 3 — prepare, in one command

```sh
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B "$DOSSIER/prepare_two_jobs.py" \
    --run-root "$ROOT" \
    --authority-uuid "$AUTH" \
    --source "$SOURCE" \
    --base "$BASE"
```

**This is the whole preparation.** In order it:

  1. refuses a run root that is not this run's own or that lies under a
     consumed instance, and refuses a `--base` that is not one full object
     name;
  2. writes both Jobs' task documents under `$ROOT/tasks/` and **checks that
     their target paths are disjoint** — `greet_a.py` and `greet_b.py`, one
     tiny change each against the one declared base. Two Jobs writing one path
     are one contended change rather than two independent development lines,
     so this is a refusal rather than a convention;
  3. derives the resolved selections — including each Job's full input
     manifest and its `job_input_identity`, computed from the task bytes so
     the manifest's `human_contract` and the worker's `task_document` cannot
     disagree — and **validates the whole proposed packet in the PINNED
     process** before opening the Authority or composing anything, through
     `two_jobs.py --check`, which runs the digest pins, the import provenance
     and the entire composition and writes nothing;
  4. performs the Authority acts through the supported API: two Works under a
     derived act identity, both implementers on `impl`, both reviewers on
     `rview`, the integrator on `integration` (the review worker passes its
     answered assignment there), the four scoped capability grants per Work,
     and `canonical_target`;
  5. composes and validates the concrete packet by running `two_jobs.py` —
     the same command this page used to print separately, not a second path.

**The order is refusals, then effects.** Every refusal above — the boundary,
the run identity, the symlink, the base, the source, the bootstrap record, a
repeat with different bytes, an existing composed target — happens before the
first byte is written. The only thing written before validation is the two
task documents, because the validator OPENS the configured task; they are
never written over differing bytes, and a validation failure leaves exactly
those two files and says so.

**And the validation happens where the composition happens.** Review
2026-09-23T21:06:44Z found the preflight validating in the preparation's own
process — `composed` → `held` → `from tools import stage_execution` →
`held_configuration`, three lines apart — so the `tools` that validated was
whichever one that process had found, and an earlier version of this step had
explicitly tolerated a checkout one. `two_jobs.py --check` now does the whole
preflight in a subprocess with `PYTHONPATH` bound to the pinned source and
`cwd` at the root: the same program, the same environment and the same
working directory as the composition that follows it. The digest pins are
part of that check, so a drifted artifact is refused before any Authority act
rather than after.

**It prints the operands the next two steps take**, from the places this run
actually used: `serve_command` and `status_command` in its receipt. Use those
rather than retyping the templates below — review 2026-09-23T20:34:15Z found
three documents naming three layouts that no reading of `<run root>` could
reconcile.

**What it does not do**: no container, credential, provider, engine or network
is reached, no Job or control store is opened, and no Git operation is
performed. **Executing the run is step 4 and a separate decision.**

A credential is named by REFERENCE — the private registry path and a slot
mapping — and no secret passes through this script or anything it writes.

### Where the operands came from

`prepare_two_jobs.ACCEPTED` carries them with their provenance: the image,
adapter and runtime from W239528 claim 244216 as accepted by
review-2026-09-23T03:19:21Z; the worker profile, policy and retention digests
from the review deployment W239533 executed; the manager source from
ASSESSMENT-249338.md's pin. Step 1 re-checks the artifact digests among them
before any of this runs.

Four identities are this gate's own and are checked for distinctness:
`baton.impl-a`, `baton.review-a`, `baton.impl-b`, `baton.review-b`.

### Running it twice

Two different things, and this page used to say only the first:

  * **The Authority act replays.** `create_work` is journalled under an act
    identity derived from the run, so calling it again answers the same two
    Works — and a Work that already exists under somebody ELSE's act is
    refused rather than absorbed. Measured rather than assumed: pointing the
    step at a Work the witness fixture had minted answered
    `Work '0000000a-W1' already exists`.
  * **The COMMAND does not replay; it refuses, early.** A completed run has a
    composed target, and the composer is create-only about that path, so a
    second invocation is refused **before** the task documents, the
    selections or the Authority are touched. An invocation with different
    operands — a different base, say — is refused the same way, by comparing
    the bytes it would write against the bytes already there.

So a repeat leaves the first run's packet exactly as it was. To prepare
again, select a fresh run root; that is the same rule as everywhere else in
this campaign, and there is no in-place re-preparation.

## Step 4 — serve the bounded run, as ONE command

```sh
BATON_V12_STAGE_EXECUTION_CONFIG="$ROOT/run/deployment.json" \
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B "$DOSSIER/two_job_supervisor.py" \
    --deployment "$ROOT/run/deployment.json" \
    --submission "$ROOT/run/submission.json" \
    --job-store "$ROOT/db/jobs.sqlite3" \
    --control-store "$ROOT/db/control.sqlite3" \
    --incarnation "<a fresh incarnation for this process>" \
    --outcome "$ROOT/run/outcome.json" \
    --total-seconds 600 --cleanup-seconds 60
```

**This is the whole run.** It opens both stores, composes the deployment
`two_jobs.py` wrote, submits the one submission carrying both Jobs, serves
through the four-admission gate, stops at `total_seconds - cleanup_seconds`
(600 − 60 = **540**, so the reserve is INSIDE the total rather than an
extension), **closes admission BEFORE cancelling anything**, cancels every
attempt this run launched, drives bounded cleanup sweeps inside what is left of
the total, derives each Job's verdict from its own frozen result and attempts
`outcome.json`.

It exits **0** when `state: settled` and **1** when `state: held`, so the exit
status is readable before any document is.

### When there is a document, and when there is not

An earlier version of this page said the command publishes "on every path".
That was wrong in both directions, and this dossier's own cases say so.

  * **Before the supervised run begins there is no outcome to owe.** Reading
    the two documents, opening the stores, composing the deployment and
    submitting all happen before `supervise` is entered. A refusal there —
    an unresolved operand, a credential registry the production factory will
    not accept, a store it cannot open — **leaves no `outcome.json`**, and
    should: nothing was admitted, no runtime exists and there is no account to
    render. The command reports the refusal itself.
  * **Once the protected run starts, finalization ATTEMPTS the document on
    every path** — the bounded stop, a serving failure, a cap refusal, an
    interruption, and a fault in the accounting itself, which is named in the
    document as `finalization_failure` and re-raised after it is written.
  * **An attempt is not a guarantee.** If the write itself fails — a full or
    unwritable run root — that failure propagates to the operator and **may
    leave no file at all**. That is the one ending an operator cannot read
    about afterwards, and the command raises rather than exiting quietly.

**So a missing `outcome.json` is not an answer about the run.** It means
either that the command refused before starting or that it could not write;
neither is evidence that anything stopped, and neither is positive cleanup. The
same goes for a process exit: see step 5.

**What it does NOT do, and what an operator must supply for a real run.** In
this build there is no daemon, so nothing answers on the worker's behalf; the
command takes a turn seam and an operator typing it passes none. With a real
engine the runtime IS the turn and no seam is involved. The witness supplies a
deterministic turn at exactly that boundary and the packet says so rather than
implying the command has run workers for real.

The three earlier steps this replaces were not typeable: step 4 served
UNBOUNDED through `tools.job_manager serve`, and step 7 handed `job`, `control`
and `composed` to the supervisor without ever defining them. The submission
step is inside this command now, so a Job cannot be submitted twice by a
retyped line.

### Its predecessors, for a deployment that wants them separately

`tools.job_manager` remains the supported surface for submitting and reading,
and `--store`, `--incarnation` and `--authority-uuid` are REQUIRED ON EVERY
COMMAND — deliberately not defaulted, because the store namespaces every
episode identity in that Authority and restart recovery distinguishes managers
by the incarnation. An earlier version of this page omitted all three and the
reviewer reproduced `exit 2` from it.

```sh
PYTHONPATH="$BOUND" "$PY" -m tools.job_manager \
    --store "$ROOT/db/jobs.sqlite3" \
    --incarnation "<a fresh incarnation for this process>" \
    --authority-uuid "$AUTH" \
    submit --document "$ROOT/run/submission.json"
```

One submission carries both Jobs, each gated ordinarily: review behind
implementation. **No integration stage is submitted**, which is what keeps the
no-integration limit — not the absence of an integrator in the pool.

`tools/stage_execution.py` reads its configuration from
`BATON_V12_STAGE_EXECUTION_CONFIG` (`CONFIG_ENV`), which carries a path only —
never credential bytes. The source of these surfaces is
`v12/python/DEPLOYMENT.md` and `tools/stage_execution.py`'s `CONFIG_ENV` and
`factory`.

## Step 5 — read the outcome

**Read the document, not the absence of one.** If `outcome.json` is not there,
step 4 says what that means and what it does not: it is never a report that the
run ended cleanly.

`state: settled` means every admitted runtime has positive cleanup, both Jobs
produced an attributed verdict, and nothing was refused or uncertain.
`state: held` names every reason in `held_because`. Positive cleanup vocabulary
is the accepted one: `complete` or `retained`; missing, failed or uncertain
cleanup is outstanding, not success.

`finalization_failure` is null on a run that finished accounting for itself. A
value there names a fault that arrived after serving: the run published what it
had, forced itself to `held`, restored its signal handler and re-raised.

`admissions`, `admitted_attempts`, `generations`, `verdicts`, `cleanup`,
`outstanding_cleanup`, `uncertainty` and `interruptions` are all in the
document. An interruption still raises after the outcome is retained, carrying
it — a `SIGTERM` mid-run is owed a readable record.

**Neither a process exit, a `SIGTERM`, nor a missing document is proof that
worker runtimes stopped.** Only the cleanup account in `outcome.json` is. The stop is `two_job_supervisor.supervise`, which reuses W239528's
accepted termination, cleanup-journal and publication machinery — bound by
digest, so a change underneath it is a refusal rather than a passing run.

## Step 6 — watch, read-only

```sh
PYTHONPATH="$BOUND" "$PY" -m tools.job_manager \
    --store "$ROOT/db/jobs.sqlite3" \
    --incarnation "<a fresh incarnation for this process>" \
    --authority-uuid "$AUTH" \
    status --control "$ROOT/db/control.sqlite3"
```

Both Jobs' stages, allocations, workers, participants and runtime identities
are in `baton.v12.job-status/4`. **Overlap is read here**, as both Jobs'
implementation stages `waiting` at one observed instant — not inferred from two
submissions.

**`--control` is what makes this read say anything**, and it is not optional in
practice. Without it the projection reports `canonical: false`, which means
"nobody looked" rather than "nothing is running". My own diagnostic asked
`status` for stage states with no composition at all and printed
`AttributeError: 'NoneType' object has no attribute 'canonical'` on every
receipt for four claims; the recipe on this page was right and the diagnostic
was wrong. It now takes the read from inside the run, where the composition is
open, and the suite asserts both ends of it: every stage `offered` before any
turn answers, every stage `completed` at the last tick.

## What is deterministically witnessed, and what is not

`test_two_jobs.py`, **85 checks**, over W130224's accepted two-Job fixture with
this arrangement's document substituted. A guard case asserts the served
document is THIS arrangement's rather than the fixture's own, so these are not
W130224's evidence re-presented as this Job's.

Witnessed: the composed document passes the product validator and carries
`correction_policy: "decline"`; the submission carries NO integration stage for
either Job; both Jobs reach their OWN reviewers on distinct attempts; each binding
names its own producer and one Work; the pool is four stage workers; both
implementations are `waiting` at one instant; each runs on its own allocated
producer; each writes its own line; each attempt mounts its own workspace; Job
B reaches its own reviewer; and five arrangement refusals, including the one
that must NOT refuse — a shared source and base.

Also witnessed, through the step 4 command itself rather than through its
parts: four admissions and no fifth; **two FROZEN attributed verdicts**, each
derived from its own Job's frozen result by the manager's own
`review_verdict_from_result`; the REAL assignment generation of every admitted
attempt, read back out of the control store the command left behind and
compared attempt by attempt through `attempts.assignment_of` — and that axis
is shown to DIFFER from the pool's in this very run, where every allocation
carries pool generation 1 while the review attempts activate assignment
generation 2; positive
cleanup for every admitted runtime; a supported `status` read taken while the
composition is open, `canonical: true`, every stage `offered` before any turn
answers and `completed` at the last tick; and `state: settled` with exit 0.

Its negatives are witnessed too: a run whose workers never answer is `held`
with "no attributed verdict" and exits 1, and an interruption inside a turn
still publishes the outcome, still records itself in `interruptions` and
`held_because`, still closes admission before cancelling, and still raises.

NOT witnessed, and covered by named accepted evidence instead: the container
boundary (the turn is the fixture's deterministic one) and the live provider
(W239528 and W239533, one Job at a time). See
[CONTINUITY-247941.md](CONTINUITY-247941.md).

## Remaining limitations

1. **The worker turn is a seam, not a running container.** The step 4 command
   drives four admissions, two verdicts and positive cleanup, and it does so
   with a deterministic turn standing exactly where a container would. With a
   real engine the runtime IS the turn. Everything on this page is therefore a
   composition and lifecycle result; none of it is evidence about a real
   provider under concurrency.
2. **No live two-Job run has occurred**, and none is proposed here. If an owner
   wants host concurrency proved against the real engine, that is a separately
   selected runnable packet with its own question.
3. **Positive cleanup for two concurrent runtimes is continuity, not a
   witness.** Accepted cleanup evidence is per-Job; the witness's fixture runs
   no containers.
4. **The operand set is unresolved**, deliberately, and every one of them is
   listed by name.
