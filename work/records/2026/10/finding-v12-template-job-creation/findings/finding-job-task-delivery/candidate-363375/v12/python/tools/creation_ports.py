"""The owners an ordinary template creation composes. W361912.

TWO OBJECTS, AND NEITHER HOLDS A RULE. `creation.create` decides; these reach
the right owner and report what it says. That split is `fresh_attempt_ports`'
and it is the same sentence from DESIGN REC-7 that produced it: "script-side
prechecks cannot substitute for manager enforcement". An adapter that decided
whether a derived profile was good enough would be the pilot's helper again
under a new name.

`DeploymentDerivation` answers the four facts an operator must not be asked
for. `NewJobBinding` is `fresh_attempt_ports.DeploymentBinding` plus the one
verb it could not have: binding a Job that has no predecessor to be derived
from. The Work authorization, the instance guard and the host exclusion are
`fresh_attempt_ports`' own classes, reused as they are -- a second copy of
`WorkAuthorization` would be a second account of the Authority.
"""

import json
from pathlib import Path

from baton_v12.contracts import ContractRefusal
from baton_v12.contracts.errors import name_value
from baton_v12.contracts.manifest import job_input_identity

from tools.fresh_attempt_ports import (BindingRefusal, DeploymentBinding,
                                       InstanceOwnership, WorkAuthorization,
                                       instance_identity)

__all__ = ["BindingRefusal", "DeploymentDerivation", "InstanceOwnership",
           "NewJobBinding", "WorkAuthorization", "instance_identity"]


