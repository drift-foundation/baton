# Operator sequence, corrected -- managed-correction W236087, claim 311743

SUPERSEDES `OPERATOR-311606.md`, which could not have run. Owner reroute 311736
reported the first cause; running the real `tools.bootstrap` from a real staged
tree in a disposable installation found the second and third. All three are
corrected here, and the corrected path was then driven end to end -- `stage`,
`tools.bootstrap`, `prepare-work`, `bind`, `check` -- with no Docker, no
provider and nothing deployed touched. A FOURTH defect -- **D** below -- was
then found by the owner running the sequence live, and is corrected here too;
the disposable proof now runs the real `baseline.prepare` as well, with nothing
pre-created by a fixture. The evidence is
`STAGE-BOOTSTRAP-EVIDENCE-312166.json`, and
`STAGE-BOOTSTRAP-EVIDENCE-311743.json` is the earlier record.

## 0. What was wrong, and what proves it is not wrong now

**A. The staged source carried no frozen resources.** `_source_files` copied
only `.py`, and `baton_v12/contracts/schema/worker-control-1.0.schema.json` and
`agent-session-1.0.schema.json` are read AT IMPORT TIME by
`baton_v12.contracts.frozen` (`WORKER_CONTROL_BYTES` and `AGENT_SESSION_BYTES`
are module-level constants). So step 1 raised `FileNotFoundError` on the schema
file, and steps 2-4 then failed for want of the `bootstrap.json` and
`packet.json` step 1 never wrote. The owner's partial staging holds 376 `.py`
files and ZERO resources; the corrected staging holds 108 files including both
assets, and `stage` now ASKS THE STAGED TREE to import itself before it
returns.

**B. The staging root was a sibling of the instance.**
`tools.stage_execution._checkout()` answers three parents above its own file,
so a source staged at `<staging_root>/manager-source` makes
`dirname(staging_root)` the tree the staged code calls its checkout -- and
`bootstrap.admit` refuses any destination inside it, because an installed
instance exists so that development in the code's own tree cannot change a
running Job. The superseded selection put the staged source at
`/home/sl/baton-instances/managed-correction-309356-source` and the instance at
`/home/sl/baton-instances/managed-correction-309356`: siblings, so step 1 could
not have succeeded whatever the assets did. The asset failure came first, which
is the only reason this went unseen. The corrected selection stages to
`/home/sl/baton-staging/managed-correction-309356-source`.

**C. `stage` was not in the sequence, and ran with no import path.**
`RUN-COMMANDS-311606.json` began at step 1, so the one command whose defect
stopped the run was the one command the machine-readable sequence did not
carry. It is step 0 now, and its `PYTHONPATH` is the ORIGIN -- because the
staged tree is what step 0 creates.

**D. Nothing created the two filesystem roots the run configures first.**
Found by the owner RUNNING this sequence: steps 0-4 all succeeded and the
supervisor then failed inside `baseline.prepare` at
`configure_workspace_storage`, because `$ROOT/run/workspaces` did not exist.
That call is the deployment's act and creates nothing; `tools.bootstrap` creates
`stores`, `repository`, `logs`, `state`, the state root and the destination --
not these -- and the accepted CONNECTED FIXTURE creates them itself, which is
exactly why no deterministic case had ever noticed. **Step 3 (`bind`) now
establishes them** with the modes the product's own rules require, records them
in the packet, and **step 4 (`check`) proves them** with the product's own
checkers, so their absence is refused before a store opens rather than after two
are open. The two roots, and nothing else, because the rest are created by the
product when it uses them (`launch.materialize` and the credential delivery each
`makedirs` their own home, and per-attempt workspace roots are established by
`workspaces.adopt_workspace_group`):

ESTABLISHED WITHOUT FOLLOWING A LINK, which review 312285 required after
measuring the cost of the first version: that one used `os.makedirs`, `os.chmod`
and `os.chown` BY NAME -- all three follow a symlink -- so a root pointed at an
unrelated directory had that directory's mode changed before validation refused.
Every component is now opened with `O_NOFOLLOW | O_DIRECTORY` from `/`, a link
or a non-directory at any component refuses before anything is created, and the
mode and group are set with `fchmod`/`fchown` on the pinned descriptor.

