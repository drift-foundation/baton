# Post-install packet for destination 2 — claim357462

The one coupled packet `review-2026-10-23T02-34-20Z.md` required: owner-run
configuration, submission, serving and reading instructions for **this exact
empty instance**, with the missing worker repositories prepared by a supported
human-only step.

**Nothing here was executed against the installation.** The real destination
was not read, written, configured or started by this claim. Everything below is
either (a) a fact from the independent readback `evidence/review-357437/READBACK.json`,
(b) a fact traced from committed source at `30245386`, or (c) a **proposal**.
The current deterministic proof is `prove.py` → `evidence/PROVE.json`, which
executes **no Git at all** and runs entirely in a disposable temporary root.
The superseded `compose.py` and `evidence/COMPOSE.json` are retained beside it;
`GIT-OPERATION-DISCLOSURE.md` records truthfully that the old script executed
`git init`, `add` and `commit`, which an agent may not do, and that its own
wording misdescribed that.

## What is already true, and is not re-litigated here

| Fact | Value |
|---|---|
| Destination | `/home/sl/baton-instances/native-coordination-pilot-w321608-2` |
| Authority | `673355e1f28e4b5683cbef09eb8f2658` |
| Installed bundle | 81 files, digest `3dbc610e0c2a0e1165367871097bd2a5bb590e271fee729b94b436a04045e7ac` |
| Executable | `9cda6dabe328ee800c2eb3cb6997d29dce179c857f9bb2968c33a4adbf043673` |
| Build commit | `302453869d07eb5579e79a6572586d3c3cf62a5c`, clean |
| `repo/target.git` HEAD | `30245386` |
| `repo/workspace` HEAD | `30245386` |
| Configuration | **empty** — no workers, no job bindings |
| Status at readback | manager/publisher/snapshot/jobs absent; runtime unknown, no snapshot |

**That last row is an unstarted empty installation. It is not evidence of the
old instance's cessation**, and nothing in this packet treats it as such.

## Why revision 4 cannot be rerun

- `revision-4/owner_operations.py` refuses before repository preparation when
  the destination exists — and destination 2 exists.
- `revision-4/prepare.py` pins `BASE = 14e52d80…` and
  `SELECTED = …w321608-1`, the old source and the old destination.
- `bootstrap.prepare_repositories` refuses this destination outright.
  **CORRECTED at claim357542**: it refuses at `custody`
  (`bootstrap.py:1880`) on the **existing runtime** — *"there is already a
  runtime at …/distro; nothing here upgrades a deployment in place"* — before
  any repository is considered. It is *also* prepared-once at the
  per-repository level (*"Nothing here replaces one"*), which is what answers
  on a destination with no installed runtime. `prove.py` asserts both and
  labels which shape produces which. Either way the refusal is **clean, before
  any effect**, and the destination is byte-unchanged.

So the gap is narrow and specific: **the two worker source repositories cannot
be added to an existing destination by any supported operation.**

## Step 1 — the missing worker repositories (human-only)

`bootstrap.repository_plan` names four repositories for this document;
`target.git` and `workspace` exist, and these two do not:

    /home/sl/baton-instances/native-coordination-pilot-w321608-2/repo/source-implementation-pilot
    /home/sl/baton-instances/native-coordination-pilot-w321608-2/repo/source-review-pilot

**Proposed, for Slawomir to run.** These are the product's own semantics, not a
new mechanism: `bootstrap._cloning` clones every non-mirror role **from the
target** with `--no-local`, which is an object-by-object copy rather than
hardlinks, and that is what keeps the identities distinct.

    D=/home/sl/baton-instances/native-coordination-pilot-w321608-2
    set -eu

    # REFUSE BEFORE ANY EFFECT, and treat a DANGLING SYMLINK as occupied:
    # `test -e` follows the link and answers false for a broken one, so the
    # name would look free while `git clone` still fails on it. `-L` catches it.
    for role in implementation-pilot review-pilot; do
      P="$D/repo/source-$role"
      if [ -e "$P" ] || [ -L "$P" ]; then
        echo "refuse: $P already exists (or is a dangling link); nothing here replaces one" >&2
        exit 1
      fi
    done
    test -d "$D/repo/target.git" || { echo "refuse: no target.git to clone from" >&2; exit 1; }

    # ONE AT A TIME, NAMING WHAT SURVIVED. If the second clone fails, the first
    # is real repository data that cannot be re-derived, so it is NAMED rather
    # than removed -- the same rule `bootstrap._cloned` applies.
    git clone --no-local "$D/repo/target.git" "$D/repo/source-implementation-pilot" \
      || { echo "refuse: first clone failed; nothing was left behind" >&2; exit 1; }
    git clone --no-local "$D/repo/target.git" "$D/repo/source-review-pilot" \
      || { echo "STOP: source-implementation-pilot WAS created and is still there;" \
                "remove it yourself or keep it, then retry -- this script deletes" \
                "no repository data" >&2; exit 1; }

