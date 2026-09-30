# Operator sequence -- the managed context-reuse experiment, claim 316689

PREPARED ONLY. Nothing in this document has been executed: no live run, no
deployed cleanup, no credential change, no engine act, no version-control act.
`EXPERIMENT-316689.json` carries the same steps as argument vectors with their
environments, and every operand's provenance.

## 0. What the owner selected, and what this does not touch

RETENTION. The two retained runtimes and every earlier run's evidence stay
exactly as they are, and every path below is NEW:

| retained | what |
| --- | --- |
| `managed-correction-314263-second` | review attempt `attempt-fc0b0a1a…`, runtime `1c3943d1fa0f`, cleanup never committed |
| `managed-correction-314263` | implementation attempt `attempt-76c61bb4…`, runtime `b93155adbe76`, cleanup never committed |
| `managed-correction-309356` | distinct; no outstanding runtime |

RETENTION PROVES NEITHER CLEANUP NOR DEPLOYED REVOCATION. Those resources stay
in an OUTSTANDING state with a real storage cost -- instances, workspaces,
retained conversations and stopped containers all still on disk -- and the
missing bounded disposition entry stays recorded as a gap. This is a deliberate
choice to keep evidence, not a settlement.

## 1. What this experiment tests, and the limit first

It tests whether a review that ANSWERS opens the correction round, so the
producer's retained conversation is restored into a fresh worker. That is what
this Work exists for and NO run has reached it: the first produced no
deliverable, and the second produced a completed implementation and a reviewer
that timed out `unable`, so there was no verdict to correct against.

THE LIMIT, STATED FIRST: the review stage timed out at 180 seconds with no
transcript to read, and that cause is still UNKNOWN. A reviewer that cannot
answer means no correction round, so THIS EXPERIMENT MAY FAIL THE SAME WAY. The
caps are unchanged and no correction verdict is forced. If it fails the same
way, the honest next step is making the reviewer's turn observable -- not
raising a cap.

What is different from the last attempt: the task contract orders the first
action for a fresh implementation and PRESERVES an existing document on a
resumed correction; the ending no longer asks for a preparation over sealed
material; and the supervisor stops on a repeated refusal, reports unresolved
cleanup by identity, and its interruption report no longer crashes.

## 2. Preparation, which STOPS AT THE FIRST ERROR

    set -e
    set -o pipefail

    export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
    export SEL=$DOSSIER/SELECTIONS-RESOLVED-316689.json
    export DEST=/home/sl/baton-instances/managed-correction-316689-packet
    export ROOT=/home/sl/baton-instances/managed-correction-316689
    export STAGED=/home/sl/baton-staging/managed-correction-316689-source/manager-source
    export ORIGIN=/home/sl/src/baton/v12/python
    export IMPORT=$STAGED/src:$STAGED
    export PYTHONDONTWRITEBYTECODE=1

    # 0. STAGE: the input documents, the modules AND the frozen resources,
    #    every one measured. Imports the ORIGIN, because the staged tree is
    #    what this step creates.
    PYTHONPATH=$ORIGIN/src:$ORIGIN python3 $DOSSIER/correction_packet.py stage \
        --selections $SEL --destination $DEST --claim 316689 \
        --provenance $DOSSIER/PROVENANCE-309356.json

    # 1. INSTALL the fresh instance. Installs; starts nothing.
    PYTHONPATH=$IMPORT python3 -m tools.bootstrap \
        --inputs $DEST/bootstrap-inputs.json --destination $ROOT \
        --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro \
        --no-repositories

    # 2. THE AUTHORITY ACTS for this run's Work. Submits no Job; journalled
    #    under an identity derived from its operands, so a repeat replays.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py prepare-work \
        --selections $SEL --destination $DEST

    # 3. BIND the packet to what the instance holds, and establish the two
    #    filesystem roots without following a link.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py bind \
        --selections $SEL --destination $DEST --claim 316689 \
        --provenance $DOSSIER/PROVENANCE-309356.json

    # 4. PROVE the packet, the staged bytes and the roots. Opens no store.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py check \
        --packet $DEST/packet.json

## 3. Execution

    set -e
    BATON_V12_STAGE_EXECUTION_CONFIG=$DEST/deployment.json PYTHONPATH=$IMPORT \
        python3 $DOSSIER/correction_supervisor.py --packet $DEST/packet.json

The caps are the packet's own and unchanged: 900 seconds total with a 60-second
reserve inside it, 180 per provider turn, 180 per verification command, two
implementation invocations and two review invocations.

## 4. Status, from another terminal

    set -e
    PYTHONPATH=$IMPORT python3 -m tools.job_manager \
        --store $ROOT/db/jobs.sqlite3 \
        --authority-uuid $(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['authority_uuid'])" $ROOT/bootstrap.json) \
        --incarnation managed-correction-316689 \
        status --control $ROOT/db/control.sqlite3

READ-ONLY: it opens the stores for reading and admits nothing. This run's Job is
`job-managed-correction-316689`. The identity is not in the delivered argument
vectors because `tools.bootstrap` mints it at step 1; `bind` writes the complete
status command into `$DEST/commands.json` once it has read the real value.

## 5. Stop, which is an ACTION and not a read

**ONE Ctrl-C in the serving terminal (SIGINT).** That is the stop: a signal to
the run that is already serving, not a command to type.

The supervisor defers the signal, closes admission, asks the composition to stop
what is still executing, runs the cleanup window inside the reserve, publishes
the outcome ATOMICALLY and only then re-raises -- exiting 130. A stopped run
still leaves its result, and reports itself INTERRUPTED rather than settled. Its
interruption report now also names any UNRESOLVED CLEANUP by attempt and runtime
identity, because a quiescent runtime is not a proved cleanup.

## 6. Outcome

    set -e
    python3 -c "import json,sys;print(json.dumps(json.load(open(sys.argv[1])), indent=2, sort_keys=True))" \
        $ROOT/run/outcome.json

## 7. What to measure afterwards, whatever happens

- the retained implementation transcript under the instance's private-context
store: entries, span, tool calls, and whether the deliverable was written and
when;
- the review attempt's provider logs and its output disposition;
- the outcome document's `stage_states`, `held_because` and `refused_acts`;
- and if the review times out again, `DIAGNOSIS-314263.json` is the template --
the honest conclusion then is that the reviewer's turn needs to be observable
before any cap is reconsidered.