| root | mode | the rule that requires it |
| --- | --- | --- |
| `$ROOT/run/workspaces` | `0o2770`, group `1000` | `workspaces.configure_workspace_storage` -> `check_workspace_storage`: a real directory (asked with `lstat`, so a link is refused) owned by the manager's uid. The mode is the one `adopt_workspace_group` establishes on the roots the manager creates INSIDE it, so the store is exactly as reachable as its contents and no more. |
| `$ROOT/run/private-contexts` | `0o700` | `context_delivery.configure_context_storage` -> `_open_absolute` and `_private`: a canonical path whose whole ancestry opens, owned by the running uid, readable and writable by the owner, with NO group or other bit set at all. |

## 1. HISTORICAL -- the FIRST failed staging, as it was on 2026-09-29 (claim 311743)

THIS SECTION IS A RECORD, NOT THE CURRENT STATE, and review 312285 asked for it
to say so plainly. It describes what the FIRST failure (the `.py`-only staging,
defect A) left behind, measured read-only at the time. **The instance listed as
ABSENT below EXISTS NOW**: the owner's later run installed it, which is what
defect D was found in. For the state to act on, read section 1b.

The inventory is preserved rather than rewritten, because it is the evidence
that the first failure left those paths untouched. Nothing below was deleted,
moved or written to, and the paths this sequence uses are NEW:

| what | where | state |
| --- | --- | --- |
| staged source (partial) | `/home/sl/baton-instances/managed-correction-309356-source` | 376 `.py`, 0 resources, 17,764,973 bytes. LEFT AS IS. |
| packet documents (partial) | `/home/sl/baton-instances/managed-correction-309356-packet` | `bootstrap-inputs.json`, `context-profile.json`, `task.json`, `prepared.json` (`file_count: 376`, no `frozen_assets`). LEFT AS IS. |
| instance | `/home/sl/baton-instances/managed-correction-309356` | ABSENT. The bootstrap never got far enough to create it. |
| `bootstrap.json`, `packet.json` | anywhere | ABSENT, which is why steps 2-4 failed. |

No manual file copying is asked for anywhere in this document, and nothing
deployed is deleted. The recovery is a re-run into fresh paths.

## 1b. HISTORICAL -- the recovery that ran, and what it produced

The recovery in this section RAN, on 2026-09-30 at 09:05Z, and the run finished
naturally: outcome `failed-or-unknown`, state `held`, implementation
`exceptional`, review `blocked`. It is kept here as the record of what was
done; the state to act on now is section 1c.

`DIAGNOSIS-314263.json` is the measurement, taken read-only from the retained
evidence. Where the 244 seconds went:

| phase | seconds | what it was |
| --- | --- | --- |
| provider startup | 6.5 | container to first session entry, of which **3.0 was the CLI waiting for stdin the adapter never sends** |
| task execution | **172.4** | 216 session entries, 73 assistant turns, **47 shell commands** -- all reads, none repeated, no error loop |
| manager overhead | 5.5 | admission, launch, cancellation, 59 cleanup sweeps |
| publication and cleanup | 60.1 | after serving, inside the reserve |

The prompt ARRIVED and the worker worked the whole time. It read the repository
continuously for 172 of its 180 seconds -- `grep` 14, `sed` 13, `ls` 6, `cat` 4
-- and **never created the file**. The runtime was destroyed, the allocation
released, and the retained conversation (715,884 bytes) is on disk; the context
use reads `held` with reason `invocation-unknown`, because the provider was
stopped before it could declare a result.

SO THE DEFECT WAS IN THE CONTRACT, NOT THE CLOCK. The task document told the
worker what to write and what would be accepted, and never told it that the turn
was bounded. An agent that does not know it is on a clock reads until the clock
ends.

## 1c. CURRENT -- the next experiment, with ONE variable changed

`NEXT-EXPERIMENT-314263-SECOND.json`. The corrected task document states the
180-second bound, cites that the first run spent 172 of those seconds reading
and wrote nothing, and **orders the first action**: write the file immediately,
before reading anything, as a skeleton with one section per numbered requirement
and, under each, what still needs confirming. Then read and rewrite each section.

