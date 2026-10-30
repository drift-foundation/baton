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

import errno
import fcntl
import json
import os
from contextlib import contextmanager
from pathlib import Path

from baton_v12.authority import Authority, Refusal
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts


class BindingRefusal(Exception):
    """An operator-facing refusal from the deployment configuration's owner.

    NAMED RATHER THAN `FileNotFoundError`, because every one of these is a
    statement about this instance rather than about a missing file: the thing
    it says is what the operator has to fix.
    """


class InstanceOwnership:
    """Become the one manager acting on this instance, or refuse. W358969 R7.

    THIS IS THE PRODUCT'S OWN EXCLUSION, not a new one.
    `workspaces.hold_manager_instance` is described by its own docstring as
    the guard taken "before a manager dispatches work or mutates a managed
    resource", and `single_worker` takes it for exactly the second reason --
    writing a configuration into a manager's store. A fresh attempt mutates
    the deployment configuration and reads the host's record of a failed
    execution, so it is the same act and it takes the same guard.

    WHAT IT ACTUALLY BUYS, stated precisely. A serving manager holding this
    instance makes this admission REFUSE instead of racing it. Two admissions
    in two processes cannot both act on one instance's configuration. And the
    host evidence is read while the guard is held, which is the difference
    between a coherent observation and an exclusion: the one writer that
    could change those answers is the manager whose guard this now holds.

    WHAT IT DOES NOT BUY, equally precisely. It is not cessation evidence. A
    guard nobody holds means no manager is running HERE; it says nothing
    about a container that is still alive, which is why the runtime and token
    axes are still read and still fail closed on unknown.
    """

    def __init__(self, control, workspace_storage, root=None):
        self._control = control
        self._place = workspace_storage
        # WHERE THE INVOCATION LOCKS LIVE. The workspace root is this
        # instance's own mutable state and is already the thing the guard
        # names, so an admission's lock sits beside it rather than in a
        # directory chosen here.
        self._root = Path(root if root is not None else workspace_storage)
        self._root.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def held(self):
        """Hold this instance, and GIVE BACK ONLY WHAT WAS TAKEN HERE.

        Review R10: `hold_manager_instance` returns the descriptor this
        PROCESS already holds when it already holds one -- correct for a
        manager composing twice, and a trap for a second caller, which
        cannot tell "I acquired this" from "I was handed somebody else's
        lifetime". Releasing the second kind drops an exclusion its owner
        still believes it has, and a spawned probe proved exactly that.

        So the question is asked BEFORE the acquisition, through
        `held_manager_instance`, and a borrowed guard is left exactly as it
        was found -- on the error path as well as the ordinary one.
        """
        from baton_v12.worker_manager import workspaces

        standing = workspaces.held_manager_instance(self._place)
        guard = workspaces.hold_manager_instance(self._control, self._place)
        borrowed = standing is not None
        try:
            yield guard
        finally:
            if not borrowed:
                # RELEASED BY THE ADMISSION THAT TOOK IT. A command is not a
                # serving manager and has no business holding an instance
                # past the operation it took it for.
                guard.release()

    @contextmanager
    def invocation(self, job_id):
        """EXCLUSIVE OWNERSHIP OF ONE ADMISSION'S EXECUTION. Review R8.

        A HOLDER IS A NAME AND THIS IS A LOCK, which is the distinction the
        candidate was missing. `fresh_attempts.holder` says which manager may
        RESUME an interrupted admission; it is a stable identity, so two
        concurrent calls under one incarnation both satisfied it and both ran
        the external effects. The instance guard did not close that gap
        either: its documented cache answers the guard this process already
        holds.

        `flock` ON THIS ADMISSION'S OWN FILE answers both halves at once. Two
        descriptors contend whether they are in two processes or two threads
        of one, so a concurrent invocation is refused rather than admitted --
        and the kernel drops the lock when a holder dies, so an INTERRUPTED
        admission leaves nothing to clear and the same request simply resumes.
        A lease with a clock would have had to guess when an unseen manager
        stopped, which is the inferred cessation this operation refuses.

        NON-BLOCKING, because a command that queued behind another admission
        would look like a slow one.
        """
        place = self._root / f".fresh-attempt.{_safe(job_id)}.invocation"
        descriptor = os.open(str(place),
                             os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as fault:
                if fault.errno not in (errno.EACCES, errno.EAGAIN,
                                       errno.EWOULDBLOCK):
                    raise
                raise ContractRefusal(
                    "refused", "precondition",
                    f"another admission of {job_id!r} is in flight on this "
                    f"host and owns its Work authorization, binding and "
                    f"submission; one of them performs those effects. Let it "
                    f"finish and run the same request again, which replays a "
                    f"completed admission and resumes an interrupted one"
                ) from None
            yield
        finally:
            os.close(descriptor)

    @classmethod
    def of(cls, control, configuration):
        """The workspace root this instance's own configuration names."""
        places = {one["deployment"].get("workspace_storage")
                  for one in configuration.get("workers") or []}
        places.discard(None)
        if len(places) != 1:
            raise BindingRefusal(
                f"this deployment's workers name {sorted(places)!r} as their "
                f"workspace storage and one instance is guarded as one root; "
                f"nothing was changed")
        return cls(control, sorted(places)[0])


def _safe(job_id):
    """A Job id as ONE path component, with nothing that could escape it."""
    return "".join(one if one.isalnum() or one in "-_." else "_"
                   for one in job_id)[:128] or "unnamed"


class HostExclusion:
    """What the Worker Manager records about each prior attempt.

    THE STORE MUST BE THIS INSTANCE'S. Review R11: absence in an arbitrarily
    supplied control store says nothing about this Job, so the handle is held
    to the path this instance's own configuration names before anything is
    read out of it, and the answer carries the host that gave it.

    ONE COMPOSED READ PER ATTEMPT, taken from `runtime_recovery_inventory`
    rather than assembled here: that reader already pairs an attempt's runtime
    axes with its workspace token, and it says in its own words that an absent
    token is "explicit uncertainty, never a synthetic non-launch proof". A
    second pairing in this file would be a second chance to get that wrong.

    ABSENCE IS REPORTED AS ABSENCE. An attempt identity the manager derived
    and this host never recorded anything under answers `None`, and what that
    means is the caller's to decide.
    """

    def __init__(self, control, expected=None):
        self._control = control
        # WHICH HOST THIS IS SUPPOSED TO BE. Review R11: absence in an
        # arbitrarily supplied control store is not evidence about this Job,
        # so the store is held to the one this instance's own configuration
        # names before a single answer is read out of it.
        self._expected = expected

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
        here = getattr(self._control, "database", None)
        if self._expected is not None \
                and os.path.realpath(str(here or "")) \
                != os.path.realpath(str(self._expected)):
            raise ContractRefusal(
                "refused", "precondition",
                f"this host's control store is {here!r} and this instance's "
                f"configuration names {self._expected!r}; evidence about a "
                f"failed execution read from another deployment's store is "
                f"evidence about another deployment")
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
        answer = {attempt_id: held.get(attempt_id)
                   for attempt_id in attempt_ids}
        # AND WHICH HOST ANSWERED, so an absence is attributable to a named
        # store rather than to "somewhere".
        answer["host"] = here
        return answer


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

    def configuration(self):
        """This instance's emitted configuration, for a caller that needs it.

        The command composes the ownership port from the same document this
        adapter binds into, and reading it twice from two places would be two
        accounts of one instance.
        """
        return self._configuration()

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
        with self._publishing():
            return self._bind(job_id, like=like, work_id=work_id)

    @contextmanager
    def _publishing(self):
        """ONE WRITER AT A TIME over this instance's configuration.

        Review R5: the first cut read, modified and prepared with nothing in
        between, through one fixed `.tmp` path -- so two admissions could
        interleave and the second could publish a document composed before
        the first one's Job existed. The instance guard excludes another
        PROCESS; this excludes another caller inside one, and both of them
        together are what make the publication effectively once.

        `flock` ON ITS OWN DESCRIPTOR, which two opens in one process contend
        for exactly as two processes do, and which the kernel releases if
        this process dies holding it.
        """
        place = self._root / ".fresh-attempt.publication"
        descriptor = os.open(str(place),
                             os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            os.close(descriptor)

    def _bind(self, job_id, *, like, work_id):
        import sys

        from tools import bootstrap

        # RE-READ INSIDE THE LOCK, because everything this composes from may
        # have been published by the caller that just released it.
        if self.binding_of(job_id) is not None:
            return self.binding_of(job_id)
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
        # A NAME THIS WRITER OWNS. One fixed `.tmp` path is a file two
        # concurrent writers would each believe was theirs; the rename onto
        # the real name is still atomic either way, but what gets renamed
        # would be whichever one finished writing last.
        temporary = Path(f"{place}.{os.getpid()}.{id(document):x}.tmp")
        try:
            temporary.write_text(json.dumps(document, indent=2,
                                            sort_keys=True) + "\n")
            temporary.replace(place)
        finally:
            if temporary.exists():
                temporary.unlink()

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
