"""The three owners a fresh attempt composes, each behind its own API. W358969.

DESIGN REC-7 says the manager composes "Work authorization and host
runtime/resource exclusion through their owning APIs" and that "script-side
prechecks cannot substitute for manager enforcement". Both halves of that
sentence shape this file.

EVERY OBJECT HERE REPORTS A FACT AND PERFORMS AT MOST ONE NAMED EFFECT.
Not one of them decides whether a runtime has ceased, whether a Work may be
reused, or whether a binding is good enough -- those are rules, the rules are
`job_manager.fresh_attempt`'s, and an adapter holding one would be the pilot's
helper again under a new name. What they do is reach the right owner: the
Worker Manager's attempt and token records, the Authority's Work projection,
and the deployment configuration's own preparation and selector.

AND NOT ONE OF THEM OPENS A STORE IT WAS NOT HANDED, reads a database file
directly, or copies one. The review that preceded this Work refused a helper
for doing exactly that; the answer is not a better copy, it is asking the
owner.
"""

import json
from pathlib import Path

from baton_v12.authority import Authority, Refusal
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts


# WHAT THIS BUILD CANNOT ESTABLISH, said out loud. AGENTS.md:267's rule is
# that an inability is the finding; this is the one this operation has.
#
# `attempts.runtime_recovery_inventory` documents its own precondition -- "the
# caller must exclude concurrent writers before using this inventory" -- and
# NO SUPPORTED SURFACE RESERVES THE WORKER MANAGER AGAINST ITS SERVING LOOP
# for a read-only consumer. A coherent snapshot is not a reservation: it makes
# the answer internally consistent, not durable. So what this operation proves
# is that the prior attempts were ceased AT ONE OBSERVED MOMENT, asked twice,
# and the manager re-asks after its reservation precisely because the first
# answer is about the past. An operator who needs the stronger statement stops
# the serving loop first, and the exact missing projection is recorded here
# rather than simulated by a PID read or a status timestamp.
UNRESERVED_EXCLUSION = (
    "no supported operation reserves the Worker Manager control store "
    "against its own serving loop for a read-only consumer, so this evidence "
    "is a coherent observation rather than an exclusion; it is asked again "
    "after the reservation and it is not proof that no writer acts next")


class BindingRefusal(Exception):
    """An operator-facing refusal from the deployment configuration's owner.

    NAMED RATHER THAN `FileNotFoundError`, because every one of these is a
    statement about this instance rather than about a missing file: the thing
    it says is what the operator has to fix.
    """


class HostExclusion:
    """What the Worker Manager records about each prior attempt.

    ONE COMPOSED READ PER ATTEMPT, taken from `runtime_recovery_inventory`
    rather than assembled here: that reader already pairs an attempt's runtime
    axes with its workspace token, and it says in its own words that an absent
    token is "explicit uncertainty, never a synthetic non-launch proof". A
    second pairing in this file would be a second chance to get that wrong.

    ABSENCE IS REPORTED AS ABSENCE. An attempt identity the manager derived
    and this host never recorded anything under answers `None`, and what that
    means is the caller's to decide.
    """

    def __init__(self, control):
        self._control = control

    def evidence_of(self, attempt_ids):
        # ONE COHERENT BOUNDARY, which is the strongest thing a read-only
        # consumer can take. `runtime_recovery_inventory` says its caller must
        # "exclude concurrent writers before using this inventory", and a
        # read-only handle HAS no exclusion to offer -- the serving loop is
        # the writer and nothing supported reserves it. `ControlStore.snapshot`
        # at least makes every attempt in this answer describe ONE state of
        # that store rather than several, so a torn read cannot produce an
        # attempt set that never existed. THE RESIDUAL IS NAMED RATHER THAN
        # PAPERED OVER: see `UNRESERVED_EXCLUSION`.
        wanted = set(attempt_ids)
        held = {}
        with self._control.snapshot() as control:
            for entry in attempts.runtime_recovery_inventory(control):
                if entry["attempt_id"] in wanted:
                    held[entry["attempt_id"]] = {"runtime": entry["runtime"],
                                                 "token": entry["token"]}
        # EVERY REQUESTED IDENTITY GETS A KEY, so "this host holds nothing for
        # it" and "nobody asked about it" cannot be confused by the caller --
        # and the caller's fail-closed rule depends on telling them apart.
        return {attempt_id: held.get(attempt_id) for attempt_id in wanted}


