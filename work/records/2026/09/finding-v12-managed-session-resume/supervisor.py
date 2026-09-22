"""The bounded one-shot owner supervisor for W236087's managed correction.

WHAT THIS IS. `LIVE-CORRECTION-PROPOSAL.md` proposes ONE managed Job with ONE
independent-review correction, and the independent review of 2026-09-22T05:58:20Z
recorded why the serving command alone cannot be that packet:

    "A serving loop alone cannot enforce the proposed one-run lifetime and
    cleanup; the final packet must stop admission, establish manager-owned
    runtime absence, stop serving and retain the outcome, failing closed on
    uncertainty."

This is that supervisor. It is an OWNER program: it uses the supported owner and
manager APIs and it fabricates no journal record, no verdict and no receipt.

REVIEW 2026-09-22T06:36:24Z REWROTE THREE THINGS HERE, and each is a defect this
file now owns rather than a refinement:

  R1 -- the declared invocation caps and `turn_seconds` were VALIDATED AND THEN
  UNUSED, and "settled" meant only that the projected stages completed. A packet
  declaring one invocation of each ran two of each and reported success, and an
  accepted FIRST review settled with no correction at all -- so exit 0 did not
  establish the question the packet exists to ask. Caps are now enforced at the
  admission boundary BEFORE an offer is issued, `turn_seconds` is bound into the
  Job's own `provider_turn` ceiling and verified as effective before serving, and
  a settled outcome now requires the actual open->changes-requested->restore->
  accepted sequence with two distinct retained proposals.

  R2 -- stopping the loop predicate stopped nothing. Cleanup called the ordinary
  admitting `sweep`, so the next eligible runtime could START during shutdown;
  the intruder was detected only afterwards and was then LEFT OUT of the cleanup
  accounting entirely. A serving fault between an admission and the next
  predicate lost that runtime from the report altogether. Admission is now
  stopped at the operations boundary itself, every started runtime is recorded
  AT THE LAUNCH CALL rather than reconstructed from a projection that races it,
  and the canonical history is re-read after a fault and again before accounting.

  R3 -- the packet pinned a frozen executable it never ran while the code that
  actually supervised was imported from a mutable checkout. The packet now binds
  the manager SOURCE that is really imported, and `verify_imported_sources`
  proves the imported `baton_v12`/`tools` files and this program's own bytes
  before a single store is opened.

WHAT IT WILL NOT DO, stated because each absence is a decision:

  * It never retries. A failed turn, a refused act, an exhausted cap or an
    exceeded bound ends the run; nothing here resubmits or re-serves.
  * It never certifies a production profile, enables anything, or advances a
    deployment.
  * It never reports success it cannot prove. Every ending it calls successful
    rests on a POSITIVE committed record read back out of the manager's own
    journal; absence, uncertainty and a `failed` cleanup are all held.
  * It never manufactures a reviewer's verdict. It READS the recorded
    dispositions and refuses a run whose sequence was not the selected one.
  * It performs no Git operation and mutates no repository of record.

THE TWO SEAMS. `serve`'s `clock`/`sleep`/`should_continue` and
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
           "verify_worker_image", "prepare", "supervise", "main"]

PACKET_SCHEMA = "baton.managed-correction-packet/2"
OUTCOME_SCHEMA = "baton.managed-correction-outcome/3"

# The cleanup endings the manager's own axis calls POSITIVE. `failed` is a
# committed record too, and it is not one of these on purpose: a destroy that
# settled `failed` is a runtime this manager could not prove gone.
POSITIVE_CLEANUP = ("complete", "retained")

# THE TWO STAGE KINDS THIS PACKET SERVES, closed. The proposal submits an
# implementation stage and a review stage and stops; a third kind reaching the
# admission gate is a workload nobody selected, and it is refused by name rather
# than admitted under whichever cap happens to be spare.
KINDS = ("implementation", "review")

# The worker's own claim namespace, mirrored here rather than imported for
# `single_worker.TASK_DOCUMENT`'s reason: `claude_agent` runs INSIDE the image
# on its own import path, and a host program that imported it would be reaching
# across the boundary the delivery exists to cross. The deterministic
# verification asserts the two copies agree.
CLAIM_NAMESPACE = "baton.git-proposal/1"

# The journal kind a recorded checkpoint verdict commits under. `review_cycles`
# EXPORTS this constant precisely so a consumer can cross-bind a materialized
# row against the act that wrote it instead of keeping its own copy of the
# journal's shape; this module reads it from there and never spells it twice.

_PACKET = ("schema", "run_id", "work", "claim", "note", "worker_image",
           "manager_runtime", "manager_source", "supervisor", "deployment",
           "context", "submission", "fixture", "bounds", "outcome_path")
_BOUNDS = ("turn_seconds", "total_seconds", "cleanup_seconds",
           "implementer_invocations", "review_invocations", "corrections",
           "retry")
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
    """One installed handler, with two modes and a memory. R2a.

    WHY A MODE RATHER THAN ANOTHER `except`. Review 2026-09-22T12:31:42Z
    reproduced an interruption arriving at a runtime READ during shutdown: the
    handler raised, the read was outside a catch, and `supervise` left with no
    engine stop ordered and no outcome on disk. Adding a catch around that one
    read would have fixed that one read; the shutdown performs several, and the
    next one added would have the same hole.

    So the signal is DEFERRED for the whole shutdown instead. While a run is
    serving, a signal raises and ends the loop, which is what an operator
    asking it to stop means. Once admission has closed, the remaining work is
    the accounting that exists to leave nothing unexplained -- so a signal
    there is RECORDED and execution continues, and `supervise` raises
    `SupervisorInterrupted` after the outcome is retained.

    NOT A SIGKILL CLAIM, and no promise about a signal delivered before this is
    installed or after it is restored. What it covers is Ctrl-C and an ordinary
    `SIGTERM` between those two points.
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
    """Run one shutdown step; never let it abandon the shutdown. R2a.

    A shutdown step that raised used to take the whole accounting with it --
    no stop ordered for the runtimes after it, and no outcome retained. Every
    step is bounded here instead: the failure is named as an uncertainty, which
    is a reason to hold, and the remaining steps still run.

    `BaseException` deliberately: an interruption arriving inside a read is the
    exact case review 2026-09-22T12:31:42Z reproduced, and it is recorded so
    `supervise` can re-raise it once the outcome is on disk.
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

# Which projected stage states still have something to stop. A completed or
# exceptional stage has already reached its ending.
ACTIVE_STATES = ("starting", "waiting", "answering", "running", "claimed",
                 "integrating")

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
    _document(packet, "the managed correction packet", _PACKET)
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
    for member in ("implementer_invocations", "review_invocations"):
        _whole_number(bounds[member], f"the packet's {member}",
                      minimum=1, maximum=8)
    _whole_number(bounds["corrections"], "the packet's corrections",
                  minimum=0, maximum=4)
    # THE WORKLOAD HAS TO BE ARITHMETICALLY POSSIBLE. R1: a packet that asked
    # for one correction out of one implementer invocation described a run
    # nothing could satisfy, and the old code accepted it and then reported a
    # different run as success. One correction is one EXTRA implementer turn
    # and one EXTRA review turn, so the counts are related rather than free.
    if bounds["implementer_invocations"] != bounds["corrections"] + 1:
        _refuse(f"{bounds['corrections']} correction(s) is "
                f"{bounds['corrections'] + 1} implementer invocation(s); this "
                f"packet declares {bounds['implementer_invocations']}")
    if bounds["review_invocations"] != bounds["corrections"] + 1:
        _refuse(f"{bounds['corrections']} correction(s) is "
                f"{bounds['corrections'] + 1} review invocation(s); this "
                f"packet declares {bounds['review_invocations']}")
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

    # R3: THE CODE THAT ACTUALLY RUNS, bound as its own artifact. The frozen
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

    if context["job_id"] != submission["job_id"]:
        _refuse("the qualification grant and the submission name different "
                "Jobs; one grant serves exactly one Job")
    return packet


def verify_imported_sources(packet, *, modules=None, program=None):
    """The modules REALLY IMPORTED are the reviewed ones. R3.

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

    # AND THIS PROGRAM ITSELF, which is outside that tree and was equally
    # unbound before. A supervisor whose own bytes moved is not the reviewed
    # supervisor however well its dependencies verify.
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

    R4, review 2026-09-22T12:55:41Z. `configure_context_storage` reads
    `configured_workspace_storage` immediately -- the context roots are checked
    for containment against the workspace root -- and the ordinary composition
    records that fact LATER, in its own preflight. So a fresh run had an
    undocumented prerequisite: somebody had to configure the workspace store
    before the supervisor's first owner act, and the operator packet never said
    so. The entrypoint test was supplying it.

    DERIVED FROM THE DEPLOYMENT, NOT CHOSEN. This reads the configuration the
    packet is bound to and takes the root its workers already name; a caller
    root of this program's own choosing would be exactly the arbitrary
    selection the boundary exists to refuse. Workers that disagree are refused
    here rather than one of them being picked.
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
    admission, which is what makes it exactly-once across a crash.
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