IT IS AN ORDER ABOUT THE FIRST ACTION RATHER THAN ADVICE ABOUT PACE, and that is
measured rather than preferred. A second session, under a contract that stated
the bound and asked for a file "within the first quarter", still spent its first
51.6 seconds on 15 more reads and had written nothing
(`INTERRUPTED-RUN-314263.json`). Telling an agent it is on a clock did not change
what it did first; telling it what to do first is testable.

**THE CAP IS NOT RAISED.** What would justify raising it is a session that wrote
the file early and was still improving it when the cap stopped it. Neither
measured session was that.

A NOTE ON WHY THIS RUN IDENTITY IS THE SECOND ONE. I started a run at
`managed-correction-314263` BY MISTAKE while syntax-checking this document -- I
extracted its shell blocks and ran them directly instead of under the stub
harness that exists for that -- and stopped it with one SIGINT, which cancelled
and fenced the attempt and published its outcome. That Job identity is spent, so
this experiment uses a fresh one. `INTERRUPTED-RUN-314263.json` records exactly
what happened, what now exists and what it measured. The spent
`managed-correction-309356` run is untouched.

    set -e
    set -o pipefail

    export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
    export SEL=$DOSSIER/SELECTIONS-RESOLVED-314263-SECOND.json
    export DEST=/home/sl/baton-instances/managed-correction-314263-second-packet
    export ROOT=/home/sl/baton-instances/managed-correction-314263-second
    export STAGED=/home/sl/baton-staging/managed-correction-314263-second-source/manager-source
    export ORIGIN=/home/sl/src/baton/v12/python
    export IMPORT=$STAGED/src:$STAGED
    export PYTHONDONTWRITEBYTECODE=1

    # 0. STAGE: the documents, the modules and the frozen resources.
    PYTHONPATH=$ORIGIN/src:$ORIGIN python3 $DOSSIER/correction_packet.py stage \
        --selections $SEL --destination $DEST --claim 314263 \
        --provenance $DOSSIER/PROVENANCE-309356.json

    # 1. INSTALL the fresh instance. Installs; starts nothing.
    PYTHONPATH=$IMPORT python3 -m tools.bootstrap \
        --inputs $DEST/bootstrap-inputs.json --destination $ROOT \
        --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro \
        --no-repositories

    # 2. THE AUTHORITY ACTS for this run's Work.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py prepare-work \
        --selections $SEL --destination $DEST

    # 3. BIND, which also establishes the two filesystem roots.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py bind \
        --selections $SEL --destination $DEST --claim 314263 \
        --provenance $DOSSIER/PROVENANCE-309356.json

    # 4. PROVE the packet, the staged bytes and the roots.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py check \
        --packet $DEST/packet.json

    # 5. RUN.
    BATON_V12_STAGE_EXECUTION_CONFIG=$DEST/deployment.json PYTHONPATH=$IMPORT \
        python3 $DOSSIER/correction_supervisor.py --packet $DEST/packet.json

WHAT TO READ AFTERWARDS, AND WHAT EACH ANSWER MEANS. If the file exists early,
the diagnosis was right and the experiment has done its job whatever the verdict.
If it still does not exist, the contract is not the binding constraint -- measure
that session the same way (`DIAGNOSIS-314263.json` is the template: the retained
transcript under the private-context store, the provider logs, the outcome
document) and do not raise the cap on that evidence either.

## 1d. The recovery sequence as it was delivered (kept for reference)

THIS IS THE STATE TO ACT ON. The owner's run installed the instance at `$ROOT`
and got as far as the supervisor -- so, unlike the inventory in section 1,
`$ROOT` exists, its stores exist, and the previous destination holds a complete
bound packet. The installation is RE-USABLE: the two registrations
`baseline.prepare` makes are the only durable acts the failed run could have
left, and the product's own readers say neither committed --
`workspaces.configured_workspace_storage` and
`context_delivery.configured_context_storage` both refuse, and
`baseline.survey` reports no pre-existing Job (`REPLAY-SAFETY-312166.json`,
taken against COPIES of the three stores so nothing deployed was written).

