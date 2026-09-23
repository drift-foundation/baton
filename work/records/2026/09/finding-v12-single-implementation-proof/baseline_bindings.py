"""Compose W239528's single-implementation packet bindings.

WHAT IT GRANTS: nothing. It opens no store, mints no session, reads no
credential, starts no runtime, performs no Git operation and enables nothing.
It writes JSON into a run directory. Running the packet is a separate,
owner-selected act performed by `baseline.py`.

WHAT IS DIFFERENT FROM THE RESUME JOB'S COMPOSER, and each difference is the
split ruling rather than a simplification:

  * ONE SUBMITTED STAGE, AND NO REVIEW STAGE. W239533 reviews this proposal in
    its own run, against its own independently bound task document; a review
    container started here would be that Job's workload arriving inside this
    one.

    THE DEPLOYMENT STILL CONFIGURES A REVIEW WORKER, and that is the manager's
    rule rather than this composer's preference. `stage_execution._held_workers`
    refuses a configuration naming no review worker in as many words -- "a Job
    that cannot be produced or independently reviewed serves nothing" -- and
    that invariant is about what a deployment is CAPABLE of, not about what one
    submission asks for. Deleting the worker to make this Job look smaller
    would be relaxing an independence rule to pass a validator, so the
    configured reviewer stays, with its own participant and principal, and
    three separate things keep it from ever running here: the submission
    declares one stage, `baseline.KINDS` is closed over `implementation`, and
    the workload evidence reports any other kind as a shortfall. What this run
    establishes is therefore stronger than "no reviewer existed" -- it is "a
    reviewer was configured and available, and this run started exactly one
    container anyway".
  * ONE IMPLEMENTER INVOCATION. A second would be a correction, and a
    correction needs a review to correct against.
  * THE FIXTURE CARRIES NO REVIEW MATERIAL. W236087's fixture shipped
    `ACCEPTANCE.md` and `REVIEW-FEEDBACK.md` beside the subject file, and its
    live implementation agent read the acceptance document out of the tree and
    graded itself against it. This tree carries the subject and the operator's
    record of the selection, and nothing that describes judging.
  * THE PROPOSAL OUTPUT IS REQUIRED. `IMPLEMENTATION_OUTPUTS` is exactly
    `("proposal",)`, and this run exists to establish that one turn produced
    one. An optional declaration would let a turn that published nothing answer
    the declaration honestly and still be counted as having run.

THE ONE VALUE IT CANNOT COMPUTE is `line_declared_base`: the declared base is a
commit object in the installed target, and creating it is an operator act this
implementer's deployment prohibits. It is an OPERAND here rather than a
placeholder in the output, so a packet is either complete or was never written.

THE MANIFEST IS THE PUBLISHED CONFORMANCE VECTOR, not a document written to
pass this build's rules -- `tests/manager/input_roots.py` gives the reason and
this follows it. What is substituted into it are the identities this deployment
is accountable for, and each is the digest of a document emitted beside the
packet rather than opaque hex:

    runtime profile   profile.runtime.json   -> profile_digest
    execution policy  policy.json            -> policy_digest
    adapter identity  adapter.json           -> adapter_digest

Naming them this way is what makes them reviewable: an owner can read what was
proposed instead of being asked to approve a hash.
"""

import argparse
import hashlib
import json
import os
import sys

__all__ = ["CONTEXT_STATE_PATH", "BOUNDS", "TASK_INSTRUCTIONS",
           "FIXTURE_DOCUMENTS", "compose", "write", "preflight", "main"]

# The conversation-specific state file the accepted `/2` profile resolves from
# the committed admission's canonical UUID. No globbing, no directory
# substitution; `provider_context._profile` refuses anything else.
CONTEXT_STATE_PATH = ".claude/projects/-output/{conversation_id}.jsonl"

