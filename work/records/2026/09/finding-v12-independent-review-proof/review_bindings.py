"""Compose W239533's review-only packet bindings.

WHAT IT GRANTS: nothing. It opens no writable store, mints no session, reads no
credential, starts no runtime, performs no Git operation and enables nothing.
It reads the producer's retained control store READ-ONLY through
`attachment.py` and writes JSON into a run directory.

WHAT IS DIFFERENT FROM W239528'S COMPOSER, and every difference is this Job's
selected scope rather than a preference:

  * ONE SUBMITTED STAGE AND IT IS A REVIEW. The implementation worker stays
    CONFIGURED for the same reason the reviewer stayed configured over there --
    `stage_execution._held_workers` refuses a deployment that names only one
    role, "a Job that cannot be produced or independently reviewed serves
    nothing" -- and it is never admitted: the submission declares one review
    stage and the supervisor's kinds are closed over `review`.
  * THE SUBJECT IS READ, NOT DECLARED. `line_declared_base`, the v12 Work, the
    nominated source, the workspace storage and the checkpoint all come out of
    the producer's own committed rows through `attachment.subject`. A packet
    cannot name a base or a checkpoint the retained run does not hold, because
    nothing here is an operand a caller could get wrong.
  * THE DECLARED OUTPUTS ARE `findings` AND `logs`, both required, and there is
    no `proposal` output at all. `claude_agent._review_report` writes
    `baton.review-report/1` into `findings`, and `review_driver`'s
    `review_verdict_from_result` reads `baton.checkpoint-review/1` out of the
    frozen findings. A review turn that published nothing would otherwise
    answer its declaration honestly and still be counted as having reviewed.
  * THE BOUNDS NAME `review_invocations`, AND REFUSE THE OTHER JOB'S. A packet
    carrying `implementer_invocations` or `corrections` is describing W239528
    or W236087; composing it under this Job's name is how a review quietly
    becomes an implementation, so both are named and refused.
  * THE TASK DOCUMENT IS THIS JOB'S OWN AND IT CARRIES CRITERIA, NOT WORK.
    The producer's `task.json` stays exactly where it is; the reviewer reads a
    different frozen document at its own `/input/task.json`.

WHAT IT DELIBERATELY SHARES WITH THE PRODUCER, each because the product
requires it and `attachment.py`'s docstring gives the mechanism: the v12
Authority and Work, the control store, the workspace storage and the nominated
source. Those four are the line's identity and custody. Everything that makes
this a separate execution -- Job store, Job identity, submission, stage,
attempt, generation, task, launch home, credential home, private-context
storage, deployment state, outcome -- is this Job's own.

WHAT IS REUSED RATHER THAN COPIED. The digest, tree, write, base, network,
evidence and Job-identity helpers are imported from W239528's accepted
`baseline_bindings`. They are that Job's reviewed bytes and importing them is
what the owner reroute means by "Reuse accepted components"; a second copy
would be a second thing to keep correct. The import is READ-ONLY -- nothing
here edits that module or its dossier.
"""

import argparse
import inspect
import json
import os
import sys

import attachment

__all__ = ["PACKET_SCHEMA", "BOUNDS", "REVIEW_CRITERIA", "REVIEW_OUTPUTS",
           "compose", "write", "preflight", "main"]

PACKET_SCHEMA = "baton.independent-review-packet/1"

# The instant the read-only opener is handed. It stamps nothing -- this module
# performs no act -- and it is a constant rather than a live clock so that
# composing the same selections twice produces the same documents byte for
# byte.
COMPOSITION_INSTANT = "1970-01-01T00:00:00.000Z"

