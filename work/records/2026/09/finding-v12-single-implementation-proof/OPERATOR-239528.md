# Operator steps for the W239528 single-implementation packet

Claim 240196, baton.claude. Prepared for independent review; **not approved for
execution by its existence**. Read with `SELECTIONS-239528.json`,
`PROVIDER-QUESTION-239528.md` and `DIAGNOSIS-239528.md`.

**Nothing in this document is performed by the implementer.** Every step below
is an owner act. This claim opened no store, started no container, minted no
grant, ran no version-control command that writes, and performed no recovery.

## What this revision corrects

Review 2026-09-22T15:32:51Z requested changes on two counts and both were
right.

- **R1.** The previous revision's steps invoked plain `python3` with no
  interpreter, import path or working directory bound. In a child with no
  inherited `PYTHONPATH` the documented composer command fails at its first
  product import. It also referred to a "Step 5a Authority preparation" this
  document did not contain, claimed `preflight` supplies a route-handler list
  it explicitly cannot verify, and reduced every artifact operand to a
  placeholder even though the image, runtime and manager source were selected
  and accepted under W236087. All four are corrected below, and
  `test_entrypoints.py` now runs both commands as commands.
- **R2.** A fresh `run_id` did not make the packet executable, because every
  packet this composer wrote named the same Job identity `job-a`. Two of them
  in one store collide at submission -- *after* `prepare` has spent a one-run
  qualification grant. The Job identity is now derived from `run_id`, a
  collision is refused **before any owner act**, and the claim that this run's
  accounting would report an older Job's outstanding runtime is withdrawn: it
  would not, and this document no longer says it does.

## The two commands, exactly

Everything below uses absolute paths and binds the interpreter and the import
path, so no step depends on a working directory or on a developer's shell.

```sh
PY=/home/sl/.local/state/baton-v12-venv/bin/python
BOUND=/home/sl/baton-runs/managed-correction-236087/manager-source
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-single-implementation-proof
RUN=/home/sl/baton-runs/single-implementation-239528/run
SEL=/home/sl/baton-runs/single-implementation-239528/selections.json
```

`$BOUND` holds `baton_v12/` and `tools/` at its root -- 106 files, re-read and
verified under this claim -- which is why **one** `PYTHONPATH` entry is enough.
This checkout's layout is different (`v12/python/src/baton_v12` and
`v12/python/tools`) and would need two;
`test_entrypoints.TheDocumentedComposerRunsAsDocumented` asserts the relocated
layout is flat, so a future relocation that nested the packages would fail a
test rather than silently break this page.

## Preconditions

1. **A NEW `run_id`, which is now also a new Job identity.**
   `managed-correction-236087`'s qualification grant is CONSUMED -- the live
   run's opening admission consumed it. `SELECTIONS-239528.json` names
   `single-implementation-239528`, from which the composer derives the Job id
   `job-single-implementation-239528`. Do not reuse either after this run.

2. **A fresh, isolated store arrangement. This is the recommended default and
   the selections file is filled in for it.**

   `/home/sl/baton-runs/single-implementation-239528/` with its own Authority,
   Job, control and integration stores. The W236087 install is left exactly as
   it is, which is also what "preserve the failed instance" requires.

   **What this run's accounting does and does not cover.** It covers the one
   Job named in the packet and nothing else. `_attempts_of` filters the status
   projection to that Job, so a runtime belonging to any other Job -- in this
   store or any other -- is not part of this outcome's attempt discovery,
   cancellation or cleanup. The previous revision said the opposite and was
   wrong. The supervisor now surveys the store before any owner act, prints
   every other Job it holds, and writes them into the outcome under
   `preexisting_jobs` with an `accounting_scope` sentence saying plainly that
   they are **NOT covered**.

   **W236087's outstanding runtime is therefore untouched and unaccounted for
   by this run**, whichever arrangement you pick. Runtime
   `14690a98be8298b66d3c2b4f231a6f05f35958ae7a033af1788e4ca1d5be7a66` remains
   `quiescent` with `cleanup: pending` and no committed destroy. Recovering it
   is a separate owner act; see `DIAGNOSIS-239528.md`.

   <details><summary>The alternative: reusing the W236087 instance</summary>

   It is now possible -- the Job identity no longer collides -- but it carries
   two prerequisites this implementer could not verify, because verifying them
   means opening that deployment's stores and this claim did not:

   - Its Job store already records `job-a`. A packet deriving its Job id from
     a fresh `run_id` will not collide, and `baseline.survey` refuses before
     any owner act if it somehow would.
   - The faulted attempt still holds an **open assignment** in that Work's
     scope at the Authority. Whether the manager admits a new assignment for
     the same participant while one is open is not established here. If it
     does not, composition refuses -- after `prepare` has committed. Confirm it
     through supported readers first, or use the fresh instance.

   </details>

3. **Step 5a below must have been performed on whichever instance you select.**
   A fresh `just bootstrap` install creates the Authority identity and stores
   and creates **no Work, no route handler and no grant**.