# The proposed bounds. ONE implementer invocation, and no review or correction
# member at all: `baseline.held_packet` reads exactly these names, so a packet
# carrying a zeroed review count is refused rather than silently tolerated.
# THE BACKSTOP IS 300 SECONDS AND THE NUMBER IS ARGUED. Owner pass 243171
# asked for "a shorter justified baseline timeout as a backstop", after a run
# that spent 443 seconds of 900 discovering that nothing was happening.
#
# WHAT IT HAS TO COVER: one provider turn at its own declared ceiling
# (`turn_seconds`, 180), plus the launch, the exchange, the ending's nine
# journalled steps and the publication. WHAT IT NO LONGER HAS TO COVER: a run
# that has stopped moving, which `baseline.STALLED_TICKS` now detects in six
# seconds. The bound stopped being the detector, so it can be the backstop it
# was always meant to be.
#
# MEASURED AGAINST THE TWO REAL RUNS: the expired-credential provider answered
# in 31 ms and its corrected path settles in seconds; the successful provider
# took 18.3 seconds and its run reached its terminal state well inside a
# minute. 300 leaves two minutes of headroom over a FULL-LENGTH 180-second
# provider turn, which neither real run came close to using.
BOUNDS = {"turn_seconds": 180, "total_seconds": 300, "cleanup_seconds": 60,
          "implementer_invocations": 1, "retry": False}

# THE REQUIREMENTS, AND ONLY THE REQUIREMENTS.
#
# `claude_agent` composes the implementation prompt from this one string:
# `_prompt` gives it to the implementation role as "you are working in a
# private copy of the source tree... Edit files here directly".
#
# W236087's live run failed exactly here. Its task document was a four-stage
# SCRIPT -- IMPLEMENTATION, FIRST REVIEW, CORRECTION, FINAL REVIEW -- including
# the finding the first review was to return. Handed to the implementation role
# as work to do, the agent did all four inside one provider turn, answered with
# "Verdict: accept", and committed its own history to the private line on the
# way; `ClaudeAgent._unmoved` refused to adopt a history it did not write and
# the turn faulted with nothing published. `DIAGNOSIS-239528.md` carries the
# evidence.
#
# So this says what the CHANGE must achieve, says that judging is not this
# stage, and says who owns the commit. The last part is not decoration: the
# provider edits and verifies, and a provider that commits takes the turn's
# only publishable account away from the adapter that is accountable for it.
TASK_INSTRUCTIONS = (
    "Change harness.py so that running it prints READY followed by a newline, "
    "and nothing else. It currently prints `before`. Change only harness.py. "
    "Run `python3 harness.py` yourself and make sure it exits 0.\n\n"
    "SCOPE. Implementing this change is your whole stage. Do not review, "
    "assess or grade your own work, and do not write a verdict, a decision or "
    "a report of any kind: an independent reviewer with its own separate run "
    "does that, and a proposal that arrived with its own approval attached "
    "would have no independent review at all.\n\n"
    "EDIT THE FILES; DO NOT COMMIT THEM. You are working in a private "
    "repository checkout, and the worker that launched you authors exactly one "
    "commit per turn and publishes it as your proposal. Leave your change in "
    "the working tree. Do not run `git commit`, `git add`, `git checkout`, "
    "`git branch`, `git stash` or any other command that moves HEAD or writes "
    "history: a turn whose history moved cannot be given an account of and is "
    "refused, so committing your own work is how it gets thrown away.\n\n"
    "Make the change, verify it, and stop there.")

# WHAT THE FIXTURE REPOSITORY CARRIES. `harness.py` is the subject and `TASK.md`
# is the operator's committed record of the selection. There is deliberately no
# acceptance or review-feedback document: this Job has no reviewer, and the one
# live run that shipped those documents had its implementation agent read them
# out of the tree and grade itself against them.
FIXTURE_DOCUMENTS = ("harness.py", "TASK.md")

# WHY `none` IS REFUSED HERE. `oci.py` passes the selected value straight to
# `--network`. A production Claude provider reaches an external API; there is
# no local provider or proxy in this packet, so a `none` network is a
# deployment that cannot answer the question the run exists to ask. Selecting
# a bounded network authorizes no call -- the owner still selects the live
# command separately -- but a packet that could never work is not a packet.
REFUSED_NETWORKS = ("none",)


class BindingRefusal(Exception):
    """This program refuses rather than emitting a document it cannot hold."""


def _refuse(message):
    raise BindingRefusal(message)


