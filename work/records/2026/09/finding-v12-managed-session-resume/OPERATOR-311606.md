# The proposed provider experiment — filled selection and exact commands

W236087 claim 311606, answering owner reroute 311598: "resolve
SELECTIONS-309356.json using the accepted source/base and configured credential
reference and principals where applicable; explain any genuinely unresolved
choice… Deliver a filled selection file and exact setup, run, status and stop
commands for independent review, then return baton.decide for live selection."

NOTHING HERE IS EXECUTED. No instance was installed, no deployed store or grant
opened, no credential byte read or copied, no container started, no image built
and no version-control act performed. `SELECTIONS-RESOLVED-311606.json` is a
filled document and `RUN-COMMANDS-311606.json` is a command list; running either
is the owner's selection, which is what this returns to `baton.decide` for.

## 1. The ten operands, and where each value came from

Every one is READ from an accepted record, not chosen here.

    source.root              /home/sl/baton-runs/two-jobs-247941-01-inputs
    source.declared_base     346a809bf0e4c47e52d881bd46d6d62a611c9816
      RE-VALIDATED THIS TURN: head is that object, the working tree is clean
      (0 entries), and `docs/v12-context-correction.md` is ABSENT -- so this Job
      produces it rather than reviewing somebody else's file, and no new commit
      is needed.

    participants.implementation   baton.impl
    participants.review           baton.review
    participants.integration      baton.merge
    receipts.verification         baton.verifier
    receipts.review               baton.approver-review
    receipts.approval             baton.approver
      ALL SIX FROM THE ACCEPTED SINGLE JOB'S OWN DEPLOYMENT RECORD
      (/home/sl/baton-runs/single-implementation-244216/run/deployment.json):
      the two worker `participant` values, its `integration_profile`'s
      `integrator_participant`, and its `receipt_participants`. The receipt
      WRITERS are deliberately not the workers -- the Authority refuses a
      receipt written by an actor it granted nothing to.

    credential_reference     w202663-development
      THE REFERENCE, FROM THAT SAME RECORD's `credential_profile`. A reference is
      a NAME the manager resolves at launch through the operator's own registry;
      nothing here reads, copies or digests a credential, and the registry itself
      was not opened.

    context_storage.excluded[0]   the selected source root, above
      The private context storage must exclude the source tree.

`SELECTIONS-RESOLVED-311606.json` is ADMITTED by `correction_packet.held_selections`
with ZERO unresolved operands, and the Work identity it would create is
`<8 hex>-W236087`, which `authority.identity.check_work_id` accepts.

## 2. The one genuinely unresolved choice, stated rather than hidden

WHETHER THE CREDENTIAL REFERENCE STILL RESOLVES TO A CURRENT SESSION. The
reference NAME is configured and is the accepted one; whether the session behind
it is live is a fact only the owner can check, and it is not checkable from here
without reading the registry this packet deliberately does not touch. W247941's
run 01 failed on an expired session, so this is a real risk rather than a
formality: CONFIRM A CURRENT SESSION BEFORE SELECTING THE RUN. If it has expired
the run will fail with a provider start error and be HELD, which is a correct
outcome and not a reason to rerun anything.

Two further owner decisions that are selections rather than unresolved operands:
whether to run this at all, and whether `/home/sl/baton-instances/managed-correction-309356`
is the root to use. The document names that root; changing it is one edit.

## 3. Setup

    export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
    export SEL=$DOSSIER/SELECTIONS-RESOLVED-311606.json
    export DEST=/home/sl/baton-instances/managed-correction-309356-packet
    export ROOT=/home/sl/baton-instances/managed-correction-309356
    export STAGED=/home/sl/baton-instances/managed-correction-309356-source/manager-source
    export IMPORT=$STAGED/src:$STAGED
    export PYTHONDONTWRITEBYTECODE=1

    # 0. STAGE: write the inputs and COPY the modules this run will import.
    #    Refuses before it writes anything.
    python3 $DOSSIER/correction_packet.py stage \
        --selections $SEL --destination $DEST --claim 311606 \
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

    # 3. BIND the packet to what the instance actually holds.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py bind \
        --selections $SEL --destination $DEST --claim 311606 \
        --provenance $DOSSIER/PROVENANCE-309356.json

    # 4. PROVE it against the tree, with the real product validators.
    #    Opens no store; refuses on any drift.
    PYTHONPATH=$IMPORT python3 $DOSSIER/correction_packet.py check \
        --packet $DEST/packet.json