4. **A bounded egress network.** `none` is refused by name: the worker reaches
   an external Claude API and this packet composes no local provider or proxy.

## Step 1 — the instance

For the recommended arrangement, bootstrap a fresh install rooted at
`/home/sl/baton-runs/single-implementation-239528/`. Record the Authority uuid
it generates into `instance.authority_uuid` in the selections file; the four
store paths are already filled in.

The image, the manager source and the installed runtime are **not** rebuilt.
They were selected, built and independently accepted under W236087 and were
re-read from disk under this claim:

    worker image      baton-v12-claude-worker:w236087-236349
                      sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd
    worker adapter    opt/baton/claude_agent.py
                      abdf903da3c767f3fe9babf84e4499f455da968a61ee3c975b9899988354bb4d
    manager source    /home/sl/baton-runs/managed-correction-236087/manager-source
                      106 files, flat layout
    installed runtime /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro
                      baton-v12-stack 04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a

`held_packet` pins every one of them and refuses before opening a store if a
byte has moved.

## Step 2 — the fixture repository, and its HEAD

The fixture is the SUBJECT of the change and the operator's record of the
selection, and nothing else:

    harness.py   print('before')
    TASK.md      the operator's committed note of what was selected

**There is deliberately no `ACCEPTANCE.md` and no `REVIEW-FEEDBACK.md`.**
W236087's fixture shipped them and its implementation agent read the acceptance
document out of the tree and graded itself against it. This Job has no reviewer,
so a document describing judging has nothing to do here.

Initialise a repository at the source root, commit those two files, and pass the
resulting HEAD as `--base`. That commit must also be the Authority's canonical
target: `retain_proposal` reads it and `publish_candidate` binds to it. Record
the HEAD and `harness.py`'s sha256 in the selections file.

This step is yours because this deployment prohibits the implementer from
performing version-control mutations. The composer refuses an unresolved base
by name rather than writing a placeholder.

## Step 5a — prepare the Authority

A fresh install creates no Work, no route handler and no grant, and
`stage_execution` resolves each configured participant's principal from the
Authority and mints sessions in the target Work's scope. A deployment whose
participants were never registered refuses at composition -- after the packet
has been written.

These are Authority mutations and therefore yours:

```python
from baton_v12.authority import Authority

STORE = "/home/sl/baton-runs/single-implementation-239528/db/authority.sqlite3"
UUID = "<the uuid step 1 generated>"
WORK = "<uuid-prefix>-W1"

authority = Authority.open(STORE, expected_authority_uuid=UUID)
try:
    authority.create_work(WORK, "impl", contract="v12-assignment-1",
                          operation_id="w239528-single-implementation")
    scope = authority.project_work(WORK)["scope"]
    authority.add_route_handler("impl", IMPLEMENTATION_PARTICIPANT)
    # The review worker is CONFIGURED and never admitted -- see step 4 -- but
    # `stage_execution` resolves its principal, so it must exist. Registering
    # the `rview` handler is not a prerequisite of THIS run, because this Job
    # submits no review stage.
    authority.add_route_handler("integration", INTEGRATOR_PARTICIPANT)
    for who, capability in ((VERIFIER, "verify"), (REVIEW_RECEIPT, "review"),
                            (APPROVER, "approve"),
                            (INTEGRATOR_PARTICIPANT, "integrate")):
        authority.grant_capability(who, capability, scope=scope)
finally:
    authority.dispose()
```

### Checking what is left, and exactly what that check can see

`baseline_bindings.preflight` reads through an open Authority handle and writes
nothing. **It is a Python helper. Neither CLI `main` calls it**, so running it
is a separate act:

```python
import json
from baton_v12.authority import Authority
import baseline_bindings

selections = json.load(open(SEL))
documents = baseline_bindings.compose(base=BASE, run_root=RUN,
                                      **selections["compose"])
authority = Authority.open(STORE, expected_authority_uuid=UUID)
try:
    print("\n".join(baseline_bindings.preflight(
        authority, documents, selections["compose"]["participants"])))
finally:
    authority.dispose()
```

**What it can and cannot establish**, stated because the previous revision
overstated it:

- It **can** say the Work does not exist or is unreadable, and that a
  configured participant resolves to no principal. Both are conclusive.
- Capabilities are only **half** conclusive. `capabilities_of` answers which
  capability NAMES a principal holds *in any scope*, not whether a grant is
  effective in this Work's scope. A missing name is conclusive; a present one
  is not.
- It **cannot** verify route handlers at all. This Authority exposes no public
  reader for a route's handlers. The previous revision claimed preflight
  "answers the exact list of missing ... route handlers"; it does not, and it
  says so itself in the line it always appends. `impl` handler registration is
  yours to assert.
- It asks about **both** configured participants, including the review one this
  Job never launches, because the deployment resolves a principal for every
  worker it configures.

## Step 3 — compose the packet

```sh
PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/baseline_bindings.py" \
    --selections "$SEL" \
    --base "$BASE" \
    --run-root "$RUN"
```