def _sha256(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            reading.update(block)
    return reading.hexdigest()


def _tree(root):
    found = {}
    for base, dirs, names in os.walk(root):
        dirs[:] = [one for one in sorted(dirs) if one != "__pycache__"]
        for name in sorted(names):
            whole = os.path.join(base, name)
            found[os.path.relpath(whole, root)] = _sha256(whole)
    return found


def _write(place, document):
    with open(place, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return place


def _base_object(value):
    if type(value) is not str or len(value) != 40 \
            or any(one not in "0123456789abcdef" for one in value):
        _refuse(f"the declared base is one full lower-case object name; this "
                f"is {value!r}. Create the fixture repository first and pass "
                f"its HEAD.")
    return value


def _network(value):
    if type(value) is not str or not value:
        _refuse("the provider network is one non-empty engine network name")
    if value in REFUSED_NETWORKS:
        _refuse(f"{value!r} is refused for a provider deployment: the worker "
                f"reaches an external Claude API and this packet composes no "
                f"local provider or proxy, so a container with that network "
                f"could never answer the question this run exists to ask. "
                f"Select the bounded egress network your deployment provides.")
    return value


def _job_identity(value, *, derived):
    """One Job identity, and it is this packet's own.

    Derived as `job-<run_id>` when the caller names none, so a fresh run
    identity is a fresh Job identity without the operator having to remember
    that they are two different things. A caller may name one explicitly --
    an operator reusing a store may need an identity that does not follow the
    run name -- and it is checked the same way either way.

    `job-a` IS REFUSED BY NAME. It is the fixture identity every earlier
    packet this composer wrote carried, and the one already recorded in the
    W236087 instance's Job store; composing it again is the collision review
    2026-09-22T15:32:51Z reproduced.
    """
    held = ("job-" + value) if derived else value
    if type(held) is not str or not held or len(held) > 96:
        _refuse(f"the Job identity is one non-empty name of at most 96 "
                f"characters; this is {held!r}")
    if any(one not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for one in held):
        _refuse(f"the Job identity {held!r} is lower-case letters, digits, "
                f"'-' and '_'; it is a durable identity, not a title")
    if held == "job-a":
        _refuse("'job-a' is the fixture Job identity and is already recorded "
                "in the W236087 instance's Job store. One Job identity names "
                "one pipeline, so composing it again is a submission this "
                "packet could not make. Derive it from a fresh run_id, or "
                "name an identity the selected store does not hold.")
    return held


def _evidence(value):
    if type(value) is not str or len(value) != 71 \
            or not value.startswith("sha256:"):
        _refuse("the evidence digest is one sha256 digest of retained "
                "evidence")
    if set(value[7:]) == {"0"}:
        _refuse("an all-zero evidence digest is a sentinel, not retained "
                "evidence. Name the digest of the accepted evidence this "
                "candidate profile rests on, or do not compose a packet.")
    return value


def compose(*, instance, run_root, source_root, base, image_reference,
            image_digest, cli_build, manager_source, supervisor_path,
            vectors, participants, credential_sources, credential_profile,
            evidence_digest, provider_network, run_id, work, claim, note,
            code_boundary=None, bounds=None, places=None, job_id=None):
    """Every document this packet needs, composed and internally consistent.

    Returns a mapping of filename to document. Nothing is written here and
    nothing is validated here: `write` does both, in that order, so a
    composition the manager would refuse never reaches the disk.
    """
    from baton_v12.contracts import digest, digest_of_bytes, job_input_identity
    from baton_v12.worker_manager import provider_context as context
    from baton_v12.worker_manager import source_boundary
    from tools import single_worker, stage_execution

    _base_object(base)
    _network(provider_network)
    _evidence(evidence_digest)
    # THE CODE TREE, BOUND ONCE. `stage_execution` infers this from its own
    # `__file__` when nobody says, and for a relocated manager source that
    # inference answers the run root's PARENT -- so the run's own stores get
    # classified as living inside the code tree and composition refuses a
    # deployment this composer had just validated under a different boundary.
    code_boundary = manager_source if code_boundary is None else code_boundary
    if not os.path.isabs(code_boundary) \
            or os.path.normpath(code_boundary) != code_boundary:
        _refuse(f"the code boundary is one absolute canonical directory; this "
                f"is {code_boundary!r}")
    held = os.path.realpath(manager_source)
    whole = os.path.realpath(code_boundary)
    if os.path.commonpath([whole, held]) != whole:
        _refuse(f"the code boundary {code_boundary!r} does not contain the "
                f"manager source {manager_source!r}, so it would not protect "
                f"the code the run imports")
    # THE JOB IDENTITY IS COMPOSED, NOT A CONSTANT. Review
    # 2026-09-22T15:32:51Z R2 reproduced this through the public submission
    # API: every packet this composer wrote named `job-a`, so two packets with
    # different `run_id`s still collided in one Job store --
    # "'job-a' is already recorded by another submission; one Job identity
    # names one pipeline". A run identity is not a Job identity, and saying
    # "select a fresh run_id" did not make the documented instance reuse
    # executable. It is derived from `run_id` by default so the two move
    # together, and `baseline.survey` refuses a collision before any owner act
    # rather than at submission, which is after a one-run grant has committed.
    job_id = _job_identity(run_id if job_id is None else job_id,
                           derived=job_id is None)
    bounds = dict(BOUNDS if bounds is None else bounds)
    # THE COMPOSER REFUSES THE OTHER JOB'S WORKLOAD. A caller passing a review
    # count or a correction count is describing W236087's run; composing it
    # here under this Job's name is how a baseline quietly becomes something
    # else, so it is named and refused rather than ignored.
    intruding = sorted({"review_invocations", "corrections"} & set(bounds))
    if intruding:
        _refuse(f"these bounds name {', '.join(intruding)}; W239528 drives one "
                f"implementation container and its review is a separate Job")
    if bounds.get("implementer_invocations") != 1:
        _refuse(f"this packet drives ONE implementation container; these "
                f"bounds declare "
                f"{bounds.get('implementer_invocations')!r}")

    # THE FOUR DIRECTORIES THIS RUN OWNS, derived under its own root. A
    # deterministic composition proof drives these documents over an already
    # configured workspace storage, so the caller may name them instead --
    # overriding WHERE they are, never what they are for.
    derived = {name: os.path.join(run_root, name) for name in
               ("workspaces", "launch", "credentials", "private-contexts",
                "deployment-state")}
    if places is not None:
        unknown = sorted(set(places) - set(derived))
        if unknown:
            _refuse(f"a run directory override names {', '.join(unknown)}, "
                    f"which this composition does not place")
        derived.update(places)
    places = derived

    # -- the three identities this deployment is accountable for ------------
    runtime_profile = {
        "schema": "baton.single-implementation-runtime-profile/1",
        "name": "claude-context-implementation",
        "engine": "docker", "network": provider_network,
        "image_reference": image_reference, "image_digest": image_digest,
        "cli_build": cli_build, "model": "opus",
        "runtime_uid": os.getuid(),
        "scratch": {"tmp_bytes": 64 * 1024 * 1024,
                    "shm_bytes": 16 * 1024 * 1024},
        "workspace_min_bytes": source_boundary.MIN_WORKSPACE_BYTES + 1,
        "note": "one bounded managed implementation; W239528"}
    policy = {
        "schema": "baton.single-implementation-execution-policy/1",
        "provider_turn_seconds": bounds["turn_seconds"],
        "verification_command_seconds": 900,
        "automatic_retry": False,
        "implementer_invocations": bounds["implementer_invocations"],
        "note": "the caps the admission gate enforces; W239528"}
    adapter = {
        "schema": "baton.single-implementation-adapter/1",
        "adapter_name": "docker-single-worker",
        "engine": "docker", "network": provider_network,
        "entrypoint": ["python3", "/opt/baton/dogfood_entry.py"],
        "argv_policy": dict(context.ARGV_POLICY),
        "environment_policy": dict(context.ENVIRONMENT_POLICY)}
    profile_digest = digest(runtime_profile)
    policy_digest = digest(policy)
    adapter_digest = digest(adapter)

    # -- the frozen task the workload reads at /input/task.json -------------
    task = {"schema": "baton.dogfood-task/2",
            "task_id": run_id,
            "instructions": TASK_INSTRUCTIONS,
            "source_root": single_worker.SOURCE_DESTINATION,
            "source_profile": "git-line",
            "declared_base": base,
            "verification": ["python3", "harness.py"]}
    task_bytes = json.dumps(task, sort_keys=True).encode("utf-8")

    # -- the input manifest, from the published vector ----------------------
    with open(vectors, "r", encoding="utf-8") as handle:
        corpus = json.loads(handle.read())
    manifest = dict(next(
        one["document"] for one in corpus["valid"]
        if one["document"].get("schema") == "baton.worker-manifest/input"))
    manifest["work_ref"] = {"authority_uuid": instance["authority_uuid"],
                            "work_id": participants["work_id"]}
    manifest["policy_digest"] = policy_digest
    manifest["runtime_profile_digest"] = profile_digest
    manifest["worker_image_digest"] = image_digest
    manifest["human_contract"] = {
        "artifact_id": run_id + "-task",
        "media_type": "application/json",
        "bytes": len(task_bytes),
        "content_digest": digest_of_bytes(task_bytes),
        "locator": "artifact://contracts/" + run_id + "-task"}
    source = dict(manifest["sources"][0])
    source["destination"] = single_worker.SOURCE_DESTINATION
    # THE EMPTY MOUNTPOINT'S MANIFEST, NOT THE SOURCE'S. `/4` nominates and
    # mounts; it does not walk, copy or hash the nominated tree, so the frozen
    # manifest declares the empty directory the read-only bind lands on.
    source["content_manifest"] = {"entries": [], "entry_count": 0,
                                  "total_bytes": 0,
                                  "tree_digest": single_worker.EMPTY_TREE_DIGEST}
    source["consumption"] = source_boundary.source_consumption("git-line")
    manifest["sources"] = [source]
    held = dict(manifest["outputs"][0])
    # ONE DECLARED RESULT, AND IT IS REQUIRED. `IMPLEMENTATION_OUTPUTS` is
    # exactly `("proposal",)`. `findings` and `logs` are the REVIEW turn's
    # outputs and this Job runs no review turn, so declaring them would be
    # declaring the next Job's half of a shared workload.
    manifest["outputs"] = [dict(held, name="proposal",
                                type="git-change-proposal", path="proposal",
                                required=True)]
    # AND THE RESERVED RECEIPT DECLARATION the contextual worker answers.
    manifest["outputs"].append({
        "name": "provider-context-receipt", "type": "directory-result",
        "path": "provider-context-receipt", "required": False,
        "constraints": {"max_bytes": 16384, "max_entries": 1,
                        "allowed_media_types": ["application/octet-stream"],
                        "link_policy": "forbid", "validator_digest": None}})
    manifest.pop("manifest_digest", None)
    manifest["manifest_digest"] = digest(manifest)

    # -- the candidate context profile, `/2` --------------------------------
    context_profile = {
        "schema": context.SESSION_PROFILE_SCHEMA,
        "qualification": "candidate",
        "evidence_digest": evidence_digest,
        "cli_build": cli_build,
        "image_digest": image_digest,
        "adapter_digest": adapter_digest,
        "runtime_profile_digest": profile_digest,
        "argv_policy_digest": digest(context.ARGV_POLICY),
        "environment_policy_digest": digest(context.ENVIRONMENT_POLICY),
        "layout_version": "claude-context-layout/2",
        "model": "opus", "reported_model": "opus",
        "cwd": "/output",
        "state_paths": [CONTEXT_STATE_PATH],
        "max_entries": 4096, "max_bytes": 64 * 1024 * 1024,
        "retention_policy_digest": instance["retention_policy_digest"]}
    context_digest = digest(context_profile)

    # -- the worker deployments ----------------------------------------------
    # `review_route` is where an answered, frozen, taken-into-custody result is
    # HANDED ON. The implementation worker's is `rview` for the reason this Job
    # runs no review turn: the retained proposal travels to the review route
    # and WAITS there for W239533's own run, rather than being consumed by a
    # container this Job started.
    #
    # THE REVIEW WORKER IS CONFIGURED AND NEVER ADMITTED. The manager's own
    # validator requires it -- see the module docstring -- and independence is
    # enforced on the configuration: `_independent` refuses a deployment whose
    # two roles share a participant or a principal, before anything is opened.
    def worker(role, *, participant, principal, review_route, contextual):
        deployment = {
            "schema": (single_worker.CONTEXT_CONFIG_SCHEMA if contextual
                       else single_worker.CONFIG_SCHEMA),
            "authority_store": instance["authority_store"],
            "authority_uuid": instance["authority_uuid"],
            "participant": participant, "principal": principal,
            "profile_name": runtime_profile["name"],
            "profile_digest": profile_digest,
            "policy_digest": policy_digest,
            "adapter_name": adapter["adapter_name"],
            "adapter_digest": adapter_digest,
            "engine": "docker", "image_digest": image_digest,
            "network": provider_network,
            "workspace_storage": places["workspaces"],
            "workspace_group": os.getgid(),
            "launch_home": os.path.join(places["launch"], role),
            "credential_home": os.path.join(places["credentials"], role),
            "credential_sources": credential_sources,
            "credential_slots": sorted(credential_profile),
            "credential_profile": dict(credential_profile),
            "nominated_source": source_root,
            "workspace_capacity": {
                "max_bytes": source_boundary.MIN_WORKSPACE_BYTES + 1},
            "input_manifest": manifest,
            "task_document": os.path.join(run_root, "task.json"),
            "launch_contract": "v12-assignment-1",
            "launch_role": role,
            "review_route": review_route,
            "retention_policy_digest": instance["retention_policy_digest"],
            "retention_disposition": "retain"}
        if contextual:
            deployment["provider_context"] = {
                "mode": "required", "storage": places["private-contexts"],
                "profile_digest": context_digest}
        return {"worker_id": f"{role}-worker", "role": role,
                "deployment": deployment}

    deployment = {
        "schema": stage_execution.CONFIG_SCHEMA,
        "authority_store": instance["authority_store"],
        "authority_uuid": instance["authority_uuid"],
        "integration_store": instance["integration_store"],
        "state_root": places["deployment-state"],
        "pool_generation": 1, "policy_generation": 1,
        "line_declared_base": base,
        "canonical_target_id": base,
        "job_work_id": participants["work_id"],
        "review_work_id": participants["work_id"],
        "checkpoint_profile": "git",
        "integration_profile": dict(instance["integration_profile"]),
        "receipt_participants": dict(participants["receipts"]),
        "retention_policy_digest": instance["retention_policy_digest"],
        "retention_disposition": "retain",
        "workers": [
            worker("implementation",
                   participant=participants["implementation"],
                   principal=participants["implementation_principal"],
                   review_route="rview", contextual=True),
            worker("review", participant=participants["review"],
                   principal=participants["review_principal"],
                   review_route="integration", contextual=False)]}

    submission = {
        "schema": "baton.v12.job-submission/2",
        "submission_id": run_id + "-submission",
        "jobs": [{
            "job_id": job_id,
            "input_digest": job_input_identity(manifest),
            "policy_digest": policy_digest,
            "test_scope": [],
            "terminal_policy": "report-and-hold",
            # THE DECLARED PER-TURN CEILING LIVES HERE, which is the only
            # place it is a bound rather than a number in a manifest.
            "execution_limits": {
                "provider_turn_seconds": bounds["turn_seconds"]},
            # ONE STAGE. No review stage and therefore no dependency: what
            # depends on this proposal is another Job's submission.
            "stages": [
                {"kind": "implementation", "work_id": participants["work_id"],
                 "profile_name": runtime_profile["name"],
                 "profile_digest": profile_digest, "depends_on": []}]}]}

    packet = {
        "schema": "baton.single-implementation-packet/1",
        "run_id": run_id, "work": work, "claim": claim, "note": note,
        "worker_image": {"reference": image_reference,
                         "config_digest": image_digest,
                         "worker_files": dict(participants["worker_files"])},
        "manager_runtime": {
            "path": instance["runtime_path"],
            "executable_sha256": _sha256(os.path.join(
                instance["runtime_path"], "baton-v12-stack")),
            "build_commit": instance["build_commit"]},
        "manager_source": {"path": manager_source,
                           "packages": ["baton_v12", "tools"],
                           "file_count": len(_tree(manager_source)),
                           "files": _tree(manager_source)},
        "supervisor": {"path": supervisor_path,
                       "sha256": _sha256(supervisor_path)},
        "code_boundary": code_boundary,
        "deployment": {
            "config_path": os.path.join(run_root, "deployment.json"),
            "config_sha256": None,
            "job_store": instance["job_store"],
            "control_store": instance["control_store"],
            "authority_store": instance["authority_store"],
            "authority_uuid": instance["authority_uuid"],
            "state_root": places["deployment-state"]},
        "context": {
            "storage_path": places["private-contexts"],
            "excluded_roots": [source_root, places["workspaces"]],
            "runtime_uid": os.getuid(),
            "profile_path": os.path.join(run_root, "context-profile.json"),
            "profile_sha256": None,
            "profile_digest": context_digest,
            "job_id": job_id},
        "submission": {"path": os.path.join(run_root, "submission.json"),
                       "sha256": None, "job_id": job_id},
        "fixture": {"source_root": source_root,
                    "files": dict(participants["fixture_files"])},
        "bounds": bounds,
        "outcome_path": os.path.join(run_root, "outcome.json")}

    return {"runtime-profile.json": runtime_profile,
            "policy.json": policy,
            "adapter.json": adapter,
            "task.json": task,
            "context-profile.json": context_profile,
            "deployment.json": deployment,
            "submission.json": submission,
            "PACKET.json": packet}


def preflight(authority, documents, participants):
    """Is the Authority actually prepared for this deployment?

    `bootstrap._compose` creates NO Work, route handler or grant for a zero-Job
    installation, and neither this composer nor `baseline.prepare` provisions
    them. A participant string in a configuration is not a registered
    participant, so without this the first thing to discover the gap is the
    composed deployment, at the point where it resolves principals and mints
    sessions.

    THIS ASKS AND WRITES NOTHING. It takes an already-open Authority handle and
    answers the list of exact missing preparations, in this module's own words.
    It grants nothing: provisioning is an owner act.

    WHAT IT CANNOT ASK. `Authority` exposes no public reader for a route's
    handlers, so route registration is reported as unverifiable here rather
    than assumed. `capabilities_of` answers which capability NAMES a principal
    holds in any scope, not whether a grant is effective in this Work's scope;
    a missing name is conclusive, a present one is not, and this says so.

    BOTH CONFIGURED PARTICIPANTS ARE ASKED ABOUT, including the review one
    this Job never launches. The deployment resolves principals for every
    worker it configures, so an unresolvable review principal refuses the
    composition whether or not a review container is ever started; discovering
    that at composition time would be discovering it after the owner acts had
    already committed.
    """
    work_id = participants["work_id"]
    missing = []
    try:
        authority.project_work(work_id)
    except Exception as failure:                             # noqa: BLE001
        missing.append(
            f"Work {work_id!r} does not exist or is unreadable "
            f"({type(failure).__name__}); create it on the implementation "
            f"route with the assignment contract the launch documents name")
        return missing
    who = participants["implementation"]
    named = {"implementation": who, "review": participants["review"]}
    for role, holder in sorted(named.items()):
        try:
            authority.principal_of(holder)
        except Exception as failure:                         # noqa: BLE001
            missing.append(f"the {role} participant {holder!r} resolves to no "
                           f"principal ({type(failure).__name__})")
    for holder, capability in sorted(
            ((participants["receipts"]["verification"], "verify"),
             (participants["receipts"]["review"], "review"),
             (participants["receipts"]["approval"], "approve"),
             (documents["deployment.json"]["integration_profile"]
              ["integrator_participant"], "integrate"))):
        try:
            held = authority.capabilities_of(holder)
        except Exception:                                    # noqa: BLE001
            held = []
        if capability not in (held or []):
            missing.append(f"participant {holder!r} holds no {capability!r} "
                           f"capability anywhere; grant it in this Work's "
                           f"scope")
    missing.append(
        "UNVERIFIABLE HERE: this Authority exposes no public reader for a "
        f"route's handlers, so `impl` handler registration for {who!r} must be "
        "asserted by the operator's own preparation rather than proved by "
        "this preflight. This Job submits no review stage, so `rview` handler "
        "registration is not a prerequisite of running it.")
    return missing


def write(run_root, documents, *, checkout=None):
    """Hold the composition against the MANAGER'S validator, then publish.

    `stage_execution.held_configuration` is the same function the serving
    deployment and `tools.bootstrap` both run, so a worker document missing its
    adapter, profile, credentials, workload, workspace or launch members is
    refused by name here rather than discovered with a container started.

    IT HOLDS AGAINST THE PACKET'S OWN CODE BOUNDARY. Passing a different one
    here is what lets a packet pass preparation and refuse at composition.
    `checkout` remains an operand only so a caller can prove the disagreement;
    it defaults to the bound value.
    """
    from tools import stage_execution

    os.makedirs(run_root, exist_ok=True)
    # THE OPERANDS THE VALIDATOR READS FROM DISK COME FIRST. `_task_bytes`
    # opens the configured task document and compares it with the manifest's
    # human contract, and the workspace/launch/credential roots are checked as
    # directories -- so holding the composition before they exist would refuse
    # for the fixture's own reason rather than the deployment's.
    places = {}
    for name in ("runtime-profile.json", "policy.json", "adapter.json",
                 "context-profile.json"):
        places[name] = _write(os.path.join(run_root, name), documents[name])
    # THE TASK IS WRITTEN AS THE EXACT BYTES THE MANIFEST DECLARES. Its
    # `human_contract` carries their length and digest and `_task_bytes`
    # compares both, so a pretty-printed copy of the same object is a
    # different document as far as the launch boundary is concerned.
    places["task.json"] = os.path.join(run_root, "task.json")
    with open(places["task.json"], "wb") as handle:
        handle.write(json.dumps(documents["task.json"],
                                sort_keys=True).encode("utf-8"))
    for one in documents["deployment.json"]["workers"]:
        for member in ("workspace_storage", "launch_home", "credential_home"):
            os.makedirs(one["deployment"][member], mode=0o700, exist_ok=True)
    os.makedirs(documents["deployment.json"]["state_root"], mode=0o700,
                exist_ok=True)
    os.makedirs(documents["PACKET.json"]["context"]["storage_path"],
                mode=0o700, exist_ok=True)

    stage_execution.held_configuration(
        documents["deployment.json"],
        checkout=(documents["PACKET.json"]["code_boundary"]
                  if checkout is None else checkout))
    for name in ("deployment.json", "submission.json"):
        places[name] = _write(os.path.join(run_root, name), documents[name])

    # THE PACKET'S OWN DIGESTS, TAKEN FROM WHAT WAS JUST WRITTEN. Composing
    # them earlier would have been hashing a document that did not exist yet.
    packet = documents["PACKET.json"]
    packet["deployment"]["config_sha256"] = _sha256(places["deployment.json"])
    packet["context"]["profile_sha256"] = _sha256(
        places["context-profile.json"])
    packet["submission"]["sha256"] = _sha256(places["submission.json"])
    places["PACKET.json"] = _write(os.path.join(run_root, "PACKET.json"),
                                   packet)
    return places


def main(argv=None, *, stream=None):
    stream = sys.stdout if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="baseline_bindings",
        description="Compose the single-implementation packet's per-Job "
                    "bindings. Grants nothing and runs nothing.")
    parser.add_argument("--selections", required=True,
                        help="the JSON document naming every owner selection")
    parser.add_argument("--base", required=True,
                        help="the fixture repository's HEAD")
    parser.add_argument("--run-root", required=True)
    taken = parser.parse_args(argv)

    with open(taken.selections, "r", encoding="utf-8") as handle:
        selections = json.load(handle)
    documents = compose(base=taken.base, run_root=taken.run_root,
                        **selections["compose"])
    # NO `checkout` OPERAND HERE. The packet's own bound boundary is what the
    # runtime will use, so validating against anything else would reproduce
    # exactly the disagreement this composition exists to avoid.
    places = write(taken.run_root, documents)
    print(json.dumps({name: _sha256(place)
                      for name, place in sorted(places.items())},
                     indent=2, sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
