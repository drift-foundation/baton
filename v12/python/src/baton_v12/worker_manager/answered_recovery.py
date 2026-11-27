"""Owner selection and attempt-scoped writer proof for an unfinished answered ending."""
from contextlib import contextmanager
from contextvars import ContextVar
import os
import re
from typing import NamedTuple

from ..contracts import ContractRefusal
from .store import manager_signature

KIND = "implementation.recover-answered"
_requested = ContextVar("answered_request", default=None)
_active = ContextVar("answered_recovery", default=None)


class WriterProof(NamedTuple):
    control: object
    attempt: str
    outputs: dict
    manifest: str
    head: str


def refuse(reason):
    raise ContractRefusal("refused", "precondition", reason)


def selection(control, attempt):
    key = KIND + ":" + attempt
    row = control.operation_record(key)
    if row is None:
        return None
    return control.replay(key, row["signature"], kind=KIND)[1]


@contextmanager
def nominated(control, request):
    token = _requested.set((control, request))
    try:
        yield
    finally:
        _requested.reset(token)


def requested(control, attempt):
    active = _requested.get()
    if active and active[0] is control and active[1]["attempt"] == attempt:
        return active[1]
    return selection(control, attempt)


def request_for(jobs, control, *, attempt, job, episode, manifest, head, actor):
    from ..job_manager import scheduler, ending
    from . import attempts
    stage = job + "/implementation"
    if not re.fullmatch("sha256:[0-9a-f]{64}", manifest) or not re.fullmatch("[0-9a-f]{40}", head):
        refuse("select the exact completion digest and Git commit")
    request = dict(attempt=attempt, job=job, episode=episode, manifest=manifest, head=head, actor=actor)
    prior = selection(control, attempt)
    if prior is not None:
        if prior != request:
            refuse("another recovery selection already binds this attempt")
        return prior
    allocation = scheduler.allocation_of(jobs, attempt)
    intent = ending.intent_of(jobs, stage, episode)
    state = attempts.attempt_runtime_of(control, attempt)
    if not allocation or allocation["stage_id"] != stage or allocation["episode"] != episode or allocation["allocation_state"] != "reserved":
        refuse("recovery requires the original reserved implementation allocation")
    if not intent or intent["attempt_id"] != attempt or intent["disposition"] != "completed" or intent["terminal_manifest_digest"] != manifest:
        refuse("selection differs from the exact registered answered ending")
    if not state or state["execution_runtime"] != "destroyed" or state["cleanup"] != "pending":
        refuse("recovery requires a destroyed runtime with its ending still pending")
    return request


def permitted(control, attempt):
    active = _active.get()
    return active is not None and active.control is control and active.attempt == attempt


def permits_destroyed(control, attempt, state):
    return state == "destroyed" and permitted(control, attempt)


def check_head(control, attempt, head):
    if permitted(control, attempt) and head != _active.get().head:
        refuse("checkpoint differs from selected recovery head")


def check_seal(control, attempt, sealed):
    if not permitted(control, attempt):
        return
    check_staged(attempt, sealed)


def check_staged(attempt, sealed):
    active = _active.get()
    if active is None or active.attempt != attempt:
        return
    if sealed.get("completion_manifest_digest") != active.manifest:
        refuse("staged completion envelope differs from selected digest")
    measured = {o["name"]: (o["status"], o["content_manifest"]) for o in sealed["outputs"]}
    if measured != active.outputs:
        refuse("sealed output differs from the selected worker completion manifest")


def _cause(failure):
    """The underlying OS error, named, for a refusal an operator has to act on."""
    detail = failure.strerror if isinstance(failure, OSError) and failure.strerror else str(failure)
    return f"{type(failure).__name__}: {detail}"


def _mount_table():
    from . import workspaces
    try:
        with open(workspaces.MOUNTINFO, encoding="utf-8") as table:
            mounts = []
            for entry in table:
                fields = entry.split(" - ", 1)[0].split()
                device, root, point = fields[2:5]
                mounts.append((device, workspaces._unescaped(root), workspaces._unescaped(point)))
    except (OSError, ValueError, IndexError) as failure:
        refuse(f"cannot read the host mount table ({_cause(failure)})")
    return mounts


def _regions(path, mounts):
    parents = [m for m in mounts if os.path.commonpath((path, m[2])) == m[2]]
    if not parents:
        refuse("no filesystem identity for a writable mount")
    # Include stacked mounts conservatively when more than one has this depth.
    depth = max(len(point) for _, _, point in parents)
    regions = [(dev, os.path.normpath(os.path.join(root, os.path.relpath(path, point))))
               for dev, root, point in parents if len(point) == depth]
    regions.extend((dev, root) for dev, root, point in mounts if os.path.commonpath((path, point)) == path)
    return regions


def mount_regions(path):
    """Filesystem coordinates exposed by a host bind, including nested bind aliases."""
    try:
        path = os.path.realpath(path, strict=True)
    except OSError as failure:
        refuse(f"cannot resolve the filesystem backing a writable mount ({_cause(failure)})")
    return _regions(path, _mount_table())


