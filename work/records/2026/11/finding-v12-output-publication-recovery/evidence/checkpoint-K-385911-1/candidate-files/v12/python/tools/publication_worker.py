"""THE HOST SIDE OF ONE DETERMINISTIC PUBLICATION: the stage owner that runs
the confined publication worker through the ORDINARY worker lifecycle, and the
seam a deployment composes around it.

W385695 internal checkpoint 2, under DESIGN REC-9 and the owner-selected
contract `work/records/2026/11/finding-v12-output-publication-recovery/
CONTRACT-PROPOSED-385720.md` sections 2 and 5.

WHAT THIS REPLACED, AND WHY IT HAD TO. The first cut of this module carried a
`PublicationWriter` whose `adopt` copied the staged bytes into the attempt's
output root IN THE MANAGER'S OWN PROCESS, on the host, and re-checked a clock
between its three steps. That is a host copy with a polite timer: no read-only
`/input`, no containment, nothing a supervisor could interrupt, and no runtime
whose stopping anybody could observe. The contract asks for the opposite on
every count, and the writer is gone rather than kept beside the real path --
a second way to "publish" that skips confinement is exactly what must not
exist.

WHAT IS HERE NOW, and none of it is a second launch protocol:

    PublicationStage    the publication worker's MOUNT and ENDING, plugged
                        into `single_worker.worker_operations(stage=...)`
                        exactly as `StageComposition` and `ManagedApplyRuntime`
                        are. Everything between the two -- the offer, the
                        claim, the attempt, the activation, the pinned input
                        root, the launch document, the workspace token, the
                        journalled runtime start and its reconciliation, the
                        command -- is the accepted composition, unchanged.
    PublicationSeam     the five members `check_publication_seam` proves.
    publication_operations()
                        composes one publication worker's ordinary operations
                        with that stage owner, over a deployment's own stores.
    staging_root()      the private root recovery-owned staging lives under.

WHAT THE STAGE OWNER DOES AT EACH END, in the order the contract fixes:

  MOUNT, before any runtime exists. It asks `publication_execution.
    prepare_launch` -- which stages the approved original READ-ONLY and
    commits the durable launch intent -- and then delivers the staged root as
    the worker's nominated source, the one read-only bind the engine adapter
    composes inside `/input`. The original is never mounted and the staged
    root is never writable in the container. It also answers the pinned
    request document, which carries the ABSOLUTE deadline.
  END, after the worker answered. It orders the runtime to stop and requires
    it OBSERVED quiescent; has `record_adoption` MEASURE both output roots
    against the approved digest; and only then runs the ordinary freeze,
    intake and retention, releases this execution's own assignment through
    its own session, and authorizes the ordinary cleanup -- which destroys
    the runtime, proves it absent and returns the workspace token.

IT DECIDES NOTHING. Whether an original may be staged, whether a launch may be
committed, whether the measured bytes are the approved ones and whether review
may be released are `job_manager.publication_execution`'s, derived from
durable state. This module says which owner each of those acts reaches.

WHAT A STOPPED OR FAILED ADOPTION LEAVES. The worker supervises its copy to
the absolute instant and faults rather than publish; the host fences the stage
at the same instant through `job_control` and the ordinary cancellation path
stops the container. Neither produces an answered terminal, so this ending is
never entered for it, nothing is frozen, and the pass journals the adoption as
UNCERTAIN. There is no retry here and no second launch.
"""

import json
import os
import sys

from baton_v12.contracts import ContractRefusal
from baton_v12.contracts.errors import name_value
from baton_v12.job_manager import (documents, episodes, publication_execution,
                                   publication_recovery, submission)
from baton_v12.worker_manager import source_boundary

__all__ = ["PublicationStage", "PublicationSeam", "DEFAULT_STAGING",
           "publication_operations", "publication_seam", "staging_root",
           "main"]

