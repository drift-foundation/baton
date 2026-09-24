# The W239533 independent-review packet

> **THIS PACKET HAS BEEN RUN ONCE.** The owner executed
> `independent-review-248377` under claim 248377 on 2026-09-23: one bounded
> live review that settled in 55.409 seconds with an `accepted` verdict, a
> destroyed runtime, `retained` cleanup and zero correction rounds. Its
> verdict was re-derived independently from the retained store under claim
> 248565 and is in [ATTRIBUTION-248565.json](ATTRIBUTION-248565.json); the
> run's own documents are retained under `live-review-248377/`.
>
> **THIS PAGE STILL AUTHORIZES NOTHING.** The twelve `<OWNER: …>` choices in
> the shipped selections remain unresolved — the owner resolved them in that
> run's own documents, not in this template — and running again is an owner
> decision. baton.claude has still reached no container, image, engine,
> provider, network or credential; what this implementer has done with the
> live run is read its retained records through supported readers.

Prepared by baton.claude, last revised under claim 248565. This page is the
operator's half of the packet; [EVIDENCE-239533.json](EVIDENCE-239533.json) is
the machine-readable half and carries every digest, receipt and limitation.
It is DERIVED — `verify.py` regenerates it from the retained files on each
verification run, and `test_packet.py` asserts that this page and that document
agree with the files they describe, so a stale claim here becomes a failing
check rather than prose that quietly ages.

```sh
"$PY" -B "$DOSSIER/packet.py" --claim <this claim>   # regenerate by hand
```

Its `receipts` list covers every retained suite receipt up to the run before
the one that wrote it; the newest `verification-N.json` in this directory is
always the current one.

## What is in the packet