### Why the previous recovery proposal failed at its first command

It began at `bind`, and `bind` refused: *the preparation module
`correction_packet.py` has CHANGED since `stage` reviewed it; `bind` refuses
drift rather than re-signing it.* (Quoted as prose, not as a command block: an
indented line in this document is a command an operator would run, and the argv
harness refuses one that is not.)

THAT REFUSAL IS CORRECT AND MUST NOT BE BYPASSED. The retained manifest in the
previous destination binds the helper digest `stage` measured under claim
311743; the helper has been corrected three times since (311994, 312166,
312305). A `bind` that re-signed it would bind a packet to code nobody reviewed
together. What the proposal omitted was the step that makes the transition
legitimate: **`stage` is the only thing that records digests, and it records
what it measures.** So the recovery starts at step 0, into a FRESH destination.

Measured read-only: the staged product tree has NOT moved -- 0 of its 108 files
differ -- and the supervisor and the descriptor supplier still match. The only
drift is the helper module.

### The recovery, five steps

    set -e
    set -o pipefail

    export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
    export SEL=$DOSSIER/SELECTIONS-RESOLVED-311743.json
    export DEST=/home/sl/baton-instances/managed-correction-309356-packet-312411
    export ROOT=/home/sl/baton-instances/managed-correction-309356
    export STAGED=/home/sl/baton-staging/managed-correction-309356-source/manager-source
    export ORIGIN=/home/sl/src/baton/v12/python
    export IMPORT=$STAGED/src:$STAGED
    export PYTHONDONTWRITEBYTECODE=1

    # 0. STAGE into a FRESH destination. This is the transition: it re-records
    #    the manifest with the corrected helper's digest, re-affirms the staged
    #    tree byte for byte, and touches nothing in the instance. The previous
    #    destination is left exactly as it is.
    PYTHONPATH=$ORIGIN/src:$ORIGIN python3 $DOSSIER/correction_packet.py stage \
        --selections $SEL --destination $DEST --claim 312411 \
        --provenance $DOSSIER/PROVENANCE-309356.json

    # 2. THE AUTHORITY ACTS, which REPLAY: journalled under an identity derived
    #    from their operands, so repeating them over the existing Authority
    #    finishes the preparation rather than composing a second one.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py prepare-work \
        --selections $SEL --destination $DEST

    # 3. BIND. This also establishes the two filesystem roots of defect D, with
    #    the modes the product's rules require, without following a link.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py bind \
        --selections $SEL --destination $DEST --claim 312411 \
        --provenance $DOSSIER/PROVENANCE-309356.json

    # 4. PROVE the packet, the staged bytes and the roots.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py check \
        --packet $DEST/packet.json

    # 5. RUN.
    BATON_V12_STAGE_EXECUTION_CONFIG=$DEST/deployment.json PYTHONPATH=$IMPORT \
        python3 $DOSSIER/correction_supervisor.py --packet $DEST/packet.json

STEP 1 IS NOT IN THIS LIST. The instance exists; `tools.bootstrap` is not
re-run, and nothing here repairs, cleans or deletes anything. No `mkdir`,
`chmod`, `chown`, `rm` or `cp` appears in any step, and no manifest is edited: a
directory made by hand is a directory nobody proved, and a digest written by
hand is a signature over code nobody reviewed.

`RECOVERY-312411.json` carries these five steps as argument vectors equal to
what the generator emits, and `RECOVERY-TRANSITION-312411.json` is the proof:
in one disposable root, an installation built through `check` exactly as the
owner's was, its retained manifest set to THE REAL HISTORICAL helper digest read
from the deployed document, `bind` refusing it with exit 2, and then these steps
all exiting 0 -- after which the old destination's ten documents, the instance
record and all 108 staged files are byte-identical, and `baseline.prepare` runs
over the recovered packet with both registrations read back.

### One thing this recovery must never become