class DeploymentDerivation:
    """The four Job facts this deployment holds about its installed workers.

    WHY THIS EXISTS AT ALL, in the words of the rule it serves.
    `stage_execution._disagreements` decides which configured worker may serve
    a stage by comparing, per stage, the serving worker's `launch_role`
    against the stage kind, its manifest Work against the binding's Work, its
    `profile_name` and `profile_digest` against the stage's,
    `job_input_identity(manifest)` against the Job's `input_digest`, and its
    `policy_digest` against the Job's. Four of those are operands a
    submission carries, and all four are facts about the workers somebody
    installed. So they are derived here and never typed.

    THE DOCUMENT IS READ THROUGH ITS OWNER.
    `stage_execution.held_configuration` proves a deployment document and
    REPLACES each worker's
    deployment with the owned form `single_worker` actually derives -- so
    reading the raw file and picking members out of it would derive from
    something no serving component ever sees. This asks the owner and then
    reads its answer.

    AND A DISAGREEMENT IS A REFUSAL, NOT A CHOICE. If two workers of one role
    carry different profiles, or the implementation and review lanes disagree
    about the Job input or the policy, this refuses naming both values. A port
    that picked one would be choosing a security operand for a Job, which is
    the invisible choice `ManagerOperations.admit` names in as many words.
    """

    def __init__(self, root, *, identity=None, kinds=("implementation",
                                                      "review")):
        self._root = Path(root)
        self._identity = identity
        # WHICH LANES THIS CREATION NEEDS, supplied rather than assumed. The
        # template says which stages a Job owes; a port that derived every
        # configured role would refuse a deployment whose integration worker
        # disagreed about a Job that has no integration stage.
        self._kinds = tuple(kinds)

    def instance(self):
        return self._identity

    def configuration(self):
        from tools import bootstrap

        place = Path(bootstrap.layout(self._root)["configuration"])
        if not place.exists():
            raise BindingRefusal(
                f"{place} does not exist; this instance has emitted no "
                f"deployment configuration, so there is nothing to derive a "
                f"Job's input, policy, Work or profiles from")
        return json.loads(place.read_text())

    def held(self):
        from tools import stage_execution

        return stage_execution.held_configuration(self.configuration())

    def derived(self, selection=None):
        """The derivation `creation.create` holds to a closed shape.

        W363066: AND WITH A SELECTION IT ANSWERS FOR THAT JOB'S OWN TASK.
        Without one it answers the installed facts, which is what a caller
        that only wants to know what this pool is configured for asks for.
        With one, `job_task.per_job_delivery` composes this Job's task bytes
        and the manifest that names them, and the `input_digest` answered is
        that manifest's Job-scoped identity -- so the Job the creation records
        and the document its workers will serve agree by construction rather
        than by a later comparison.
        """
        held = self.held()
        lanes = {}
        for kind in self._kinds:
            found = [one for one in held["workers"]
                     if one["role"] == kind]
            if not found:
                raise BindingRefusal(
                    f"this instance configures no {kind!r} worker, and a Job "
                    f"with a {kind} stage that no worker can serve would "
                    f"never run. Install one before creating a Job that owes "
                    f"that stage")
            lanes[kind] = found
        answer = {"work_id": self._agreed(lanes, self._work_of, "the Work"),
                  "input_digest": self._agreed(lanes, self._input_of,
                                               "the submitted input"),
                  "policy_digest": self._agreed(lanes, self._policy_of,
                                                "the submitted policy"),
                  "profiles": {kind: self._profile(kind, found)
                               for kind, found in lanes.items()}}
        if selection is None:
            return answer
        return dict(answer, **self._for_task(lanes, selection))

    def _for_task(self, lanes, selection):
        """This Job's own task, and the input identity that names it.

        THE INSTALLED TASK IS THE BASE AND EVERY LANE MUST AGREE ABOUT IT,
        for the reason the other four facts must: a Job carries one task, and
        a port that picked one lane's would be choosing which document the
        reviewer reads. `_agreed` is reused rather than restated.

        AND THE ANSWER CARRIES THE BYTES. `creation` stores them so the
        serving composition can deliver exactly these, which is what makes
        the delivery immutable: the path they were read from is never reopened
        and a later configuration change cannot move what a recorded Job runs.
        """
        from tools import job_task

        installed_task = self._agreed(lanes, self._task_of,
                                      "the installed task document")
        installed_manifest = json.loads(self._agreed(
            lanes, self._manifest_of, "the installed input manifest"))
        # THE WORK IS THIS PORT'S OWN ANSWER and is added here rather than
        # asked of the caller. A creation that had to learn the Work before it
        # could compose a selection would have to call this port twice --
        # once for the deployment's facts and once for the task -- and two
        # readings of one configuration are two chances to compose a Job from
        # halves of different ones.
        held = job_task.per_job_delivery(
            installed_task, installed_manifest,
            dict(selection,
                 work_id=self._agreed(lanes, self._work_of, "the Work")))
        return {"task_document": held["task_document"],
                "input_manifest": held["input_manifest"],
                "input_digest": job_input_identity(
                    held["input_manifest"],
                    what="a created Job's own input")}

    # -- the four derivations, each from the owned worker document ----------

    @staticmethod
    def _work_of(worker):
        return worker["deployment"]["input_manifest"]["work_ref"]["work_id"]

    @staticmethod
    def _input_of(worker):
        # THE JOB-SCOPED PROJECTION, which is the same function
        # `_disagreements` compares with. W202663 added it precisely so a
        # review worker on its own image and an implementation worker on
        # another can share ONE Job input identity; a whole-manifest digest
        # here would make every heterogeneous pool underivable.
        return job_input_identity(
            worker["deployment"]["input_manifest"],
            what="a configured worker's input")

    @staticmethod
    def _policy_of(worker):
        return worker["deployment"]["policy_digest"]

    @staticmethod
    def _task_of(worker):
        # THE HELD BYTES, which `single_worker._held` already proved against
        # this manifest's own human contract. Reading the configured PATH here
        # would be a second read of a document the owner deliberately reads
        # once, and would reopen a name that may have moved since.
        return worker["deployment"]["task_bytes"]

    @staticmethod
    def _manifest_of(worker):
        # AS CANONICAL TEXT, because `_agreed` compares with `!=` over a dict
        # key and a manifest is a document. The caller decodes the one it
        # agreed on.
        return json.dumps(worker["deployment"]["input_manifest"],
                          sort_keys=True, ensure_ascii=False)

    def _agreed(self, lanes, reading, what):
        """One value every lane's workers agree on, or a named refusal."""
        seen = {}
        for kind, found in lanes.items():
            for worker in found:
                seen.setdefault(reading(worker), []).append(
                    f"{kind}/{worker['worker_id']}")
        if len(seen) != 1:
            raise BindingRefusal(
                f"this instance's configured workers disagree about {what}: "
                + "; ".join(f"{value!r} from {', '.join(sorted(who))}"
                            for value, who in sorted(
                                seen.items(), key=lambda one: str(one[0])))
                + f". A Job carries one {what} and this port will not choose "
                f"one of them for it")
        return next(iter(seen))

    def _profile(self, kind, found):
        named = {(one["deployment"]["profile_name"],
                  one["deployment"]["profile_digest"]): one["worker_id"]
                 for one in found}
        if len(named) != 1:
            raise BindingRefusal(
                f"this instance's {kind!r} workers carry "
                f"{len(named)} different runtime profiles "
                + "; ".join(f"{profile!r} on {worker!r}"
                            for profile, worker in sorted(
                                named.items(),
                                key=lambda one: str(one[0])))
                + f". A stage requests one profile and this port will not "
                f"choose which")
        (profile_name, profile_digest), _worker = next(iter(named.items()))
        return {"profile_name": profile_name,
                "profile_digest": profile_digest}


