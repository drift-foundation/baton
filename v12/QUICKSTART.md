# Operator quickstart — the native v12 coordination instance

One deployment, one two-stage Job, one human owner. This page is the operating
surface only; every procedure it points at is owned by its own record and is
cited rather than repeated.

This page describes **the installed instance 4**, built from
`614668e0831e8c87cdae11ca43620e0d544a84d5`. Earlier pilot records describe
**instance 1** at source `14e52d80679de5e844f72324df632da5e01cf393`; their
reasoning still holds, but their destination, Job and command inventory do
not apply here and are marked historical below.

* How this instance was prepared and installed, operand by operand:
  `baton:work/records/2026/10/finding-v12-native-pilot-instance-packet/fresh5-361402/COMMANDS.md`
* The bundle it runs, with its digests and its disclosed `dirty` build stamp:
  `baton:work/records/2026/10/finding-v12-native-pilot-instance-packet/bundle-361217/BUNDLE.md`
* The ordered supported operations, the receipt boundary, retention and
  rollback: `baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/PACKET.md`
  (§5, §7, §9) — *historical identifiers; the reasoning applies, the instance
  names do not*
* The owner's disposition procedure, operand by operand:
  `baton:work/records/2026/10/finding-v12-pilot-owner-disposition/PROCEDURE.md`
  — *take the operands from the table below, not from its examples*
* The deployment's own lifecycle, selector and runtime verification:
  `v12/STACK.md`; the normative specification: `v12/DESIGN.md`

Paths below are derived from the one destination, never configured twice
(`v12/python/tools/instance.py`). With `DEST=/home/sl/baton-instances/native-coordination-pilot-w321608-4`:

| What | Where |
| --- | --- |
| the command | `$DEST/distro/baton-v12-stack` |
| the selector every lifecycle verb takes | `$DEST/instance.json` |
| authority store / its identity | `$DEST/db/authority.sqlite3`, `$DEST/authority-identity.json` |
| Job store / control store | `$DEST/db/jobs.sqlite3`, `$DEST/db/control.sqlite3` |
| the published status document | `$DEST/state/status.json` |
| an attempt's retained raw output | `$DEST/state/launch/logs` |
| the supervisors' own output | `$DEST/logs` |

The Job is `quickstart-d` with two stages, `implementation` then `review`, and
no integration stage; its terminal policy is `report-and-hold`. Its Work is
`19b4f145-W1` under authority `19b4f1459c2442e4aec8c7cd23e92312`, and each
invocation is bounded at **3600s of provider turn and 900s of verification
command**. The deployment also carries a `git` integration profile whose
integrator is `baton.integrator-pilot`; **this Job has no integration stage
and does not use it**.

## Supported commands

Every line is `$DEST/distro/baton-v12-stack <subcommand>`, and every operand
after the subcommand is that subcommand's own.

**Where `--instance` goes.** On the installed command the subcommand comes
first and `--instance` immediately after it:
`monitor --instance $DEST/instance.json --interval 3` is read,
`monitor --interval 3 --instance $DEST/instance.json` is rejected as an
unrecognized argument, and `--instance … monitor` is rejected as a subcommand
name. The bare source parser declares `--instance` at the top level, so a
line copied from `v12/python/tools/stack.py` has the operands the other way
round; the deployed order is the one above
(`v12/python/tools/stack_command.py` lifts a leading `--instance`/`--root`
pair and appends the verb).