# ONE REVIEW INVOCATION, NO RETRY. A second review of the same checkpoint would
# be a second opinion on identical bytes, and the thing this Job establishes is
# that one independent reviewer receives the criteria and the proposal and
# returns its own verdict.
#
# THE SECONDS ARE W239528'S MEASURED ONES, and they are proposed rather than
# inherited: its accepted live run settled in 13.813865043s of a 300-second
# backstop with a 180-second turn ceiling, and a review turn reads a one-file
# change instead of writing one. Keeping the same three numbers means the only
# thing that changed between the two runs is the workload, which is what makes
# a comparison between them mean anything. W244180's OPERATOR.md is right that
# they are "historical inputs, not approval of W239533's bounds"; they are
# named here so a reviewer can accept or move them on the evidence.
BOUNDS = {"turn_seconds": 180, "total_seconds": 300, "cleanup_seconds": 60,
          "review_invocations": 1, "retry": False}

# The outputs a review turn publishes. Both required: see the module docstring.
REVIEW_OUTPUTS = ("findings", "logs")

# The bounds members that belong to the other two Jobs.
FOREIGN_BOUNDS = ("implementer_invocations", "corrections")

# THE CRITERIA, AND ONLY THE CRITERIA.
#
# `claude_agent._review_prompt` composes the review prompt from this one
# string. What it must NOT contain is a verdict, an expected answer, or
# anything that reads as "the change is correct" -- W236087's live failure was
# a task document that scripted all four stages including the finding the
# review was to return, and the agent read the script and produced the scripted
# answer. A criteria document that says what a good change looks like, without
# saying what THIS change is, is the difference between a review and a form.
#
# It also has to say that the reviewer is not the implementer: the reviewer
# holds a read-only checkout and a turn that tried to fix what it found would
# be doing W236087's correction inside this Job.
REVIEW_CRITERIA = (
    "You are the independent reviewer of a change somebody else proposed. "
    "The change is already made; your stage is to judge it and to say why.\n\n"
    "WHAT TO JUDGE IT AGAINST. The requirement the implementer was given was: "
    "running `harness.py` must print READY followed by a newline and nothing "
    "else, changing only `harness.py`. Read the actual files in front of you "
    "and decide whether that is what the change does. Run "
    "`python3 harness.py` yourself and look at what it prints and what it "
    "exits with; a change that passes by inspection and fails when run has "
    "not met the requirement.\n\n"
    "WHAT A VERDICT IS. Report `accepted` if the change meets the requirement, "
    "`changes-requested` if it does not and you can say what would fix it, and "
    "`rejected` if it should not be taken at all. Every one of the three is a "
    "valid review result. `changes-requested` and `rejected` are not failures "
    "of your stage and there is no outcome here that is better for you than "
    "another one -- your findings are the product, not your verdict.\n\n"
    "SAY WHY, FROM WHAT YOU READ. Each finding names what you looked at and "
    "what you observed there. Do not report a finding you did not verify, and "
    "do not pad the list: one finding you actually checked is worth more than "
    "five you assumed.\n\n"
    "YOU ARE NOT THE IMPLEMENTER. Your checkout is read-only and you have no "
    "stage in which to fix anything. Do not edit files, do not commit, and do "
    "not write a corrected version of the change: if the change needs work, "
    "saying exactly what it needs IS your whole contribution, and somebody "
    "else's separate run does the correcting.")


def _reuse():
    """W239528's accepted helpers, imported rather than copied.

    Kept in a function so the import failure is this module's own message.
    `baseline_bindings` lives in the sibling dossier and is read-only here.
    """
    try:
        import baseline_bindings
    except ImportError as failure:
        raise attachment.AttachmentRefusal(
            f"W239528's accepted `baseline_bindings` is not importable "
            f"({failure}); bind its dossier on PYTHONPATH. This module reuses "
            f"its reviewed helpers rather than keeping a second copy of them."
        ) from failure
    return baseline_bindings


def _refuse(message):
    raise _reuse().BindingRefusal(message)