| Part | File |
| --- | --- |
| This page | `OPERATOR-239533.md` |
| Consolidated evidence and limitations | `EVIDENCE-239533.json` |
| Operator selections, with every open choice | `SELECTIONS-239533.json` |
| Subject survey and attachment preflight | `attachment.py` |
| Review-only composer (step 2's entry point) | `review_bindings.py` |
| Bounded review supervisor (step 4's entry point) | `review_supervisor.py` |
| Successor manager-source builder and verifier | `snapshot_247947.py` |
| Successor manager-source manifest, 106 files | `MANAGER-SOURCE-independent-review-247947.json` |
| The product change this packet depends on | `OWNER-PRODUCT-CHANGE-247423.md`, `PRODUCT-CHANGE-247423.json` |
| Pre-existing-error corroboration | `preexisting_errors.py`, `PREEXISTING-ERRORS-247666.json` |
| Deterministic verification | `verify.py`, `test_*.py`, `verification-N.json/.log` |

Exact SHA256 for every one of those is in `EVIDENCE-239533.json` under
`programs`, `suites` and `documents`, alongside `reused` — the accepted bytes
this dossier imports rather than copies, including W239528's `baseline.py` and
the product's `tools/stage_execution.py`.

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

## The operator-selected inputs

Twelve, listed exactly and in full under `operator_selected_inputs` in
`EVIDENCE-239533.json`, read out of the selections document rather than
transcribed. By member:

`compose.run_id`, `compose.claim`, `compose.supervisor_path`,
`compose.vectors`, `compose.cli_build`, `compose.provider_network`,
`compose.evidence_digest`, `compose.instance.job_store`,
`compose.instance.runtime_path`, `compose.instance.build_commit`,
`compose.credential_profile.api.provider` and
`compose.credential_profile.api.reference`.

Three deserve a note before they are chosen:

  * **`compose.provider_network`** — `none` is refused by name. The reviewer
    reaches an external Claude API, so a run on no network produces a failed
    turn rather than a review.
  * **`compose.credential_profile.api.reference`** — a VALID token is required.
    An expired one reproduces the failure path W239528 already recorded; that
    is a known negative and not this run's question.
  * **`compose.evidence_digest`** — an all-zero sentinel is refused. This
    candidate context profile has to rest on named accepted evidence.

A packet composed from an unresolved selections document is refused by name
rather than written, so resolving all twelve is a precondition of step 2 and
not a formality. The owner resolved them for `independent-review-248377` in
that run's own documents; **this template still ships every one of them
unresolved**, and the resolved values are not copied back into it, because a
template that carries one run's credential reference and run identity is no
longer a template.

## Step 0 — bind the environment

```sh
BOUND=/home/sl/baton-runs/independent-review-247947/manager-source
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-independent-review-proof
PY=/home/sl/.local/state/baton-v12-venv/bin/python
SEL="$DOSSIER/SELECTIONS-239533.json"
RUN=<the run root you selected>
```

`PYTHONPATH` is bound on every command below for the reason review
2026-09-23T03:42:19Z established on the sibling page: these programs import
`baton_v12`, and an unbound shell answers `ModuleNotFoundError`.

**`BOUND` IS THIS JOB'S OWN SNAPSHOT, not the producer's.** W239528's
`single-implementation-242687/manager-source` predates the `correction_policy`
change owner selection 247421 made, so a run bound to it has no boundary to
decline the correction round with and `review_supervisor.held_packet` refuses
the packet composed from it. The successor is built and verified by
[snapshot_247947.py](snapshot_247947.py) and bound by
[MANAGER-SOURCE-independent-review-247947.json](MANAGER-SOURCE-independent-review-247947.json);
106 files, carrying `tools/stage_execution.py` at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. The
producer's snapshot is verified UNCHANGED as part of every build and is never
written to. Re-verify before step 2:

```sh
"$PY" -B "$DOSSIER/snapshot_247947.py" --verify
```

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

**THE SUBJECT HAS MOVED, BECAUSE THE REVIEW HAPPENED.** Read at claim 248565,
the line is `accepted` at revision 1 and its attachment
`review-3536ffc9…aea156` is `ended`. A line that is no longer `review-ready`
is REFUSED by this step and by the composer, which is correct: this packet
reviews a retained proposal once, and reviewing it again is a different
selection with a different subject state. **Do not treat that refusal as a
defect.**

The values below are what the selections still record, read at claim 244629
before the run. For comparison: line
`line-0d5b62ba…044c8d` `review-ready` at revision 1, checkpoint
`checkpoint-ab8207ba…b711a9` `frozen`, base `cee07eeb…`, head `f84ae35d…`, tree
`5b4c0f45…`, one changed path (`harness.py`), producer worker
`implementation-worker` / `baton.impl` / `principal:baton.impl`, and NO review
attachment. If any of that has moved, stop and report it — the composer refuses
on the same disagreement, so drift is a refusal rather than a wrong review.

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
`held_because` says why. Exit 2 means it refused before anything opened. Exit
130 means it was interrupted; the outcome is still on disk and the path is
printed.

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

Deterministic checks cannot establish it, and this packet does not claim to.
Every verdict in this dossier is minted from a fixture turn this implementer
wrote the report for; what is unproved is whether a real reviewer, given only
the criteria and the bytes, produces a report the adapter accepts at all.

> Given independently delivered criteria and read-only access to the retained
> proposal's exact bytes, does the production reviewer return its OWN valid
> `baton.review-report/1` — a verdict from the allowed three, with non-empty
> findings it actually verified — through the real adapter boundary, and does
> the manager derive that verdict from the frozen output and bind it to this
> checkpoint's base, head and tree?

Three things would each answer it negatively and are worth naming in advance,
so that a run that hits one is read as evidence rather than as a bug:

  * the reviewer writes no report, or a malformed one — `review_verdict_from_result`
    refuses and the outcome holds with "no readable verdict". The adapter
    requires `findings` to be non-empty TEXT, and a malformed report is
    deliberately not a verdict: an exit status is not a decision.
  * the reviewer reports a base, head or tree other than the checkpoint's —
    the cross-binding refuses and the outcome names both;
  * the reviewer edits the checkout or attempts a commit — its checkout is
    read-only and the criteria say so, so this would appear as a failed turn
    rather than as a verdict.

A `changes-requested` or `rejected` answer is **not** one of those. It is the
reviewer doing its job.

## What has been executed, at its real width

**The live run, first, because it is the only thing here that answers the
provider question.** The owner ran `review_supervisor.main` with the documented
`--packet` and `--incarnation` against the real image, provider and credential;
it settled. `attribution.py` then re-derived the verdict from the pinned
control store through `ControlStore.open_readonly`, one snapshot and public
readers only — `line_of`, `checkpoint_of`, `review_of`, `frozen_output_of`,
`load_manifest`, `cleanup_of`, `writer_of` and
`review_driver.review_verdict_from_result`. It re-derives as `accepted`,
agrees with the published outcome on all eight compared members, and shows the
reviewer's worker, participant and principal all differing from the producer's.
No raw SQLite, no copied database, no `immutable=` handle and no write-capable
fallback was used. **THE EXECUTED PACKET DIFFERED FROM THE COMPOSED ONE BY THE
REMOVAL OF `bounds._note` AND NOTHING ELSE** — the metadata defect described
below, since corrected.

Then the two deterministic proofs, which remain **separate — neither subsumes
the other.**

**The `main` startup proof.** On disposable fixtures with `PYTHONPATH` bound to
the successor snapshot alone, `test_review_bindings.TheDocumentedCommandsRunAgainstTheSUCCESSORSource`
runs step 2's composition command and then enters step 4's entry point,
`review_supervisor.main`, with the documented `--packet` and `--incarnation` at
12/4 bounds. Two of `main`'s own seams are supplied so nothing is started:
`image_inspect`, so no engine is reached, and `compose`, so no container can
be. Everything else is real — the packet validation, the imported-source check,
the Job and control stores, the pre-submission survey, and the supervised run
that publishes an outcome. That outcome is **`held`**, because a composition
that starts nothing answers nothing about the reviewer. It proves the STARTUP
PATH, not a review.

**The real-coordination lifecycle.** `test_review_lifecycle` settles a run with
one attributed verdict, a stopped runtime and `retained` cleanup, over a real
Job store, control store, composition, admission gate, line, writer, frozen
checkpoint, review attachment and frozen review output — phase one being
W239528's accepted baseline run, so the checkpoint under review is one that
Job's accepted program actually made. Its PROVIDER is the fixture's
deterministic worker turn, the same one W239528's accepted suite and the
product's own `ManagedSessionResume` use. It calls `supervise` directly with an
injected clock; **it does not enter `main`.**

**So: no DETERMINISTIC case here both enters `main` and settles.** The live run
does both, and it is the only thing that does. Do not read a deterministic case
as evidence for it, and do not read the live run as evidence that the suite
covers the entry point end to end.

## The two template defects the live run found

Both were found by an owner running these exact commands, and neither was
caught by preparation acceptance, because every case in the suite wrote its own
synthetic selections — a document this suite invents has no prose in it.

  * **Step 2 refused with a `TypeError`.** `review_bindings.main` passed
    `selections["compose"]` through as `**kwargs`, and the shipped template
    carries `_manager_source_note`, which `compose` has no operand for. The
    CLI failed before `compose` was entered.
  * **Step 4 refused at startup.** `compose` copied `bounds` verbatim into
    `PACKET.json`, so `bounds._note` reached `held_packet`, which requires
    exactly the five execution members.

Corrected under claim 248565 by normalizing at composition: a leading
underscore marks a documentation member everywhere in this packet, and
`review_bindings.without_documentation` removes them recursively before
anything is composed or written. **Neither entry point was loosened** —
`compose` still has no operand called `_manager_source_note` and `held_packet`
still requires exactly five bounds members, because a packet is an execution
document and prose belongs in the template a human reads. An unknown member
that is NOT documentation is now refused by name rather than reaching Python as
a `TypeError`, so stripping prose cannot swallow a typo.
`test_review_bindings.TheACTUALShippedTemplateComposesAndStarts` runs the
shipped file through both entry points and pins both defects as still being
defects without the normalization.

## What this implementer has NOT established

Read `not_established` in [EVIDENCE-239533.json](EVIDENCE-239533.json) before
`established`. In short: this implementer has still reached no provider; the
deterministic suite still has no case that both enters `main` and settles; the
live result is ONE run and not a rate — it establishes no reliability figure
and nothing about a reviewer that disagrees, since `changes-requested` has been
settled only deterministically; the supported reader refused for the reviewer
at claim 248523 and opened here at claim 248565 with the CAUSE UNKNOWN; the
imported termination,
discovery, cancellation, cleanup-accounting and publication machinery is
W239528's, bound by digest and proved by that Job's suite rather than re-proved
here; the bounds are proposed rather than validated against a review workload;
the signal handling is not a `SIGKILL` claim; and the cumulative verification
spending is partly UNKNOWN — the retained receipts are exact, superseded and
ad-hoc runs were not receipted, and the difference is not estimated.

What the deterministic checks DO cover is listed in `established`, each entry
naming the module that carries it: the attachment arrangement and its supported
read-only survey, review-only composition, packet validation, the correction
boundary, one reviewer admitted and ended with an attributed verdict,
`changes-requested` with zero correction rounds, and the failure, interruption,
stall, bound and cleanup properties.
