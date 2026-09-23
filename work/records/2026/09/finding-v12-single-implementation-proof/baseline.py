"""The bounded one-shot supervisor for W239528's single implementation proof.

WHAT THIS JOB IS, AND WHY IT IS NOT THE OTHER ONE. Owner decision
`../finding-v12-managed-session-resume/OWNER-SPLIT-20260922.md`: "we need to
split the job, then run these separately". W239528 owns ONE implementation
container -- implementation requirements only, one proposal, a real stop, and
positive cleanup. The independent review of that proposal is W239533's own run,
and the restored-context correction is W236087's. So there is no review stage
here, no correction, no restore, and no disposition: a member this file does
not carry is a decision, not an omission.

WHAT IT ESTABLISHES, in the FINDING's words:

    "one implementation-only task through the real manager and worker adapter;
    explicit provider edit/verification versus adapter commit/publication
    ownership; independently inspected, attributed proposal bytes; stopped
    execution and positive cleanup. No reviewer container, correction or resume
    in this run. Do not count model prose as proposal acceptance or quiescence
    as cleanup."

Each clause is a check below, and the third is the one W236087's live run made
necessary. That run's provider committed its own history inside the container;
`ClaudeAgent._unmoved` refused to adopt it and the turn faulted with nothing
published. See `DIAGNOSIS-239528.md`. A baseline that asked only "was a
proposal retained" would pass on a proposal nobody could attribute, so
`line_attribution` reads the commit object out of the manager's own durable
line and proves the ADAPTER authored it, one commit on top of the declared
base.

WHERE THIS CODE CAME FROM, stated because reuse without provenance is just
copying. Its packet validation, admission gate, termination discipline,
cancellation seam and cleanup accounting are W236087's `supervisor.py` reduced
to one stage; that file stays where it is, unedited, and `PROVENANCE-239528.md`
records the digest it was taken from. The split ruling is why this is a
separate module rather than an import: W236087 continues to change for resume,
and a baseline proof that moved when it did would not be a baseline.

WHAT IT WILL NOT DO, each absence a decision:

  * It never retries. A failed turn, a refused act, an exhausted cap or an
    exceeded bound ends the run.
  * It never certifies a production profile, enables anything, or advances a
    deployment.
  * It never reports success it cannot prove. Every ending it calls successful
    rests on a POSITIVE committed record read back out of the manager's own
    journal; absence, uncertainty and a `failed` cleanup are all held.
  * It reads Git and never writes it. `line_attribution` runs `cat-file` and
    `rev-parse` against a repository the manager owns; the verbs are checked
    against a closed list before the child is started.
  * It performs no Git operation on any repository of record and mutates no
    coordination store.

THE SEAMS. `serve`'s `clock`/`sleep`/`should_continue` and
`stage_execution.operations_from`'s engine/credential/checkout operands are the
accepted injection points, and `supervise` takes an already-composed operations
object for exactly that reason: the deterministic verification drives THIS code
with the accepted simulated engine and provider, and the live command composes
the same code over the production ones. There is no second controller and no
test-only branch.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

__all__ = ["PACKET_SCHEMA", "OUTCOME_SCHEMA", "CANCEL_CAPABILITY",
           "SupervisorRefusal", "SupervisorInterrupted",
           "AdmissionGate", "held_packet", "verify_imported_sources",
           "verify_worker_image", "survey", "prepare", "supervise",
           "line_attribution", "main"]

PACKET_SCHEMA = "baton.single-implementation-packet/1"
OUTCOME_SCHEMA = "baton.single-implementation-outcome/1"

# The cleanup endings the manager's own axis calls POSITIVE. `failed` is a
# committed record too, and it is not one of these on purpose: a destroy that
# settled `failed` is a runtime this manager could not prove gone.
POSITIVE_CLEANUP = ("complete", "retained")

# THE ONE STAGE KIND THIS PACKET SERVES, closed. W239528 submits an
# implementation stage and stops. A `review` stage reaching the admission gate
# is not a smaller version of this run -- it is the NEXT Job's workload
# arriving in this one -- so it is refused by name rather than admitted under
# whichever cap happens to be spare.
KINDS = ("implementation",)

# The worker's own claim namespace and commit identity, mirrored here rather
# than imported. `claude_agent` runs INSIDE the image on its own import path,
# and a host program that imported it would be reaching across the boundary the
# delivery exists to cross. The deterministic verification asserts that these
# three copies and the adapter's agree, so a drift is a failing test rather
# than a baseline quietly proving attribution against the wrong name.
CLAIM_NAMESPACE = "baton.git-proposal/1"
COMMIT_NAME = "Baton worker"
COMMIT_EMAIL = "worker@baton.invalid"

# THE ONLY GIT VERBS THIS PROGRAM MAY RUN, closed and checked before the child
# starts. Every one of them reads; none of them can move a reference, write an
# object or touch a worktree. AGENTS.md permits reviewing history and nothing
# else, and a closed list is how that rule survives a later edit to this file.
GIT_READS = ("cat-file", "rev-parse", "rev-list")

_PACKET = ("schema", "run_id", "work", "claim", "note", "worker_image",
           "manager_runtime", "manager_source", "supervisor", "code_boundary",
           "deployment", "context", "submission", "fixture", "bounds",
           "outcome_path")
# NO `review_invocations` AND NO `corrections`. Carrying them as zeroes would
# have described this run as a correction that happens to make none; it is a
# different workload, and the packet says so by not having the members.
_BOUNDS = ("turn_seconds", "total_seconds", "cleanup_seconds",
           "implementer_invocations", "retry")
_DEPLOYMENT = ("config_path", "config_sha256", "job_store", "control_store",
               "authority_store", "authority_uuid", "state_root")
_CONTEXT = ("storage_path", "excluded_roots", "runtime_uid", "profile_path",
            "profile_sha256", "profile_digest", "job_id")
_IMAGE = ("reference", "config_digest", "worker_files")
_RUNTIME = ("path", "executable_sha256", "build_commit")
_SOURCE = ("path", "packages", "file_count", "files")
_SELF = ("path", "sha256")
_SUBMISSION = ("path", "sha256", "job_id")
_FIXTURE = ("source_root", "files")


class SupervisorRefusal(Exception):
    """Refusal in this program's own words. Never a partial run's excuse."""


class SupervisorInterrupted(BaseException):
    """Ctrl-C or SIGTERM, AFTER the shutdown accounting has been retained.

    A `BaseException` on purpose: an interruption is not an ordinary failure a
    caller may absorb, and the operator who sent it is owed the process exiting.
    The retained outcome travels on `.outcome` so a caller that does want to
    read what the run left behind can, without the interrupt being swallowed.
    """

    def __init__(self, why, outcome):
        super().__init__(why)
        self.outcome = outcome


class Termination:
    """One installed handler, with two modes and a memory.

    While a run is serving, a signal raises and ends the loop, which is what an
    operator asking it to stop means. Once admission has closed, the remaining
    work is the accounting that exists to leave nothing unexplained -- so a
    signal there is RECORDED and execution continues, and `supervise` raises
    `SupervisorInterrupted` after the outcome is retained. Deferring the whole
    shutdown rather than catching at each read is the point: the shutdown
    performs several reads, and the next one added would otherwise have the
    same hole.

    NOT A SIGKILL CLAIM, and no promise about a signal delivered before this is
    installed or after it is restored.
    """

    __slots__ = ("received", "_mode", "_previous")

    def __init__(self):
        self.received = []
        self._mode = "raise"
        self._previous = {}

    def install(self):
        """BEST EFFORT. `signal.signal` refuses outside the main thread, and a
        supervisor that declined to run there would be refusing for its own
        convenience rather than for the run's safety."""
        import signal

        for number in (getattr(signal, "SIGTERM", None),
                       getattr(signal, "SIGINT", None)):
            if number is None:
                continue
            try:
                self._previous[number] = signal.signal(number, self._handle)
            except (ValueError, OSError, RuntimeError):
                continue
        return self

    def restore(self):
        import signal

        for number, previous in list(self._previous.items()):
            try:
                signal.signal(number, previous)
            except (ValueError, OSError, RuntimeError):
                pass
        self._previous.clear()

    def defer(self):
        """Stop raising. Every later signal is remembered, not thrown."""
        self._mode = "defer"

    @property
    def why(self):
        return "; ".join(self.received) or None

    def _handle(self, number, frame):
        del frame
        said = f"signal {number}"
        self.received.append(said)
        if self._mode == "raise":
            raise KeyboardInterrupt(said)


def _guarded(thunk, default, *, what, uncertainty, interrupted):
    """Run one shutdown step; never let it abandon the shutdown.

    The failure is named as an uncertainty, which is a reason to hold, and the
    remaining steps still run. `BaseException` deliberately: an interruption
    arriving inside a read is recorded so `supervise` can re-raise it once the
    outcome is on disk.
    """
    try:
        return thunk()
    except BaseException as failure:                         # noqa: BLE001
        said = f"{type(failure).__name__}: {failure}"
        uncertainty.append(f"{what} did not complete: {said}")
        if not isinstance(failure, Exception):
            interrupted.append(said)
        return default


# THE CAPABILITY A DEPLOYMENT OFFERS FOR STOPPING WHAT IS STILL EXECUTING.
# `attempts.request_cancellation` is the accepted manager-owned path -- fence
# at the Authority, then the agent's cancel and the adapter's stop -- and it
# needs the port, agent and adapter the COMPOSITION holds per attempt. So the
# supervisor asks the composed deployment for this named method rather than
# reaching for another object's private handles, and says so plainly when the
# composition does not carry one.
CANCEL_CAPABILITY = "cancel_attempt"

# THE TWO RUNTIME AXIS VALUES THAT MEAN THERE IS NOTHING LEFT TO STOP. Every
# other value -- `not-started`, `start-requested`, `running`, `stopping`,
# `cancel-requested`, `uncertain` -- is a runtime this manager may still have
# to order stopped, and `uncertain` above all: an ambiguous inspection is not
# permission to leave a container running.
GONE = ("destroyed",)


def _refuse(message):
    raise SupervisorRefusal(message)