# A LEADING UNDERSCORE MARKS A DOCUMENTATION MEMBER, everywhere in this
# packet's documents. `SELECTIONS-239533.json` explains its own operands in
# `_note`, `_independence` and `_manager_source_note` members, and until claim
# 248565 those notes reached two entry points that had no idea they were prose:
# the CLI passed `selections["compose"]` straight through as `**kwargs`, so
# `_manager_source_note` raised `TypeError` before `compose` was entered, and
# `compose` copied `bounds` verbatim into `PACKET.json`, so `bounds._note` made
# `review_supervisor.held_packet` refuse at startup. Both were found by an
# owner running the actual documented commands against the actual shipped
# template -- the synthetic selections every test wrote had no notes in them.
DOCUMENTATION = "_"


def without_documentation(value):
    """The same structure with every `_`-prefixed member removed, recursively.

    Normalization happens HERE, at composition, rather than by loosening the
    supervisor: a packet is an execution document and the five bound members
    are exactly five. Prose belongs in the template a human reads.
    """
    if isinstance(value, dict):
        return {name: without_documentation(inner)
                for name, inner in value.items()
                if not str(name).startswith(DOCUMENTATION)}
    if isinstance(value, list):
        return [without_documentation(inner) for inner in value]
    return value


def compose(*, instance, run_root, image_reference, image_digest, cli_build,
            manager_source, supervisor_path, vectors, participants,
            credential_sources, credential_profile, evidence_digest,
            provider_network, run_id, work, claim, note, producer,
            code_boundary=None, bounds=None, places=None, job_id=None):
    """Every document this review packet needs, composed from the real subject.

    `producer` names the retained run: its control store, its v12 Authority and
    Work, and its run root. Everything about WHAT is reviewed is then read out
    of that store rather than passed in, so a packet that names the wrong
    proposal cannot be composed.
    """
    from baton_v12.contracts import digest, digest_of_bytes, job_input_identity
    from baton_v12.worker_manager import provider_context as context
    from baton_v12.worker_manager import source_boundary
    from tools import single_worker, stage_execution

    instance = without_documentation(instance)
    participants = without_documentation(participants)
    producer = without_documentation(producer)
    credential_profile = without_documentation(credential_profile)

    shared = _reuse()
    shared._network(provider_network)
    shared._evidence(evidence_digest)

    # -- THE SUBJECT, READ THROUGH THE SUPPORTED READ-ONLY OPENER -----------
    # `ControlStore.open_readonly`, one coherent snapshot, public readers only.
    # The handle is closed here: a composer that left a connection open on the
    # producer's retained store would hold it for as long as the caller lived.
    # `clock` is an operand of the opener and stamps nothing, because nothing
    # in this module writes; `attachment.reading` says why it is not defaulted.
    reader = attachment.reading(producer["control_store"],
                                clock=lambda: COMPOSITION_INSTANT)
    try:
        held, refused = attachment.attachable(
            reader,
            line_id=producer["line_id"],
            authority_uuid=producer["authority_uuid"],
            work_id=producer["work_id"],
            checkpoint_id=producer["checkpoint_id"],
            reviewer_worker_id="review-worker",
            reviewer_participant=participants["review"],
            reviewer_principal=participants["review_principal"],
            profile_name=producer.get("profile_name", "git"))
    finally:
        reader.close()
    if refused:
        _refuse("this proposal cannot be reviewed by this deployment:\n  - "
                + "\n  - ".join(refused))
    base = held["declared_base"]
    shared._base_object(base)

    code_boundary = manager_source if code_boundary is None else code_boundary
    if not os.path.isabs(code_boundary) \
            or os.path.normpath(code_boundary) != code_boundary:
        _refuse(f"the code boundary is one absolute canonical directory; this "
                f"is {code_boundary!r}")
    whole = os.path.realpath(code_boundary)
    if os.path.commonpath([whole, os.path.realpath(manager_source)]) != whole:
        _refuse(f"the code boundary {code_boundary!r} does not contain the "
                f"manager source {manager_source!r}")

    job_id = shared._job_identity(run_id if job_id is None else job_id,
                                  derived=job_id is None)
    # THE PACKET CARRIES EXECUTION BOUNDS, NOT THE TEMPLATE'S PROSE ABOUT
    # THEM. `held_packet` requires exactly the five members, and it is right
    # to: `bounds._note` reaching a serving entry point is the defect this
    # normalization closes, not a strictness to be relaxed.
    bounds = without_documentation(dict(BOUNDS if bounds is None else bounds))
    intruding = sorted(set(FOREIGN_BOUNDS) & set(bounds))
    if intruding:
        _refuse(f"these bounds name {', '.join(intruding)}; W239533 drives one "
                f"REVIEW container. Implementation belongs to W239528 and "
                f"correction to W236087, and a packet that carried their "
                f"counts would be describing their runs under this Job's name")
    if bounds.get("review_invocations") != 1:
        _refuse(f"this packet drives ONE review container; these bounds "
                f"declare {bounds.get('review_invocations')!r}")

    # THE FOUR DIRECTORIES THIS RUN OWNS. `workspaces` is NOT among them: the
    # line's custody is the producer's configured workspace storage, recorded
    # immutably in the control store this deployment shares, and naming a
    # different one is refused by `configured_workspace_storage` before any
    # line is reached. See `attachment.py`'s docstring for why that is the
    # arrangement rather than an accident.
    derived = {name: os.path.join(run_root, name) for name in
               ("launch", "credentials", "private-contexts",
                "deployment-state")}
    if places is not None:
        unknown = sorted(set(places) - set(derived) - {"workspaces"})
        if unknown:
            _refuse(f"a run directory override names {', '.join(unknown)}, "
                    f"which this composition does not place")
        derived.update({one: places[one] for one in places
                        if one != "workspaces"})
    places = dict(derived)
    places["workspaces"] = (places.get("workspaces")
                            or producer["workspace_storage"])

    runtime_profile = {
        "schema": "baton.independent-review-runtime-profile/1",
        "name": "claude-context-review",
        "engine": "docker", "network": provider_network,
        "image_reference": image_reference, "image_digest": image_digest,
        "cli_build": cli_build, "model": "opus",
        "runtime_uid": os.getuid(),
        "scratch": {"tmp_bytes": 64 * 1024 * 1024,
                    "shm_bytes": 16 * 1024 * 1024},
        "workspace_min_bytes": source_boundary.MIN_WORKSPACE_BYTES + 1,
        "note": "one bounded managed review; W239533"}
    policy = {
        "schema": "baton.independent-review-execution-policy/1",
        "provider_turn_seconds": bounds["turn_seconds"],
        "verification_command_seconds": 900,
        "automatic_retry": False,
        "review_invocations": bounds["review_invocations"],
        "note": "the caps the admission gate enforces; W239533"}
    adapter = {
        "schema": "baton.independent-review-adapter/1",
        "adapter_name": "docker-single-worker",
        "engine": "docker", "network": provider_network,
        "entrypoint": ["python3", "/opt/baton/dogfood_entry.py"],
        "argv_policy": dict(context.ARGV_POLICY),
        "environment_policy": dict(context.ENVIRONMENT_POLICY)}
    profile_digest = digest(runtime_profile)
    policy_digest = digest(policy)
    adapter_digest = digest(adapter)

    # -- the frozen CRITERIA the reviewer reads at /input/task.json ---------
    # `declared_base` is the producer's own, read above: the reviewer is told
    # which base the change is against, and it is the base the checkpoint
    # actually names rather than a branch tip that may have moved.
    task = {"schema": "baton.dogfood-task/2",
            "task_id": run_id,
            "instructions": REVIEW_CRITERIA,
            "source_root": single_worker.SOURCE_DESTINATION,
            "source_profile": "git-line",
            "declared_base": base,
            "verification": ["python3", "harness.py"]}
    task_bytes = json.dumps(task, sort_keys=True).encode("utf-8")

    with open(vectors, "r", encoding="utf-8") as handle:
        corpus = json.loads(handle.read())
    manifest = dict(next(
        one["document"] for one in corpus["valid"]
        if one["document"].get("schema") == "baton.worker-manifest/input"))
    manifest["work_ref"] = {"authority_uuid": producer["authority_uuid"],
                            "work_id": producer["work_id"]}
    manifest["policy_digest"] = policy_digest
    manifest["runtime_profile_digest"] = profile_digest
    manifest["worker_image_digest"] = image_digest
    manifest["human_contract"] = {
        "artifact_id": run_id + "-criteria",
        "media_type": "application/json",
        "bytes": len(task_bytes),
        "content_digest": digest_of_bytes(task_bytes),
        "locator": "artifact://contracts/" + run_id + "-criteria"}
    source = dict(manifest["sources"][0])
    source["destination"] = single_worker.SOURCE_DESTINATION
    source["content_manifest"] = {"entries": [], "entry_count": 0,
                                  "total_bytes": 0,
                                  "tree_digest": single_worker.EMPTY_TREE_DIGEST}
    source["consumption"] = source_boundary.source_consumption("git-line")
    manifest["sources"] = [source]
    held_output = dict(manifest["outputs"][0])
    manifest["outputs"] = [
        dict(held_output, name=name, type="text-result", path=name,
             required=True) for name in REVIEW_OUTPUTS]
    manifest.pop("manifest_digest", None)
    manifest["manifest_digest"] = digest(manifest)

    def worker(role, *, participant, principal, review_route, task_document):
        return {"worker_id": f"{role}-worker", "role": role, "deployment": {
            "schema": single_worker.CONFIG_SCHEMA,
            "authority_store": instance["authority_store"],
            "authority_uuid": producer["authority_uuid"],
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
            "nominated_source": held["source_path"],
            "workspace_capacity": {
                "max_bytes": source_boundary.MIN_WORKSPACE_BYTES + 1},
            "input_manifest": manifest,
            "task_document": task_document,
            "launch_contract": "v12-assignment-1",
            "launch_role": role,
            "review_route": review_route,
            "retention_policy_digest": instance["retention_policy_digest"],
            "retention_disposition": "retain"}}

    deployment = {
        "schema": stage_execution.CONFIG_SCHEMA,
        "authority_store": instance["authority_store"],
        "authority_uuid": producer["authority_uuid"],
        "integration_store": instance["integration_store"],
        "state_root": places["deployment-state"],
        "pool_generation": 1, "policy_generation": 1,
        # READ, NOT DECLARED. Any other value reaches another line, or none.
        "line_declared_base": base,
        "canonical_target_id": base,
        "job_work_id": producer["work_id"],
        "review_work_id": producer["work_id"],
        "checkpoint_profile": held["profile_name"],
        "integration_profile": dict(instance["integration_profile"]),
        "receipt_participants": dict(participants["receipts"]),
        "retention_policy_digest": instance["retention_policy_digest"],
        "retention_disposition": "retain",
        # THE NO-CORRECTION BOUNDARY, owner selection 247421. A review-only
        # deployment declines the round a `changes-requested` verdict would
        # otherwise open in this Job store: the correction belongs to a
        # separately selected Job. `StageComposition.routed` never reaches
        # `open_correction`, so this fails closed BEFORE the effect rather
        # than reporting it afterwards.
        "correction_policy": stage_execution.DECLINE_CORRECTION,
        "workers": [
            # CONFIGURED AND NEVER ADMITTED -- the mirror image of W239528's
            # reviewer. Its task document is this Job's criteria too: a
            # configured worker that pointed at the producer's implementation
            # task would be a second copy of W239528's workload sitting in
            # this deployment waiting to be admitted by mistake.
            worker("implementation",
                   participant=participants["implementation"],
                   principal=participants["implementation_principal"],
                   review_route="rview",
                   task_document=os.path.join(run_root, "task.json")),
            worker("review", participant=participants["review"],
                   principal=participants["review_principal"],
                   review_route="integration",
                   task_document=os.path.join(run_root, "task.json"))]}

    submission = {
        "schema": "baton.v12.job-submission/2",
        "submission_id": run_id + "-submission",
        "jobs": [{
            "job_id": job_id,
            "input_digest": job_input_identity(manifest),
            "policy_digest": policy_digest,
            "test_scope": [],
            "terminal_policy": "report-and-hold",
            "execution_limits": {
                "provider_turn_seconds": bounds["turn_seconds"]},
            # ONE STAGE, AND IT IS THE REVIEW. There is no implementation
            # stage to depend on: the thing it would have produced is already
            # frozen in the producer's line.
            "stages": [
                {"kind": "review", "work_id": producer["work_id"],
                 "profile_name": runtime_profile["name"],
                 "profile_digest": profile_digest, "depends_on": []}]}]}

    packet = {
        "schema": PACKET_SCHEMA,
        "run_id": run_id, "work": work, "claim": claim, "note": note,
        "subject": held,
        "producer_run_root": producer["run_root"],
        "producer_control_store": producer["control_store"],
        "worker_image": {"reference": image_reference,
                         "config_digest": image_digest,
                         "worker_files": dict(participants["worker_files"])},
        "manager_runtime": {
            "path": instance["runtime_path"],
            "executable_sha256": shared._sha256(os.path.join(
                instance["runtime_path"], "baton-v12-stack")),
            "build_commit": instance["build_commit"]},
        "manager_source": {"path": manager_source,
                           "packages": ["baton_v12", "tools"],
                           "file_count": len(shared._tree(manager_source)),
                           "files": shared._tree(manager_source)},
        "supervisor": {"path": supervisor_path,
                       "sha256": shared._sha256(supervisor_path)},
        "code_boundary": code_boundary,
        "deployment": {
            "config_path": os.path.join(run_root, "deployment.json"),
            "config_sha256": None,
            "job_store": instance["job_store"],
            "control_store": producer["control_store"],
            "authority_store": instance["authority_store"],
            "authority_uuid": producer["authority_uuid"],
            "state_root": places["deployment-state"]},
        "context": {
            "storage_path": places["private-contexts"],
            "excluded_roots": [held["source_path"], places["workspaces"]],
            "runtime_uid": os.getuid(),
            "profile_path": None, "profile_sha256": None,
            "profile_digest": None,
            "job_id": job_id},
        "submission": {"path": os.path.join(run_root, "submission.json"),
                       "sha256": None, "job_id": job_id},
        "criteria": {"path": os.path.join(run_root, "task.json"),
                     "sha256": None,
                     "content_digest": digest_of_bytes(task_bytes)},
        "bounds": bounds,
        "outcome_path": os.path.join(run_root, "outcome.json")}

    return {"runtime-profile.json": runtime_profile,
            "policy.json": policy,
            "adapter.json": adapter,
            "task.json": task,
            "deployment.json": deployment,
            "submission.json": submission,
            "PACKET.json": packet}