class AdmissionGate:
    """The operations object, with admission BOUNDED and STOPPABLE. R1, R2.

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

    EVERY STARTED RUNTIME IS RECORDED AT THE CALL. The previous version
    reconstructed the set from the status projection between ticks, and review
    2026-09-22T06:36:24Z showed a fault between an admission and the next
    predicate losing that runtime from the report entirely. `launch` is the act
    that starts one, so the identity is taken there, BEFORE delegating: a launch
    that then faults is still a runtime this run must account for.
    """

    __slots__ = ("_operations", "_caps", "admissions", "launched",
                 "stage_kinds", "refusals", "stopped")

    def __init__(self, operations, *, caps):
        self._operations = operations
        self._caps = dict(caps)
        self.admissions = {kind: 0 for kind in self._caps}
        self.launched = {}
        self.stage_kinds = {}
        self.refusals = []
        self.stopped = False

    # -- the three admitting acts -------------------------------------------

    def admit(self, stage, job):
        kind = stage.get("kind") if type(stage) is dict else None
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
        return answer

    def claim(self, stage):
        self._allowed("claim",
                      stage.get("kind") if type(stage) is dict else None)
        return self._operations.claim(stage)

    def launch(self, attempt, job):
        kind = None
        if type(attempt) is dict:
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

    def _allowed(self, act, kind):
        if self.stopped:
            self._deny(act, "admission is closed for this run")
        del kind

    def _deny(self, act, why):
        from baton_v12.contracts import ContractRefusal

        self.refusals.append({"act": act, "why": why})
        raise ContractRefusal(
            "refused", "precondition",
            f"the managed correction supervisor refuses to {act}: {why}")