**Then the product's own proof verifies them**, writing nothing:
`bootstrap.repositories_proved` requires each repository to identify itself,
refuses any two sharing a common directory, refuses borrowed objects via
`objects/info/alternates`, refuses two that are one directory by device and
inode, and requires the target to hold every declared base. All of that is
exercised in `evidence/COMPOSE.json`.

**This is the one capability gap in this packet**, and it is stated as such
rather than papered over: there is no supported command that adds a worker
repository to a prepared destination. The human clone plus the product's own
verification is the smallest honest path; it is not an updater and implements
nothing.

## Step 2 — native registration, and the Work that must be read back

Registration mints the Work, routes and grants on the installed authority.
**The Work id is SELECTED, then validated** — corrected at claim357900, because
the old wording here still called it a readback operand. It is
`673355e1-W1`, chosen by this packet, created by the supported operation at
`bootstrap.py:746`, **collision-checked** by the authority, and additionally
**prefix-checked**: `contracts/manifest.py` refuses a Work reference that does
not carry its authority's own prefix. Those two refusals are the safety
property. It is not an allocation and not a readback; the readback is the
installed configuration.

Routes and grants to register, carried forward unchanged:

| Route | Handler |
|---|---|
| `impl` | `baton.claude-pilot` |
| `rview` | `baton.reviewer-pilot` |
| `owner` | `baton.slaw` |
| `diagnosis` | `baton.diagnostician-pilot` |

| Participant | Capability |
|---|---|
| `baton.verifier-pilot` | `verify` |
| `baton.reviewer-receipt-pilot` | `review` |
| `baton.slaw` | `approve`, `integrate`, `close` |

The Work id is **not** pending: it is the selected `673355e1-W1` above.
`PENDING(the scope and policy generation the registration reports)` — those two
*are* readbacks, available only once the supported operation has created the
Work.

## Step 3 — configuration

Inputs in this packet, to be applied through the supported bootstrap
configuration path against the **existing** installation:

- `configure-inputs.json` — destination 2, authority `673355e1…`, both stage
  workers (`implementation-pilot`, `review-pilot`), each nominating its **own**
  source repository, job `quickstart-b` at base `30245386`.
- `task.json` — the quickstart-only contract, `task_id`
  `w321608-native-operator-quickstart-2`, `declared_base` `30245386`.
- `submission.json` — `sub-w321608-quickstart-2`, job `quickstart-b`, two
  stages with the review depending on the implementation, **3600s
  provider-turn and 900s ordinary verification per invocation**.

Preserved from the accepted install and not re-selected: integration target and
workspace, integration profile and `baton.integrator-pilot`, retention
disposition and policy digest, receipt participants, policy and pool
generations, and the installed identity.

**On the 7320s token lifetime**: that is one attempt's token under the accepted
composed policy. It is **not** a cumulative execution grant and must not be
turned into one.

## Step 3b — the exact configuration command

**Corrected at claim357834.** The earlier version used ambient `python3`;
`configure.py` imports `tools.bootstrap`, `tools.instance` and `baton_v12` from
the reviewed checkout, so it runs with **that build's own prepared
interpreter** rather than whatever `python3` resolves to.

    SRC=/home/sl/baton-builds/w325959-30245386-356981/src/v12/python
    PY=/home/sl/baton-builds/w325959-30245386-356981/venv/bin/python
    PKT=/home/sl/src/baton/work/records/2026/10/finding-v12-native-pilot-instance-packet/post-install-357462
    D=/home/sl/baton-instances/native-coordination-pilot-w321608-2

    # PREFLIGHT ONLY -- writes nothing, and refuses by name on any conflict.
    cd "$SRC" && PYTHONPATH=src:. "$PY" "$PKT/configure.py" \
        --destination "$D" --packet "$PKT"

    # THEN, and only after reading that output:
    cd "$SRC" && PYTHONPATH=src:. "$PY" "$PKT/configure.py" \
        --destination "$D" --packet "$PKT" --owner-selected

`SRC` is the clean reviewed checkout at `30245386` — the one the build came
from — not this working tree, which is dirty against that commit. `PY` is the venv that build prepared; the reviewer supplied its
exact path, so this is **resolved** rather than pending.