def write(run_root, documents, *, checkout=None):
    """Hold the composition against the MANAGER'S validator, then publish.

    The producer's workspace storage is NOT created here. It exists, it holds
    the line being reviewed, and a composer that called `makedirs` on it would
    be reaching into another Job's retained custody to make its own validation
    pass.
    """
    from tools import stage_execution

    shared = _reuse()
    os.makedirs(run_root, exist_ok=True)
    places = {}
    for name in ("runtime-profile.json", "policy.json", "adapter.json"):
        places[name] = shared._write(os.path.join(run_root, name),
                                     documents[name])
    places["task.json"] = os.path.join(run_root, "task.json")
    with open(places["task.json"], "wb") as handle:
        handle.write(json.dumps(documents["task.json"],
                                sort_keys=True).encode("utf-8"))
    storage = documents["PACKET.json"]["subject"]["line_path"]
    for one in documents["deployment.json"]["workers"]:
        for member in ("launch_home", "credential_home"):
            os.makedirs(one["deployment"][member], mode=0o700, exist_ok=True)
        shared_storage = one["deployment"]["workspace_storage"]
        if not os.path.isdir(shared_storage):
            _refuse(f"the producer's workspace storage {shared_storage!r} is "
                    f"not a directory. The line being reviewed lives under it; "
                    f"this is an operational finding about the retained run, "
                    f"not a directory for this composer to create.")
        if not os.path.isdir(storage):
            _refuse(f"the line checkout {storage!r} is gone. There is nothing "
                    f"to review and no packet to write.")
    os.makedirs(documents["deployment.json"]["state_root"], mode=0o700,
                exist_ok=True)
    os.makedirs(documents["PACKET.json"]["context"]["storage_path"],
                mode=0o700, exist_ok=True)

    stage_execution.held_configuration(
        documents["deployment.json"],
        checkout=(documents["PACKET.json"]["code_boundary"]
                  if checkout is None else checkout))
    for name in ("deployment.json", "submission.json"):
        places[name] = shared._write(os.path.join(run_root, name),
                                     documents[name])

    packet = documents["PACKET.json"]
    packet["deployment"]["config_sha256"] = shared._sha256(
        places["deployment.json"])
    packet["submission"]["sha256"] = shared._sha256(places["submission.json"])
    packet["criteria"]["sha256"] = shared._sha256(places["task.json"])
    places["PACKET.json"] = shared._write(
        os.path.join(run_root, "PACKET.json"), packet)
    return places