Once `baseline.prepare` has COMMITTED, the workspace root's device and inode are
pinned inside the context-storage signature -- `configure_context_storage` adds
that root to its own excluded set -- so a workspace directory that is deleted
and re-made is a DIFFERENT root to the journal, and a second `prepare` is
refused with "already recorded with a different kind or signature". That is
correct, and it means **deleting or re-making `$ROOT/run/workspaces` or
`$ROOT/run/private-contexts` on an installation whose `prepare` has committed is
a fresh instance, not a repair.** It does not affect this recovery: nothing has
registered yet, so those roots have never been pinned, and `bind` creates them
once and never removes them.

## 2. Setup, which STOPS AT THE FIRST ERROR

`set -e` and `set -o pipefail` are the point: the failed run continued past a
broken step 1 into three more failures, which is how one cause produced four
reports. With these, the sequence stops where it breaks.

    set -e
    set -o pipefail

    export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
    export SEL=$DOSSIER/SELECTIONS-RESOLVED-311743.json
    export DEST=/home/sl/baton-instances/managed-correction-309356-packet-311743
    export ROOT=/home/sl/baton-instances/managed-correction-309356
    export STAGED=/home/sl/baton-staging/managed-correction-309356-source/manager-source
    export ORIGIN=/home/sl/src/baton/v12/python
    export IMPORT=$STAGED/src:$STAGED
    export PYTHONDONTWRITEBYTECODE=1

    # 0. STAGE: write the input documents and COPY the modules AND the frozen
    #    resources this run will import, measuring every one. Refuses before it
    #    writes; refuses a staged tree that does not import; refuses a staging
    #    root whose parent holds the instance. Imports the ORIGIN, because the
    #    staged tree is what this step creates.
    PYTHONPATH=$ORIGIN/src:$ORIGIN python3 $DOSSIER/correction_packet.py stage \
        --selections $SEL --destination $DEST --claim 311743 \
        --provenance $DOSSIER/PROVENANCE-309356.json

    # 1. INSTALL the instance from the accepted runtime. Installs; starts nothing.
    PYTHONPATH=$IMPORT python3 -m tools.bootstrap \
        --inputs $DEST/bootstrap-inputs.json --destination $ROOT \
        --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro \
        --no-repositories

    # 2. THE AUTHORITY ACTS. Creates the Work under the assignment contract,
    #    registers impl/rview/integration handlers, grants the four receipt
    #    capabilities in the Work's own scope, sets the canonical target.
    #    Submits NO Job. Journalled under an identity derived from its operands,
    #    so repeating it finishes an interrupted preparation and a CHANGED one is
    #    refused before anything is granted.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py prepare-work \
        --selections $SEL --destination $DEST

    # 3. BIND the packet to what the instance actually holds. Asks the staged
    #    tree to import itself again, and refuses an instance inside its
    #    checkout, because both are conditions the RUN needs.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py bind \
        --selections $SEL --destination $DEST --claim 311743 \
        --provenance $DOSSIER/PROVENANCE-309356.json

    # 4. PROVE it against the tree, with the real product validators.
    #    Opens no store; refuses on any drift.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py check \
        --packet $DEST/packet.json

`RUN-COMMANDS-311743.json` carries steps 0-5 and 7 as argument vectors with
their environments, EQUAL member-for-member to what the generator emits for this
selection, and lists step 6 as pending because it needs the identity the
bootstrap has not minted yet. Every delivered argv element is a literal: no
placeholder and no shell expression.

## 3. Run

    set -e
    BATON_V12_STAGE_EXECUTION_CONFIG=$DEST/deployment.json PYTHONPATH=$IMPORT \
        python3 $DOSSIER/correction_supervisor.py --packet $DEST/packet.json

The supervisor holds the bounds: 900 seconds total with a 60-second reserve
inside it, 180 per provider turn, 180 per verification command, two
implementation invocations and two review invocations, and five stop conditions.

## 4. Status, from another terminal

    set -e
    PYTHONPATH=$IMPORT python3 -m tools.job_manager \
        --store $ROOT/db/jobs.sqlite3 \
        --authority-uuid $(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['authority_uuid'])" $ROOT/bootstrap.json) \
        --incarnation managed-correction-309356 \
        status --control $ROOT/db/control.sqlite3