The second command writes the task document, makes one
`bootstrap.main(["--inputs", …])` call, reads the installed `deployment.json`
back through `stage_execution.held_configuration`, confirms the installed
selections, and emits four files under `$D/generated/`. It **does not submit**
and **does not start** anything.

## Step 3c — the submission, as its own selection

**Corrected at claim357834** against the installed bundle's own help, which the
reviewer read: the operands are `--store`, `--incarnation` and
`--authority-uuid` on `manager`, then `submit --document`. There is **no**
`--instance` and **no** `--submission`; the earlier spelling here was invalid.

    C=/home/sl/baton-instances/native-coordination-pilot-w321608-2/distro/baton-v12-stack
    D=/home/sl/baton-instances/native-coordination-pilot-w321608-2

    "$C" manager \
        --store "$D/db/jobs.sqlite3" \
        --incarnation w325959-owner-submit-2 \
        --authority-uuid 673355e1f28e4b5683cbef09eb8f2658 \
        submit --document "$D/generated/submission.json"

The store path is the layout's own `job_store`. **Admitting a Job is a separate
decision from configuring the deployment**, which is why this is its own step.

## Step 4 — the owner-run lifecycle commands

Served by the installed command (`tools/stack_command.py`), driven through the
instance selector. These are the shapes to run; none was run here.

    C=/home/sl/baton-instances/native-coordination-pilot-w321608-2/distro/baton-v12-stack
    I=/home/sl/baton-instances/native-coordination-pilot-w321608-2/instance.json

    "$C" identity                         # what this build IS
    "$C" status    --instance "$I"        # process health, snapshot, jobs, runtime boundary
    "$C" start     --instance "$I"        # SEPARATE live-serving selection
    "$C" monitor   --instance "$I" --interval 5   # read-only
    "$C" repository --instance "$I"       # read-only
    "$C" stop      --instance "$I"        # only this deployment's processes; stores retained

Reading a failed attempt — the diagnostics surface this campaign added.
**CORRECTED at claim357542**: an earlier revision of this file wrote
`view --instance "$I"`, which does not exist. `stack_command.py:85` forwards
`view` straight to `job_viewer.main`, whose parser at `job_viewer.py:862`
**requires `--status` and has no `--instance`**. The concrete locator is the
publisher's own snapshot: `stack.py:135 snapshot_path(root)` is
`<root>/status.json`, and `stack.py:1417` sets `root = document["state"]` when
driven with `--instance`. So:

    S=/home/sl/baton-instances/native-coordination-pilot-w321608-2/state/status.json

    "$C" view --status "$S"                    # read-only; needs a PUBLISHED snapshot
    "$C" view --status "$S" --job quickstart-b # one Job in detail
    "$C" attempt-diagnostics "$S"              # the actionable cause report

**Both read the published snapshot, so both need the publisher to have written
one.** At the readback the snapshot was absent, which is why `status` reported
`snapshot absent` — these two commands have nothing to read until serving has
published at least once.

`attempt-diagnostics` is a pure projection over one `baton.v12.job-status/7`
document and opens no store. **It exists in this bundle** because this bundle
was built from `30245386`; the old instance 1 bundle predates it.

What `status` can answer, and what it cannot, is recorded in
`OPERATIONAL-PROPOSAL-356877.md` Part B and is unchanged: no store schema
versions, no token guard state, no per-attempt cessation facts.

## Separated selections

Each needs its own owner decision; none is taken here.

1. **Worker repository preparation** — step 1, human-only clones plus the
   product's verification.
2. **Registration and configuration** — steps 2 and 3, after which the Work id
   becomes a resolved fact rather than a readback marker.
3. **Submission** — step 3's `submission.json`, refusing identifier collisions
   rather than reusing `quickstart-a` or `sub-w321608-quickstart-1`.
4. **Serving and live execution** — `start`, and any live provider use. **A
   live-provider question would be**: does this exact installed native
   two-stage path produce a useful independently reviewed candidate with real
   provider protocol and authentication and the owner receipt flow?
   Deterministic composition cannot answer that. **No live execution is
   selected here.**

## Resolved versus future readback operands

**Resolved**: destination, authority, bundle digest and executable, build
commit, target and workspace HEADs, both worker source paths, task and
submission identifiers, per-invocation limits, routes, grants, actors.

**Future readback, honestly named**: the Work id, scope and policy generation
from registration; the composed input manifest and its public `input_digest`;
every post-configuration store fact; every runtime and status observation after
`start`; and all receipts. **No value is stated for any of these.**

## Old instance 1

Authority `1cdb8d19`, Work `1cdb8d19-W1`, Job `quickstart-a`: **unresolved and
untouched.** No updater, no recovery, no resubmission, no backlog migration.
This packet does not recover that Job and does not claim to.