| Subcommand | What an operator runs it for |
| --- | --- |
| `identity` | what this build IS, recorded before it is trusted; `--version` answers with nothing else available |
| `start --instance $DEST/instance.json` | the scheduler and its snapshot publisher |
| `status --instance $DEST/instance.json` | process health, snapshot freshness, Job count, and the runtime boundary |
| `monitor --instance $DEST/instance.json [--interval 3] [--ticks N]` | the read-only list view: each stage's kind, state, elapsed, activity and reason. Ctrl-C leaves it; leaving it does not stop scheduling |
| `stop --instance $DEST/instance.json` | only the processes this deployment owns |
| `repository --instance $DEST/instance.json` | what this instance's own configured repository is; it needs the selector and refuses without it |
| `manager --store $DEST/db/jobs.sqlite3 --incarnation <yours> --authority-uuid 19b4f1459c2442e4aec8c7cd23e92312 submit --document <submission.json>` | admit the prepared two-stage submission, once |
| `manager <the same three operands> status --control $DEST/db/control.sqlite3 --observe tools.stage_execution:observing_factory` | the status projection as JSON, which is the document the publisher writes |
| `manager <the same three operands> fresh-attempt --prior-job <job> --control $DEST/db/control.sqlite3 --authority $DEST/db/authority.sqlite3 --instance $DEST` | admit a fresh attempt at a Job **whose execution failed** — see the boundary below |
| `view --status $DEST/state/status.json --job quickstart-d` | one Job in detail: stage state, work, episode, offer, **attempt**, runtime, assignment, and the frozen result locators |
| `attempt-diagnostics $DEST/state/status.json` | a read-only diagnostic projection over one status document |
| `logs --logs $DEST/state/launch/logs --attempt <attempt-id> …` | one attempt's retained raw output; opens no store and reaches no engine |
| `record …` | the canonical dossier (`read`, `bind`, `cite`, `verify`) and the retained-instance recovery set (`recovery-manifest`, `recovery-check`) |
| `disposition …` | the owner's own surface: `pending`, `approve`/`deny`, `integrated`, `close` |

The authority uuid above is this instance's own, as
`$DEST/authority-identity.json` records it — never a preflight or fixture
UUID. Nothing else in the bundle belongs to this loop: `bootstrap` installed
this destination once and a prepared destination refuses reuse, and `publish`
and the manager's serving loop are children `start` supervises rather than
things to invoke by hand.

`attempt-diagnostics` takes **one positional status document and nothing
else** — no store, instance or engine operand — so it has no `--help`:
passing one is read as a filename and refused as unreadable. It opens no
store, calls no engine and settles nothing; a cause it reports is not an
acceptance and not a freshness verdict.

`manager fresh-attempt` exists in this build, and its boundary is narrow: it
admits a fresh attempt at a Job **whose execution failed**, carrying that
Job's submitted specification, limits and scope forward unchanged, and it
refuses unless this host's own control store shows every prior runtime ceased
and its resource returned — `unknown` refuses rather than proceeds. A Job
whose stages **completed** has nothing for it to repeat: a candidate an
operator disagrees with is a disposition question, not an execution one.

This instance's bundle is built from the selected source
`614668e0831e8c87cdae11ca43620e0d544a84d5`, which is also the Job's declared
base, and `identity` reports that commit with `dirty: true` — disclosed in
`bundle-361217/BUNDLE.md`, where the modified entries are records outside
`v12/`. A source-level entry is still not a deployed one: anything added to
the source after this commit is absent here until a new bundle is built,
bound by independent review and installed.

## Execution is not acceptance

A stage state is a projection computed from receipts and the Worker Manager's
public reads, written nowhere (`v12/python/src/baton_v12/job_manager/projection.py`).
`completed` therefore says that this stage's execution ended and its output was
frozen. It does not say the candidate is good, and nothing downstream of it
treats it as approved: dependencies gate on `completed` and nothing else, and
the review stage producing a verdict is the independent pickup of the
candidate — not a judgment of it.

This is not a hypothetical here. `quickstart-d` ran both stages to
`completed` with a review verdict of `ACCEPTED`, and the candidate it
produced described the wrong deployment. Two `completed` stages and a
producer's verdict are exactly as much as this control plane claims.

The three judgments are separate people, and this deployment's are:

| Judgment | Actor |
| --- | --- |
| verification receipt | `baton.verifier-pilot` |
| review receipt | `baton.reviewer-receipt-pilot` |
| approval, integration, closure | `baton.slaw`, the human owner |

The owner holds neither `verify` nor `review`. The two receipts are authority
acts by those configured actors on the published candidate, with the
verification judge evaluating the requirement clauses itself; the installed
command has no verb for either, by design. The sequence and the exact calls are
PACKET §9 B — read them there.