`RUN-COMMANDS-311606.json` carries steps 1–5 and 7 as argument vectors with
their environments, EQUAL member-for-member to what the generator emits for this
selection, and lists step 6 as pending because it needs the identity the
bootstrap has not minted yet. Every delivered argv element is a literal: no
placeholder and no shell expression.

## 4. Run

    # 5. The owner acts, then BOUNDED serving, in the foreground.
    BATON_V12_STAGE_EXECUTION_CONFIG=$DEST/deployment.json PYTHONPATH=$IMPORT \
        python3 $DOSSIER/correction_supervisor.py --packet $DEST/packet.json

It holds 900 seconds total with 60 RESERVED INSIDE that for the manager-owned
stop and absence collection, caps the invocations at the admission gate (two
implementer, two review), holds the Job's own 180-second provider turn, stops on
the first terminal state, and retains its outcome even when interrupted.

## 5. Status, from another terminal

    PYTHONPATH=$IMPORT python3 -m tools.job_manager \
        --store $ROOT/db/jobs.sqlite3 \
        --authority-uuid $(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['authority_uuid'])" $ROOT/bootstrap.json) \
        --incarnation managed-correction-309356 \
        status --control $ROOT/db/control.sqlite3

READ-ONLY: it opens the stores for reading and admits nothing. It reports every
Job in the store; this run's is `job-managed-correction-309356`.

THE IDENTITY IS NOT IN THE DELIVERED COMMAND LIST, and an earlier version of this
document wrongly said it was. `tools.bootstrap` mints it at step 1, so
`RUN-COMMANDS-311606.json` lists step 6 as PENDING with the read-only resolver
above rather than writing a placeholder -- a placeholder in an argv element would
be passed to the manager verbatim. After step 3, `bind` writes the COMPLETE
seven-step list with the real identity in it:

    python3 -c "import json,sys;print(json.dumps(json.load(open(sys.argv[1]))['commands'], indent=2))" \
        $DEST/commands.json

The `$(...)` substitution in the command above is for a HUMAN typing into a
shell, which expands it; the argument-vector form in `commands.json` carries the
literal value instead.

## 6. Stop

    ONE Ctrl-C in the serving terminal (SIGINT).

The supervisor defers the signal, closes admission, asks the composition to stop
what is still executing, runs the cleanup window inside the reserve, publishes
the outcome ATOMICALLY, and only then re-raises -- exiting 130. So a stopped run
still leaves its result at `$ROOT/run/outcome.json`, and the run reports itself
interrupted rather than settled. A second Ctrl-C during cleanup ends the window
and is reported; it does not escape with the accounting half done. `SIGKILL`
cannot be caught and nothing here pretends otherwise.

To read the result afterwards:

    python3 -c "import json,sys;print(json.dumps(json.load(open(sys.argv[1])), indent=2, sort_keys=True))" \
        $ROOT/run/outcome.json

## 7. What each ending means, so the result is not over-read

    accepted-without-correction   A COMPLETE, HONEST RESULT. The first
      independent review accepted the opening proposal, so no restore happened
      and THE RUN PROVES NOTHING ABOUT RESTORE. It is not a failure and MUST NOT
      be rerun to obtain one.
    corrected-and-accepted        The only ending that answers the provider
      question. Acceptance requires the restored conversation, improvement
      against the ACTUAL feedback, exact attribution, the predecessor's token
      returned before the restored activation, and a second independent
      acceptance.
    rejected                      A valid result at either stage. It ends the
      run and no correction is manufactured from it.
    failed-or-unknown             Provider failure (including an expired
      session), a failed context save, an unreadable verdict, a timeout, an
      interruption or unproved cleanup. The run is HELD, every failure keeps its
      attribution, and no retry follows.

## 8. What this experiment does not establish

The deterministic proof in this dossier covers the controller, custody,
projection, token governance, attribution and the four endings with a SCRIPTED
provider and a simulated engine. A live run would answer only the remaining
question -- whether the actual qualified CLI consumes its own conversation and
improves against real feedback. The production deployment-comparison branch stays
unproved either way, this packet selects a CANDIDATE qualification by design, and
the historical transaction-boundary test failure recorded in this dossier remains
UNKNOWN.