`PYTHONPATH` names the bound tree and nothing else. This exact shape is
exercised by `test_entrypoints.TheDocumentedComposerRunsAsDocumented`, in a
child process with `PYTHONPATH` removed from the environment and then set to a
relocated copy of the real `baton_v12` and `tools` -- including a regression
that runs it **without** the binding and asserts it fails at the first product
import having written nothing.

It writes `runtime-profile.json`, `policy.json`, `adapter.json`, `task.json`,
`context-profile.json`, `deployment.json`, `submission.json` and `PACKET.json`,
holds the deployment against `stage_execution.held_configuration` -- the same
validator the serving deployment runs -- and prints the digest of each file it
wrote. It grants nothing, opens no store and starts nothing.

**The run root must not be inside the code boundary.** `held_packet` refuses a
packet whose Job store, control store, deployment state root, context storage
or outcome directory is inside the tree the code lives in, and it refuses before
a store is opened rather than after the owner acts have committed.

## Step 4 — read what was composed

Before running anything:

- **`task.json`'s `instructions`.** Confirm they are the requirement and the
  commit-ownership paragraph, with no stage script and no verdict vocabulary.
  That one string is what W236087's live run got wrong and it is the cheapest
  thing on this page to check.
- **`deployment.json`.** It configures TWO workers. That is the manager's rule,
  not a mistake: `stage_execution` refuses a deployment naming no review
  worker, because a Job that cannot be independently reviewed serves nothing.
  The review worker holds its own participant and principal and is never
  admitted -- the submission declares one stage, the supervisor's gate refuses
  the `review` kind by name, and it also refuses any stage belonging to another
  Job.
- **`PACKET.json`'s `submission.job_id`.** It should read
  `job-single-implementation-239528`. If it reads `job-a`, you are running an
  older composer.

## Step 5 — run it

```sh
PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/baseline.py" \
    --packet "$RUN/PACKET.json" \
    --incarnation single-implementation-239528
```

What it does, in order, stopping at the first refusal:

1. Reads the packet and PROVES every artifact it binds -- fixture bytes,
   deployment configuration, submission, context profile, manager source,
   installed runtime, its own program bytes -- before opening anything.
2. Proves the packages this process really imports resolve inside the bound
   manager source, and asks the engine whether the image is the one named.
   (Exit 2. `test_entrypoints` drives this with a byte-identical *relocated*
   copy of the real source, which every digest verifies and which this process
   does not import: exactly the case the digests alone cannot catch.)
3. Opens the Job store and **surveys it before any owner act**: a Job identity
   already recorded is refused here, with exit 2 and nothing spent. Every other
   Job it holds is printed and carried into the outcome.
4. Opens the control store, performs the four owner acts
   (`configure_workspace_storage`, `configure_context_storage`,
   `certify_context_profile`, `authorize_qualification_run`) and composes the
   deployment under the packet's own code boundary.
5. Submits one Job, verifies the declared per-turn ceiling is the JOB's own,
   and serves with admission bounded at the gate and scoped to this Job.
6. Closes admission, re-reads canonical history, orders the stop for anything
   still executing, sweeps the cleanup window through the CLOSED gate, and
   takes a final canonical read.
7. Writes `outcome.json` and exits `0` only if the outcome is `settled`.

It never retries. A failed turn, a refused act, an exhausted cap or an exceeded
bound ends the run.

`test_entrypoints.TheDocumentedSupervisorRunsThroughMain` drives this entry
point itself -- exit 0 on a settled run, exit 1 on an elapsed bound with the
engine asked to stop, exit 2 on an unimported source and exit 2 on a Job
identity collision -- with only the engine and provider subprocess simulated.

## Step 6 — read the outcome

`settled` requires ALL of:

* one implementation attempt and no other kind;
* one provider context, OPENED at generation 0 and not restored;
* one retained proposal, offered against the declared base, with a head that is
  not that base;
* that proposal's commit **authored and committed by
  `Baton worker <worker@baton.invalid>`, with exactly the declared base as its
  single parent**;
* a positive committed cleanup for every runtime *this Job* started;
* a successful final canonical read, no interruption, no uncertainty, no
  intruder and no gate refusal.

Anything else is `held`, with `held_because` naming each reason.

Read `accounting_scope` and `preexisting_jobs` too. They are not failures --
they are the outcome telling you what it did **not** answer.

**Do not read `held` as a defect in the packet and do not re-run.** If the
provider committed its own history, the outcome will say the proposal could not
be read and the stage went exceptional -- which is the W236087 failure
reproducing on a real provider, and is an ANSWER to the question in
`PROVIDER-QUESTION-239528.md`, not a reason to try again. A second run needs a
new run identity, hence a new Job identity, and a new selection.

## What this run does not establish

It says nothing about review, correction or session resume. It certifies no
production profile, enables nothing and advances no deployment. It accounts for
one Job. One run is one sample: a settled outcome is one provider turn that
followed the contract, not a rate.

## Recovery this document does NOT authorize

* Cleaning up W236087's outstanding runtime.
* Re-running under a spent grant or a recorded Job identity.
* Any write-capable fallback for a read that refused.
* Closing any Work.