def _attempts_of(job, operations, job_id):
    """Every attempt identity this Job's stages have held, live and historical.

    The live `attempt_id` alone is the CURRENT one; a corrected implementation
    has already replaced its first, and a reader that saw only the live attempt
    would be reporting positive absence for one runtime and silently none for
    the other. A PURE READ: it opens nothing and writes nothing, which is why it
    is safe to repeat after a fault.
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
    stage the manager cannot advance is the end of the correction, and going on
    to admit the next one would be the automatic second attempt the proposal
    excludes. `completed` on every configured stage is the other ending, and it
    is a STOP rather than a success -- what makes a run successful is decided by
    `_workload_evidence`, not by the projection.
    """
    if not states:
        return None
    if any(state == "exceptional" for state in states.values()):
        return "exceptional"
    if all(state == "completed" for state in states.values()):
        return "completed"
    return None


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

    R1: this number used to be validated and then dropped, so a packet could
    declare 180 seconds while every turn ran under the build's 3600-second
    default. The Job states it in its submission, the manager resolves it, and
    this refuses before serving unless the EFFECTIVE value is the declared one
    and its origin is the Job rather than a compatibility default.
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
              monotonic=None):
    """One bounded correction, with the termination handler held throughout.

    THE HANDLER IS INSTALLED HERE AND RESTORED HERE, around everything. Review
    2026-09-22T11:53:11Z: it used to be restored the instant `serve` returned,
    so a SIGTERM arriving during cancellation, cleanup or publication resumed
    the default behaviour and killed the process with no outcome on disk. The
    shutdown is the part of a run that most needs the handler, so it is the
    part that keeps it.

    NOT A SIGKILL CLAIM. `SIGKILL` cannot be caught and nothing here pretends
    otherwise; what this covers is Ctrl-C and an ordinary `SIGTERM`.
    """
    termination = Termination().install()
    try:
        return _supervise(job, control, operations, packet, clock=clock,
                          sleep=sleep, monotonic=monotonic,
                          termination=termination)
    finally:
        termination.restore()


