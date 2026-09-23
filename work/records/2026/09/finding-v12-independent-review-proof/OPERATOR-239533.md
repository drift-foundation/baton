# Running W239533's independent review

> **NOT RUNNABLE YET.** Owner reroute 247421: the packet stays non-runnable
> until the no-correction boundary is implemented AND independently accepted.
> The boundary is implemented under claim 247423 (see
> [OWNER-PRODUCT-CHANGE-247423.md](OWNER-PRODUCT-CHANGE-247423.md)) and has
> not yet been accepted; R3b -- the actual supervisor admitting and ending one
> reviewer through a deterministic provider -- is also outstanding. Do not run
> steps 2 or 4 until both are accepted.


Prepared by baton.claude under claim 247159. **This page is a packet awaiting
selection, not an authorization.** Nothing here has been executed: no
container, image, provider, network or credential has been reached by this
implementer, and no deployed store has been opened under this claim.

Resolve every `<OWNER: ...>` in [SELECTIONS-239533.json](SELECTIONS-239533.json)
before step 2. A packet composed from an unresolved selections document is
refused by name rather than written.

## What this run does, and what it cannot do

It starts ONE review container against W239528's retained frozen checkpoint and
stops. It admits no implementation stage — the admission gate's only cap is
`review` — and it starts no correction container whatever the verdict says.