The approval cannot be reached any other way. The Job carries no integration
stage, so nothing in it can write the three receipts that include the approval
and make it immutable; composing an integration stage into a human-approved
Work re-creates that call site and takes the decision away from the owner by
configuration. Measured in
`baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/rehearsal-324985/RECEIPT-BOUNDARY.md`.

Two reading traps worth keeping apart: `record verify` resolves the dossier's
citations against a root and is *not* a verification receipt, and a passing
verification command closes nothing. A structural verification command is the
narrowest of these: `quickstart-d`'s checked four headings, a byte floor and
three markers, and passed on a document about another instance. What the
owner owes next is answered, read-only, by `disposition pending --work
19b4f145-W1 --participant baton.slaw`; the acts themselves are PROCEDURE.md
§§1–4.

## Reading a failed attempt

An `exceptional` stage is where this control plane stops owing an act. Its
successors stay blocked, the gate that will never open is reported as closed
rather than treated as satisfied, nothing silently retries, and nothing routes
the failure to anybody automatically — that last part is selected policy, not a
missing operation (PACKET §9 D). An empty provider turn cannot falsely
complete it.

1. See it. `monitor` shows each stage's state and its `reason` line. For the
   identities, take the detail view: `view --status $DEST/state/status.json
   --job quickstart-d`, which prints the stage's `attempt`, `runtime`, engine,
   assignment and either its frozen results or an honest
   `unavailable (no frozen output in this snapshot)`.
2. Summarise it. `attempt-diagnostics $DEST/state/status.json` projects the
   same document into the failure axes — which component ordered a runtime
   stopped, which records are absent, what is simply unknown. It resolves no
   locator and judges no freshness; it tells you which attempt to read.
3. Read its output. `logs --logs $DEST/state/launch/logs --attempt <attempt-id>
   locators` names every stream, where it is and what it honestly is; then
   `logs … read --stream provider.stderr --text` (or `worker.stdout`,
   `worker.stderr`, `provider.stdout`, `verification.stdout`,
   `verification.stderr`), with `--from-byte`/`--limit` bounding the window and
   `follow` for one that is still moving.
4. Read it as evidence. The delivery root is the launch home's own `logs`
   directory above, not `$DEST/logs`, which is the supervisors' output. Missing
   is not empty: a stream never opened, one that could not be written, one
   truncated at a ceiling and one cut short on a drain's clock are four
   different facts and the capture state says which. Nothing in this manager
   reads a log to decide anything.

The retained attempt, its capacity and its evidence are held, which is what
`report-and-hold` exists for. If the failure needs an owner other than the
operator, giving it one is a deployment act on a dedicated diagnosis route,
performed without stealing the execution claim or clearing a runtime hold; one
principal holds one active claim, which is why a separate participant is
needed at all. Both supported shapes — adding a diagnostic handler to the
Work's route, or a dedicated diagnostic Work on its own route — are PACKET
§9 D, with the evidence in
`baton:work/records/2026/10/finding-v12-pilot-diagnostic-recovery-matrix/matrix-325259/MATRIX3.md`,
which names that handler `baton.diagnostician` — and **this deployment's
configuration configures no diagnostic handler at all**: the participants
`$DEST/deployment.json` names are the two stage workers
(`baton.claude-pilot`, `baton.reviewer-pilot`), the three receipt actors and
the integrator. That is a statement about this instance's configuration, not
a claim about who exists in its authority. Selecting a handler is therefore a
coordination decision and not a command on this page.

## Cancelling or holding safely

`stop` stops the supervisor processes this deployment owns. It is not cessation:
the attempts the manager opened live in runtimes it does not own, so `status`
and `stop` both print the runtime boundary, and an `unknown` there means
precisely that what is still executing was not resolved. An open episode prints
the sentence with it. Stopping admissions, positively accounting for every
runtime and launch, and admitting one writable instance are the three
obligations no command here discharges (PACKET §5).

Cancelling the live assignment is an authority act by the configured owner of
that assignment, not an installed verb, and what it leaves behind is exact: the
handler is gone, the cancellation is in the assignment events, and **the Work is
still `open` with no outcome** — a cancelled assignment is not a cancelled Work.
The **runtime-quiescence gate survives the cancellation**, and the number in it
is the **cancelled assignment's own generation** — never the pool generation
and never the allocation's. `Authority.cancel` fences
`runtime-quiescence:<that assignment's generation>`
(`v12/python/src/baton_v12/authority/core.py`), and an assignment carrying no
generation is refused outright rather than fenced with a blank.