def _supervise(job, control, operations, packet, *, clock, sleep, monotonic,
               termination=None):
    """One Job, one correction, bounded -- then a real stop, then accounting.

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
        "implementation": bounds["implementer_invocations"],
        "review": bounds["review_invocations"]})
    started = monotonic()
    measured = {"submitted_at": clock()}
    # EVERY READ THAT DID NOT ANSWER, NAMED. R2b: these become reasons to hold
    # rather than silence, and the list is reported whatever else happens.
    uncertainty = []
    # EVERY INTERRUPTION, from whichever direction it arrived: the installed
    # handler's record, and anything a shutdown step raised.
    caught = []
    termination = Termination() if termination is None else termination

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
    # R2a: AN INTERRUPTION IS A SHUTDOWN, NOT AN ESCAPE. `KeyboardInterrupt`
    # and `SystemExit` are not `Exception`, so the previous handler let a
    # Ctrl-C or a SIGTERM leave every started runtime unaccounted for. SIGTERM
    # is routed into the same path; installing it is best-effort because a
    # non-main thread cannot, and a supervisor that refused to run there would
    # be refusing for its own convenience.
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
    # R2: closing the gate FIRST is what makes the cleanup window unable to
    # start anything; re-reading afterwards is what recovers an attempt that a
    # fault hid from the last predicate. Both are required -- the launch record
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
    # R2a: closing the gate stops the NEXT runtime; it does nothing about one
    # already waiting on a provider turn, and an ordinary sweep has nothing to
    # finish while that runtime waits. The stop belongs to the deployment that
    # started it -- fence at the Authority, then order the quiescence -- so
    # this asks for it through a named capability and reports honestly when the
    # composition offers none, rather than reporting a leak as a clean stop.
    measured["cancellation"] = _guarded(
        lambda: _cancel_active(operations, control, packet, admitted,
                               held["states"], uncertainty,
                               reason=measured["stopped"], interrupted=caught),
        {}, what="the cancellation of what was still executing",
        uncertainty=uncertainty, interrupted=caught)

    # -- 5. THE CLEANUP WINDOW, WHICH CANNOT ADMIT ANYTHING ----------------
    # Endings still need ticks to settle, so this keeps sweeping -- through the
    # CLOSED gate, so `admit`, `claim` and `launch` all refuse and the sweep can
    # only drive work that already exists to its ending. An attempt identity
    # that appears anyway is a fault AND is accounted for; the previous version
    # reported it and then left it out of the cleanup map.
    cleanup_started = monotonic()
    intruders, sweeps = [], 0
    while monotonic() - cleanup_started < bounds["cleanup_seconds"]:
        if not _cleanups(control, packet, admitted)["outstanding"]:
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

    # -- 6. POSITIVE, MANAGER-OWNED CLEANUP FOR EVERY STARTED RUNTIME ------
    # THE FINAL CANONICAL READ IS A PRECONDITION OF SUCCESS, not a courtesy.
    # R2b: without it the accounting rests on this process's own launch record,
    # which cannot answer whether the store holds anything else. It is taken
    # ONCE, here, so the reported set is the last thing this run knew rather
    # than a snapshot from the middle of the cleanup window.
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
    measured["admitted_attempts"] = sorted(admitted)
    # AND THE ORDER THEY REALLY STARTED IN. `admitted` is keyed in launch
    # order, and the sequence checks below are ABOUT the order -- sorting
    # attempt identities is sorting hex digests, which reported this run's
    # first review as its second.
    measured["started_order"] = list(admitted)
    measured["unexpected_attempts"] = sorted(set(intruders))
    accounting = _guarded(
        lambda: _cleanups(control, packet, admitted),
        {"cleanup": {}, "outstanding": sorted(admitted)},
        what="the cleanup accounting", uncertainty=uncertainty,
        interrupted=caught)
    measured["cleanup"] = accounting["cleanup"]
    measured["outstanding_cleanup"] = accounting["outstanding"]

    # -- 7. THE WORKLOAD THIS RUN ACTUALLY PRODUCED ------------------------
    workload = _guarded(
        lambda: _workload_evidence(job, control, packet, admitted,
                                   held["kinds"]),
        {"shortfalls": ["the workload evidence could not be read"]},
        what="the workload evidence", uncertainty=uncertainty,
        interrupted=caught)
    measured["workload"] = workload

    # -- 8. THE OUTCOME, AND IT FAILS CLOSED -------------------------------
    # RECORDED HERE AND NOT EARLIER: an interruption can arrive during the
    # cancellation or the cleanup window, and a member captured before those
    # would report the run as uninterrupted while this function raises.
    # EVERY INTERRUPTION THIS RUN SAW, whichever direction it arrived from:
    # the deferred signals the handler recorded, and anything a shutdown step
    # raised. Recorded here rather than earlier because the shutdown is exactly
    # where the later ones arrive.
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
    if not admitted:
        reasons.append("no runtime was ever admitted, so this run answered "
                       "nothing about the provider")
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

    R2b, review 2026-09-22T07:03:13Z: this used to catch every exception and
    return empty facts, so an unreadable canonical history after the stop was
    indistinguishable from a history containing nothing -- and an otherwise
    completed run was reported settled with no reasons at all. A failed read is
    not evidence of absence. It cannot be: the locally recorded launch set says
    what THIS process started, and says nothing about what else the store holds.

    So the failure is retained as a named uncertainty, the accounting continues
    over the runtimes that ARE known, and `supervise` refuses to call the run
    settled without a successful final read. Raising here instead would have
    reintroduced the hole R2 closed by abandoning the accounting mid-way.

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
                   *, reason, interrupted=None):
    """Order the stop for every runtime this run left executing. R2a.

    WHY THIS IS NOT A SWEEP. Closing the admission gate stops the NEXT runtime.
    One already waiting on a provider turn is unaffected by it, and the ordinary
    ending path has nothing to finish while that runtime waits -- so a timeout
    used to be reported as `held` with the container still running and the
    engine never asked to stop it.

    WHY IT IS A CAPABILITY AND NOT A DIRECT CALL. The accepted path is
    `attempts.request_cancellation(store, port, agent, adapter, ...)`, which
    fences the exact participant and generation at the Authority BEFORE
    ordering quiescence. Its port, cooperative agent and runtime adapter are
    per-attempt objects the composed deployment builds at launch; a supervisor
    that reconstructed them from another module's private state would be a
    second controller composing a security boundary it does not own.

    THE DECISION IS PER ATTEMPT AND NOT PER STAGE. Review 2026-09-22T11:53:11Z:
    this used to read the stage-kind projection, so a launched attempt whose
    kind was unknown, or whose stage state was unreadable, was passed over and
    reported as though nothing were executing -- and a completed older
    generation could be cancelled because its stage had a newer waiting
    attempt. `attempt_runtime_of` answers about THIS attempt: whether a runtime
    was ever attached and what the manager last observed of it.

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
        # attempt's read must not cost the stop of every attempt after it --
        # which is what a guard around the whole loop would have done. The
        # read answers absence-of-knowledge and this attempt is cancelled on
        # that basis, exactly as an ordinary unreadable fact is.
        facts, why = _guarded(
            lambda: _runtime_facts(control, attempt, uncertainty),
            (None, "the runtime read did not complete"),
            what=f"the runtime read for {attempt}", uncertainty=uncertainty,
            interrupted=interrupted if interrupted is not None else [])
        if facts is not None and facts["runtime_id"] is None:
            said[attempt] = {"requested": True, "state": None,
                             "execution_runtime": facts["execution_runtime"],
                             "why": "no runtime was ever attached to this "
                                    "attempt, so there is nothing to stop"}
            continue
        if facts is not None and facts["execution_runtime"] in GONE:
            said[attempt] = {"requested": True, "runtime_id": facts["runtime_id"],
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
            # Review 2026-09-22T11:53:11Z: `KeyboardInterrupt` here left the
            # run without a retained outcome at all, which is the one state
            # this program exists to prevent. It is recorded, the remaining
            # runtimes are still ordered stopped, and `supervise` raises it
            # after the outcome is on disk.
            said[attempt] = dict(held, requested=False,
                                 why=f"{type(failure).__name__}: {failure}")
            uncertainty.append(f"the cancellation of {attempt} refused: "
                               f"{type(failure).__name__}: {failure}")
            if not isinstance(failure, Exception) and interrupted is not None:
                interrupted.append(f"{type(failure).__name__}: {failure}")
            continue
        said[attempt] = held
    return said


def _runtime_facts(control, attempt_id, uncertainty):
    """What this manager durably holds about ONE attempt's runtime.

    `attempt_runtime_of` is a read and nothing else. Absence and an unreadable
    row are different answers and neither is emptiness: both leave the decision
    to order a stop in place, because a runtime this manager cannot describe is
    the one it must not assume is gone.
    """
    from baton_v12.worker_manager import attempts

    try:
        found = attempts.attempt_runtime_of(control, attempt_id)
    except BaseException as failure:                         # noqa: BLE001
        # BaseException: review 2026-09-22T12:31:42Z reproduced an
        # interruption arriving exactly here, which left the shutdown with no
        # stop ordered and no outcome retained. An unreadable fact is a reason
        # to ORDER the stop, so the read answers absence-of-knowledge and the
        # caller goes on to cancel.
        why = f"{type(failure).__name__}: {failure}"
        uncertainty.append(f"this manager could not describe the runtime of "
                           f"{attempt_id}: {why}. A failed read is not "
                           f"evidence that nothing is executing.")
        return None, why
    if found is None:
        why = "this manager holds no attempt row for it"
        uncertainty.append(f"this manager could not describe the runtime of "
                           f"{attempt_id}: {why}. A failed read is not "
                           f"evidence that nothing is executing.")
        return None, why
    return found, None


def _bounded(value, depth=2):
    """A cancellation answer, reduced to something an outcome may carry.

    `request_cancellation` answers a nested document -- the journalled intent,
    the Authority fence, the session quiescence and the ordered quiescence --
    and the useful facts are one and two levels down. Scalars travel, nested
    documents travel to a bounded depth, and anything else becomes bounded
    text rather than being dropped, so a reader is never left wondering what
    was in the members this summary removed.
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
    publication, freeze, then cleanup -- and the owner's own instruction for
    this Work was to "extend this path rather than add a second controller". So
    the closed gate is what stops admission and the ordinary ending path is what
    performs the stop and exclusion; this reads back what it committed.
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


def _workload_evidence(job, control, packet, admitted, kinds):
    """Did this run perform the SELECTED correction? R1.

    The old success condition was "every projected stage completed and every
    cleanup positive", which an accepted FIRST review satisfies without any
    correction at all. What the packet exists to establish is a SEQUENCE, so
    this reads the sequence back out of the manager's own records:

      * one context, opened once and RESTORED once, under one grant, with the
        same conversation and distinct uses and invocations;
      * two distinct retained proposals, because a correction that produced the
        same head corrected nothing;
      * a first review recorded `changes-requested` and a last review recorded
        `accepted`, read as the dispositions they were COMMITTED as.

    NOTHING HERE MANUFACTURES A VERDICT. Each fact is a read, and a run whose
    reviewer accepted immediately, asked for a second correction, or rejected,
    is reported as the run it was and held.
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
    reviews = named("review")
    evidence = {"implementation_attempts": implementation,
                "review_attempts": reviews,
                "generations": [], "conversations": [], "modes": [],
                "proposal_heads": [], "dispositions": [], "shortfalls": []}

    want = packet["bounds"]
    if len(implementation) != want["implementer_invocations"]:
        shortfalls.append(
            f"the packet declares {want['implementer_invocations']} "
            f"implementer invocation(s) and this run has "
            f"{len(implementation)}")
    if len(reviews) != want["review_invocations"]:
        shortfalls.append(f"the packet declares {want['review_invocations']} "
                          f"review invocation(s) and this run has "
                          f"{len(reviews)}")

    evidence.update(_context_evidence(control, implementation, want,
                                      shortfalls))
    evidence["proposal_heads"] = _proposal_heads(control, implementation,
                                                 shortfalls)
    evidence["dispositions"] = _dispositions(control, reviews, want,
                                             shortfalls)
    evidence["shortfalls"] = shortfalls
    return evidence


def _context_evidence(control, implementation, want, shortfalls):
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
                              f"provider context, so it cannot be part of a "
                              f"session-resume correction")
            continue
        modes.append(binding["mode"])
        conversations.append(binding["conversation_id"])
        generations.append(binding["generation"])
        uses.append(binding["use_id"])
    expected = ["open"] + ["restore"] * want["corrections"]
    if modes != expected:
        shortfalls.append(f"the selected sequence is {expected} and this run's "
                          f"context modes were {modes}")
    if len(set(conversations)) > 1:
        shortfalls.append("the correction ran on more than one conversation, "
                          "so nothing was resumed")
    if len(set(uses)) != len(uses):
        shortfalls.append("two invocations shared one context use")
    # ONE GENERATION PER INVOCATION, COUNTED FROM THE OPENING ONE. The
    # manager numbers a context's generations from zero -- `_qualified` refuses
    # a "third generation" at index 2 -- so this asserts the sequence rather
    # than a base this module would otherwise be restating.
    if generations != list(range(len(modes))):
        shortfalls.append(f"the retained generations are {generations} rather "
                          f"than one per invocation, counted from the open")
    return {"modes": modes, "conversations": sorted(set(conversations)),
            "generations": generations}