# WHERE A DEPLOYMENT ALLOCATES PRIVATE RECOVERY STAGING, under its own state
# root. A sibling of the stores rather than a child of custody, which is
# `recovery_execution.DEFAULT_WORKSPACES`' reason: a writable tree inside the
# immutable evidence it is a copy of is a wider boundary than the contract
# declares. And the contract's own sentence, kept by the location: "private
# staging is not custody".
DEFAULT_STAGING = "publication-staging"
PRIVATE = 0o700


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


class PublicationSeam:
    """The five members `check_publication_seam` proves, as one object.

    IT CARRIES CONFIGURATION AND READERS: the control store the attempt and
    its custody live in, the host owner of the original, the host's cessation
    evidence, the private staging root, and the serving composition's read of
    the confined worker's exchange.
    """

    def __init__(self, *, control, host, exclusion, workspaces, runtime,
                 ending=None):
        self.control = control
        self.host = host
        self.exclusion = exclusion
        self.workspaces = workspaces
        self.runtime = runtime
        # THE SERVING DEPLOYMENT'S OWN PRIOR-ASSIGNMENT ENDING PORT, or
        # `None`. Not one of the five members the execution acts decide with:
        # it is what `manager._publish` uses to end a failed execution's
        # still-held assignment through the producer's OWN session, which
        # only the serving composition holds. A seam without one serves
        # publication stages and ends nothing.
        self.ending = ending