def _document(value, what, members):
    if type(value) is not dict:
        _refuse(f"{what} is one JSON object; this is "
                f"{type(value).__name__}")
    missing = sorted(one for one in members if one not in value)
    extra = sorted(one for one in value if one not in members)
    if missing or extra:
        _refuse(f"{what} names exactly {', '.join(members)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""))
    return value


def _digest_of_file(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            reading.update(block)
    return reading.hexdigest()


def _pin(path, expected, what):
    """One named file, at the exact bytes the packet was signed over."""
    if not os.path.isabs(path):
        _refuse(f"{what} is named by an absolute path; this is {path!r}")
    try:
        found = _digest_of_file(path)
    except OSError as failure:
        _refuse(f"{what} could not be read at {path!r}: {failure.strerror}")
    if found != expected:
        _refuse(f"{what} at {path!r} is sha256 {found}, and this packet is "
                f"bound to {expected}")
    return found


def _whole_number(value, what, *, minimum=1, maximum=86400):
    if type(value) is not int or not minimum <= value <= maximum:
        _refuse(f"{what} is a whole number of seconds in "
                f"[{minimum}, {maximum}]; this is {value!r}")
    return value


def _relative(name, what):
    if os.path.isabs(name) or os.path.normpath(name) != name \
            or name.startswith(".."):
        _refuse(f"{what} {name!r} is one relative canonical path")
    return name


def _object_name(value, what):
    if type(value) is not str or len(value) != 40 \
            or any(one not in "0123456789abcdef" for one in value):
        _refuse(f"{what} is one full lower-case object name; this is "
                f"{value!r}")
    return value


def held_packet(path):
    """Read the packet and PROVE every artifact it binds, before anything opens.

    Nothing durable is touched here and no store is opened: a packet whose
    fixture bytes, deployment configuration, submission, context profile,
    manager source or supervisor program have moved since it was reviewed is
    refused with the artifact named, which is the difference between running a
    reviewed packet and running whatever is on disk under its name.
    """
    with open(path, "rb") as handle:
        packet = json.loads(handle.read().decode("utf-8"))
    _document(packet, "the single-implementation packet", _PACKET)
    if packet["schema"] != PACKET_SCHEMA:
        _refuse(f"this supervisor reads {PACKET_SCHEMA!r}; the packet names "
                f"{packet['schema']!r}")

    bounds = _document(packet["bounds"], "the packet's bounds", _BOUNDS)
    _whole_number(bounds["turn_seconds"], "the per-turn bound")
    _whole_number(bounds["total_seconds"], "the overall bound")
    _whole_number(bounds["cleanup_seconds"], "the reserved cleanup bound")
    if bounds["retry"] is not False:
        _refuse("this supervisor never retries; the packet's bounds must say "
                "so with `retry: false`")
    # EXACTLY ONE, AND THE NUMBER IS NOT A RANGE. This Job is one container
    # answering one implementation question. Two implementer turns would be a
    # correction, which is W236087's Job and needs a review to correct against;
    # zero is a run that answers nothing. Both are refused before a store opens
    # rather than discovered in the outcome.
    if bounds["implementer_invocations"] != 1:
        _refuse(f"this packet drives ONE implementation container; its bounds "
                f"declare {bounds['implementer_invocations']!r} implementer "
                f"invocation(s). A correction round belongs to the resume Job.")
    if bounds["cleanup_seconds"] >= bounds["total_seconds"]:
        _refuse("the reserved cleanup bound is inside the overall bound, not "
                "beside it")

    deployment = _document(packet["deployment"], "the packet's deployment",
                           _DEPLOYMENT)
    _pin(deployment["config_path"], deployment["config_sha256"],
         "the deployment configuration")

    context = _document(packet["context"], "the packet's context selection",
                        _CONTEXT)
    _pin(context["profile_path"], context["profile_sha256"],
         "the context profile document")
    if type(context["excluded_roots"]) is not list \
            or not all(type(one) is str and os.path.isabs(one)
                       for one in context["excluded_roots"]):
        _refuse("the context storage's excluded roots are absolute paths")
    if type(context["runtime_uid"]) is not int or context["runtime_uid"] < 0:
        _refuse("the context storage names one runtime uid")

    submission = _document(packet["submission"], "the packet's submission",
                           _SUBMISSION)
    _pin(submission["path"], submission["sha256"], "the Job submission")

    fixture = _document(packet["fixture"], "the packet's fixture", _FIXTURE)
    if type(fixture["files"]) is not dict or not fixture["files"]:
        _refuse("the fixture names at least one file and its digest")
    for name, expected in sorted(fixture["files"].items()):
        _relative(name, "the fixture file")
        _pin(os.path.join(fixture["source_root"], name), expected,
             f"the fixture file {name!r}")

    image = _document(packet["worker_image"], "the packet's worker image",
                      _IMAGE)
    if type(image["worker_files"]) is not dict or not image["worker_files"]:
        _refuse("the worker image binds the effective worker bytes it carries")

    runtime = _document(packet["manager_runtime"],
                        "the packet's manager runtime", _RUNTIME)
    _pin(os.path.join(runtime["path"], "baton-v12-stack"),
         runtime["executable_sha256"], "the installed manager runtime")

    # THE CODE THAT ACTUALLY RUNS, bound as its own artifact. The frozen
    # runtime above is the INSTALLATION -- it owns the stores' layout and is
    # what `just start` would execute -- and pinning it said nothing about the
    # modules this process imports. Both are named, and only this one is
    # claimed to be the supervising implementation.
    source = _document(packet["manager_source"],
                       "the packet's manager source", _SOURCE)
    if type(source["packages"]) is not list or not source["packages"] \
            or any(type(one) is not str or not one
                   for one in source["packages"]):
        _refuse("the manager source names the packages it provides")
    if type(source["files"]) is not dict or not source["files"]:
        _refuse("the manager source binds the files it is made of")
    if source["file_count"] != len(source["files"]):
        _refuse(f"the manager source declares {source['file_count']} files "
                f"and binds {len(source['files'])}")
    for name, expected in sorted(source["files"].items()):
        _relative(name, "the manager source file")
        _pin(os.path.join(source["path"], name), expected,
             f"the manager source file {name!r}")

    program = _document(packet["supervisor"], "the packet's supervisor", _SELF)
    _pin(program["path"], program["sha256"], "the supervisor program")

    # THE CODE TREE MUTABLE STATE MAY NOT BE WRITTEN INTO, bound rather than
    # inferred. `stage_execution._checkout` walks three parents above its own
    # `__file__` when no boundary is given, which answers this distribution's
    # working tree for an ordinary checkout and answers the RUN ROOT'S PARENT
    # for a relocated manager source. One bound value, used by both ends.
    boundary = packet["code_boundary"]
    if type(boundary) is not str or not os.path.isabs(boundary) \
            or os.path.normpath(boundary) != boundary:
        _refuse(f"the code boundary is one absolute canonical directory; this "
                f"is {boundary!r}")
    if not os.path.isdir(boundary):
        _refuse(f"the code boundary {boundary!r} is not a directory")
    # AND THIS RUN'S OWN MUTABLE STATE IS OUTSIDE IT, checkable from the packet
    # alone, before a store is opened, rather than discovered at composition.
    whole = os.path.realpath(boundary)
    for what, place in (("the Job store", deployment["job_store"]),
                        ("the control store", deployment["control_store"]),
                        ("the deployment state root", deployment["state_root"]),
                        ("the context storage", context["storage_path"]),
                        ("the retained outcome",
                         os.path.dirname(packet["outcome_path"]))):
        held = os.path.realpath(place)
        if os.path.commonpath([whole, held]) == whole:
            _refuse(f"{what} at {place!r} is inside the code boundary "
                    f"{boundary!r}; mutable deployment state is never written "
                    f"into the tree the code lives in, and composition would "
                    f"refuse this after the owner acts had already committed")

    if context["job_id"] != submission["job_id"]:
        _refuse("the qualification grant and the submission name different "
                "Jobs; one grant serves exactly one Job")
    return packet


def verify_imported_sources(packet, *, modules=None, program=None):
    """The modules REALLY IMPORTED are the reviewed ones.

    `held_packet` hashes files on disk. That is not the same statement as "this
    process is running them": Python resolves `baton_v12` and `tools` through
    `sys.path`, and a checkout earlier on that path would supply different code
    while every pinned digest still verified. So this asks the imported module
    objects where they came from, and refuses anything resolved outside the
    bound source tree.

    CALLED BEFORE ANY STORE IS OPENED, which is the only moment at which
    refusing is free.
    """
    root = os.path.realpath(packet["manager_source"]["path"])
    names = list(packet["manager_source"]["packages"]) if modules is None \
        else list(modules)
    resolved = {}
    for name in names:
        module = sys.modules.get(name)
        if module is None:
            __import__(name)
            module = sys.modules[name]
        places = [os.path.realpath(one)
                  for one in (list(getattr(module, "__path__", []))
                              or [getattr(module, "__file__", "") or ""])]
        if not places or any(not one for one in places):
            _refuse(f"the imported package {name!r} names no location, so "
                    f"this process cannot say which bytes it is running")
        for place in places:
            if os.path.commonpath([root, place]) != root:
                _refuse(f"the imported package {name!r} resolves to {place!r}, "
                        f"outside the bound manager source {root!r}; the "
                        f"reviewed bytes are not the bytes this process runs")
        resolved[name] = places

    # AND THIS PROGRAM ITSELF, which is outside that tree. A supervisor whose
    # own bytes moved is not the reviewed supervisor however well its
    # dependencies verify.
    here = os.path.realpath(__file__ if program is None else program)
    _pin(os.path.realpath(packet["supervisor"]["path"]),
         packet["supervisor"]["sha256"], "the supervisor program")
    if here != os.path.realpath(packet["supervisor"]["path"]):
        _refuse(f"this process is running {here!r} and the packet binds "
                f"{packet['supervisor']['path']!r}")
    return resolved


def verify_worker_image(packet, *, image_inspect):
    """The artifact really is the one the packet names, asked of the engine.

    `image_inspect(reference)` answers the engine's own document. A packet whose
    image is absent, or whose configuration digest has moved, is refused here --
    before an Authority is opened -- rather than discovered by a container that
    started with the wrong worker bytes in it.
    """
    image = packet["worker_image"]
    found = image_inspect(image["reference"])
    if type(found) is not dict:
        _refuse(f"the engine answered no document for image "
                f"{image['reference']!r}")
    if found.get("Id") != image["config_digest"]:
        _refuse(f"image {image['reference']!r} is {found.get('Id')!r} and this "
                f"packet is bound to {image['config_digest']!r}")
    return found


def _workspace_root(packet):
    """The one workspace store this deployment's workers are configured with.

    `configure_context_storage` reads `configured_workspace_storage`
    immediately -- the context roots are checked for containment against the
    workspace root -- so a fresh run has a prerequisite the operator document
    would otherwise have to remember.

    DERIVED FROM THE DEPLOYMENT, NOT CHOSEN. This reads the configuration the
    packet is bound to and takes the root its workers already name; a caller
    root of this program's own choosing would be exactly the arbitrary
    selection the boundary exists to refuse.
    """
    with open(packet["deployment"]["config_path"], "rb") as handle:
        configuration = json.loads(handle.read().decode("utf-8"))
    workers = configuration.get("workers")
    if type(workers) is not list or not workers:
        _refuse("the deployment configuration names no worker, so it names no "
                "workspace store for this run to be prepared with")
    roots = set()
    for one in workers:
        held = (one.get("deployment") or {}).get("workspace_storage")
        if type(held) is not str or not os.path.isabs(held):
            _refuse(f"worker {one.get('worker_id')!r} names no absolute "
                    f"workspace storage")
        roots.add(held)
    if len(roots) != 1:
        _refuse(f"this deployment's workers name {len(roots)} workspace "
                f"stores ({', '.join(sorted(roots))}); one manager holds one, "
                f"and choosing between them is not this program's decision")
    return roots.pop()


def prepare(control, packet):
    """The four owner acts, in the order the admission boundary requires.

    IDEMPOTENT BY CONSTRUCTION AND NOT BY A FLAG. Each of these is a journalled
    operation whose identity is derived from its own operands, so repeating this
    program's preparation after an interrupted run replays what committed rather
    than composing a second storage, a second profile or a second grant.

    THE GRANT IS NOT CONSUMED HERE. Consumption commits inside the opening
    admission, which is what makes it exactly-once across a crash -- and what
    makes a spent grant a new run identity's problem rather than a replay.
    """
    from baton_v12.worker_manager import context_delivery, provider_context
    from baton_v12.worker_manager import workspaces

    selection = packet["context"]
    with open(selection["profile_path"], "rb") as handle:
        profile = json.loads(handle.read().decode("utf-8"))

    # THE WORKSPACE STORE FIRST, because the context storage's own containment
    # checks read it. Re-affirming the same root is a no-op that commits, and a
    # manager already holding attempts under a DIFFERENT root refuses here --
    # that refusal is the point and is not bypassed.
    workspace = _workspace_root(packet)
    workspaces.configure_workspace_storage(control, workspace)

    context_delivery.configure_context_storage(
        control, selection["storage_path"],
        excluded_roots=list(selection["excluded_roots"]),
        runtime_uid=selection["runtime_uid"])
    certified = provider_context.certify_context_profile(control, profile)
    if certified["profile_digest"] != selection["profile_digest"]:
        _refuse(f"the certified profile is "
                f"{certified['profile_digest']!r} and this packet is bound to "
                f"{selection['profile_digest']!r}")
    if profile.get("qualification") != "candidate":
        _refuse("this supervisor drives ONE candidate qualification run; the "
                f"packet's profile is {profile.get('qualification')!r}")
    grant = provider_context.authorize_qualification_run(
        control, run_id=packet["run_id"],
        profile_digest=selection["profile_digest"],
        storage_path=selection["storage_path"],
        authority_uuid=packet["deployment"]["authority_uuid"],
        job_id=selection["job_id"], note=packet["note"])
    return {"workspace_storage": workspace,
            "profile_digest": certified["profile_digest"],
            "qualification_run": grant["run_id"],
            "storage_path": selection["storage_path"]}


def survey(job, packet):
    """What this Job store ALREADY holds, read BEFORE any owner act.

    Review 2026-09-22T15:32:51Z R2, and both halves of it.

    THE COLLISION IS REFUSED HERE BECAUSE HERE IS BEFORE. A Job identity is
    recorded once -- `submit` refuses a second submission reusing one, saying
    "one Job identity names one pipeline" -- and this program used to reach
    that refusal at step 4 of `_supervise`, which is AFTER `prepare` has
    configured storage, certified a profile and minted a one-run qualification
    grant. Those acts commit. Discovering the collision afterwards means
    spending a grant on a run that cannot submit, and a candidate grant is
    exactly-once. `job_rows` and `stage_rows` are pure reads over the open
    store, so asking first costs nothing.

    AND EVERY OTHER JOB IS NAMED RATHER THAN ASSUMED ABSENT. The reviewer's
    second point: `_attempts_of` filters the status projection to the selected
    Job, so a runtime belonging to a DIFFERENT Job in the same store is not
    part of this run's attempt accounting, its cancellation or its cleanup --
    and the operator document previously implied it would be. What this run
    can honestly do is say which other Jobs the store holds and state plainly
    that it accounts for none of them. That is what `accounting_scope` in the
    outcome is.

    A PURE READ. It opens nothing, writes nothing and journals nothing.
    """
    from baton_v12.job_manager import job_rows, stage_rows

    selected = packet["submission"]["job_id"]
    recorded = {one["job_id"]: one for one in job_rows(job)}
    if selected in recorded:
        _refuse(
            f"this Job store already records {selected!r}, submitted by "
            f"{recorded[selected]['submission_id']!r}. One Job identity names "
            f"one pipeline, so this packet cannot be submitted here -- and a "
            f"run identity is not a Job identity: composing a fresh `run_id` "
            f"over a reused Job id collides exactly like this. Select an "
            f"unused Job store or compose a Job id this store does not hold. "
            f"Refused BEFORE the owner acts, so no qualification grant was "
            f"spent on it.")
    stages = {}
    for one in stage_rows(job):
        if one["job_id"] == selected:
            continue
        stages.setdefault(one["job_id"], []).append(one["kind"])
    return {"selected_job": selected,
            "preexisting_jobs": sorted(one for one in recorded),
            "preexisting_stages": {one: sorted(stages[one])
                                   for one in sorted(stages)},
            "accounting_scope": (
                f"this run accounts for Job {selected!r} and for nothing "
                f"else. Attempt discovery, cancellation and cleanup all read "
                f"the status projection filtered to that Job, so a runtime "
                f"belonging to another Job in this store is NOT covered by "
                f"this outcome and its absence is NOT established by it.")}


class AdmissionGate:
    """The operations object, with admission BOUNDED and STOPPABLE.

    WHY A PROXY RATHER THAN A FLAG THE LOOP CHECKS. `job_manager.serve` calls
    `sweep` and only THEN returns to the stop predicate, so a predicate is a
    decision taken one whole tick after the act it meant to prevent. The
    manager reaches admission through exactly three calls on this object --
    `admit` issues the offer, `claim` takes it and `launch` starts the runtime
    -- so refusing them here is the earliest point at which "no more runtimes"
    is a fact rather than an intention. Everything else it calls settles work
    that already exists and is forwarded untouched, which is what lets the
    cleanup window keep driving endings without being able to start anything.

    THE REFUSAL IS AN ORDINARY `ContractRefusal`. `manager._delegate` records a
    non-durable refusal as a deferral and `_start` contains one as `deferred`,
    so a gated tick is a level-triggered condition the manager already knows how
    to report -- not an exception that ends the sweep with endings unsettled.

    EVERY STARTED RUNTIME IS RECORDED AT THE CALL, before delegating: a launch
    that then faults is still a runtime this run must account for, and a set
    reconstructed from the status projection between ticks loses it.

    AND ADMISSION IS SCOPED TO ONE JOB. Review 2026-09-22T15:32:51Z R2: `serve`
    sweeps the STORE, not this packet's Job, so a store holding an earlier
    Job's eligible stage would have had that stage admitted here -- spending
    this run's single implementation cap on somebody else's workload and
    starting a container against it. The caps are counted by KIND, so nothing
    about them would have noticed. A stage naming another Job is refused
    without ever reaching the composed deployment, and that refusal is recorded
    in `foreign` rather than in `refusals`: it is the boundary working, not a
    reason to end this run, and treating it as a cap refusal would let any
    unrelated Job in the store abort a correct one.
    """

    __slots__ = ("_operations", "_caps", "_job_id", "admissions", "launched",
                 "stage_kinds", "stage_jobs", "refusals", "foreign", "stopped")

    def __init__(self, operations, *, caps, job_id=None):
        self._operations = operations
        self._caps = dict(caps)
        self._job_id = job_id
        self.admissions = {kind: 0 for kind in self._caps}
        self.launched = {}
        self.stage_kinds = {}
        self.stage_jobs = {}
        self.refusals = []
        self.foreign = []
        self.stopped = False

    # -- the three admitting acts -------------------------------------------

    def admit(self, stage, job):
        kind = stage.get("kind") if type(stage) is dict else None
        self._ours("admit", stage, kind)
        self._allowed("admit", kind)
        cap = self._caps.get(kind)
        if cap is None:
            self._deny("admit", f"this packet serves {', '.join(self._caps)} "
                                f"and a {kind!r} stage reached the admission "
                                f"gate")
        if self.admissions[kind] >= cap:
            self._deny("admit", f"the packet declares {cap} {kind} "
                                f"invocation(s) and all of them are spent")
        answer = self._operations.admit(stage, job)
        # COUNTED AFTER THE ACT COMMITTED. A refused admission is not an
        # invocation, and counting the attempt would retire a cap nobody used.
        self.admissions[kind] += 1
        if type(stage) is dict and stage.get("stage_id") is not None:
            self.stage_kinds[stage["stage_id"]] = kind
            self.stage_jobs[stage["stage_id"]] = stage.get("job_id")
        return answer

    def claim(self, stage):
        kind = stage.get("kind") if type(stage) is dict else None
        self._ours("claim", stage, kind)
        self._allowed("claim", kind)
        return self._operations.claim(stage)

    def launch(self, attempt, job):
        kind = None
        if type(attempt) is dict:
            # FOREIGNNESS IS DECIDED BEFORE THE LAUNCH IS RECORDED. An attempt
            # this gate never admitted is not one this run started, and
            # recording it would put another Job's runtime into this run's
            # cleanup obligation.
            self._ours("launch", attempt, None)
            kind = self.stage_kinds.get(attempt.get("stage_id"))
            if attempt.get("attempt_id") is not None:
                self.launched[attempt["attempt_id"]] = kind
        self._allowed("launch", kind)
        return self._operations.launch(attempt, job)

    # -- everything else is the composed deployment's, untouched ------------

    def __getattr__(self, name):
        return getattr(self._operations, name)

    @property
    def canonical(self):
        return self._operations.canonical

    # -- the gate itself -----------------------------------------------------

    def stop(self):
        """Close admission. Idempotent, and it settles nothing by itself."""
        self.stopped = True

    @property
    def exhausted(self):
        return [kind for kind, cap in self._caps.items()
                if self.admissions.get(kind, 0) >= cap]

    def _ours(self, act, document, kind):
        """Refuse an act for a stage or attempt belonging to another Job.

        `launch` is handed an ATTEMPT, which carries no `job_id`; what it
        carries is the `stage_id` this gate recorded when it admitted the
        stage. An attempt whose stage this gate never admitted is therefore
        foreign by construction, which is the conservative answer and the
        correct one: this run did not start it.
        """
        if self._job_id is None or type(document) is not dict:
            return
        if act == "launch":
            held = document.get("stage_id")
            if held is not None and held in self.stage_jobs:
                return
            said = (f"attempt on stage {held!r}, which this run never "
                    f"admitted")
        else:
            if document.get("job_id") == self._job_id:
                return
            said = f"{kind!r} stage of Job {document.get('job_id')!r}"
        from baton_v12.contracts import ContractRefusal

        why = (f"this run serves Job {self._job_id!r} and this is a {said}. "
               f"The serving loop sweeps the whole store; this packet's "
               f"workload is one Job, and admitting another one's stage would "
               f"spend this run's invocation on it and start a container "
               f"against work nobody selected here.")
        self.foreign.append({"act": act, "why": why})
        raise ContractRefusal(
            "refused", "precondition",
            f"the single-implementation supervisor refuses to {act}: {why}")

    def _allowed(self, act, kind):
        if self.stopped:
            self._deny(act, "admission is closed for this run")
        del kind

    def _deny(self, act, why):
        from baton_v12.contracts import ContractRefusal

        self.refusals.append({"act": act, "why": why})
        raise ContractRefusal(
            "refused", "precondition",
            f"the single-implementation supervisor refuses to {act}: {why}")


def _attempts_of(job, operations, job_id):
    """Every attempt identity this Job's stages have held, live and historical.

    A PURE READ: it opens nothing and writes nothing, which is why it is safe
    to repeat after a fault.
    """
    from baton_v12.job_manager import status

    document = status(job, operations, observed_at=_moment())
    seen, states, limits = {}, {}, None
    for entry in document["jobs"]:
        if entry["job_id"] != job_id:
            continue
        limits = entry.get("execution_limits")
        for stage in entry["stages"]:
            states[stage["kind"]] = stage["state"]
            for attempt in [stage.get("attempt_id")] + [
                    one.get("attempt_id") for one in stage.get("episodes", [])]:
                if attempt is not None:
                    seen[attempt] = stage["kind"]
    return seen, states, limits


def _terminal(states):
    """The one-Job stop condition, in the projection's own vocabulary.

    `exceptional` is terminal for THIS run because this run has no retry: a
    stage the manager cannot advance is the end of the baseline, and going on
    would be the automatic second attempt the packet excludes. `completed` on
    every configured stage is the other ending, and it is a STOP rather than a
    success -- what makes a run successful is decided by `_workload_evidence`,
    not by the projection.
    """
    if not states:
        return None
    if any(state == "exceptional" for state in states.values()):
        return "exceptional"
    if all(state == "completed" for state in states.values()):
        return "completed"
    return None


# HOW MANY CONSECUTIVE UNCHANGED TICKS MEAN NOTHING IS GOING TO HAPPEN.
# W239528, owner pass 243171. The successful baseline run reached a state it
# could never leave -- the provider completed, the adapter published an
# attributed proposal, the runtime was destroyed and its cleanup committed, and
# then the composed stage held its ending because the provider context could
# not be sealed. Nothing after that point could change, and the supervisor
# swept for 443 seconds of a 900-second bound until an operator pressed Ctrl-C.
#
# A BOUND IS A BACKSTOP, NOT A DETECTOR. Shortening it would have made the same
# non-answer arrive sooner; what was missing is noticing that the run had
# stopped moving. So this counts CONSECUTIVE IDENTICAL observations of the
# canonical state, and every condition below has to hold for all of them.
#
# SIX, AND THE NUMBER IS ARGUED RATHER THAN PICKED. `serve` ticks at one
# second, so six is six seconds of a run that is doing nothing -- long enough
# that an ending mid-flight across several journalled operations is not
# mistaken for a stall, short enough that an operator is not watching a dead
# run. It is deliberately not one: a single tick between two acts of the same
# ending is ordinary.
STALLED_TICKS = 6


def _observation(states, attempts, cleanup):
    """What "unchanged" MEANS, as a comparable value.

    The stage states, the accountable attempt identities and the cleanup axis
    of each. If any of the three moves, the run is progressing -- an ending
    that commits one more step changes the cleanup axis, and an admission
    changes the attempt set.
    """
    return (tuple(sorted(states.items())),
            tuple(sorted(attempts)),
            tuple(sorted((one, str(held.get("cleanup")))
                         for one, held in sorted(cleanup.items()))))


def _moment():
    moment = datetime.now(timezone.utc)
    return (moment.strftime("%Y-%m-%dT%H:%M:%S.")
            + f"{moment.microsecond // 1000:03d}Z")


def _publish(path, document):
    """Atomically, because an interrupted write must not become the outcome."""
    body = json.dumps(document, indent=2, sort_keys=True) + "\n"
    temporary = path + ".partial"
    with open(temporary, "w", encoding="utf-8") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return document


def _turn_ceiling(limits, packet):
    """`turn_seconds` is the Job's OWN provider-turn ceiling, or it is nothing.

    A declared bound that is validated and then dropped is not a bound: the Job
    states it in its submission, the manager resolves it, and this refuses
    before serving unless the EFFECTIVE value is the declared one and its
    origin is the Job rather than a compatibility default.
    """
    from baton_v12.job_manager import execution_limits

    want = packet["bounds"]["turn_seconds"]
    if type(limits) is not dict:
        _refuse("the submitted Job reports no execution limits, so its "
                "provider-turn ceiling cannot be the declared one")
    boundary = (limits.get("boundaries") or {}).get("provider_turn")
    if type(boundary) is not dict:
        _refuse("the submitted Job reports no provider-turn boundary")
    if boundary.get("seconds") != want:
        _refuse(f"the packet declares a {want}s provider turn and the "
                f"submitted Job's effective ceiling is "
                f"{boundary.get('seconds')!r}s; bind "
                f"execution_limits.provider_turn_seconds in the submission")
    if boundary.get("origin") != execution_limits.JOB:
        _refuse(f"the provider-turn ceiling came from "
                f"{boundary.get('origin')!r} rather than the Job; a declared "
                f"bound this run did not request is not a bound it has")
    return boundary


def supervise(job, control, operations, packet, *, clock=None, sleep=None,
              monotonic=None, inspect=None, surveyed=None):
    """One bounded implementation, with the termination handler held throughout.

    THE HANDLER IS INSTALLED HERE AND RESTORED HERE, around everything. The
    shutdown is the part of a run that most needs it, so it is the part that
    keeps it: a SIGTERM arriving during cancellation, cleanup or publication
    must not resume the default behaviour and kill the process with no outcome
    on disk.

    NOT A SIGKILL CLAIM. `SIGKILL` cannot be caught and nothing here pretends
    otherwise; what this covers is Ctrl-C and an ordinary `SIGTERM`.
    """
    termination = Termination().install()
    try:
        return _supervise(job, control, operations, packet, clock=clock,
                          sleep=sleep, monotonic=monotonic,
                          termination=termination, inspect=inspect,
                          surveyed=surveyed)
    finally:
        termination.restore()


def _supervise(job, control, operations, packet, *, clock, sleep, monotonic,
               termination=None, inspect=None, surveyed=None):
    """One Job, one implementation, bounded -- then a real stop, then accounting.

    THE PHASES ARE SEPARATE ON PURPOSE. Submission is not serving; serving is
    not stopping; stopping is not cleanup; cleanup is not the outcome; and the
    outcome is decided by what the run PRODUCED rather than by how the loop
    ended.
    """
    clock = _moment if clock is None else clock
    sleep = time.sleep if sleep is None else sleep
    monotonic = time.monotonic if monotonic is None else monotonic
    from baton_v12.job_manager import read_submission, serve, submit, sweep

    bounds = packet["bounds"]
    job_id = packet["submission"]["job_id"]
    gate = AdmissionGate(operations, caps={
        "implementation": bounds["implementer_invocations"]}, job_id=job_id)
    started = monotonic()
    measured = {"submitted_at": clock(), "job_id": job_id}
    # EVERY READ THAT DID NOT ANSWER, NAMED. These become reasons to hold
    # rather than silence, and the list is reported whatever else happens.
    uncertainty = []
    # EVERY INTERRUPTION, from whichever direction it arrived: the installed
    # handler's record, and anything a shutdown step raised.
    caught = []
    termination = Termination() if termination is None else termination

    # WHAT THIS STORE ALREADY HELD, and what this run does NOT account for.
    # `main` surveys before the owner acts and hands the answer here; a caller
    # driving `supervise` directly surveys at the last moment it still can,
    # which is before the submission. Either way the outcome carries it,
    # because an outcome that did not say what it excluded would be read as
    # covering everything.
    if surveyed is None:
        surveyed = _guarded(lambda: survey(job, packet), None,
                            what="the pre-submission Job survey",
                            uncertainty=uncertainty, interrupted=caught)
    measured["preexisting_jobs"] = (
        [] if surveyed is None else surveyed["preexisting_jobs"])
    measured["preexisting_stages"] = (
        {} if surveyed is None else surveyed["preexisting_stages"])
    measured["accounting_scope"] = (
        surveyed["accounting_scope"] if surveyed is not None else
        f"this run accounts for Job {job_id!r} and for nothing else; the "
        f"store could not be surveyed, so what else it holds is unknown.")

    # -- 1. ONE SUBMISSION, AND A REPEAT REPLAYS IT ------------------------
    with open(packet["submission"]["path"], "r", encoding="utf-8") as handle:
        recorded = submit(job, read_submission(handle.read()))
    measured["submission_id"] = recorded["submission_id"]

    # -- 2. THE DECLARED PER-TURN CEILING IS THE JOB'S, BEFORE SERVING -----
    _seen, _states, limits = _attempts_of(job, gate, job_id)
    measured["provider_turn"] = _turn_ceiling(limits, packet)

    # -- 3. BOUNDED SERVING, WITH ADMISSION BOUNDED AT THE GATE ------------
    held = {"stop": None, "states": {}, "kinds": {}}

    def should_continue():
        seen, states, _limits = _attempts_of(job, gate, job_id)
        held["kinds"].update(seen)
        held["states"] = states
        reached = _terminal(states)
        if reached is not None:
            held["stop"] = reached
            return False
        # A RUN THAT HAS STOPPED MOVING SAYS SO, rather than spending its
        # bound discovering it. The cleanup read is the manager's own journal
        # and is the axis an ending still in flight keeps moving; a stage that
        # cannot advance while every runtime it started is already positively
        # excluded has nothing left that could change it.
        #
        # THE CLEANUP READ IS GUARDED AGAINST ORDINARY FAILURE AND NOT
        # AGAINST AN INTERRUPTION, and the difference is the whole of review
        # 2026-09-23T00:50:59Z R1.
        #
        # AN UNREADABLE JOURNAL IS PROGRESS-NEUTRAL. It is not evidence that
        # nothing is happening, so a read that does not answer resets the
        # counter rather than advancing it -- failing towards keeping the run
        # alive, which is the direction that cannot invent a stall. The
        # failure is recorded in this run's real `uncertainty`, which is a
        # reason to hold.
        #
        # AN INTERRUPTION IS NOT AN UNREADABLE JOURNAL. The first version of
        # this used `_guarded` with DISPOSABLE `uncertainty=[]` and
        # `interrupted=[]` lists. `_guarded` catches `BaseException`, so the
        # `KeyboardInterrupt` the installed handler raises was swallowed here,
        # the predicate returned True, and ORDINARY SERVING RESUMED: the
        # reviewer's probe injected SIGINT before any provider turn and
        # watched a whole turn execute afterwards, and a direct
        # `KeyboardInterrupt` was discarded into a `settled` outcome. An
        # operator who asks a run to stop is owed it stopping.
        #
        # So only `Exception` is caught. `KeyboardInterrupt` and `SystemExit`
        # travel out of the predicate, out of `serve`, and into the shutdown
        # handler around it -- which closes admission, cancels what is
        # executing, accounts for it and retains the outcome. That path
        # already exists; this stops standing in front of it.
        accountable = {one: kind for one, kind in gate.launched.items()}
        accountable.update({one: kind for one, kind in seen.items()})
        try:
            settled = _cleanups(control, packet, accountable)
        except Exception as failure:                         # noqa: BLE001
            uncertainty.append(
                f"the progress read did not complete: "
                f"{type(failure).__name__}: {failure}. A failed read is not "
                f"evidence that nothing is happening, so this tick counts as "
                f"progress.")
            settled = None
        now = (None if settled is None
               else _observation(states, accountable, settled["cleanup"]))
        if now is not None and accountable and not settled["outstanding"] \
                and now == held.get("observation"):
            held["stalled"] = held.get("stalled", 0) + 1
            if held["stalled"] >= STALLED_TICKS:
                held["stop"] = "no-progress"
                return False
        else:
            held["stalled"] = 0
        held["observation"] = now
        if gate.refusals:
            # A CAP REFUSAL IS THE END OF THIS RUN, not a condition to wait
            # out. Letting the loop spin to the overall bound would have been
            # the same answer an hour later.
            held["stop"] = "invocation-cap-refused"
            return False
        if monotonic() - started >= bounds["total_seconds"]:
            held["stop"] = "overall-bound-exceeded"
            return False
        return True

    serving_failure = None
    interrupted = None
    # AN INTERRUPTION IS A SHUTDOWN, NOT AN ESCAPE. `KeyboardInterrupt` and
    # `SystemExit` are not `Exception`, so an unqualified handler would let a
    # Ctrl-C or a SIGTERM leave every started runtime unaccounted for.
    try:
        serve(job, gate, clock=clock, sleep=sleep,
              should_continue=should_continue, interval=1)
    except Exception as failure:                             # noqa: BLE001
        # A SERVING FAULT STOPS ADMISSION AND STILL OWES CLEANUP. It is not
        # re-raised: the runtimes this run started are the manager's to account
        # for whether or not the loop ended politely.
        serving_failure = f"{type(failure).__name__}: {failure}"
        held["stop"] = held["stop"] or "serving-failed"
    except BaseException as failure:                         # noqa: BLE001
        interrupted = f"{type(failure).__name__}: {failure}"
        held["stop"] = held["stop"] or "interrupted"

    # -- 4. ADMISSION IS CLOSED, AND THE CANONICAL HISTORY IS RE-READ ------
    # Closing the gate FIRST is what makes the cleanup window unable to start
    # anything; re-reading afterwards is what recovers an attempt that a fault
    # hid from the last predicate. Both are required -- the launch record
    # catches a runtime the projection has not caught up with, and the
    # projection catches one this process did not launch itself.
    gate.stop()
    # AND THE SIGNAL IS DEFERRED FROM HERE ON. Everything below is the
    # accounting that exists to leave nothing unexplained; an operator asking
    # the run to stop while it happens is recorded and answered after the
    # outcome is retained, rather than abandoning it half done.
    termination.defer()
    measured["stopped"] = held["stop"] or "stopped-without-a-reason"
    measured["serving_failure"] = serving_failure
    measured["admissions"] = dict(gate.admissions)
    measured["gate_refusals"] = list(gate.refusals)
    # ANOTHER JOB'S STAGE REACHING THE GATE IS REPORTED AND IS NOT A FAILURE.
    # It is the Job scope working. Counting it as a refusal would let any
    # unrelated Job in the store end a correct run.
    measured["foreign_admissions"] = list(gate.foreign)
    measured["served_seconds"] = monotonic() - started
    admitted = dict(gate.launched)
    refreshed, states, _limits, _read = _guarded(
        lambda: _refresh(job, gate, job_id, uncertainty,
                         "after the serving loop"),
        ({}, {}, None, False), what="the post-stop canonical read",
        uncertainty=uncertainty, interrupted=caught)
    held["states"] = states or held["states"]
    held["kinds"].update(refreshed)
    for attempt, kind in refreshed.items():
        admitted.setdefault(attempt, kind)

    # -- 4b. ASK THE COMPOSITION TO STOP WHAT IS STILL EXECUTING -----------
    # Closing the gate stops the NEXT runtime; it does nothing about one
    # already waiting on a provider turn, and an ordinary sweep has nothing to
    # finish while that runtime waits. The stop belongs to the deployment that
    # started it -- fence at the Authority, then order the quiescence -- so
    # this asks for it through a named capability and reports honestly when the
    # composition offers none, rather than reporting a leak as a clean stop.
    measured["cancellation"] = _guarded(
        lambda: _cancel_active(operations, control, packet, admitted,
                               held["states"], uncertainty,
                               reason=measured["stopped"],
                               launched=set(gate.launched),
                               interrupted=caught),
        {}, what="the cancellation of what was still executing",
        uncertainty=uncertainty, interrupted=caught)

    # -- 4c. CLASSIFY, ONCE, BEFORE ANYTHING IS CHARGED --------------------
    # Every consumer below reads the same accountable set: the cleanup window,
    # the final accounting and the workload counts. A blocked stage's
    # projection identity is not a turn that happened.
    def classify():
        for attempt in sorted(admitted):
            if attempt in origins:
                continue
            origins[attempt] = _guarded(
                lambda one=attempt: _origin(control, one, set(gate.launched),
                                            uncertainty)[0],
                FOREIGN, what=f"the origin of {attempt}",
                uncertainty=uncertainty, interrupted=caught)
        return {one: kind for one, kind in admitted.items()
                if origins.get(one) != UNALLOCATED}

    origins = {}
    accountable = classify()

    # -- 5. THE CLEANUP WINDOW, WHICH CANNOT ADMIT ANYTHING ----------------
    # Endings still need ticks to settle, so this keeps sweeping -- through the
    # CLOSED gate, so `admit`, `claim` and `launch` all refuse and the sweep can
    # only drive work that already exists to its ending. An attempt identity
    # that appears anyway is a fault AND is accounted for.
    cleanup_started = monotonic()
    intruders, sweeps = [], 0
    while monotonic() - cleanup_started < bounds["cleanup_seconds"]:
        if not _cleanups(control, packet, accountable)["outstanding"]:
            break
        try:
            sweep(job, gate, now=clock())
            sweeps += 1
        except BaseException as failure:                     # noqa: BLE001
            # ALSO A SECOND INTERRUPT. An operator pressing Ctrl-C again
            # during shutdown must not escape with the accounting half done;
            # it ends the window and is reported, like any other fault here.
            if not isinstance(failure, Exception):
                interrupted = interrupted or \
                    f"{type(failure).__name__}: {failure}"
            serving_failure = serving_failure or \
                f"cleanup sweep: {type(failure).__name__}: {failure}"
            break
        finally:
            fresh, states, _limits, _read = _guarded(
                lambda: _refresh(job, gate, job_id, uncertainty,
                                 "during the cleanup window"),
                ({}, {}, None, False), what="a cleanup-window canonical read",
                uncertainty=uncertainty, interrupted=caught)
            held["states"] = states or held["states"]
            held["kinds"].update(fresh)
            for attempt, kind in list(gate.launched.items()) + list(
                    fresh.items()):
                if attempt not in admitted:
                    intruders.append(attempt)
                    admitted[attempt] = kind
            accountable = classify()
        try:
            sleep(1)
        except BaseException as failure:                     # noqa: BLE001
            if not isinstance(failure, Exception):
                interrupted = interrupted or \
                    f"{type(failure).__name__}: {failure}"
            uncertainty.append(
                f"the cleanup window ended early: "
                f"{type(failure).__name__}: {failure}")
            break
    measured["cleanup_sweeps"] = sweeps
    # AND WHY IT STOPPED MOVING, when that is why it stopped. An operator
    # reading `no-progress` is owed the number of unchanged ticks it rests on.
    measured["stalled_ticks"] = held.get("stalled", 0)
    measured["stalled_after"] = STALLED_TICKS

    # -- 6. POSITIVE, MANAGER-OWNED CLEANUP FOR EVERY STARTED RUNTIME ------
    # THE FINAL CANONICAL READ IS A PRECONDITION OF SUCCESS, not a courtesy.
    # Without it the accounting rests on this process's own launch record,
    # which cannot answer whether the store holds anything else.
    final, states, _limits, final_read = _guarded(
        lambda: _refresh(job, gate, job_id, uncertainty,
                         "for the final accounting"),
        ({}, {}, None, False), what="the final canonical read",
        uncertainty=uncertainty, interrupted=caught)
    held["states"] = states or held["states"]
    held["kinds"].update(final)
    for attempt, kind in final.items():
        if attempt not in admitted:
            intruders.append(attempt)
            admitted[attempt] = kind
    measured["final_canonical_read"] = final_read
    measured["stage_states"] = dict(held["states"])
    # THE RUNTIMES THIS RUN MUST ACCOUNT FOR, and nothing else. An identity the
    # manager answers no row for, that this run never launched, is reported in
    # `unallocated_attempts` and in `attempt_origins` -- it is not a runtime,
    # and counting it as one made a blocked stage read as a turn that happened.
    measured["admitted_attempts"] = sorted(accountable)
    measured["observed_attempts"] = sorted(admitted)
    # AND THE ORDER THEY REALLY STARTED IN. `admitted` is keyed in launch
    # order; sorting attempt identities sorts hex digests.
    measured["started_order"] = [one for one in admitted
                                 if one in accountable]
    measured["unexpected_attempts"] = sorted(set(intruders))
    accountable = classify()
    measured["attempt_origins"] = origins
    measured["unallocated_attempts"] = sorted(
        one for one, origin in origins.items() if origin == UNALLOCATED)
    accounting = _guarded(
        lambda: _cleanups(control, packet, accountable),
        {"cleanup": {}, "outstanding": sorted(accountable)},
        what="the cleanup accounting", uncertainty=uncertainty,
        interrupted=caught)
    measured["cleanup"] = accounting["cleanup"]
    measured["outstanding_cleanup"] = accounting["outstanding"]

    # -- 7. THE WORKLOAD THIS RUN ACTUALLY PRODUCED ------------------------
    workload = _guarded(
        lambda: _workload_evidence(job, control, packet, accountable,
                                   held["kinds"], inspect=inspect),
        {"shortfalls": ["the workload evidence could not be read"]},
        what="the workload evidence", uncertainty=uncertainty,
        interrupted=caught)
    measured["workload"] = workload

    # -- 8. THE OUTCOME, AND IT FAILS CLOSED -------------------------------
    # RECORDED HERE AND NOT EARLIER: an interruption can arrive during the
    # cancellation or the cleanup window, and a member captured before those
    # would report the run as uninterrupted while this function raises.
    for one in termination.received:
        if one not in caught:
            caught.append(one)
    if interrupted is None and caught:
        interrupted = caught[0]
    measured["interrupted"] = interrupted
    measured["interruptions"] = list(caught)
    reasons = []
    reasons.extend(uncertainty)
    if not final_read:
        reasons.append("the final canonical accounting could not be read, so "
                       "this run cannot say what it left behind")
    if interrupted is not None:
        reasons.append(f"the run was interrupted: {interrupted}")
    for attempt, said in sorted(measured["cancellation"].items()):
        if not said.get("requested"):
            reasons.append(f"execution on {attempt} was not stopped: "
                           + said.get("why", "no reason recorded"))
    if serving_failure is not None:
        reasons.append("the serving loop did not end cleanly")
    if intruders:
        reasons.append("a runtime was admitted after admission closed: "
                       + ", ".join(sorted(set(intruders))))
    if gate.refusals:
        reasons.append("the admission gate refused: "
                       + "; ".join(one["why"] for one in gate.refusals))
    if accounting["outstanding"]:
        reasons.append("this manager cannot prove positive cleanup for "
                       + ", ".join(accounting["outstanding"]))
    if not accountable:
        reasons.append("no runtime was ever admitted, so this run answered "
                       "nothing about the provider")
    if held["stop"] == "no-progress":
        reasons.append(
            f"the run stopped because nothing changed for {STALLED_TICKS} "
            f"consecutive ticks while its stages were not terminal and every "
            f"runtime it started was already positively excluded. The stage "
            f"states were {dict(held['states'])}. This is a run that could "
            f"not have finished, reported when it stopped moving rather than "
            f"when its overall bound elapsed.")
    if held["stop"] != "completed":
        reasons.append(f"the run stopped {measured['stopped']!r} rather than "
                       f"completing its stages")
    reasons.extend(workload["shortfalls"])

    outcome = {"schema": OUTCOME_SCHEMA, "run_id": packet["run_id"],
               "work": packet["work"], "claim": packet["claim"],
               "job_id": job_id,
               "state": "settled" if not reasons else "held",
               "held_because": reasons,
               "retry": False, "finished_at": clock(),
               "uncertainty": uncertainty, **measured}
    _publish(packet["outcome_path"], outcome)
    if interrupted is not None:
        # THE OUTCOME IS ON DISK AND THE INTERRUPT IS NOT SWALLOWED. An
        # operator who pressed Ctrl-C is owed both.
        raise SupervisorInterrupted(interrupted, outcome)
    return outcome


def _refresh(job, operations, job_id, uncertainty, what):
    """Re-read canonical history, and RECORD a read that did not answer.

    A failed read is not evidence of absence. It cannot be: the locally
    recorded launch set says what THIS process started, and says nothing about
    what else the store holds. So the failure is retained as a named
    uncertainty, the accounting continues over the runtimes that ARE known, and
    `supervise` refuses to call the run settled without a successful final read.

    Answers `(seen, states, limits, read)` -- `read` is False when the canonical
    history could not be read, and no caller may treat that as emptiness.
    """
    try:
        seen, states, limits = _attempts_of(job, operations, job_id)
        return seen, states, limits, True
    except Exception as failure:                             # noqa: BLE001
        uncertainty.append(
            f"the canonical attempt history could not be read {what}: "
            f"{type(failure).__name__}: {failure}. A failed read is not "
            f"evidence that no further runtime exists.")
        return {}, {}, None, False


def _cancel_active(operations, control, packet, admitted, states, uncertainty,
                   *, reason, launched=(), interrupted=None):
    """Order the stop for every runtime this run left executing.

    WHY THIS IS NOT A SWEEP. Closing the admission gate stops the NEXT runtime.
    One already waiting on a provider turn is unaffected by it, and the ordinary
    ending path has nothing to finish while that runtime waits -- so a timeout
    would otherwise be reported as `held` with the container still running and
    the engine never asked to stop it.

    WHY IT IS A CAPABILITY AND NOT A DIRECT CALL. The accepted path is
    `attempts.request_cancellation(store, port, agent, adapter, ...)`, which
    fences the exact participant and generation at the Authority BEFORE
    ordering quiescence. Its port, cooperative agent and runtime adapter are
    per-attempt objects the composed deployment builds at launch; a supervisor
    that reconstructed them from another module's private state would be a
    second controller composing a security boundary it does not own.

    THE DECISION IS PER ATTEMPT AND NOT PER STAGE. `attempt_runtime_of` answers
    about THIS attempt: whether a runtime was ever attached and what the manager
    last observed of it.

    AN UNREADABLE FACT IS A REASON TO ORDER THE STOP, not to skip it. A known
    launched attempt this manager cannot currently describe is exactly the one
    that must not be left running on a guess.

    ITS RETURN IS NOT ABSENCE. `request_cancellation` reports what it ORDERED;
    positive exclusion arrives through the ending path and `cleanup_of`, which
    is what the accounting below still requires.
    """
    del packet
    cancel = getattr(operations, CANCEL_CAPABILITY, None)
    said = {}
    for attempt in sorted(admitted):
        # BOUNDED PER ATTEMPT, not per loop. An interruption arriving at ONE
        # attempt's read must not cost the stop of every attempt after it.
        facts, state, why = _guarded(
            lambda: _runtime_facts(control, attempt, uncertainty),
            (None, UNREADABLE, "the runtime read did not complete"),
            what=f"the runtime read for {attempt}", uncertainty=uncertainty,
            interrupted=interrupted if interrupted is not None else [])
        if state == ABSENT and attempt not in launched:
            # AN ANSWERED ABSENCE, and this run never launched it. There is no
            # assignment to fence and no runtime identity to name, so a
            # cancellation would refuse; that refusal is not news about a
            # container. AN UNREADABLE STATE DOES NOT REACH HERE.
            said[attempt] = {
                "requested": True, "runtime_id": None,
                "execution_runtime": None,
                "why": "this manager answers that it holds no attempt row for "
                       "this identity and this run never launched it, so no "
                       "runtime was allocated for it. That is not a claim "
                       "that nothing is running anywhere."}
            continue
        if facts is not None and facts["runtime_id"] is None:
            said[attempt] = {"requested": True, "state": None,
                             "execution_runtime": facts["execution_runtime"],
                             "why": "no runtime was ever attached to this "
                                    "attempt, so there is nothing to stop"}
            continue
        if facts is not None and facts["execution_runtime"] in GONE:
            said[attempt] = {"requested": True,
                             "runtime_id": facts["runtime_id"],
                             "execution_runtime": facts["execution_runtime"],
                             "why": f"this manager observed the runtime "
                                    f"{facts['execution_runtime']}"}
            continue
        held = {"runtime_id": None if facts is None else facts["runtime_id"],
                "execution_runtime": (None if facts is None
                                      else facts["execution_runtime"]),
                "stage_state": states.get(admitted[attempt])}
        if facts is None:
            held["unreadable"] = why
        if cancel is None:
            held.update(requested=False, why=(
                f"this composition carries no {CANCEL_CAPABILITY!r}, so "
                f"nothing ordered the runtime to stop; the assignment must be "
                f"fenced at the Authority before a runtime is removed and only "
                f"the deployment that launched it holds that port"))
            uncertainty.append(f"execution on {attempt} was left running: "
                               + held["why"])
            said[attempt] = held
            continue
        try:
            held.update(requested=True, answer=_bounded(
                cancel(attempt_id=attempt, reason=reason)))
        except BaseException as failure:                     # noqa: BLE001
            # A SECOND INTERRUPT DOES NOT ESCAPE WITH THE ACCOUNTING UNDONE.
            # It is recorded, the remaining runtimes are still ordered stopped,
            # and `supervise` raises it after the outcome is on disk.
            said[attempt] = dict(held, requested=False,
                                 why=f"{type(failure).__name__}: {failure}")
            uncertainty.append(f"the cancellation of {attempt} refused: "
                               f"{type(failure).__name__}: {failure}")
            if not isinstance(failure, Exception) and interrupted is not None:
                interrupted.append(f"{type(failure).__name__}: {failure}")
            continue
        said[attempt] = held
    return said


# WHAT A RUNTIME READ CAN ANSWER, and the third is not the second. `ABSENT` is
# this manager answering authoritatively that it holds no attempt row.
# `UNREADABLE` is the read not completing at all. Collapsing them labels a
# discovered attempt whose read RAISED as "no runtime was ever allocated" --
# absence inferred from a question that was never answered.
ABSENT, UNREADABLE = "absent", "unreadable"

# HOW AN ATTEMPT IDENTITY CAME TO THIS RUN'S ATTENTION, and they are not the
# same fact. `STARTED` is this run's OWN launch record, taken at the call.
# `FOREIGN` is an attempt this run did not launch but which must still be
# accounted for -- either the manager holds a runtime for it, or its state
# could not be read, which is the conservative side of the same line.
# `UNALLOCATED` is an identity the manager ANSWERS that it holds no row for and
# that this run never launched: a projection identity for a stage that started
# nothing. Only that third one is excluded from the cleanup demand, because a
# `runtime.destroy` for a runtime that was never allocated cannot exist.
#
# NOTHING HERE INFERS QUIESCENCE. An unreadable state is `FOREIGN`, not
# `UNALLOCATED`, and the exclusion rests on an answer rather than on silence.
STARTED, FOREIGN, UNALLOCATED = "started", "foreign", "unallocated"


def _runtime_facts(control, attempt_id, uncertainty):
    """What this manager durably holds about ONE attempt's runtime.

    Answers `(facts, state, why)`: a row and `None`, or `None` with `ABSENT`
    when the manager answered that it holds none, or `None` with `UNREADABLE`
    when the read did not complete. `attempt_runtime_of` is a read and nothing
    else, and a well-formed id naming no attempt answers `None` by its own
    contract -- which is an ANSWER, and the only one that may retire an
    obligation.
    """
    from baton_v12.worker_manager import attempts

    try:
        found = attempts.attempt_runtime_of(control, attempt_id)
    except BaseException as failure:                         # noqa: BLE001
        # BaseException: an interruption arriving here must not abandon the
        # shutdown. It also must not become evidence of absence.
        why = f"{type(failure).__name__}: {failure}"
        uncertainty.append(f"this manager could not describe the runtime of "
                           f"{attempt_id}: {why}. A failed read is not "
                           f"evidence that nothing is executing.")
        return None, UNREADABLE, why
    if found is None:
        return None, ABSENT, "this manager holds no attempt row for it"
    return found, None, None


def _origin(control, attempt_id, launched, uncertainty):
    """Which of the three this identity is, from records rather than guesses.

    ONLY AN ANSWERED ABSENCE MAY EXCLUDE. An identity this run launched is
    `STARTED`. One the manager holds a runtime for is `FOREIGN`. One the
    manager positively answers no row for, and that this run never launched, is
    `UNALLOCATED`. Everything else -- including a read that did not complete --
    is `FOREIGN`, which is the conservative side: it keeps the stop order and
    the cleanup obligation.
    """
    if attempt_id in launched:
        return STARTED, None
    facts, state, why = _runtime_facts(control, attempt_id, uncertainty)
    if state == ABSENT:
        return UNALLOCATED, why
    if state == UNREADABLE:
        uncertainty.append(
            f"{attempt_id} is treated as a runtime this run must account for "
            f"because its state could not be read; absence was not "
            f"established.")
        return FOREIGN, why
    if facts["runtime_id"] is None:
        return UNALLOCATED, "this manager holds no runtime for it"
    return FOREIGN, None


def _bounded(value, depth=2):
    """A cancellation answer, reduced to something an outcome may carry.

    `request_cancellation` answers a nested document -- the journalled intent,
    the Authority fence, the session quiescence and the ordered quiescence --
    and the useful facts are one and two levels down. Scalars travel, nested
    documents travel to a bounded depth, and anything else becomes bounded text
    rather than being dropped, so a reader is never left wondering what was in
    the members this summary removed.
    """
    if isinstance(value, (str, int, float, bool, type(None))):
        return value if not isinstance(value, str) else value[:512]
    if isinstance(value, dict) and depth > 0:
        return {str(name): _bounded(value[name], depth - 1)
                for name in sorted(value, key=str)}
    if isinstance(value, (list, tuple)) and depth > 0:
        return [_bounded(one, depth - 1) for one in value[:16]]
    return str(value)[:512]


def _cleanups(control, packet, attempts):
    """What the manager's own journal says about each started runtime.

    `cleanup_of` is the READ half of `authorize_cleanup`: it opens no session,
    takes no adapter and writes nothing, so asking it is not a way to make an
    ending happen. Absence is absence and a `failed` ending is a failure; both
    are outstanding, and neither is rounded up to proved-gone.

    THE SUPERVISOR DOES NOT CALL `authorize_cleanup` ITSELF. The ending driver
    owns the composition a destroy belongs to -- seal, intake, retention,
    publication, freeze, then cleanup. So the closed gate is what stops
    admission and the ordinary ending path is what performs the stop and
    exclusion; this reads back what it committed.
    """
    from baton_v12.contracts import ContractRefusal
    from baton_v12.worker_manager import intake

    policy = _retention_of(packet)
    found, outstanding = {}, []
    for attempt in sorted(attempts):
        try:
            record = intake.cleanup_of(
                control, attempt_id=attempt, retention_policy_digest=policy)
        except ContractRefusal as refusal:
            found[attempt] = {"cleanup": None, "why": refusal.message}
            outstanding.append(attempt)
            continue
        if record is None:
            found[attempt] = {"cleanup": None, "why": "no committed cleanup"}
            outstanding.append(attempt)
            continue
        found[attempt] = {"cleanup": record["cleanup"],
                          "state": record.get("state"),
                          "why": record.get("why")}
        if record["cleanup"] not in POSITIVE_CLEANUP:
            outstanding.append(attempt)
    return {"cleanup": found, "outstanding": outstanding}


def _retention_of(packet):
    """The retention policy the DEPLOYMENT is configured with.

    Read from the configuration rather than restated in the packet: the destroy
    identity binds this digest, so a second copy that drifted would ask the
    journal about an act the manager never committed and report it as absent.
    """
    with open(packet["deployment"]["config_path"], "rb") as handle:
        configuration = json.loads(handle.read().decode("utf-8"))
    held = configuration.get("retention_policy_digest")
    if type(held) is not str or not held:
        _refuse("the deployment configuration names no retention policy "
                "digest, and the cleanup identity binds one")
    return held


def _declared_base(packet):
    """The canonical target this run's proposal must be offered against."""
    with open(packet["deployment"]["config_path"], "rb") as handle:
        configuration = json.loads(handle.read().decode("utf-8"))
    return _object_name(configuration.get("line_declared_base"),
                        "the deployment's declared base")


def _workload_evidence(job, control, packet, admitted, kinds, *, inspect=None):
    """Did this run perform the SELECTED implementation? W239528.

    What the packet exists to establish is one turn's worth of a specific
    thing, so this reads it back out of the manager's own records:

      * ONE implementation attempt and no other kind, because a second turn is
        a correction and a review turn is the next Job;
      * one provider context, OPENED and not restored, at its first generation;
      * ONE retained proposal, offered against the declared base;
      * and that proposal's commit ATTRIBUTED to the adapter -- authored and
        committed by it, exactly one commit on top of that base.

    THE LAST CLAUSE IS WHY THIS FUNCTION IS NOT THE OTHER ONE'S. W236087's live
    run retained no proposal at all because the provider had committed its own
    history and `_unmoved` refused to adopt it. A baseline that asked only
    "was something retained" would accept a proposal whose commits came from
    whoever happened to be in the container. See `DIAGNOSIS-239528.md`.

    NOTHING HERE MANUFACTURES A VERDICT, and this run has none to manufacture:
    there is no reviewer, no disposition and no acceptance in it. Whether the
    proposal is GOOD is W239533's question. Whether it is this adapter's,
    against this base, is this one's.
    """
    del job
    shortfalls = []
    # IN LAUNCH ORDER. `admitted` is an ordered mapping keyed by the launch
    # that started each runtime, and the gate's own recorded kind is preferred
    # over the projection's because it was taken at that call.
    def named(kind):
        return [one for one in admitted
                if (admitted[one] or kinds.get(one)) == kind]

    implementation = named("implementation")
    evidence = {"implementation_attempts": implementation,
                "generations": [], "conversations": [], "modes": [],
                "proposals": [], "dispositions": [], "attribution": [],
                "shortfalls": []}

    want = packet["bounds"]
    if len(implementation) != want["implementer_invocations"]:
        shortfalls.append(
            f"the packet declares {want['implementer_invocations']} "
            f"implementer invocation(s) and this run has "
            f"{len(implementation)}")
    # NO STAGE KIND BUT THIS ONE. The gate refuses a foreign kind at admission,
    # and this is the same statement read back from what actually ran -- so a
    # review container that reached this Job by some other path is a shortfall
    # rather than an unexamined extra row.
    foreign = sorted({(admitted[one] or kinds.get(one)) for one in admitted}
                     - {"implementation"} - {None})
    if foreign:
        shortfalls.append(f"this Job serves the implementation stage alone and "
                          f"this run also ran {', '.join(foreign)}; review and "
                          f"correction are separate Jobs")

    evidence.update(_context_evidence(control, implementation, shortfalls))
    retained = _proposals(control, implementation, packet, shortfalls)
    evidence["proposals"] = retained["proposals"]
    # WHAT EACH TURN ACTUALLY ENDED AS, reported whether or not it produced a
    # proposal. A failed run's outcome says `unable` where an operator can
    # find it rather than only inside a shortfall sentence.
    evidence["dispositions"] = retained["dispositions"]
    evidence["attribution"] = _attributions(control, implementation,
                                            evidence["proposals"], shortfalls,
                                            inspect=inspect)
    evidence["shortfalls"] = shortfalls
    return evidence


def _context_evidence(control, implementation, shortfalls):
    """One context, OPENED once, at its first generation.

    `restore` is the resume Job's mode and appears here only as a failure: a
    baseline that resumed something did not establish a baseline. The manager
    numbers a context's generations from zero, so the opening invocation is
    generation 0 and nothing else is.
    """
    from baton_v12.contracts import ContractRefusal
    from baton_v12.worker_manager import provider_context as context

    modes, conversations, generations, uses = [], [], [], []
    for attempt in implementation:
        try:
            binding = context.context_invocation_of(control, attempt)
        except ContractRefusal as refusal:
            shortfalls.append(f"attempt {attempt} has no readable context "
                              f"invocation: {refusal.message}")
            continue
        if binding is None:
            shortfalls.append(f"implementer attempt {attempt} ran with no "
                              f"provider context, so this run says nothing "
                              f"about the managed context path")
            continue
        modes.append(binding["mode"])
        conversations.append(binding["conversation_id"])
        generations.append(binding["generation"])
        uses.append(binding["use_id"])
    if modes != ["open"]:
        shortfalls.append(f"this baseline opens exactly one context and "
                          f"restores none; this run's context modes were "
                          f"{modes}")
    if len(set(conversations)) > 1:
        shortfalls.append("more than one conversation was opened for a "
                          "single-container run")
    if len(set(uses)) != len(uses):
        shortfalls.append("two invocations shared one context use")
    if generations != list(range(len(modes))):
        shortfalls.append(f"the retained generations are {generations} rather "
                          f"than one per invocation, counted from the open")
    return {"modes": modes, "conversations": sorted(set(conversations)),
            "generations": generations}


def _proposals(control, implementation, packet, shortfalls):
    """The retained proposal each implementer turn published, and its base.

    THE WORKER'S OWN CLAIM, read back from the frozen result manifest. It
    carries what the turn was built on and what it produced; the manager's
    measurements are deliberately not in it, which is why the base is checked
    against the DEPLOYMENT's declared target rather than taken on the worker's
    word for what the target was.
    """
    from baton_v12.contracts import ContractRefusal
    from baton_v12.worker_manager import frozen_output_of, load_manifest

    try:
        base = _declared_base(packet)
    except SupervisorRefusal as refusal:
        shortfalls.append(str(refusal))
        base = None
    found, dispositions = [], []
    for attempt in implementation:
        # THE DISPOSITION FIRST, because a turn that ended `unable` has no
        # proposal BY CONTRACT and saying so is the actionable answer. The
        # expired-credential run reported `KeyError: 'baton.git-proposal/1'`,
        # which names this program's own lookup rather than the fact an
        # operator needs: the provider turn did not complete.
        try:
            frozen = frozen_output_of(control, attempt)
        except (ContractRefusal, KeyError, TypeError) as why:
            shortfalls.append(f"attempt {attempt} froze no readable result: "
                              f"{type(why).__name__}: {why}")
            continue
        # ABSENCE IS AN ANSWER AND IS NOT AN ERROR. `frozen_output_of` answers
        # `None` for an attempt that froze nothing, which is exactly what a
        # turn the adapter REFUSED looks like -- it never got as far as a
        # result. Reading a member off it would turn that answer into an
        # AttributeError and lose the whole workload document behind a guard.
        if frozen is None:
            dispositions.append({"attempt_id": attempt, "disposition": None})
            shortfalls.append(
                f"attempt {attempt} froze no result at all, so its turn ended "
                f"before it could answer. The adapter refuses a turn it "
                f"cannot give an account of; the attempt's retained events "
                f"carry the refusal.")
            continue
        disposition = frozen.get("disposition")
        dispositions.append({"attempt_id": attempt,
                             "disposition": disposition})
        if disposition != "completed":
            shortfalls.append(
                f"attempt {attempt} ended {disposition!r} rather than "
                f"'completed', so it published no proposal. An implementation "
                f"turn that could not do its work is an ANSWER -- the "
                f"attempt's retained provider log carries what the provider "
                f"reported -- and it is not a proposal this run may count.")
            continue
        try:
            manifest = load_manifest(control, frozen["manifest_digest"],
                                     "resultManifest")
            proposal = next(one for one in manifest["outputs"]
                            if one["name"] == "proposal")
            claim = proposal["result_metadata"][CLAIM_NAMESPACE]
            held = {"attempt_id": attempt, "base": claim["base"],
                    "head": claim["head"], "transport": claim["transport"]}
        except (ContractRefusal, KeyError, StopIteration, TypeError) as why:
            shortfalls.append(f"attempt {attempt} reported 'completed' and "
                              f"retained no readable proposal: "
                              f"{type(why).__name__}: {why}")
            continue
        if base is not None and held["base"] != base:
            shortfalls.append(
                f"attempt {attempt} offered its proposal against "
                f"{held['base']} and this deployment's canonical target is "
                f"{base}")
        if held["head"] == held["base"]:
            shortfalls.append(f"attempt {attempt} published a proposal whose "
                              f"head is its base, so it proposed nothing")
        found.append(held)
    if not found:
        shortfalls.append("this run retained no proposal at all, so it "
                          "established nothing about the implementation path")
    return {"proposals": found, "dispositions": dispositions}


def _attributions(control, implementation, proposals, shortfalls, *,
                  inspect=None):
    """WHO AUTHORED the retained commit, read out of the manager's own line.

    This is the check W236087's live failure earned. That provider committed
    its own work inside the container -- the retained reflog shows a `proposal`
    branch created by the runtime and two commits authored under the operator's
    own identity -- and the adapter refused to adopt a history it did not
    write. The refusal was correct, and it means the ONLY way a proposal exists
    at all is that the adapter authored it.

    So this does not take that on trust either. `writer_for_attempt` names the
    durable private line this attempt wrote on, `line_of` gives its path, and
    the commit object is read there: author, committer and parents. An
    attribution that names anything but this adapter, or a commit with other
    than exactly the declared base as its single parent, is a shortfall.

    READ-ONLY, AND THE VERBS ARE A CLOSED LIST. `_git_read` refuses anything
    outside `GIT_READS` before the child is started; nothing here can move a
    reference, write an object or touch a worktree.
    """
    from baton_v12.contracts import ContractRefusal
    from baton_v12.worker_manager import attempts as attempt_rows

    inspect = line_attribution if inspect is None else inspect
    heads = {one["attempt_id"]: one for one in proposals}
    found = []
    for attempt in implementation:
        claim = heads.get(attempt)
        if claim is None:
            # Already reported by `_proposals`; there is nothing to attribute.
            continue
        try:
            generation = attempt_rows.assignment_of(control,
                                                    attempt)["generation"]
            said = inspect(control, attempt_id=attempt, generation=generation,
                           head=claim["head"], base=claim["base"])
        except (ContractRefusal, SupervisorRefusal, KeyError, OSError,
                TypeError, ValueError) as why:
            shortfalls.append(f"attempt {attempt} has no readable proposal "
                              f"attribution: {type(why).__name__}: {why}")
            continue
        found.append(said)
        if said["author"] != said["committer"]:
            shortfalls.append(
                f"attempt {attempt} published a commit authored by "
                f"{said['author']!r} and committed by {said['committer']!r}; "
                f"this adapter is both or the proposal is not its account")
        if said["author"] != f"{COMMIT_NAME} <{COMMIT_EMAIL}>":
            shortfalls.append(
                f"attempt {attempt} published a commit attributed to "
                f"{said['author']!r} rather than to the worker adapter "
                f"{COMMIT_NAME} <{COMMIT_EMAIL}>. The provider edits and "
                f"verifies; the adapter commits and publishes.")
        if said["parents"] != [claim["base"]]:
            shortfalls.append(
                f"attempt {attempt} published a commit whose parents are "
                f"{said['parents']} rather than exactly its declared base "
                f"{claim['base']}; this adapter authors one commit per turn")
    return found


def line_attribution(control, *, attempt_id, generation, head, base):
    """Read one commit object out of the durable line this attempt wrote on.

    THE REPOSITORY IS THE MANAGER'S, named by the manager. `writer_for_attempt`
    answers the writer row for this attempt and generation, and `line_of`
    answers its `line_path`; neither is a path this program chose. A supervisor
    that guessed at a workspace layout would be inspecting whatever it found.
    """
    from baton_v12.worker_manager import review_cycles

    _object_name(head, "the proposal head")
    _object_name(base, "the proposal base")
    writer = review_cycles.writer_for_attempt(control, attempt_id=attempt_id,
                                              generation=generation)
    if writer is None:
        _refuse(f"this manager holds no line writer for attempt "
                f"{attempt_id} generation {generation}, so there is no "
                f"repository to attribute its proposal in")
    line = review_cycles.line_of(control, writer["line_id"])
    place = line["line_path"]
    if not os.path.isdir(place):
        _refuse(f"the durable line at {place!r} is not a directory this "
                f"process can read")
    # `cat-file commit` PRINTS THE OBJECT, header lines then the message. It
    # resolves nothing beyond the name it is given and writes nothing.
    body = _git_read(place, "cat-file", "commit", head)
    author, committer, parents = None, None, []
    for line_text in body.split("\n"):
        if line_text == "":
            break
        name, _space, rest = line_text.partition(" ")
        if name == "parent":
            parents.append(rest.strip())
        elif name in ("author", "committer"):
            # "<name> <<email>> <epoch> <offset>" -- the identity is everything
            # up to the closing angle bracket; the time is not attribution.
            closing = rest.rfind(">")
            identity = rest[:closing + 1] if closing != -1 else rest
            if name == "author":
                author = identity
            else:
                committer = identity
    if author is None or committer is None:
        _refuse(f"the commit {head} in {place!r} carries no author or "
                f"committer line, so nothing about it can be attributed")
    return {"attempt_id": attempt_id, "line_id": writer["line_id"],
            "line_path": place, "head": head, "base": base,
            "author": author, "committer": committer, "parents": parents}


def _git_read(repository, *argv, timeout=60):
    """One read-only Git command, with the verb checked before the child runs.

    AGENTS.md permits reviewing history and nothing else, and this is the one
    place this program touches Git at all. The verb is checked against
    `GIT_READS`; the environment is closed so no user or system configuration
    can install an alias, a hook path or a credential helper; and
    `--no-optional-locks` keeps even an incidental index refresh from writing.
    """
    import subprocess

    if not argv or argv[0] not in GIT_READS:
        _refuse(f"this program runs only {', '.join(GIT_READS)}; it was asked "
                f"for {argv[0] if argv else '<nothing>'!r}")
    answer = subprocess.run(
        ["git", "--no-optional-locks", "-C", repository, *argv],
        capture_output=True, timeout=timeout, check=False,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
             "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
             "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
             "HOME": os.devnull, "LC_ALL": "C"})
    if answer.returncode != 0:
        _refuse(f"`git {' '.join(argv)}` in {repository!r} exited "
                f"{answer.returncode}: "
                f"{answer.stderr.decode('utf-8', 'replace').strip()[:512]}")
    return answer.stdout.decode("utf-8", "replace")


def _compose(packet, job, control, stream):
    """The production composition, from the packet's own configuration.

    THE CODE BOUNDARY IS PASSED, not inferred. Leaving it to the default meant
    `operations_from` derived it from `stage_execution.__file__` -- three
    parents up -- which for a relocated manager source answers the run root's
    PARENT and classifies this run's own stores as living inside the code tree.
    The packet binds one value and both ends read it.
    """
    from tools import stage_execution

    with open(packet["deployment"]["config_path"], "rb") as handle:
        configuration = json.loads(handle.read().decode("utf-8"))
    print(f"composing the reviewed deployment under code boundary "
          f"{packet['code_boundary']}", file=stream, flush=True)
    return stage_execution.operations_from(configuration, job, control,
                                           checkout=packet["code_boundary"])


def main(argv=None, *, stream=None, compose=None, image_inspect=None):
    stream = sys.stderr if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="baseline",
        description="Drive ONE bounded managed implementation and stop.")
    parser.add_argument("--packet", required=True,
                        help="the reviewed packet manifest")
    parser.add_argument("--incarnation", required=True,
                        help="this supervising process's control incarnation")
    taken = parser.parse_args(argv)

    try:
        packet = held_packet(taken.packet)
        # THE BYTES, THEN THE IMPORTS, THEN THE ENGINE -- all of it before a
        # store is opened, because refusing is only free until then.
        verify_imported_sources(packet)
        verify_worker_image(
            packet,
            image_inspect=_engine_inspect if image_inspect is None
            else image_inspect)
    except SupervisorRefusal as refusal:
        print(f"refused before anything opened: {refusal}", file=stream)
        return 2

    from baton_v12.job_manager import JobStore
    from baton_v12.worker_manager import ControlStore

    deployment = packet["deployment"]
    # THE JOB STORE'S AUTHORITY BINDING IS THIS PACKET'S. A store's episode
    # identities are derived in its own Authority's namespace, so the store is
    # opened against the Authority the deployment names rather than whichever
    # one the file happens to hold.
    with JobStore.open(deployment["job_store"],
                       authority_uuid=deployment["authority_uuid"],
                       incarnation=taken.incarnation, clock=_moment) as job:
        # THE STORE IS SURVEYED BEFORE ANY OWNER ACT. A Job identity this
        # store already records cannot be submitted, and reaching that at
        # submission time would mean `prepare` had already spent a one-run
        # qualification grant on a run that could never start. The refusal
        # travels out as exit 2, the same status every other before-anything
        # refusal uses.
        try:
            surveyed = survey(job, packet)
        except SupervisorRefusal as refusal:
            print(f"refused before any owner act: {refusal}", file=stream)
            return 2
        if surveyed["preexisting_jobs"]:
            print(f"this Job store also holds "
                  f"{', '.join(surveyed['preexisting_jobs'])}; "
                  f"{surveyed['accounting_scope']}", file=stream, flush=True)
        with ControlStore.open(deployment["control_store"],
                               incarnation=taken.incarnation,
                               clock=_moment) as control:
            prepare(control, packet)
            operations = (compose or _compose)(packet, job, control, stream)
            try:
                outcome = supervise(job, control, operations, packet,
                                    surveyed=surveyed)
            except SupervisorInterrupted as stopped:
                # THE OUTCOME IS ALREADY ON DISK; WHAT WAS MISSING WAS SAYING
                # SO. W239528, owner pass 243171: an operator pressed Ctrl-C
                # and got an uncaught traceback out of this function, so the
                # one thing they needed -- where the retained outcome is --
                # was the one thing not printed. `supervise` retains the
                # outcome BEFORE it raises, deliberately, and this is the
                # other half of that contract.
                #
                # THE INTERRUPT IS STILL HONOURED. It is not swallowed into a
                # success: the exit status is the interrupted one and the
                # report says the run did not finish.
                interrupted = stopped.outcome
                print(f"interrupted: {stopped}", file=stream)
                print(f"the outcome WAS retained at "
                      f"{packet['outcome_path']}", file=stream)
                print(f"state {interrupted['state']!r}, stopped "
                      f"{interrupted['stopped']!r}; "
                      f"{len(interrupted.get('held_because') or [])} "
                      f"held reason(s)", file=stream)
                print(json.dumps(interrupted, indent=2, sort_keys=True),
                      file=stream)
                return 130
            finally:
                closing = getattr(operations, "close", None)
                if closing is not None:
                    closing()
    print(json.dumps(outcome, indent=2, sort_keys=True), file=stream)
    if outcome["state"] != "settled":
        print(f"held: the outcome is retained at {packet['outcome_path']}",
              file=stream)
    return 0 if outcome["state"] == "settled" else 1


def _engine_inspect(reference):
    """The engine's own document for one image, and nothing else.

    A read. It starts no container, pulls nothing and writes nothing; an image
    this host does not hold answers absence, which `verify_worker_image`
    refuses by name.
    """
    import subprocess

    answer = subprocess.run(
        ["docker", "image", "inspect", reference],
        capture_output=True, timeout=120, check=False)
    if answer.returncode != 0:
        return None
    return json.loads(answer.stdout.decode("utf-8"))[0]


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