def preflight(authority, documents, participants):
    """W239528's preflight, asked about this deployment.

    The question is the same one -- is this Authority actually prepared for the
    participants this deployment configures -- and the answer is the accepted
    implementation of it. What differs is the closing note: this Job DOES
    submit a review stage, so `rview` handler registration IS a prerequisite of
    running it, and the reused note says the opposite. It is replaced rather
    than left to be read the wrong way.
    """
    shared = _reuse()
    missing = [one for one in
               shared.preflight(authority, documents, participants)
               if not one.startswith("UNVERIFIABLE HERE:")]
    missing.append(
        "UNVERIFIABLE HERE: this Authority exposes no public reader for a "
        "route's handlers. THIS JOB SUBMITS A REVIEW STAGE, so `rview` "
        "handler registration for "
        f"{participants['review']!r} IS a prerequisite of running it and must "
        "be asserted by the operator's own preparation.")
    return missing


def main(argv=None, *, stream=None):
    stream = sys.stdout if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="review_bindings",
        description="Compose the independent-review packet's per-Job "
                    "bindings. Grants nothing and runs nothing.")
    parser.add_argument("--selections", required=True,
                        help="the JSON document naming every owner selection")
    parser.add_argument("--run-root", required=True)
    taken = parser.parse_args(argv)

    with open(taken.selections, "r", encoding="utf-8") as handle:
        selections = json.load(handle)
    # NO `--base`. W239528's composer takes one because an implementation
    # declares the base it will work from; a review reads the base its subject
    # was actually produced against, and a base an operator typed here could
    # only ever disagree with the checkpoint.
    chosen = without_documentation(selections["compose"])
    # AND AN UNKNOWN SUBSTANTIVE MEMBER IS REFUSED BY NAME rather than reaching
    # Python as a `TypeError` from a `**kwargs` call the operator never made.
    accepted = set(inspect.signature(compose).parameters)
    unknown = sorted(set(chosen) - accepted - {"run_root"})
    if unknown:
        _refuse(f"this selections document names {', '.join(unknown)}, which "
                f"this composition has no operand for. A documentation member "
                f"starts with {DOCUMENTATION!r}; anything else is a selection "
                f"that has to mean something here.")
    chosen.pop("run_root", None)
    documents = compose(run_root=taken.run_root, **chosen)
    places = write(taken.run_root, documents)
    print(json.dumps({name: _reuse()._sha256(place)
                      for name, place in sorted(places.items())},
                     indent=2, sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