def prospective_regions(path):
    """Where a bind source is written now, or would be after a container restart.

    W386542 (field, 2026-11-27): exited containers keep binds whose sources were
    since removed. A restart can recreate such a source (the short `-v` form
    creates missing directories), so absence is not exclusion: the place it
    would be recreated is judged instead.

    M386591: the walk is physical, component by component, as the kernel walks
    it. Each existing component is resolved through its symlinks before the
    next is applied, so `..` leaves the directory a link actually reached,
    never the lexical parent of the link. Only a missing tail is joined
    lexically; it can hold no mount point or link, and a `..` inside it would
    depend on what a restart creates, so it refuses. Any failure to establish a
    component -- permission, a dangling link, a loop, a non-directory -- is
    uncertainty and refuses, naming the component.
    """
    if not isinstance(path, str) or not os.path.isabs(path):
        refuse("writable mount source is not an absolute host path")
    parts = [part for part in path.split("/") if part not in ("", ".")]
    real = "/"
    for index, part in enumerate(parts):
        if part == "..":
            real = os.path.dirname(real)  # `real` holds no link, so this is the physical parent
            continue
        probe = os.path.join(real, part)
        try:
            real = os.path.realpath(probe, strict=True)
        except FileNotFoundError as failure:
            if os.path.lexists(probe):
                refuse(f"writable mount source component {probe!r} is a link that does not resolve ({_cause(failure)})")
            tail = parts[index:]
            if ".." in tail:
                refuse(f"writable mount source {path!r} climbs out of the missing component {probe!r}")
            return _regions(os.path.join(real, *tail), _mount_table())
        except OSError as failure:
            refuse(f"cannot establish writable mount source component {probe!r} ({_cause(failure)})")
        if index + 1 < len(parts) and not os.path.isdir(real):
            refuse(f"writable mount source component {probe!r} is not a directory")
    return _regions(real, _mount_table())


def overlaps(exposed, protected):
    return any(a == b and os.path.commonpath((p, q)) in (p, q) for a, p in exposed for b, q in protected)


@contextmanager
def verified(control, adapter, profile, request, terminal, writer, line):
    from . import attempts, intake, sealing, tokens, workspaces
    attempt = request["attempt"]
    state = attempts.attempt_runtime_of(control, attempt)
    if (state["execution_runtime"] != "destroyed" or not state["runtime_id"]
            or terminal.get("ending") != "answered" or terminal.get("disposition") != "completed"
            or terminal.get("manifest_digest") != request["manifest"]):
        refuse("recovery terminal or runtime differs from the selected answered attempt")
    prepared = workspaces.settlement_preparation(control, attempt)
    row = attempts._require_attempt(control, attempt)
    operation = attempts._start_operation_id(row)
    domain = tokens.domain_of("workspace", tokens.workspace_identity(row))
    generation = tokens.generation_of(control, domain, execution=attempt, operation=operation)
    token_state = tokens.token_of(control, domain, generation) if generation is not None else None
    if (not token_state or not token_state["returned"] or token_state["container"] != state["runtime_id"]
            or domain != tokens.domain_of("workspace", prepared["workspace"])
            or not attempts.start_submission_returned(control, row)):
        refuse("the exact runtime launch and workspace token have not settled")
    observed, _, _ = attempts._observed(adapter, state["runtime_id"])
    helpers, unknown = intake._surviving_writers(adapter, control, attempt)
    if observed != "absent" or helpers or unknown:
        refuse("recovery cannot exclude the original runtime and custody writers")
    adapter.prove_no_writable_mount(os.path.dirname(line["line_path"]))
    if writer["state"] == "active":
        if writer["based_checkpoint_id"] != line["current_checkpoint_id"]:
            refuse("the writer's entry checkpoint changed")
        adapter.prove_line_consumable(control, assignment_id=attempt, generation=writer["assignment_generation"])
    elif writer["state"] != "revoked" or writer["revocation_reason"] != "checkpoint":
        refuse("the interrupted checkpoint does not own this writer")
    if profile.head_of(line["line_path"]) != request["head"]:
        refuse("the clean implementation line differs from the selected candidate")
    envelope, measured = sealing._completion_envelope(adapter.assignment_roots, adapter.declared_outputs,
        attempts._fixed_assignment(attempts._require_attempt(control, attempt)), "completed")
    if measured != request["manifest"]:
        refuse("retained completion envelope differs from the selected digest")
    outputs = envelope["outputs"]
    for output in outputs:
        if output["name"] == "handoff":
            handoff = output["result_metadata"].get("baton.native-handoff/1")
            if not isinstance(handoff, dict) or handoff.get("kind") != "final-submission":
                refuse("recovery requires an ordinary final submission")
    proposals = [o["result_metadata"]["baton.git-proposal/1"] for o in outputs if "baton.git-proposal/1" in o["result_metadata"]]
    if len(proposals) != 1 or not isinstance(proposals[0], dict) or proposals[0].get("head") != request["head"] or proposals[0].get("base") != line["declared_base"]:
        refuse("retained proposal does not identify the selected head and line base")
    expected = {o["name"]: (o["status"], o["content_manifest"]) for o in outputs}
    control.transact(KIND + ":" + attempt, KIND, manager_signature(KIND, request), lambda connection: request)
    token = _active.set(WriterProof(control, attempt, expected, measured, request["head"]))
    try:
        yield
    finally:
        _active.reset(token)