class PublicationStage:
    """One deployment's publication worker: its mount, its ending, and the
    read of its exchange.

    ONE OBJECT PER CONFIGURED PUBLICATION WORKER, holding no state a restart
    needs: every answer is derived from the Job store's committed records and
    the Worker Manager's own journal, so a re-entry after a crash composes the
    same mount and the same ending.
    """

    def __init__(self, *, jobs, control, host, exclusion, identity,
                 workspaces, clock):
        self._jobs = jobs
        self._control = control
        self._identity = identity
        self._clock = clock
        self._operations = None
        self.seam = PublicationSeam(control=control, host=host,
                                    exclusion=exclusion,
                                    workspaces=workspaces, runtime=self)

    def bind(self, operations):
        """The composed worker operations this stage owner is plugged into."""
        self._operations = operations
        return self

    # -- the seam's `runtime` member -----------------------------------------

    def instance(self):
        return self._identity

    def terminal_of(self, attempt_id):
        """THE CONFINED WORKER'S EXCHANGE TERMINAL, or `None`. A read.

        Through the composed worker's own exchange observation, which is what
        the projection reads on every tick -- so this is not a second account
        of the exchange. `None` means no terminal is readable: nothing was
        launched, nothing has answered, or the episode this attempt ran under
        is no longer the live one.
        """
        stage = self._stage_of(attempt_id)
        if stage is None or self._operations is None:
            return None
        view = self._operations.observe(stage).get("exchange") or {}
        terminal = view.get("terminal")
        if terminal is None:
            return None
        return {one: terminal.get(one) for one in
                ("ending", "disposition", "manifest_digest")}

    def _stage_of(self, attempt_id, *, ended=False):
        """The publication stage this attempt ran under, as a stage document.

        `ended` ALSO ANSWERS FOR AN EPISODE THAT IS NO LONGER LIVE, which is
        what a settlement needs: by the time a failed publication is settled
        the manager may already have ended its episode, and the attempt is
        still that stage's own.
        """
        for admitted in publication_recovery.admissions_of(self._jobs):
            stage_id = documents.stage_id(admitted["job_id"],
                                          documents.PUBLICATION_STAGE)
            held = episodes.live_of(self._jobs, stage_id)
            if held is None or held["attempt_id"] != attempt_id:
                held = None
                if ended:
                    for one in episodes.episodes_of(self._jobs, stage_id):
                        if one["attempt_id"] == attempt_id:
                            held = one
                if held is None:
                    continue
            for row in submission.stages_of(self._jobs, admitted["job_id"]):
                if row["stage_id"] == stage_id:
                    return episodes.attempting(row, held)
        return None

    def observation_of(self, attempt_id):
        """A FRESH READ OF THE ENGINE about this attempt's runtime, answered
        as KNOWN or NOT KNOWN. It starts nothing and removes nothing.

        `single_worker.refresh_runtime` is the serving loop's one runtime
        read: it asks the engine about the exact attached identity and
        records the answer. When the engine could not be asked, or refused,
        NOTHING was learned -- and the axis already on record is then the
        last observation somebody made, not what is true now. That
        difference is this method's whole answer.
        """
        from baton_v12.job_manager import RefreshUnavailable
        from baton_v12.worker_manager import attempt_runtime_of

        recorded = attempt_runtime_of(self._control, attempt_id)
        said = None if recorded is None else {
            "execution_runtime": recorded["execution_runtime"],
            "cleanup": recorded["cleanup"]}
        stage = self._stage_of(attempt_id, ended=True)
        if stage is None or self._operations is None or recorded is None:
            return {"known": False, "recorded": said,
                    "why": "this deployment holds no stage for the attempt"}
        try:
            self._operations.refresh_runtime(stage)
        except RefreshUnavailable as unreachable:
            return {"known": False, "recorded": said,
                    "why": "the engine could not be asked ("
                           + type(unreachable.__cause__
                                  or unreachable).__name__ + ")"}
        except ContractRefusal as refusal:
            return {"known": False, "recorded": said,
                    "why": f"the engine's answer was refused "
                           f"({refusal.category}/{refusal.code})"}
        seen = attempt_runtime_of(self._control, attempt_id)
        if seen["execution_runtime"] == "uncertain":
            return {"known": False, "recorded": said,
                    "why": "the engine cannot say whether the runtime exists"}
        return {"known": True, "recorded": said,
                "execution_runtime": seen["execution_runtime"],
                "cleanup": seen["cleanup"]}

    def settle(self, attempt_id, *, reason):
        """THE SUPPORTED FOURTH ENDING, for a publication that did not
        publish: the composition's own `abandon_attempt`.

        IT IS THE OPERATION THAT ALREADY OWNS THIS. It commits or replays its
        own intent before any external call, force-removes the exact runtime,
        settles only on positive absence, retains the workspace under the
        configured retention policy, returns the governed workspace token and
        discharges the quiescence gate it installed. Nothing here re-decides
        any of that, and a refusal from it propagates: an engine that cannot
        prove the runtime absent leaves the token held.
        """
        stage = self._stage_of(attempt_id, ended=True)
        if stage is None or self._operations is None:
            _refuse(f"this deployment holds no publication stage for attempt "
                    f"{name_value(attempt_id)}; a settlement is performed "
                    f"through the composition that started the runtime",
                    category="refused", code="capability")
        return self._operations.abandon_attempt(
            attempt_id=attempt_id, reason=reason, stage=stage)

    def _decision(self, stage):
        """The admitted recovery THIS stage belongs to, by its own Job."""
        for admitted in publication_recovery.admissions_of(self._jobs):
            if admitted["job_id"] == stage.get("job_id"):
                return admitted["decision_id"]
        _refuse(f"stage {name_value(stage.get('stage_id'))} belongs to no "
                f"admitted publication recovery; the publication worker "
                f"serves exactly the stage a recovery admission created")

    # -- before a runtime starts ---------------------------------------------

    def mount(self, worker, stage, roots, preparing=None):
        """The roots and the READ-ONLY source this execution is started over.

        THE LAUNCH IS DECIDED HERE, ONCE, WHILE NOTHING HAS STARTED. A runtime
        that is anything but `not-started` already has a committed intent --
        this is then a re-entry (a restart, or the ending re-deriving the
        roots) and decides nothing again; it composes the same boundary over
        the staging the record names.
        """
        from baton_v12.worker_manager import attempt_runtime_of

        del preparing
        decision_id = self._decision(stage)
        state = attempt_runtime_of(self._control, stage["attempt_id"])
        if state["execution_runtime"] == "not-started":
            staging = publication_execution.prepare_launch(
                self._jobs, self.seam, decision_id=decision_id,
                now=self._clock())["staging"]
        else:
            staging = publication_execution.staging_of(
                self._jobs, stage["job_id"])
            if staging is None:
                _refuse(f"publication attempt "
                        f"{name_value(stage['attempt_id'])} has a runtime "
                        f"record and no staged input; there is nothing this "
                        f"manager staged to deliver it")
        # THE STAGED ROOT'S PARENT IS WHAT IS NOMINATED, because the staged
        # original and the recovery's own provenance are two sibling trees
        # under it and the worker is delivered both -- read-only, by the one
        # bind the adapter composes and proves.
        locator = staging["staged"]["locator"]
        if not str(locator).startswith("file://"):
            _refuse(f"a staged locator is a file:// locator; this is "
                    f"{name_value(locator)}", category="integrity",
                    code="path")
        delivered = os.path.dirname(str(locator)[len("file://"):])
        return {"roots": roots,
                "boundary": source_boundary.compose_source_boundary(
                    source_boundary.nominate_source(delivered), roots,
                    worker.given["workspace_capacity"])}

    def publication_document_for(self, stage):
        """The pinned request this execution's worker reads, as bytes.

        CANONICAL AND DERIVED FROM RECORDS, so a restart delivers byte for
        byte what the first composition did -- `single_worker` proves the
        delivered document against this answer on every re-entry.
        """
        request = publication_execution.publication_request(
            self._jobs, self._decision(stage))
        if request is None:
            return None
        return json.dumps(request, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")

    # -- after the worker answered -------------------------------------------

    def historical(self, stage, assignment):
        """An ending whose cleanup already settled is resumed from records."""
        from baton_v12.worker_manager import attempt_runtime_of

        state = attempt_runtime_of(self._control, stage["attempt_id"])
        if state is not None and state["cleanup"] in ("complete", "retained"):
            return {"attempt_id": stage["attempt_id"],
                    "assignment": assignment}
        return None

    def end(self, worker, stage, job, context):
        """THE ORDINARY ENDING, with the one measurement only this path owes.

        THE ORDER IS THE CONTRACT'S AND EVERY STEP REPLAYS:

          1. order the exact runtime to stop and require it OBSERVED
             quiescent, then reconcile it -- an absent runtime is not the
             same proof, because its writer was never seen to finish;
          2. `record_adoption` -- this manager's measurement of both output
             roots against the approved original, the worker's zero counts,
             its own fence and bound, and the durable result. A refusal here
             stops the ending with NOTHING FROZEN and no disposition taken;
          3. record the worker's own disposition, now that it is accepted;
          4. the ordinary freeze, held to the terminal's own envelope digest;
          5. the ordinary intake and the configured retention decision;
          6. release this execution's OWN assignment through its own session,
             so the reused Work returns to `queued` for the independent
             reviewer; and only then
          7. authorize the ordinary cleanup, which destroys the runtime,
             proves it absent and returns the workspace token.
        """
        from baton_v12.worker_manager import (attempt_runtime_of,
                                              authorize_cleanup,
                                              decide_retention, load_manifest,
                                              observe, reconcile_runtime,
                                              request_freeze, request_intake,
                                              tokens)

        del job
        control, attempt_id = self._control, stage["attempt_id"]
        decision_id = self._decision(stage)
        state = attempt_runtime_of(control, attempt_id)
        if state["cleanup"] in ("complete", "retained"):
            recorded = publication_execution.result_of(self._jobs,
                                                       stage["job_id"])
            return {"attempt_id": attempt_id, "outcome": "published"
                    if recorded is not None else "ended",
                    "cleanup": state["cleanup"]}
        disposition = context["disposition"]
        if disposition != "completed":
            _refuse(f"publication attempt {name_value(attempt_id)}'s worker "
                    f"answered disposition {name_value(disposition)}; a "
                    f"deterministic adoption either completes or is not a "
                    f"publication, and nothing is frozen for one that did "
                    f"not", category="runtime-observation",
                    code="quiescence-unknown")
        adapter = context["adapter"]
        stopped = adapter.stop({"runtime_id": state["runtime_id"],
                                "operation_id":
                                    f"publication-quiesce:{attempt_id}"})
        if stopped.get("state") != "quiescent":
            _refuse(f"publication attempt {name_value(attempt_id)}'s runtime "
                    f"was ordered to stop and observed "
                    f"{name_value(stopped.get('state'))}; an adoption is "
                    f"measured and frozen only over a positively quiescent "
                    f"runtime", category="runtime-observation",
                    code="quiescence-unknown")
        reconcile_runtime(control, adapter, attempt_id=attempt_id)
        # THE ADOPTION IS DECIDED BEFORE THE WORKER'S ANSWER IS RECORDED AS
        # ITS DISPOSITION (review 2026-11-23T20-28-00Z). `record_adoption` is
        # where this store's fence and the absolute bound are asked, and an
        # answer it refuses is an answer this manager did not accept. Writing
        # `completed` on the attempt first left a fenced publication that the
        # supported fourth ending then refused to settle -- it ends an attempt
        # whose answer was never taken, and the row said this one's had been.
        adopted = publication_execution.record_adoption(
            self._jobs, self.seam, decision_id=decision_id,
            now=self._clock())
        observe(control, attempt_id=attempt_id, axis="worker_disposition",
                value=disposition)
        frozen = request_freeze(control, worker.port, adapter,
                                attempt_id=attempt_id,
                                disposition=disposition)
        sealed = load_manifest(control, frozen["manifest_digest"],
                               "resultManifest")
        validated = (sealed or {}).get("completion_manifest_digest")
        if context["terminal"]["manifest_digest"] != validated:
            _refuse(f"publication attempt {name_value(attempt_id)}'s worker "
                    f"answered completion manifest "
                    f"{name_value(context['terminal']['manifest_digest'])} "
                    f"and this manager validated {name_value(validated)}; a "
                    f"terminal that names another envelope is not evidence "
                    f"about the output this manager froze",
                    category="refused", code="operation-collision")
        receipt = request_intake(control, worker.port, adapter,
                                 attempt_id=attempt_id)
        decided = decide_retention(
            control, worker.port, adapter, attempt_id=attempt_id,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition=worker.given["retention_disposition"],
            retention_policy_digest=worker.given["retention_policy_digest"])
        # THE EXECUTION ENDS BECAUSE IT FINISHED, which is ART-7 from this
        # side: the release does not depend on anybody accepting the result.
        # `end`, not `cancel` -- see `single_worker._AuthoritySession.end`.
        live = worker.session.assignment_of(
            context["assignment"]["work_ref"]["work_id"])
        if live is not None and live == context["assignment"]:
            worker.session.end({
                "expect": context["assignment"],
                "operation_id": f"publication-release:{attempt_id}",
                "disposition": "release",
                "reason": "deterministic publication collected"})
        authorize_cleanup(
            control, worker.port, adapter, attempt_id=attempt_id,
            retention_policy_digest=worker.given["retention_policy_digest"],
            govern=tokens.workspace_governance())
        return {"attempt_id": attempt_id, "outcome": "published",
                "disposition": disposition,
                "adopted": adopted["adopted"]["tree_digest"],
                "manifest_digest": frozen["manifest_digest"],
                "result_id": frozen["result_id"],
                "receipt_digest": receipt["receipt_digest"],
                "artifacts": sorted(one["artifact_id"]
                                    for one in receipt["artifacts"]),
                "retention": decided["disposition"]}


def staging_root(instance_root):
    """The private staging root of one instance, created if absent.

    0700 BECAUSE THIS MANAGER IS THE ONLY WRITER. The staged original is
    delivered READ-ONLY to one execution, and a group-writable scratch tree
    beside an approved original is a wider boundary than the one the contract
    declares.
    """
    place = os.path.join(os.path.realpath(str(instance_root)),
                         DEFAULT_STAGING)
    os.makedirs(place, mode=PRIVATE, exist_ok=True)
    os.chmod(place, PRIVATE)
    return place


def publication_operations(given, *, jobs, control, authority, provider,
                           host, exclusion, identity, workspaces=None,
                           engine_run=None, clock=None,
                           execution_context=None, lifetime_policy=None,
                           dispose=None, ending=None, served=None):
    """ONE publication worker's ordinary operations, with its stage owner.

    `served` IS THE PER-RECOVERY OPERAND SETS (review 2026-11-23T18-55-03Z
    R3): `{recovery_job_id: deployment}`, each the installed document as
    `stage_execution._served_deployment` derived it for that recovery's Work
    and original task. Given, the answer is ONE capacity -- one worker id,
    one participant, one stage owner, one seam -- whose stage-specific
    operations are selected by the stage's own Job, exactly as the
    integration role's are; a publication stage of a Job this deployment
    derived nothing for is refused rather than served under another
    recovery's manifest. `None` is the single composition over `given`
    itself, which is what a caller holding one already-derived document
    wants.

    `given` IS THE WORKER'S OWN DEPLOYMENT DOCUMENT, already held by
    `single_worker._held` under the publication role -- so its image, its
    profile, its input manifest and its (empty) credential profile are the
    deployment's facts and none is this function's choice.

    NO PROVIDER IS COMPOSED IN. `provider` is the deployment's credential
    provider callable and a publication worker declares no credential slot,
    so it is never asked; it is an operand only because the worker lifecycle
    takes one.
    """
    from . import single_worker

    stage = PublicationStage(
        jobs=jobs, control=control, host=host, exclusion=exclusion,
        identity=identity,
        workspaces=workspaces or staging_root(identity["root"]),
        clock=clock if clock is not None else jobs._now)
    def composed(document):
        return single_worker.worker_operations(
            document, control, authority, provider, engine_run=engine_run,
            clock=clock, stage=stage,
            dispose=dispose if dispose is not None else (lambda: None),
            execution_context=(execution_context
                               if execution_context is not None
                               else single_worker.job_execution_reader(jobs)),
            lifetime_policy=lifetime_policy)

    operations = composed(given)
    if served is not None:
        held = {}
        try:
            for job_id in sorted(served):
                held[job_id] = composed(served[job_id])
        except BaseException:
            # A PARTIAL COMPOSITION RELEASES WHAT IT ALREADY BUILT.
            for one in held.values():
                one.close()
            operations.close()
            raise
        operations = PerRecoveryOperations(operations, held)
    stage.bind(operations)
    stage.seam.ending = ending
    # THE SEAM RIDES ON THE OPERATIONS IT WAS COMPOSED WITH, which is where
    # `manager._publish` discovers it -- so a deployment that composed a
    # publication worker reaches the pass and one that did not reaches none.
    operations.recovery_publication = stage.seam
    return operations, stage


class PerRecoveryOperations:
    """ONE publication capacity, one held operand set per bound recovery.

    `stage_execution._PerJobIntegration`'s shape and its reasons, for the
    other role that is installed once and serves many Jobs. The pool holds a
    single publication worker and this changes none of that: one worker id,
    one participant, one principal, one reservation at a time. What is
    selected here is the OPERANDS -- `single_worker` holds a stage to its
    deployment's own Work and submitted input, and for a recovery those are
    the original Job's -- so a stage reaches the operations composed for ITS
    recovery and the worker's own validator keeps every one of its checks.

    `installed` ANSWERS WHAT IS ABOUT THE DEPLOYMENT AND NOT ABOUT A STAGE:
    the canonical operation identity, the journal reads, the restart
    settlement and the transport pump are one control store's and one
    participant's, whichever recovery is in hand, and it exists whether or
    not any recovery is bound yet. IT SERVES NO STAGE. A publication stage is
    served under its own recovery's derived document or refused.
    """

    canonical = True

    def __init__(self, installed, held):
        self.installed = installed
        self.held = dict(held)
        self.port = installed.port
        self.recovery_publication = None

    @property
    def _worker(self):
        return self.installed._worker

    def _serving(self, stage):
        job_id = stage.get("job_id")
        held = self.held.get(job_id)
        if held is None:
            _refuse(f"stage {name_value(stage.get('stage_id'))} names Job "
                    f"{name_value(job_id)} and this deployment derived "
                    f"publication operands for "
                    f"{sorted(self.held) or 'no recovery'}; a publication "
                    f"stage is served under its own recovery's Work and "
                    f"task, so one this deployment binds nothing for is "
                    f"refused rather than served under another recovery's "
                    f"manifest or the installed one")
        return held

    def worker_for(self, stage):
        """The launch composition THIS stage is served by. For a reader that
        needs the exact per-recovery worker rather than the shared one."""
        return self._serving(stage)._worker

    # -- about this deployment ------------------------------------------------

    def canonical_operation(self, act, offer_id):
        return self.installed.canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        return self.installed.receipt_of(operation_id)

    def binding_intent(self, stage, job):
        return self.installed.binding_intent(stage, job)

    def recover(self, *, now):
        return self.installed.recover(now=now)

    def attach(self, offer_ids):
        return self.installed.attach(offer_ids)

    def drain(self, handlers, *, quiescent=()):
        return self.installed.drain(handlers, quiescent=quiescent)

    # -- about one recovery's stage -------------------------------------------

    def admit(self, stage, job):
        return self._serving(stage).admit(stage, job)

    def claim(self, stage):
        return self._serving(stage).claim(stage)

    def settle_offer(self, stage, *, now):
        return self._serving(stage).settle_offer(stage, now=now)

    def launch(self, stage, job):
        return self._serving(stage).launch(stage, job)

    def dispatch(self, stage, job):
        return self._serving(stage).dispatch(stage, job)

    def conclude(self, stage, job):
        return self._serving(stage).conclude(stage, job)

    def observe(self, stage):
        return self._serving(stage).observe(stage)

    def refresh_runtime(self, stage):
        return self._serving(stage).refresh_runtime(stage)

    def abandon_attempt(self, *, attempt_id, reason, stage, seconds=None,
                        reclaim=None):
        """The fourth ending, routed to the operands THIS stage ran under --
        the composition whose adapter carries what its start created."""
        return self._serving(stage).abandon_attempt(
            attempt_id=attempt_id, reason=reason, stage=stage,
            seconds=seconds, reclaim=reclaim)

    def close(self):
        for _job_id, one in sorted(self.held.items()):
            one.close()
        self.installed.close()


def publication_seam(stage):
    """The seam `advance_publication` is handed for one composed stage."""
    return stage.seam


def main(argv=None):                                      # pragma: no cover
    """Print the approved publication declarations, for an operator to read.

    THE ONE READ THIS MODULE OFFERS AN OPERATOR, and it is a read: the two
    declared outputs a recovery publishes under, with the owner-selected
    ceilings and the provenance descriptor's own bound. It records nothing,
    stages nothing and publishes nothing.
    """
    taken = list(sys.argv[1:] if argv is None else argv)
    if taken:
        raise SystemExit("usage: publication_worker")
    declaration = publication_recovery.corrective_declaration()
    json.dump({"candidate": declaration["output"],
               "declaration": declaration["descriptor"],
               "declaration_digest": declaration["digest"],
               "provenance": publication_recovery.PROVENANCE_OUTPUT},
              sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main())
