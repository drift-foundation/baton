"""Compose the W236087 managed-correction packet's per-Job bindings.

WHY THIS EXISTS. Review 2026-09-22T06:36:24Z: "Prepare concrete proposed
values/documents for review within the owner-selected preparation scope; do not
confuse drafting them with granting or executing them. The prior review did not
prohibit preparing proposed bindings." The previous handoff declined to author
the per-Job worker documents at all and called the whole thing an owner
selection; that was too broad. This program DRAFTS them, and every document it
emits is held against the manager's own validator before it is written.

WHAT IT GRANTS: nothing. It opens no store, mints no session, reads no
credential, starts no runtime, performs no Git operation and enables nothing.
It writes JSON into a run directory. Running the packet is a separate, owner-
selected act performed by `supervisor.py`.

THE ONE VALUE IT CANNOT COMPUTE is `line_declared_base`: the declared base is a
commit object in the installed target, and creating it is an operator act this
implementer's deployment prohibits. It is an OPERAND here rather than a
placeholder in the output, so a packet is either complete or was never written.

THE MANIFEST IS THE PUBLISHED CONFORMANCE VECTOR, not a document written to
pass this build's rules -- `tests/manager/input_roots.py` gives the reason and
this follows it: a manifest written to satisfy the validator proves less than
the one the worker-contract finding published. What this substitutes into it are
the identities this deployment is accountable for, and each of those is the
digest of a document emitted beside the packet rather than opaque hex:

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

__all__ = ["CONTEXT_STATE_PATH", "compose", "write", "main"]

# The conversation-specific state file the accepted `/2` profile resolves from
# the committed admission's canonical UUID. No globbing, no directory
# substitution; `provider_context._profile` refuses anything else.
CONTEXT_STATE_PATH = ".claude/projects/-output/{conversation_id}.jsonl"

# The proposed bounds, from LIVE-CORRECTION-PROPOSAL.md. One correction is one
# extra implementer turn and one extra review turn; `supervisor.held_packet`
# refuses a packet whose counts do not agree with that.
BOUNDS = {"turn_seconds": 180, "total_seconds": 900, "cleanup_seconds": 60,
          "implementer_invocations": 2, "review_invocations": 2,
          "corrections": 1, "retry": False}

# THE WORKLOAD BOTH ROLES READ. One Job carries ONE input manifest -- every
# stage is compared against the Job's single input digest -- so there is one
# task document and one human contract, and the review criteria travel inside
# it rather than in a second document no stage could satisfy. The fixture
# repository carries the same three prose documents read-only at
# `/input/source`, so the reviewer can read the criteria it is being held to.
TASK_INSTRUCTIONS = (
    "IMPLEMENTATION. Change harness.py to print ready. Change only "
    "harness.py. Run python3 harness.py and publish the ordinary proposal. "
    "The initial output is `before`.\n\n"
    "FIRST REVIEW. Inspect the actual published proposal. If it prints "
    "`ready` rather than `READY`, return changes-requested with exactly this "
    "finding: \"Change the output to READY and preserve the trailing "
    "newline. Change only harness.py and rerun python3 harness.py.\" The "
    "same text is at source/REVIEW-FEEDBACK.md. Judge what was actually "
    "published; do not return a verdict this document asked for if the "
    "proposal does not warrant it.\n\n"
    "CORRECTION. Apply the review's findings to harness.py and rerun "
    "python3 harness.py.\n\n"
    "FINAL REVIEW. Accept only if harness.py prints READY with its trailing "
    "newline preserved, python3 harness.py really ran under the corrected "
    "attempt, and the retained candidate bytes are the ones the proposal "
    "names. The criteria are at source/ACCEPTANCE.md. An unexpected failure "
    "or a second correction request ends this one-run selection; there is no "
    "third implementer invocation.")

# THE PROSE DOCUMENTS THE FIXTURE REPOSITORY CARRIES beside `harness.py`, so
# each role can read the criteria it is held to from its own read-only mount.
FIXTURE_DOCUMENTS = ("harness.py", "TASK.md", "REVIEW-FEEDBACK.md",
                     "ACCEPTANCE.md")

# WHY `none` IS REFUSED HERE. Review 2026-09-22T07:03:13Z R4: the first draft
# copied the image-inspection container's `--network none` posture into the
# live deployment, and `oci.py` passes the selected value straight to
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
                f"is {value!r}. Create the fixture repository first -- "
                f"OPERATOR-236349.md step 4 -- and pass its HEAD.")
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
            bounds=None, places=None):
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
    bounds = dict(BOUNDS if bounds is None else bounds)
    # THE FIVE DIRECTORIES THIS RUN OWNS, derived under its own root. A
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
        "schema": "baton.managed-correction-runtime-profile/1",
        "name": "claude-context-implementation",
        "engine": "docker", "network": provider_network,
        "image_reference": image_reference, "image_digest": image_digest,
        "cli_build": cli_build, "model": "opus",
        "runtime_uid": os.getuid(),
        "scratch": {"tmp_bytes": 64 * 1024 * 1024,
                    "shm_bytes": 16 * 1024 * 1024},
        "workspace_min_bytes": source_boundary.MIN_WORKSPACE_BYTES + 1,
        "note": "one bounded managed correction; W236087"}
    policy = {
        "schema": "baton.managed-correction-execution-policy/1",
        "provider_turn_seconds": bounds["turn_seconds"],
        "verification_command_seconds": 900,
        "automatic_retry": False,
        "implementer_invocations": bounds["implementer_invocations"],
        "review_invocations": bounds["review_invocations"],
        "corrections": bounds["corrections"],
        "note": "the caps the admission gate enforces; W236087"}
    adapter = {
        "schema": "baton.managed-correction-adapter/1",
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
    manifest["outputs"] = [
        dict(held, name=name, type=kind, path=name, required=False)
        for name, kind in (("proposal", "git-change-proposal"),
                           ("findings", "directory-result"),
                           ("logs", "directory-result"))]
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

    # -- the two worker deployments -----------------------------------------
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
            # INDEPENDENCE IS THE WHOLE REASON A REVIEW EXISTS, and the
            # composition refuses a deployment whose two roles share a
            # participant or a principal before anything is opened.
            worker("review", participant=participants["review"],
                   principal=participants["review_principal"],
                   review_route="integration", contextual=False)]}

    submission = {
        "schema": "baton.v12.job-submission/2",
        "submission_id": run_id + "-submission",
        "jobs": [{
            "job_id": "job-a",
            "input_digest": job_input_identity(manifest),
            "policy_digest": policy_digest,
            "test_scope": [],
            "terminal_policy": "report-and-hold",
            # THE DECLARED PER-TURN CEILING LIVES HERE, which is the only
            # place it is a bound rather than a number in a manifest.
            "execution_limits": {
                "provider_turn_seconds": bounds["turn_seconds"]},
            "stages": [
                {"kind": "implementation", "work_id": participants["work_id"],
                 "profile_name": runtime_profile["name"],
                 "profile_digest": profile_digest, "depends_on": []},
                {"kind": "review", "work_id": participants["work_id"],
                 "profile_name": runtime_profile["name"],
                 "profile_digest": profile_digest,
                 "depends_on": [{"job_id": "job-a",
                                 "kind": "implementation"}]}]}]}

    packet = {
        "schema": "baton.managed-correction-packet/2",
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
            "job_id": "job-a"},
        "submission": {"path": os.path.join(run_root, "submission.json"),
                       "sha256": None, "job_id": "job-a"},
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
    """Is the Authority actually prepared for this deployment? R4.

    `bootstrap._compose` creates NO Work, route handler or grant for a zero-Job
    installation -- it says so in as many words -- and neither this composer nor
    `supervisor.prepare` provisions them. A participant string in a
    configuration is not a registered participant, so without this the first
    thing to discover the gap is the composed deployment, at the point where it
    resolves principals and mints five sessions.

    THIS ASKS AND WRITES NOTHING. It takes an already-open Authority handle and
    answers the list of exact missing preparations, in this module's own words.
    It grants nothing: provisioning is an owner act and its commands are in
    OPERATOR-236529.md step 5a.

    WHAT IT CANNOT ASK. `Authority` exposes no public reader for a route's
    handlers, so route registration is reported as unverifiable here rather
    than assumed. `capabilities_of` answers which capability NAMES a principal
    holds in any scope, not whether a grant is effective in this Work's scope;
    a missing name is conclusive, a present one is not, and this says so.
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
    named = {"implementation": participants["implementation"],
             "review": participants["review"]}
    for role, who in sorted(named.items()):
        try:
            authority.principal_of(who)
        except Exception as failure:                         # noqa: BLE001
            missing.append(f"the {role} participant {who!r} resolves to no "
                           f"principal ({type(failure).__name__})")
    for who, capability in sorted(
            ((participants["receipts"]["verification"], "verify"),
             (participants["receipts"]["review"], "review"),
             (participants["receipts"]["approval"], "approve"),
             (documents["deployment.json"]["integration_profile"]
              ["integrator_participant"], "integrate"))):
        try:
            held = authority.capabilities_of(who)
        except Exception:                                    # noqa: BLE001
            held = []
        if capability not in (held or []):
            missing.append(f"participant {who!r} holds no {capability!r} "
                           f"capability anywhere; grant it in this Work's "
                           f"scope")
    missing.append(
        "UNVERIFIABLE HERE: this Authority exposes no public reader for a "
        "route's handlers, so `impl` and `rview` handler registration for "
        f"{named['implementation']!r} and {named['review']!r} must be "
        "asserted by the operator's own preparation rather than proved by "
        "this preflight")
    return missing


def write(run_root, documents, *, checkout):
    """Hold the composition against the MANAGER'S validator, then publish.

    `stage_execution.held_configuration` is the same function the serving
    deployment and `tools.bootstrap` both run, so a worker document missing its
    adapter, profile, credentials, workload, workspace or launch members is
    refused by name here rather than discovered with a container started.
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

    stage_execution.held_configuration(documents["deployment.json"],
                                       checkout=checkout)
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
        prog="packet_bindings",
        description="Compose the managed-correction packet's per-Job "
                    "bindings. Grants nothing and runs nothing.")
    parser.add_argument("--selections", required=True,
                        help="the JSON document naming every owner selection")
    parser.add_argument("--base", required=True,
                        help="the fixture repository's HEAD, from step 4")
    parser.add_argument("--run-root", required=True)
    taken = parser.parse_args(argv)

    with open(taken.selections, "r", encoding="utf-8") as handle:
        selections = json.load(handle)
    documents = compose(base=taken.base, run_root=taken.run_root,
                        **selections["compose"])
    places = write(taken.run_root, documents,
                   checkout=selections["checkout"])
    print(json.dumps({name: _sha256(place)
                      for name, place in sorted(places.items())},
                     indent=2, sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