def _proposal_heads(control, implementation, shortfalls):
    """The retained proposal each implementer turn published."""
    from baton_v12.contracts import ContractRefusal
    from baton_v12.worker_manager import frozen_output_of, load_manifest

    heads = []
    for attempt in implementation:
        try:
            frozen = frozen_output_of(control, attempt)
            manifest = load_manifest(control, frozen["manifest_digest"],
                                     "resultManifest")
            proposal = next(one for one in manifest["outputs"]
                            if one["name"] == "proposal")
            heads.append(proposal["result_metadata"][CLAIM_NAMESPACE]["head"])
        except (ContractRefusal, KeyError, StopIteration, TypeError) as why:
            shortfalls.append(f"attempt {attempt} retained no readable "
                              f"proposal: {type(why).__name__}: {why}")
    if len(heads) > 1 and len(set(heads)) != len(heads):
        shortfalls.append("two implementer turns retained the same proposal "
                          "head, so the correction changed nothing")
    return heads


def _dispositions(control, reviews, want, shortfalls):
    """The verdicts the independent reviews RECORDED, read as committed.

    Reached through `review_cycles.VERDICT_KIND`, which that module exports
    precisely so a consumer can cross-bind a materialized row against the act
    that wrote it, and then through its own `verdict_of`, which proves every
    member of the row against those operands.
    """
    from baton_v12.contracts import ContractRefusal
    from baton_v12.worker_manager import attempts, review_cycles

    found = []
    for attempt in reviews:
        try:
            generation = attempts.assignment_of(control, attempt)["generation"]
            attachment = review_cycles.review_for_attempt(
                control, attempt_id=attempt, generation=generation)
            if attachment is None:
                shortfalls.append(f"review attempt {attempt} attached to no "
                                  f"checkpoint")
                continue
            record = control.operation_record(
                review_cycles.VERDICT_KIND + ":"
                + attachment["attachment_id"])
            if record is None or record["state"] != "committed":
                shortfalls.append(f"review attempt {attempt} recorded no "
                                  f"committed verdict")
                continue
            operands = json.loads(record["signature"])["operands"]
            verdict = review_cycles.verdict_of(control,
                                               operands["verdict_id"])
            found.append(verdict["disposition"])
        except (ContractRefusal, KeyError, TypeError, ValueError) as why:
            shortfalls.append(f"review attempt {attempt} has no readable "
                              f"verdict: {type(why).__name__}: {why}")
    expected = ["changes-requested"] * want["corrections"] + ["accepted"]
    if found != expected:
        shortfalls.append(f"the selected review sequence is {expected} and "
                          f"this run recorded {found}")
    return found