class WorkAuthorization:
    """The Authority's own answer about one Work, and its own creation act.

    ABSENCE IS CONFIRMED BY A SECOND OWNER READ rather than by reading a
    refusal's prose. `project_work` refuses an unknown Work, and branching on
    the wording of that refusal would be a branch that changes when the
    sentence is improved -- so an unknown Work is one whose CREATION RECORD is
    also absent, which is a fact rather than a message.
    """

    def __init__(self, authority, *, route):
        self._authority = authority
        self._route = route

    def work_of(self, work_id):
        try:
            return self._authority.project_work(work_id)
        except Refusal:
            if self._authority.work_creation(work_id) is None:
                return None
            raise

    def create_work(self, work_id, *, operation_id):
        self._authority.create_work(work_id, self._route,
                                    operation_id=operation_id)
        return self._authority.project_work(work_id)

    @classmethod
    def opened(cls, path, *, authority_uuid, route):
        return cls(Authority.open(path,
                                  expected_authority_uuid=authority_uuid),
                   route=route)


class DeploymentBinding:
    """The deployment configuration: what it binds, and what can serve it.

    THE OWNER OF THIS DOCUMENT IS `bootstrap`, so an additive binding is
    prepared by `bootstrap.prepare` over this instance's own install document
    rather than by editing `deployment.json` in place. That call revalidates
    the WHOLE deployment through `stage_execution.held_configuration` and
    refuses to change anything a repeated bootstrap must preserve -- which is
    why adding a Job this way cannot quietly move an existing Job's Work, base
    or target.

    AND THE SECOND QUESTION IS ASKED OF THE SELECTOR, not of the document.
    `stage_execution.servable_workers` is the scheduler's own rule; a
    comparison written here would be a copy of it, and the pilot proved what
    that copy costs -- a configuration that validated cleanly and whose stages
    no worker could ever be selected for.
    """

    def __init__(self, root, *, stream=None):
        self._root = Path(root)
        self._stream = stream

    # -- the two documents, read as ordinary files -------------------------

    def _configuration(self):
        from tools import bootstrap

        place = Path(bootstrap.layout(self._root)["configuration"])
        if not place.exists():
            raise BindingRefusal(
                f"{place} does not exist; this instance has no emitted "
                f"deployment configuration to bind a fresh attempt into")
        return json.loads(place.read_text())

    def _install(self):
        """The input document `prepare` consumes, as this instance kept it.

        `bootstrap.install` writes it beside the configuration precisely so a
        later in-place preparation does not have to be handed a document
        somebody reconstructed.
        """
        place = self._root / "install-inputs.json"
        if not place.exists():
            raise BindingRefusal(
                f"{place} does not exist; an additive binding is prepared "
                f"from this instance's own install document and there is "
                f"nothing here to add to")
        return json.loads(place.read_text())

    # -- the port ----------------------------------------------------------

    def binding_of(self, job_id):
        for one in self._configuration().get("job_bindings") or []:
            if one.get("job_id") in (job_id, None):
                return one
        return None

    def bind(self, job_id, *, like, work_id):
        """Add one Job binding, derived from the one being replaced.

        THE INPUT CONTRACT IS `bootstrap._JOB`, which names `work_id` ONCE.
        The first cut of this adapter wrote `job_work_id` -- the EMITTED
        binding's spelling -- and `prepare` refused every call with "nothing
        reads jobs[1].job_work_id". The two documents are not the same
        document: `deployment.json` is what `stage_execution` consumes and
        `install-inputs.json` is what `bootstrap` consumes, and this is the
        second one.

        DERIVED RATHER THAN COMPOSED FROM OPERANDS. The source worker, the
        declared base and the canonical target are this deployment's facts
        about the specification being re-attempted; a fresh attempt that chose
        its own would be a different Job wearing the same task.
        """
        import sys

        from tools import bootstrap

        document, jobs, prior = self._reconciled(like)
        if any(one.get("job_id") == job_id for one in jobs):
            # ALREADY IN THE INPUT DOCUMENT AND NOT IN THE CONFIGURATION: an
            # interrupted publication, repaired by preparing the document it
            # already describes rather than by appending a second entry.
            fresh = [one for one in jobs if one.get("job_id") == job_id][0]
            if fresh.get("work_id") != work_id:
                raise BindingRefusal(
                    f"this instance's install document already names Job "
                    f"{job_id!r} on Work {fresh.get('work_id')!r} and this "
                    f"fresh attempt runs under {work_id!r}; nothing was "
                    f"changed")
            document = dict(document, jobs=jobs)
        else:
            fresh = dict(prior, job_id=job_id, work_id=work_id)
            document = dict(document, jobs=jobs + [fresh])
        # THE INPUT FILE IS WRITTEN FIRST, and that ordering is the recovery
        # story. `prepare` publishes the configuration; if this process dies
        # between the two, an input document that was written AFTERWARDS would
        # be missing a Job the configuration binds -- and `conflicts` refuses
        # exactly that, so the NEXT retry could never be prepared at all. An
        # input naming a Job the configuration does not yet bind is the
        # harmless direction: `prepare` is what makes it real, and running it
        # again finishes the job.
        self._publish_install(document)
        bootstrap.prepare(document,
                          stream=self._stream if self._stream is not None
                          else sys.stdout)
        return self.binding_of(job_id)

    def _reconciled(self, like):
        """The install document, PROVED against what this instance now binds.

        AN INITIAL INSTALL INPUT IS NOT THE CURRENT CONFIGURATION, and
        assuming it is would silently prepare a document that DROPS a Job --
        which `bootstrap.conflicts` refuses, late and with a sentence about a
        Job that "stops being named" rather than about the stale file that
        caused it. So the disagreement is found here, named here, and refused
        here.
        """
        document = self._install()
        jobs = [dict(one) for one in self._install_jobs(document)]
        named = {one.get("job_id") for one in jobs}
        bound = {one.get("job_id") for one in
                 (self._configuration().get("job_bindings") or [])}
        missing = sorted(one for one in bound - named if one is not None)
        if missing:
            raise BindingRefusal(
                f"this instance binds {', '.join(repr(one) for one in missing)}"
                f" and its install document does not name "
                f"{'them' if len(missing) > 1 else 'it'}; preparing from that "
                f"document would drop a configured Job, so nothing was "
                f"changed. Reconcile install-inputs.json with deployment.json "
                f"before a fresh attempt is admitted here")
        prior = None
        for one in jobs:
            if one.get("job_id") == like:
                prior = one
        if prior is None:
            raise BindingRefusal(
                f"this instance's install document names no Job {like!r}, so "
                f"there is nothing for a fresh attempt to be derived from")
        return document, jobs, prior

    def _publish_install(self, document):
        """Keep the input document and the emitted configuration in step.

        A later fresh attempt derives from this file, so an instance whose
        configuration binds three Jobs and whose install document names two
        would prepare a document that DROPS one -- and `bootstrap.conflicts`
        refuses exactly that, which would make the second retry impossible
        for a reason the operator could not see.

        WRITTEN ATOMICALLY, by rename, so an interrupted write cannot leave
        the document this adapter derives from as partial JSON.
        """
        place = self._root / "install-inputs.json"
        temporary = Path(str(place) + ".tmp")
        temporary.write_text(json.dumps(document, indent=2, sort_keys=True)
                             + "\n")
        temporary.replace(place)

    @staticmethod
    def _install_jobs(document):
        from tools import bootstrap

        return bootstrap.jobs_of(document)

    def serving(self, job_id, *, stage, job):
        """Which configured workers can serve THIS stage of THIS Job.

        THE OPERANDS ARE THE SUBMITTED ONES. The first cut of this adapter
        built the Job's input digest and every stage's profile OUT OF the
        implementation worker it was about to compare them against, so the
        comparison could not fail and a review stage was judged by the
        implementation worker's profile. What the selector exists to decide is
        whether the configured pool can serve the SPECIFICATION being
        re-attempted -- so the caller supplies that specification and this
        passes it through untouched.
        """
        from tools import stage_execution

        configured = self._configuration()
        binding = self.binding_of(job_id)
        if binding is None:
            return []
        try:
            compatible = stage_execution.servable_workers(
                configured, binding, dict(stage, job_id=job_id), job)
        except ContractRefusal:
            # THE SELECTOR'S OWN REFUSAL IS AN ANSWER HERE, not a failure.
            # `_job_workers` refuses when nothing can serve the stage, and
            # the caller's rule is "an empty answer refuses" -- so this
            # reports what the scheduler found rather than re-wording it.
            return []
        return [one["worker_id"] for one in compatible]