READ-ONLY: it opens the stores for reading and admits nothing. It reports every
Job in the store; this run's is `job-managed-correction-309356`.

THIS SHAPE IS THE GENERATED ONE, AND THE PREVIOUS REVISION OF THIS DOCUMENT GOT
IT WRONG. Review 311971 R1: it read `--job-store` and `status --job` and omitted
the required `--incarnation` and the intended `--control`, and
`tools.job_manager` refuses that with **exit 2 at the parser**, before a store
is opened -- so the one command an operator would reach for while a run was
serving could not have run. The command above is `commands()` step 6 argv for
argv, and it is held to the REAL parser by a case in
`test_correction_packet.py` and recorded in
`STATUS-PARSER-EVIDENCE-311994.json`: the regressed shape exits 2, and this one
runs to completion against disposable empty stores and answers a status
document.

THE IDENTITY IS NOT IN THE DELIVERED COMMAND LIST. `tools.bootstrap` mints it at
step 1, so `RUN-COMMANDS-311743.json` lists step 6 as PENDING with the read-only
resolver above rather than writing a placeholder -- a placeholder in an argv
element would be passed to the manager verbatim. After step 3, `bind` writes the
COMPLETE eight-step list with the real identity in it:

    python3 -c "import json,sys;print(json.dumps(json.load(open(sys.argv[1]))['commands'], indent=2))" \
        $DEST/commands.json

The `$(...)` substitution above is for a HUMAN typing into a shell, which
expands it; the argument-vector form in `commands.json` carries the literal
value instead.

## 5. Stop, which is an ACTION and not a read

**ONE Ctrl-C in the serving terminal (SIGINT).** That is the stop: not a
command to run, a signal to send to the run that is already serving. It is
written as prose rather than in a command block because there is nothing to
type.

Review 311971 R2: the previous revision of this section contained NO STOP
ACTION. It printed a document, from the wrong path, and called that stopping.

The supervisor defers the signal, closes admission, asks the composition to stop
what is still executing, runs the cleanup window inside the reserve, publishes
the outcome ATOMICALLY, and only then re-raises -- exiting 130. So a stopped run
still leaves its result at `$ROOT/run/outcome.json`, and the run reports itself
INTERRUPTED rather than settled. A second Ctrl-C during cleanup ends the window
and is reported; it does not escape with the accounting half done. `SIGKILL`
cannot be caught and nothing here pretends otherwise.

READING THE RESULT IS A SEPARATE ACT, and the path is the bound one -- the
instance's run directory, which is what the packet binds and what generated step
7 reads. `$DEST` holds the packet's own documents and never holds an outcome:

    set -e
    python3 -c "import json,sys;print(json.dumps(json.load(open(sys.argv[1])), indent=2, sort_keys=True))" \
        $ROOT/run/outcome.json

## 6. What was PROVED in a disposable installation, and what was not

PROVED, by `staged_bootstrap_trace.py` into one temporary root that was then
removed (`STAGE-BOOTSTRAP-EVIDENCE-311743.json`):

- the real `stage` over the real reviewed selection, with only the instance,
staging, store, context and workspace paths redirected -- 108 files staged, both
frozen assets among them, every one measured;
- the DEFECT reproduced by subtraction on a copy of that same staged tree:
`FileNotFoundError` naming `worker-control-1.0.schema.json`, raised from
`baton_v12/contracts/frozen.py` at import;
- the corrected tree importing `tools.bootstrap` and
`baton_v12.contracts.frozen` with the staged tree as its ONLY import path, the
loaded bytes equal to the staged bytes (51419 and 48212);
- `tools.bootstrap` run FROM that staged tree: exit 0, Authority minted,
`deployment.json` and `bootstrap.json` written, stores created;
- `prepare-work`, `bind` and `check` -- the three steps that failed for want of
what bootstrap never wrote -- all exit 0, and the bound packet proved by `check`
with the product's own validators.

NOT PROVED, and not claimed: the deployed instance itself (this sequence has not
been run against `/home/sl/baton-instances`), the live run and its four endings,
the credential reference's currency, production comparison, and any actual live
restore. The bounds and the endings remain as `PACKET-309356.md` states them.