def _compose(packet, job, control, stream):
    """The production composition, from the packet's own configuration."""
    from tools import stage_execution

    with open(packet["deployment"]["config_path"], "rb") as handle:
        configuration = json.loads(handle.read().decode("utf-8"))
    print("composing the reviewed deployment", file=stream, flush=True)
    return stage_execution.operations_from(configuration, job, control)


def main(argv=None, *, stream=None, compose=None, image_inspect=None):
    stream = sys.stderr if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="supervisor",
        description="Drive ONE bounded managed correction and stop.")
    parser.add_argument("--packet", required=True,
                        help="the reviewed packet manifest")
    parser.add_argument("--incarnation", required=True,
                        help="this supervising process's control incarnation")
    taken = parser.parse_args(argv)

    try:
        packet = held_packet(taken.packet)
        # R3: THE BYTES, THEN THE IMPORTS, THEN THE ENGINE -- all of it before
        # a store is opened, because refusing is only free until then.
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
    # THE JOB STORE'S AUTHORITY BINDING IS THIS PACKET'S. `single_worker`'s
    # rule: a store's episode identities are derived in its own Authority's
    # namespace, so the store is opened against the Authority the deployment
    # names rather than whichever one the file happens to hold. Review
    # 2026-09-22T12:31:42Z asked for an entrypoint test and this is the first
    # thing it found: these two operands are required and were never passed,
    # so `main` raised a `TypeError` before opening anything.
    with JobStore.open(deployment["job_store"],
                       authority_uuid=deployment["authority_uuid"],
                       incarnation=taken.incarnation, clock=_moment) as job:
        with ControlStore.open(deployment["control_store"],
                               incarnation=taken.incarnation,
                               clock=_moment) as control:
            prepare(control, packet)
            operations = (compose or _compose)(packet, job, control, stream)
            try:
                outcome = supervise(job, control, operations, packet)
            finally:
                closing = getattr(operations, "close", None)
                if closing is not None:
                    closing()
    print(json.dumps(outcome, indent=2, sort_keys=True), file=stream)
    return 0 if outcome["state"] == "settled" else 1


def _engine_inspect(reference):
    """The engine's own document for one image, and nothing else.

    A read. It starts no container, pulls nothing and writes nothing; an image
    this host does not hold answers absence, which `verify_worker_image` refuses
    by name.
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
