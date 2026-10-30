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
        wanted = set(attempt_ids)
        held = {}
        for entry in attempts.runtime_recovery_inventory(self._control):
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
            raise FileNotFoundError(
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
            raise FileNotFoundError(
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

        DERIVED RATHER THAN COMPOSED FROM OPERANDS. The source worker, the
        declared base and the canonical target are this deployment's facts
        about the specification being re-attempted; a fresh attempt that chose
        its own would be a different Job wearing the same task.
        """
        import sys

        from tools import bootstrap

        document = self._install()
        jobs = list(bootstrap.jobs_of(document))
        prior = None
        for one in jobs:
            if one.get("job_id") == like:
                prior = one
        if prior is None:
            raise FileNotFoundError(
                f"this instance's install document binds no Job {like!r}, so "
                f"there is nothing for a fresh attempt to be derived from")
        fresh = dict(prior, job_id=job_id, job_work_id=work_id)
        if "review_work_id" in prior:
            fresh["review_work_id"] = work_id
        document = dict(document, jobs=jobs + [fresh])
        bootstrap.prepare(document,
                          stream=self._stream if self._stream is not None
                          else sys.stdout)
        self._publish_install(document)
        return self.binding_of(job_id)

    def _publish_install(self, document):
        """Keep the input document and the emitted configuration in step.

        A later fresh attempt derives from this file, so an instance whose
        configuration binds three Jobs and whose install document names two
        would prepare a document that DROPS one -- and `bootstrap.conflicts`
        refuses exactly that, which would make the second retry impossible
        for a reason the operator could not see.
        """
        place = self._root / "install-inputs.json"
        temporary = Path(str(place) + ".tmp")
        temporary.write_text(json.dumps(document, indent=2, sort_keys=True)
                             + "\n")
        temporary.replace(place)

    def serving(self, job_id, kind):
        from tools import stage_execution

        configured = self._configuration()
        binding = self.binding_of(job_id)
        if binding is None:
            return []
        # THE SELECTOR COMPARES A JOB'S OWN DIGESTS, so they are taken from
        # the binding's deployment rather than invented: `_disagreements`
        # reads `job["input_digest"]` and `job["policy_digest"]`, which for a
        # fresh attempt are the prior Job's preserved ones and are already in
        # the worker manifest this binding names.
        worker = None
        for one in configured.get("workers") or []:
            if one.get("worker_id") == binding.get("source_worker_id"):
                worker = one
        if worker is None:
            return []
        held = worker["deployment"]
        job = {"input_digest": stage_execution.job_input_identity(
                   held["input_manifest"], what="a configured worker's input"),
               "policy_digest": held["policy_digest"]}
        stage = {"stage_id": f"{job_id}/{kind}", "job_id": job_id,
                 "kind": kind, "work_id": binding.get("job_work_id"),
                 "profile_name": held["profile_name"],
                 "profile_digest": held["profile_digest"]}
        try:
            compatible = stage_execution.servable_workers(
                configured, binding, stage, job)
        except ContractRefusal:
            # THE SELECTOR'S OWN REFUSAL IS AN ANSWER HERE, not a failure.
            # `_job_workers` refuses when nothing can serve the stage, and
            # the caller's rule is "an empty answer refuses" -- so this
            # reports what the scheduler found rather than re-wording it.
            return []
        return [one["worker_id"] for one in compatible]