Those axes really do diverge on this instance. Its own published snapshot
records the implementation assignment at generation 1 and the review
assignment at generation 2, while both allocation generations, the resource
token's generation and the deployment's pool generation are 1. So *as an
example, for the review assignment as that snapshot records it*, a re-claim
after a cancellation would be refused with
`Work is blocked by 'runtime-quiescence:2'` — an example for that one
assignment, not a constant of this deployment. Read the generation off the
assignment you are actually ending: `disposition pending` reports it under
`work.assignment`, and `view --status $DEST/state/status.json --job
quickstart-d` prints it with the runtime. Discharging the gate needs the
engine's own absence sentence naming that exact runtime identity. Uncertainty
stays held; it is never advanced to make a re-claim possible
(`matrix-325259` scenario 8, PACKET §7).

Both of `quickstart-d`'s stages have **completed**, so nothing here is an
instruction to cancel either one; the generations above are read from the
retained snapshot to show which number the rule uses.

An honest ending is a closure that claims nothing:

    $DEST/distro/baton-v12-stack disposition close \
        --authority-store $DEST/db/authority.sqlite3 \
        --authority-uuid 19b4f1459c2442e4aec8c7cd23e92312 \
        --participant baton.slaw --work 19b4f145-W1 \
        --outcome non-satisfying --rationale "<the operator's own reason>" \
        --operation-id <yours> [--expect-assignment <file>]

The terminal outcomes are `satisfying`, `non-satisfying`, `rejected` and
`cancelled`, and only `satisfying` records an acceptance. A non-satisfying
closure records none, and the parser's `--proposal`,
`--expect-candidate-digest` and `--root` are **refused at the verb** when the
outcome is not `satisfying`, because an ending that is not satisfying checks
no candidate; the call changes nothing when it refuses. If a Handler still
holds the Work, the authority requires `--expect-assignment` naming that exact
identity, which `disposition pending` reports under `work.assignment`. The
rationale is the operator's own prose and is what the record keeps; the same
request replays, a different one refuses and changes nothing. The Work stays
the historical authority even when abandoned.

Nothing in these commands deletes or rewrites evidence. This instance's
retention disposition is `retain` (`v12/instance-retention.md`), proposals,
receipts and citations are reported at closure either way, and the recovery set
is `record recovery-manifest` with `record recovery-check` over a restored
one — a clean check is a precondition for an operator's admission and never an
admission itself. Slawomir owns backup, restore and every Git operation.

### Retained failed-execution settlement

The installed command accepts an explicit instance selector and the exact Job,
stage and episode. Preview is read-only and does not reserve eligibility:

```sh
"$DEST/distro/baton-v12-stack" manager settlement-preview --instance "$DEST/instance.json" --job JOB --stage JOB/implementation --episode 1 --operation-id OPERATION > preview.json
```

Save the `request` object from that response as `request.json`, then select the
operation explicitly:

```sh
"$DEST/distro/baton-v12-stack" manager settle-stopped --instance "$DEST/instance.json" --document request.json
"$DEST/distro/baton-v12-stack" manager settlement-status --instance "$DEST/instance.json" --document request.json
```

The request binds the installed package and deployment, Job episode, original
assignment, exact runtime and resource generation, and validated faulted exchange.
Settlement refuses while another manager holds the instance. It rechecks
eligibility, fences execution permission, observes cessation again, records
`failed-stopped`, and returns only that generation. Unknown runtime or writer
state stays held. Files, failed exchange, result-consumption obligations and
Authority disposition remain independent; settlement supplies no successful
review verdict and performs no cleanup.

Retry the unchanged request after interruption. Status distinguishes
`not-selected`, `held`, `release-pending`, `returned-receipt-pending`, and
`settled`. A committed request can resume after independent Authority disposition;
a new selection requires the expected current assignment. Preview and status
open existing stores read-only, with no migration or writable fallback. Preview
may inspect the exact runtime; status reads only durable settlement records.