It is NOT a fully separate instance, and the page says so rather than letting
the run root's name imply otherwise. Four things are the producer's and have to
be: the v12 Authority and Work (they are the line's identity), the control
store (the line, its writer, its frozen checkpoint and the review attachment
are records in it), and the workspace storage and nominated source (the line's
custody is recorded immutably against them). [attachment.py](attachment.py)
carries the mechanism and the measurement. **The review therefore APPENDS to
W239528's retained control store and its boundary lands under W239528's
workspace storage.** What is this Job's own is its Job store, Job identity,
submission, stage, attempt, generation, criteria, launch home, credential home,
private-context storage, deployment state and outcome — and its worker,
participant and principal, which is where independence actually lives.

## Step 0 — bind the environment

```sh
BOUND=/home/sl/baton-runs/single-implementation-242687/manager-source
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-independent-review-proof
PY=/home/sl/.local/state/baton-v12-venv/bin/python
SEL="$DOSSIER/SELECTIONS-239533.json"
RUN=<the run root you selected>
```

`PYTHONPATH` is bound on every command below for the reason review
2026-09-23T03:42:19Z established on the sibling page: these programs import
`baton_v12`, and an unbound shell answers `ModuleNotFoundError`.

## Step 1 — re-read the subject, and confirm it is still attachable

```sh
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B -c '
import json, sys, attachment
chosen = json.load(open(sys.argv[1]))["compose"]["producer"]
reader = attachment.reading(chosen["control_store"], clock=attachment.now)
try:
    held, refused = attachment.attachable(
        reader, line_id=chosen["line_id"],
        authority_uuid=chosen["authority_uuid"], work_id=chosen["work_id"],
        checkpoint_id=chosen["checkpoint_id"],
        reviewer_worker_id="review-worker", reviewer_participant="baton.review",
        reviewer_principal="principal:baton.review",
        profile_name=chosen["profile_name"])
finally:
    reader.close()
print(json.dumps({"line_state": held["line_state"],
                  "checkpoint": held["checkpoint_id"],
                  "head": held["head_object"], "base": held["base_object"],
                  "producer": held["producer"], "refusals": refused},
                 indent=2))' "$SEL"
```

It opens the producer's control store through `ControlStore.open_readonly` and
reads `line_of`, `checkpoint_of` and `writer_of` inside ONE coherent
`snapshot()`. It writes nothing. **SQLite still owns its coordination files**: a
`wal` database opened read-only gets its `-shm` and `-wal` companions if they
are absent, and claim 244629's earlier survey already created exactly those two
beside this store. They are disclosed in [PROGRESS.md](PROGRESS.md) and left in
place.

An empty `refusals` list is what lets you continue. A non-empty one names
`WRONG`, `STALE`, `LINE STATE`, `PROFILE` or `NOT INDEPENDENT AT` and each is a
state to report, not one to reset.

The values recorded at claim 244629, for comparison: line
`line-0d5b62ba…044c8d` `review-ready` at revision 1, checkpoint
`checkpoint-ab8207ba…b711a9` `frozen`, base `cee07eeb…`, head `f84ae35d…`, tree
`5b4c0f45…`, one changed path (`harness.py`), producer worker
`implementation-worker` / `baton.impl` / `principal:baton.impl`, and NO review
attachment. If any of that has moved, stop and report it.

## Step 2 — compose the packet

```sh
PYTHONPATH="$BOUND:$DOSSIER:$DOSSIER/../finding-v12-single-implementation-proof" \
    "$PY" -B "$DOSSIER/review_bindings.py" \
    --selections "$SEL" \
    --run-root "$RUN"
```

There is **no `--base` operand**, and that is deliberate: a review reads the
base its subject was actually produced against. It prints one SHA256 per
document it wrote.

The composer runs step 1's check itself before composing anything, so a subject
that has drifted between the two steps refuses here too. It then holds the
composed deployment against `stage_execution.held_configuration` — the same
validator the serving deployment and `tools.bootstrap` run — before publishing
`deployment.json`, `submission.json` and `PACKET.json`.

It creates this run's launch, credential, private-context and deployment-state
roots. It does **not** create the producer's workspace storage: that directory
holds the line being reviewed, and a composer that called `makedirs` on it
would be reaching into another Job's retained custody to make its own
validation pass. A missing one is reported as an operational finding.

## Step 3 — prepare the Authority, if this instance has not been

The reviewer participant and its principal must be registered in the
producer's Authority and hold the capabilities the deployment resolves.
`review_bindings.preflight` answers the exact gaps; it asks and writes nothing.
Its closing note differs from the sibling Job's in one way that matters: **this
Job submits a review stage, so `rview` handler registration IS a prerequisite
of running it.**

## Step 4 — run the bounded review

```sh
PYTHONPATH="$BOUND:$DOSSIER:$DOSSIER/../finding-v12-single-implementation-proof" \
    "$PY" -B "$DOSSIER/review_supervisor.py" \
    --packet "$RUN/PACKET.json" \
    --incarnation "<a fresh control incarnation for this process>"
```

Before a store opens it proves the packet's pinned artifacts, the bound manager
source, the bound image, and **the digest of the accepted `baseline.py` it
imports** — `f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5`.
It refuses `review_invocations` other than 1, any `retry` but `false`, a
cleanup reserve outside the overall bound, a subject whose head is its base,
and a deployment whose control store is not the subject's.

Then: one submission; bounded serving with admission capped at one `review`;
a no-progress stop after 6 unchanged ticks; admission closed BEFORE
cancellation; cancellation through the composition's own port; a cleanup
window that can settle endings and admit nothing; a final canonical read; and
an outcome published at `$RUN/outcome.json` **on every path** — including a
submission that refuses, a serving failure and an interruption.

THE RESERVED CLEANUP IS INSIDE THE TOTAL, and the arithmetic is exact: with
300 total and 60 reserved, serving stops at 240 and the cleanup window is
additionally bounded by what is left of the 300. An earlier version served for
the whole 300 and then opened a further 60, which a packet declaring "reserved"
does not mean.

Exit 0 means `state: settled`. Exit 1 means the outcome is `held` and
`held_because` says why. Exit 130 means it was interrupted; the outcome is
still on disk and the path is printed.

## Step 5 — read the outcome

`workload` carries the review evidence: the attempts, the attachment and its
checkpoint, and the verdict read from the reviewer's own FROZEN OUTPUT through
`review_driver.review_verdict_from_result`, which cross-binds the claim against
the attempt, the manifest, the assignment and the checkpoint's base, head and
tree.

**All three dispositions are successful reviews.** `accepted`,
`changes-requested` and `rejected` are results; the shortfall is a run that
produced no attributed verdict at all.

**NO CORRECTION ROUND IS OPENED, and it is declined before the act.** The
deployment this packet composes carries `correction_policy: "decline"`, the
product change owner reroute 247421 selected, so `StageComposition.routed`
never reaches `review_driver.open_correction` and records
`correction_declined` instead. The correction a `changes-requested` verdict
calls for belongs to a separately selected Job.

`review_supervisor.held_packet` REFUSES a packet whose deployment does not
carry that policy, so the boundary is a precondition of running rather than a
promise here. `correction_rounds_opened` remains in the outcome as a
belt-and-braces read of the Job store's own stage records, and a non-empty one
still holds the run.


Accept the proof only with an attributed valid verdict **and** positive stop
and cleanup evidence. Positive cleanup vocabulary is `complete` or `retained`;
missing, failed or uncertain cleanup is outstanding, not success.

## Step 6 — stop

Ctrl-C or `SIGTERM`. The handler is installed around the whole run and
restored at the end, so a signal arriving during cancellation, cleanup or
publication does not kill the process with no outcome on disk. It is not a
`SIGKILL` claim and nothing here pretends otherwise. Do not substitute
process-name kills, raw store edits or evidence deletion.

## The real-provider question this run exists to answer

Deterministic checks cannot establish it, and this packet does not claim to:

> Given independently delivered criteria and read-only access to the retained
> proposal's exact bytes, does the production reviewer return its OWN valid
> `baton.review-report/1` — a verdict from the allowed three, with non-empty
> findings it actually verified — through the real adapter boundary, and does
> the manager derive that verdict from the frozen output and bind it to this
> checkpoint's base, head and tree?

Three things would each answer it negatively and are worth naming in advance,
so that a run that hits one is read as evidence rather than as a bug:

  * the reviewer writes no report, or a malformed one — `review_verdict_from_result`
    refuses and the outcome holds with "no readable verdict";
  * the reviewer reports a base, head or tree other than the checkpoint's —
    the cross-binding refuses and the outcome names both;
  * the reviewer edits the checkout or attempts a commit — its checkout is
    read-only and the criteria say so, so this would appear as a failed turn
    rather than as a verdict.

A `changes-requested` or `rejected` answer is **not** one of those. It is the
reviewer doing its job.

## What this implementer has NOT established

No provider, container, image, network or credential was reached. No deployed
store was opened under claim 247159. The supervisor's termination, admission,
discovery, cancellation, cleanup and publication machinery is W239528's,
imported unchanged and bound by digest — it was proved by that Job's own suite,
not re-proved here. What this dossier's 64 focused deterministic checks cover
is the attachment boundary, the review composition, the documented command
through `write`/`held_configuration`, this supervisor's packet validation,
admission shape and verdict evidence, and the orchestration itself driven over
real Job and control stores -- the serving bound, the reserved-cleanup
arithmetic, a refusing submission, a serving failure, an interruption, and an
outcome published on every one of those paths. See
[verification-6.json](verification-6.json).