## Status of this packet — the configuration is applied and read back

`configure.py` was **rewritten at claim357725** to the shape the review
required, and all four earlier findings are answered:

**It applies the configuration.** The supported in-place operation is
`bootstrap.main(["--inputs", document])` with **no** `--destination` — the
`v12/justfile` calls it *"the older form and still works"* — and `prepare`
reuses this root's existing Authority. The driver makes **one** such call and
then **reads the installed `deployment.json` back** through
`tools.stage_execution.held_configuration`, the real runtime consumer. The
proof confirms the installed deployment composes **both stage workers** and
binds the Job.

**It registers nothing itself.** The supported operation already does
(`bootstrap.py:731` routes, `:746` `create_work`, `:758`/`:760`/`:771` grants),
so the duplicate was **deleted** — which removes the write-before-check defect
at its source rather than reordering around it.

**The manifest is cross-bound, not merely sealed.** Ten members are replaced
from the accepted documents before the seal: three recomputed
(`retention_policy_digest`, `policy_digest`, `runtime_profile_digest`) and the
seven accountability digests. The proof asserts the inherited `3a532add` policy
and the `cccc…` retention **placeholder** are both gone, every accountability
digest is replaced, and **worker and manifest agree** on policy and retention.
One finding came out of doing it: `adapter_digest` is a **worker** member, not a
manifest one, and adding it is refused by the frozen schema's
`unevaluatedProperties`.

**Preflight precedes every write**, in cost order: reviewed packet hashes,
selector validity and the product's own bundle check, authority identity,
selected authority and runtime digest, **exact** layout equality for
`state_root` and containment under `repo/` for the integration paths, the
selected base on every job, task-document conflict, emitted-output conflict,
the selected Work not already existing, then repository presence and the
product's independence proof. The first write happens only after all of it.

### The Work identity, stated accurately

`jobs[0].work_id` is **`673355e1-W1`, selected by this packet**, created by the
supported operation at `bootstrap.py:746`, and **collision-checked by the
authority** — that refusal is the safety property. It is **not** an authority
allocation and is not described as a readback. What is read back is the
installed configuration. Preflight refuses a marker in that field, because the
supported operation needs a real identifier to create; the "selected" semantics
live here in prose, since the product **refuses unknown members** in the input
document (*"a selection this helper cannot carry is refused rather than
accepted and dropped"*).

### Proof — 97 checks, zero failures, no Git executed

`prove.py` **imports `configure.compose`**, so the proved path is the owner
path. Two refusal orderings are both demonstrated: a second apply trips the
**emitted-output** check first, *before the authority is opened*; with the
outputs moved aside, the **already-created Work** is what refuses. Both leave
the installation **byte-unchanged** by `tree_digest`, so a partial repeat
strands nothing. An absent-repository installation and a pre-existing output
each refuse with **no deployment document written**.

Still owner-selected and not taken: the human worker-repository preparation of
step 1, `configure.py --owner-selected`, the submission, and serving.

## A correction to this packet's own earlier finding

The earlier revision said `prepare_repositories` refuses at the
per-repository existence check. **Against a real installed destination it
refuses earlier**, at `custody` (`bootstrap.py:1880`), on the existing runtime:
*"there is already a runtime at …/distro; nothing here upgrades a deployment in
place."* The earlier disposable shape had no `distro`, which is why it reached
the later check and why the earlier claim named the wrong site. `prove.py`
asserts **both** refusals and labels which shape produces which. The gap itself
is unchanged: no supported operation adds a worker source repository to a
prepared destination.

## Limits of the evidence behind this packet

**The current proof** is `prove.py` → `evidence/PROVE.json`: 27 checks, zero
failures, **no Git executed at all** — the repository boundary is simulated
through the product's own injected runner seam and every such answer is
labelled. It drives a real disposable Authority, Work, routes, grants, dossier
and submission resolution. It is **not** evidence about the production
destination, not a live run, and not an engine, provider or model proof. No
production authority was opened and no production store was read.

**The superseded run**, `evidence/COMPOSE.json` (24 checks): retained unchanged
as history. **CORRECTED — an earlier version of this section claimed "no
version-control history was mutated", and that was false.** `compose.py`
executed `git init`, `git add` and `git commit` in its temporary root, which an
agent may not do. `GIT-OPERATION-DISCLOSURE.md` records it with line numbers.
Nothing in `/home/sl/src/baton` was ever staged, committed or rewritten, but
that is a narrower statement than the one this section used to make, and the
difference is exactly what made the old wording inaccurate.