class NewJobBinding(DeploymentBinding):
    """`DeploymentBinding`, plus binding a Job with no predecessor.

    THE INHERITED HALF IS REUSED RATHER THAN RESTATED: `binding_of`,
    `serving`, `_publishing`, `_publish_install`, `_configuration` and
    `_install` are that class's and are unchanged, so a creation and a fresh
    attempt publish through one writer lock, one atomic install write and one
    `bootstrap.prepare`.

    WHAT IS NEW IS THAT THERE IS NOTHING TO BE `like`. `DeploymentBinding.bind`
    derives the source worker, the declared base and the canonical target from
    the Job being replaced, and an ordinary creation has no such Job -- so
    those three are derived from THIS INSTANCE instead: the installed
    implementation worker is the producer, and the base and target are the
    deployment's own, read from whichever place this instance's install
    document keeps them.

    IT STILL DERIVES AND NEVER INVENTS. A deployment that names no declared
    base or no canonical target is refused naming what is missing, because a
    Job bound to a base nobody declared is one `bootstrap.prepare` would
    refuse later with a sentence about a document rather than about the
    instance.
    """

    def create_binding(self, job_id, *, work_id, template_version):
        with self._publishing():
            return self._create(job_id, work_id=work_id,
                                template_version=template_version)

    def _create(self, job_id, *, work_id, template_version):
        import sys

        from tools import bootstrap

        # RE-READ INSIDE THE LOCK, because the caller that just released it
        # may have published exactly this.
        existing = self.binding_of(job_id)
        if existing is not None:
            return existing
        document = self._install()
        jobs = [dict(one) for one in self._install_jobs(document)]
        named = {one.get("job_id") for one in jobs}
        bound = {one.get("job_id") for one in
                 (self._configuration().get("job_bindings") or [])}
        missing = sorted(one for one in bound - named if one is not None)
        if missing:
            raise BindingRefusal(
                f"this instance binds "
                f"{', '.join(repr(one) for one in missing)} and its install "
                f"document does not name "
                f"{'them' if len(missing) > 1 else 'it'}; preparing from that "
                f"document would drop a configured Job, so nothing was "
                f"changed. Reconcile install-inputs.json with "
                f"deployment.json before a Job is created here")
        if any(one.get("job_id") == job_id for one in jobs):
            # ALREADY IN THE INPUT DOCUMENT AND NOT IN THE CONFIGURATION: an
            # interrupted publication, finished by preparing the document it
            # already describes rather than by appending a second entry.
            fresh = [one for one in jobs if one.get("job_id") == job_id][0]
            if fresh.get("work_id") != work_id:
                raise BindingRefusal(
                    f"this instance's install document already names Job "
                    f"{job_id!r} on Work {fresh.get('work_id')!r} and this "
                    f"creation runs under {work_id!r}; nothing was changed")
            document = dict(document, jobs=jobs)
        else:
            document = dict(document,
                            jobs=jobs + [self._entry(document, jobs, job_id,
                                                     work_id)])
        # THE INPUT FILE FIRST, which is the inherited recovery story: an
        # input naming a Job the configuration does not yet bind is the
        # harmless direction, and `prepare` is what makes it real.
        self._publish_install(document)
        bootstrap.prepare(document,
                          stream=self._stream if self._stream is not None
                          else sys.stdout)
        return self.binding_of(job_id)

    def _entry(self, document, jobs, job_id, work_id):
        """One `bootstrap._JOB` entry, every member DERIVED from the instance.

        `_JOB` is `("job_id", "work_id", "line_declared_base",
        "canonical_target_id", "source_worker_id")` and the first two are the
        operation's. The other three are this deployment's facts and are read
        from it: from an existing Job entry when there is one, and from the
        document's own one-Job members when this is the first.
        """
        held = {"job_id": job_id, "work_id": work_id}
        for member, where in (("line_declared_base", "line_declared_base"),
                              ("canonical_target_id", "canonical_target_id")):
            found = self._carried(document, jobs, member)
            if found in (None, ""):
                raise BindingRefusal(
                    f"this instance's install document names no {where!r}, "
                    f"so a created Job has no declared base or canonical "
                    f"target to be bound to. Nothing was changed")
            held[member] = found
        producer = self._producer(document, jobs)
        held["source_worker_id"] = producer
        return held

    @staticmethod
    def _carried(document, jobs, member):
        """One deployment fact, from a Job entry or from the document.

        THE EXISTING JOBS COME FIRST, because a document that both names a
        global base and binds Jobs is a one-Job install that has grown, and
        what the bound Jobs agree on is what this instance is really running.
        """
        for one in jobs:
            if one.get(member) not in (None, ""):
                return one.get(member)
        return document.get(member)

    @staticmethod
    def _producer(document, jobs):
        """Which installed worker is this Job's producer.

        `servable_workers` narrows the implementation lane to
        `binding["source_worker_id"]` BY IDENTITY -- "a Job names its
        producer, and another worker that merely agrees on every digest is
        still some other Job's source" -- so this member decides whether the
        created Job's implementation stage can be served at all.
        """
        for one in jobs:
            if one.get("source_worker_id") not in (None, ""):
                return one.get("source_worker_id")
        from tools import bootstrap

        found = [one for one in bootstrap.workers_of(document)
                 if one.get("role") == "implementation"]
        if len(found) != 1:
            raise BindingRefusal(
                f"this instance's install document names {len(found)} "
                f"implementation workers and a created Job names exactly one "
                f"producer; the implementation lane is narrowed to that "
                f"worker by identity, so this port will not choose which")
        return found[0]["worker_id"]


def agreeing(named, supplied, what, identity):
    """A caller's store operand held to the instance that owns it.

    `fresh_attempt_ports._agreeing` with a creation's sentence. Exported
    because the command composes the same four stores and the check that a
    name is not merely compared with itself is the one W359719 R14 was
    corrected for.
    """
    import os

    if os.path.realpath(str(supplied)) != identity[named]:
        raise ContractRefusal(
            "refused", "precondition",
            f"the {what} this command was given is {str(supplied)!r} and "
            f"instance {identity['root']!r} owns {identity[named]!r}; an "
            f"ordinary Job is created in the instance whose workers will "
            f"serve it, and a store that belongs to another deployment "
            f"answers for another deployment")
    return identity[named]


def check_text(value, what):
    """One non-empty string operand, named."""
    if type(value) is not str or value == "":
        raise ContractRefusal("integrity", "schema",
                              f"{what} is text; this is {name_value(value)}")
    return value
