"""Prepare ONE fresh two-Job instance, deriving every technical operand.

Owner reroute 250730: "Complete operator preparation: derive technical operands
from accepted configuration and supported APIs instead of leaving them as owner
questions. Deliver exact setup commands and a preparation script that
creates/registers required identities, routes, scoped capabilities and inputs
through supported APIs, resolves selections, and composes/validates the
concrete packet."

So this replaces the twelve `<OWNER: ...>` questions in SELECTIONS-247941.json
with four operands nobody can derive -- the fresh run root, the fixture source,
its base revision and the Authority uuid the bootstrap minted -- and derives
the rest from the configuration W239528 and W239533 were accepted on.

WHAT IT DOES, in order:

  1. refuses a run root that is not this run's own, or that lies under any
     instance this campaign has consumed;
  2. writes the two Jobs' task documents, whose target paths are DISJOINT --
     that is this gate's own limit, and it is checked rather than trusted;
  3. derives the resolved selections, including each Job's full input manifest
     and its `job_input_identity`, and writes them beside the run;
  4. performs the Authority acts through the supported API: two Works, the
     route handlers every configured worker needs, the scoped capability
     grants and the canonical target;
  5. composes and validates the concrete packet by running `two_jobs.py` --
     the same command ADOPTION-247941.md step 3 prints, not a second path.

WHAT IT DOES NOT DO, and the separation is the owner's: it starts no container,
reads no credential, runs no provider, opens no Job or control store, and
performs no Git operation. Bootstrapping the instance and executing the run are
separate operator steps. A credential is named by REFERENCE only; no secret
passes through this file or anything it writes.

REPLAY IS AN ACT IDENTITY, not a guess. `create_work` is journalled, and the
identity is derived from the run, so running this twice against the same
Authority replays the same two acts and answers the same Works. A DIFFERENT
packet pointed at the same Authority derives a different identity and is not
absorbed into this one.
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

# THE PINNED SNAPSHOT. Every module this preparation imports, and the one the
# composer subprocess imports, is the selected product rather than the
# checkout -- the distinction W247941's review made a standing requirement.
SNAPSHOT = "/home/sl/baton-runs/independent-review-247947/manager-source"

# EVERY RUN ROOT THIS CAMPAIGN HAS CONSUMED. Each holds other work and is
# preserved evidence; a successor takes a new identity and none of these.
CONSUMED = (
    "managed-correction-236087",
    "single-implementation-239528",
    "single-implementation-success-239528",
    "single-implementation-242687",
    "single-implementation-244216",
    "independent-review-247947",
    "independent-review-248377",
)

# THE ACCEPTED CONFIGURATION, and where each value comes from. These are the
# operands the owner said to DERIVE rather than ask for: every one of them is
# read from a run that was independently accepted, and `verify_247941.py
# --pins` re-checks the artifact digests among them before use.
ACCEPTED = {
    "_provenance": {
        "image_and_adapter": "W239528 claim 244216, accepted by "
                             "review-2026-09-23T03-19-21Z.md",
        "worker_and_policy_digests": "the executed review deployment at "
                                     "/home/sl/baton-runs/"
                                     "independent-review-248377/run/"
                                     "deployment.json, accepted by W239533",
        "manager_source": "ASSESSMENT-249338.md's pinned snapshot",
    },
    "manager_source": SNAPSHOT,
    "manager_source_files": 106,
    "runtime_path": "/home/sl/baton-runs/managed-correction-236087"
                    "/build/stack/out/distro",
    "runtime_build": "1e576ff2186db69e8b44da9d38874ff7e99ebbe3",
    "runtime_executable_sha256":
        "04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a",
    "image_reference": "baton-v12-claude-worker:w239528-244216",
    "image_digest": "sha256:c862c055c6430addc918ca078a9e4d55f"
                    "6bd8173ed9c9878a8ad9d6cad334ca2",
    "adapter_sha256":
        "18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d",
    "stage_execution_sha256": "6a212c3a2edc5ddb7059e86350d95924"
                              "aca4b059c059855939e4fd9771ab5801",
    "adapter_name": "docker-single-worker",
    "adapter_digest": "sha256:1390f120f21a84a53ef0b0940b2ca199"
                      "228adc3a5211d5bdc76838a444a0c9ce",
    "engine": "docker",
    "provider_network": "bridge",
    "credential_sources": "/home/sl/.baton/credential-sources.json",
    "credential_slots": ["claude"],
    # A REFERENCE, NEVER A SECRET. The manager resolves this through the
    # private registry above; nothing here or in anything this writes carries
    # credential bytes.
    "credential_profile": {"claude": {"provider": "operator-file",
                                      "reference": "w202663-development"}},
    "retention_policy_digest": "sha256:0f4cd2d13c46e81cb6e721119e48b342"
                               "efb3a7a0d831e241c429601aa2eae45a",
    "retention_disposition": "retain",
    "policy_digest": "sha256:82f94ecee8cc3959e4381a9573db8530"
                     "f86f4b5fd801619f030931795403e62b",
    "checkpoint_profile": "git",
    "launch_contract": "v12-assignment-1",
    "review_route": "rview",
    "reviewed_route": "integration",
    "workspace_group": 1000,
    "workspace_capacity": {"max_bytes": 83886081},
    "policy_generation": 1,
    "pool_generation": 1,
    "correction_policy": "decline",
    "profile_name": "claude-context-review",
    "profile_digest": "sha256:432b508360842aa830239df6081923be"
                      "e2f48dd2b5da5754ee10eefce3f85d25",
    "integration_profile": {
        "instructions_digest": "sha256:fafc35958002db5284b54f4d22cf59a7"
                               "dccfb5ac05e15baa69db73fcff06d6f2",
        "integrator_participant": "baton.merge",
        "profile_kind": "git",
        "profile_version": 1,
    },
    "receipt_participants": {"approval": "baton.approver",
                             "review": "baton.approver-review",
                             "verification": "baton.verifier"},
}

# FOUR DISTINCT IDENTITIES, which is this gate's own limit rather than the
# product's: two Jobs sharing a producer or a reviewer would not be two
# independent development Jobs.
ROLES = {
    "job-a": {"producer_participant": "baton.impl-a",
              "reviewer_participant": "baton.review-a",
              "producer_worker_id": "implementation-worker-a",
              "reviewer_worker_id": "review-worker-a"},
    "job-b": {"producer_participant": "baton.impl-b",
              "reviewer_participant": "baton.review-b",
              "producer_worker_id": "implementation-worker-b",
              "reviewer_worker_id": "review-worker-b"},
}

# THE TWO TINY DISJOINT CHANGES the owner selected, one file each. Disjoint is
# checked below rather than assumed: it is what makes two lines over one base
# two independent development Jobs instead of one contended file.
TASKS = {
    "job-a": {"path": "greet_a.py", "prints": "A-READY"},
    "job-b": {"path": "greet_b.py", "prints": "B-READY"},
}

TASK_SCHEMA = "baton.dogfood-task/2"
SELECTIONS_SCHEMA = "baton.v12.two-job-selections/1"

INSTRUCTIONS = """\
THE CHANGE THIS JOB IS ABOUT. `python3 {path}` must print exactly `{prints}`
followed by a newline, and nothing else, and exit 0. `{path}` is the only file
this Job may add or alter; another development line is being written against
this same base at the same time and it owns everything else.

ONE DOCUMENT, TWO STAGES, and the Job's input identity is deliberately shared
between them -- the manager delivers this same requirement to both, because it
is the same requirement they are held to. Read the part that is yours.

IF YOUR STAGE IS THE IMPLEMENTATION. Make that change and nothing else. Do not
judge your own work: the verdict is a separate run by somebody else, and a turn
that both writes and accepts has reviewed nothing.

IF YOUR STAGE IS THE REVIEW. Your checkout is READ-ONLY and you have no stage
in which to fix anything. Judge the change in front of you against the
requirement above: run `python3 {path}` yourself and look at what it prints and
what it exits with, because a change that passes by inspection and fails when
run has not met it, and check that nothing outside `{path}` was touched.

  Report `accepted` if it meets the requirement, `changes-requested` if it does
  not and you can say what would fix it, and `rejected` if it should not be
  taken at all. **All three are valid results and none is better for you than
  another** -- your findings are the product, not your verdict. Name what you
  looked at and what you observed there, and do not report a finding you did
  not verify.

EITHER WAY, say what you did from what you actually ran rather than from what
you intended.
"""


class PreparationRefusal(Exception):
    """Refused rather than prepared. Never a partial instance's excuse."""


def _refuse(message):
    raise PreparationRefusal(message)


# WHERE THE PINNED VALIDATOR REFUSES MUTABLE DEPLOYMENT STATE. Review
# 2026-09-23T20:34:15Z composed the shape this page printed and got:
# "the configured integration_store at '/home/sl/baton-runs/two-jobs-.../db/
# integration.sqlite3' is inside the checkout at '/home/sl/baton-runs'".
# `held_configuration` derives "the checkout" from the source that imported it,
# so binding the PINNED snapshot makes `/home/sl/baton-runs` a checkout. The
# instance therefore lives elsewhere, and the validator is not weakened.
BOUNDARIES = ("/home/sl/baton-runs", "/home/sl/src/baton")

# THE SUPPORTED DEFAULT, outside both boundaries and on real disk.
SUGGESTED_ROOT = "/home/sl/baton-instances"


def _components(place):
    """The path's REAL components. Review 2026-09-23T20:34:15Z: the lexical
    check accepted a fresh-named symlink pointing into a consumed root, so
    every refusal below could be walked around with one `ln -s`. `realpath`
    asks where the directory actually is."""
    whole = os.path.realpath(os.path.abspath(os.path.expanduser(place)))
    return whole, [one for one in whole.split(os.sep) if one]


def layout(run_root):
    """Every durable place, from the BOOTSTRAP's own rule.

    `tools.bootstrap.layout` puts the four stores under `db/`, the stage
    deployment's mutable root beside them and the record at `bootstrap.json`.
    Deriving the same places here is what makes the preparation, the supervisor
    command and the read-only inspection name one set of paths -- review
    2026-09-23T20:34:15Z found three that could not be reconciled, and my
    previous "correction" reconciled them to the wrong side.
    """
    return {
        "run_root": run_root,
        "record": os.path.join(run_root, "bootstrap.json"),
        "authority_store": os.path.join(run_root, "db", "authority.sqlite3"),
        "job_store": os.path.join(run_root, "db", "jobs.sqlite3"),
        "control_store": os.path.join(run_root, "db", "control.sqlite3"),
        "integration_store": os.path.join(run_root, "db",
                                          "integration.sqlite3"),
        "state_root": os.path.join(run_root, "deployment-state"),
        "run": os.path.join(run_root, "run"),
        "tasks": os.path.join(run_root, "tasks"),
        "selections": os.path.join(run_root, "selections-resolved.json"),
        "deployment": os.path.join(run_root, "run", "deployment.json"),
        "submission": os.path.join(run_root, "run", "submission.json"),
        "outcome": os.path.join(run_root, "run", "outcome.json"),
        "bootstrap_inputs": os.path.join(run_root, "bootstrap-inputs.json"),
        "workspace_storage": os.path.join(run_root, "run", "workspaces"),
        "launch_home": os.path.join(run_root, "run", "launch"),
        "credential_home": os.path.join(run_root, "run", "credentials"),
    }


# THE OWNED ROOTS A LIVE PREFLIGHT REQUIRES TO EXIST. Owner 2026-09-23:
# `worker_preflight` refused because `run/workspaces` was not there, and
# `workspaces.check_workspace_storage` asks with `lstat` -- an absent name is a
# refusal, a symlink is a refusal, and a directory this uid does not own is a
# refusal. The packet named these and created none.
PROVISIONED = ("workspace_storage", "launch_home", "credential_home",
               "state_root")


def provision(places):
    """Create the owned roots the composed deployment names. 0o700, ours.

    AFTER THE COMPOSER, never before: `run/` must not exist when the composer
    runs, and these live under it. Each is created with `exist_ok` because the
    composer may have made one already, and each is then READ BACK through the
    product's own check so this reports what the live preflight will find
    rather than what it intended.
    """
    from baton_v12.worker_manager import workspaces
    held = {}
    for name in PROVISIONED:
        place = places[name]
        os.makedirs(place, mode=0o700, exist_ok=True)
        held[name] = {"path": place, "created": True}
    # THE PRODUCT'S OWN JUDGMENT on the one it refuses most sharply, so a
    # provisioning that satisfies this file but not the manager is a refusal
    # here rather than a refusal at the operator's next command.
    workspaces.check_workspace_storage(places["workspace_storage"])
    held["workspace_storage"]["held_by_product"] = True
    return held


# THE BOOTSTRAP SCHEMA, and the exact set it accepts.
# `tools.bootstrap.REQUIRED` is this list; `workers` and `jobs` are
# deliberately NOT here, because an installation configures no capacity:
# "a worker, a Work, a declared base, a
# canonical target and a producer are supplied together when a Job is created".
BOOTSTRAP_SCHEMA = "baton.v12.stack-bootstrap/1"


def bootstrap_inputs(run_root):
    """The instance document `tools.bootstrap --inputs` takes, DERIVED.

    Review 2026-09-23T20:52:13Z: the page named the tool and left its required
    operand as `<see v12/STACK.md>`, which is another open configuration task
    rather than the derivation the owner selected. Every member below comes
    from the same ACCEPTED configuration as the rest of this preparation.

    A FRESH INSTALL NAMES NO JOBS AND NO WORKERS, and that is the tool's own
    rule rather than a simplification here. Running it on a disposable
    destination answers `job   none; no Work, grant or placeholder was
    created` -- so the two Works this preparation creates are its own, and
    nothing the bootstrap did competes with them.
    """
    return {
        "schema": BOOTSTRAP_SCHEMA,
        "state_root": layout(run_root)["state_root"],
        "checkpoint_profile": ACCEPTED["checkpoint_profile"],
        "integration_profile": dict(ACCEPTED["integration_profile"]),
        "retention_policy_digest": ACCEPTED["retention_policy_digest"],
        "retention_disposition": ACCEPTED["retention_disposition"],
        "pool_generation": ACCEPTED["pool_generation"],
        "policy_generation": ACCEPTED["policy_generation"],
        "receipt_participants": dict(ACCEPTED["receipt_participants"]),
    }


def fresh(run_root, run_id):
    """Is this instance this run's own, on a path the validator accepts?

    THREE REFUSALS, all before anything is written. Review
    2026-09-23T20:34:15Z: the first version compared LEXICAL components, so a
    fresh-named symlink into a consumed root walked around every one of them,
    and the selected root was then refused by the validator anyway. This
    resolves the path first and checks the boundary here rather than at the
    composition, after task files already exist.
    """
    whole, parts = _components(run_root)
    if run_id in CONSUMED:
        _refuse(f"run id {run_id!r} is a CONSUMED instance: its stores hold "
                f"other work and its evidence is preserved. A successor takes "
                f"a new identity.")
    if run_id not in parts:
        _refuse(f"run root {whole!r} does not name this run {run_id!r} in its "
                f"own RESOLVED path; a successor's stores are its own")
    for older in CONSUMED:
        if older in parts:
            _refuse(f"run root {whole!r} resolves under {older!r}, which "
                    f"holds other work and is preserved evidence")
    for boundary in BOUNDARIES:
        held, _ = _components(boundary)
        if whole == held or whole.startswith(held + os.sep):
            _refuse(
                f"run root {whole!r} is inside {held!r}, which this "
                f"deployment's own validator treats as the checkout: "
                f"'mutable deployment state belongs outside the working "
                f"tree'. Select a disk-backed root elsewhere, for example "
                f"under {SUGGESTED_ROOT}; the validator is not weakened to "
                f"admit one.")
    return whole


def receipt_of(places, *, expected=None):
    """The Authority identity, READ FROM THE BOOTSTRAP'S OWN RECEIPT.

    Review 2026-09-23T20:34:15Z asked for the preparation to be bound to a
    supported fresh bootstrap receipt rather than to a uuid typed beside it.
    The record is what `tools.bootstrap` emits; this reads it, and an operand
    that disagrees with it is a refusal rather than a silent preference.
    """
    if not os.path.isfile(places["record"]):
        _refuse(f"there is no bootstrap record at {places['record']!r}; "
                f"bootstrap the fresh instance first -- this preparation "
                f"creates no instance and mints no identity")
    with open(places["record"], "r", encoding="utf-8") as handle:
        held = json.load(handle)
    found = held.get("authority_uuid")
    if type(found) is not str or len(found) != 32 \
            or any(one not in "0123456789abcdef" for one in found):
        _refuse(f"{places['record']!r} carries no 32-hex authority_uuid")
    if expected is not None and expected != found:
        _refuse(f"--authority-uuid {expected!r} disagrees with the bootstrap "
                f"record's {found!r}; the receipt is the identity")
    if not os.path.exists(places["authority_store"]):
        _refuse(f"{places['authority_store']!r} does not exist; bootstrap the "
                f"fresh instance first")
    return found


def unchanged(place, raw):
    """Would writing these bytes CHANGE something already there?

    Answers before anything is written, so a repeat is either an exact replay
    or a refusal that left the earlier run's bytes alone. Review
    2026-09-23T20:34:15Z: `main` overwrote both task documents and the
    resolved selections before it opened the Authority or looked at the
    composer's create-only target.
    """
    if not os.path.exists(place):
        return True
    with open(place, "rb") as handle:
        return handle.read() == raw


def digest_of_bytes(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def task_document(job_id, *, run_id, base):
    """One Job's frozen task, stating the requirement and nothing else.

    W239528's live run learned this at an owner's expense: a task document
    that scripts several stages is handed to the IMPLEMENTATION role as work
    to do, and the agent reviewed its own change. This states the requirement
    and says plainly that judging is not this stage.
    """
    held = TASKS[job_id]
    return {
        "schema": TASK_SCHEMA,
        "task_id": f"{run_id}-{job_id}",
        "declared_base": base,
        "source_profile": "git-line",
        "source_root": "source",
        "instructions": INSTRUCTIONS.format(**held),
        "verification": ["python3", held["path"]],
    }


def disjoint(documents):
    """The two tasks touch no common path, or this refuses by name."""
    touched = {job_id: {TASKS[job_id]["path"]} for job_id in documents}
    shared = set.intersection(*touched.values())
    if shared:
        _refuse(f"both Jobs' tasks touch {sorted(shared)}; two Jobs writing "
                f"one path are one contended change rather than two "
                f"independent development lines")
    return {job_id: sorted(one) for job_id, one in touched.items()}


def input_manifest(*, authority_uuid, work_id, task_path, raw, artifact_id):
    """One Job's input manifest, built from the task bytes just written.

    THE HUMAN CONTRACT IS THE TASK. `single_worker._held` compares the
    worker's `task_document` bytes against this manifest's `human_contract`
    digest, so the two are derived together here rather than filled in twice
    and hoped to agree.
    """
    del task_path
    manifest = {
        "schema": "baton.worker-manifest/input",
        "manifest_id": "input-manifest-1",
        "version": {"major": 1, "minor": 0},
        "created_at": "2026-08-21T22:00:00.000Z",
        "assignment_contract": ACCEPTED["launch_contract"],
        "work_ref": {"authority_uuid": authority_uuid, "work_id": work_id},
        "worker_image_digest": ACCEPTED["image_digest"],
        "runtime_profile_digest": ACCEPTED["profile_digest"],
        "policy_digest": ACCEPTED["policy_digest"],
        "human_contract": {
            "artifact_id": artifact_id,
            "bytes": len(raw),
            "content_digest": digest_of_bytes(raw),
            "locator": f"artifact://contracts/{artifact_id}",
            "media_type": "application/json",
        },
        "sources": [{
            "name": "source", "destination": "source", "required": True,
            "consumption": {"baton.source-boundary/1": {
                "delivery": "nominated-mount", "profile": "git-line",
                "workspace": "disk"}},
            "content_manifest": {
                "entries": [], "entry_count": 0, "total_bytes": 0,
                "tree_digest": "sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab"
                               "4d8e11ba873c2f11161202b945"},
        }],
        "outputs": [
            {"name": name, "path": name, "required": True,
             "type": "text-result",
             "constraints": {
                 "allowed_media_types": ["application/octet-stream",
                                         "text/plain"],
                 "link_policy": "forbid", "max_bytes": 1048576,
                 "max_entries": 100, "validator_digest": None}}
            for name in ("findings", "logs")],
        "record_binding": {
            "root": "baton-repository",
            "path": "work/records/2026/09/finding-v12-real-jobs-adoption-gate",
            "finding_digest": "sha256:" + "d" * 64,
            "plan_digest": "sha256:" + "e" * 64},
        "extensions": {},
        "credential_policy_digest": "sha256:" + "b" * 64,
        "mount_policy_digest": "sha256:" + "9" * 64,
        "network_policy_digest": "sha256:" + "8" * 64,
        "resource_policy_digest": "sha256:" + "7" * 64,
        "retention_policy_digest": "sha256:" + "c" * 64,
        "role_instructions_digest": "sha256:" + "2" * 64,
        "tool_policy_digest": "sha256:" + "a" * 64,
        "toolchain_digest": "sha256:" + "4" * 64,
    }
    # THE PRODUCT'S OWN RULE, not a re-implementation of it.
    # `verify_manifest_digest` recomputes `digest(...)` over every member but
    # `manifest_digest` and refuses a manifest whose declared identity its own
    # bytes do not produce. A first draft of this file hashed canonical text
    # itself and met that refusal; asking the product is the fix.
    from baton_v12.contracts import digest
    manifest["manifest_digest"] = digest(
        {name: value for name, value in manifest.items()
         if name != "manifest_digest"})
    return manifest


def resolved(*, run_root, run_id, source, base, authority_uuid, work_ids,
             tasks):
    """The selections, with every `<OWNER>` derived rather than asked."""
    from baton_v12.contracts import job_input_identity
    places = layout(run_root)
    run = places["run"]
    instance = {
        "run_root": run_root,
        "authority_store": places["authority_store"],
        "authority_uuid": authority_uuid,
        "job_store": places["job_store"],
        "integration_store": places["integration_store"],
        "state_root": places["state_root"],
        "workspace_storage": places["workspace_storage"],
        "launch_home": places["launch_home"],
        "credential_home": places["credential_home"],
        "submission_id": f"submission-{run_id}",
        # THE INSTANCE-LEVEL MEMBERS a `/2` document still carries. Each Job's
        # own Work and base are in `job_bindings`; these are what `_MEMBERS`
        # requires, and Job A's are the ones an instance reads.
        "job_work_id": work_ids["job-a"],
        "review_work_id": work_ids["job-a"],
        "line_declared_base": base,
        "canonical_target_id": base,
    }
    for name in ("adapter_name", "adapter_digest", "engine", "image_digest",
                 "provider_network", "credential_sources", "credential_slots",
                 "credential_profile", "retention_policy_digest",
                 "retention_disposition", "policy_digest",
                 "checkpoint_profile", "launch_contract", "review_route",
                 "reviewed_route", "workspace_group", "workspace_capacity",
                 "policy_generation", "pool_generation", "correction_policy",
                 "integration_profile", "receipt_participants"):
        instance[name] = ACCEPTED[name]

    jobs = []
    for job_id in sorted(ROLES):
        held = dict(ROLES[job_id])
        raw = tasks[job_id]["raw"]
        manifest = input_manifest(
            authority_uuid=authority_uuid, work_id=work_ids[job_id],
            task_path=tasks[job_id]["path"], raw=raw,
            artifact_id=f"{run_id}-{job_id}-contract")
        held.update({
            "job_id": job_id,
            "work_id": work_ids[job_id],
            "implementation_principal":
                f"principal:{held['producer_participant']}",
            "review_principal": f"principal:{held['reviewer_participant']}",
            "nominated_source": source,
            "declared_base": base,
            "canonical_target_id": base,
            "task_document": tasks[job_id]["path"],
            "profile_name": ACCEPTED["profile_name"],
            "profile_digest": ACCEPTED["profile_digest"],
            "review_profile_name": ACCEPTED["profile_name"],
            "review_profile_digest": ACCEPTED["profile_digest"],
            "implementation_input_manifest": manifest,
            "review_input_manifest": manifest,
            "input_digest": job_input_identity(manifest),
            "test_scope": [TASKS[job_id]["path"]],
        })
        jobs.append(held)

    return {
        "_schema": SELECTIONS_SCHEMA,
        "_work": "W247941",
        "_derived_by": "prepare_two_jobs.py",
        "_run_id": run_id,
        "_accepted_from": ACCEPTED["_provenance"],
        "arrangement": dict(
            {name: ACCEPTED[name] for name in (
                "manager_source", "manager_source_files", "runtime_path",
                "runtime_build", "runtime_executable_sha256",
                "image_reference", "image_digest", "adapter_sha256",
                "stage_execution_sha256")},
            instance=instance, jobs=jobs),
    }


def prepare(authority, document, *, base, operation_prefix):
    """The Authority acts, against an ALREADY OPEN handle.

    Taking the handle rather than opening one is what lets a disposable
    Authority drive this exact function; `main` opens the one the run names.
    """
    arrangement = document["arrangement"]
    integrator = arrangement["instance"]["integration_profile"][
        "integrator_participant"]
    receipts = arrangement["instance"]["receipt_participants"]
    made = []
    for job in arrangement["jobs"]:
        authority.create_work(
            job["work_id"], "impl", contract="v12-assignment-1",
            operation_id=f"{operation_prefix}-{job['job_id']}")
        scope = authority.project_work(job["work_id"])["scope"]
        # BOTH IMPLEMENTERS HANDLE `impl` AND BOTH REVIEWERS `rview`. The
        # handler table is keyed on (route, participant), so a route may have
        # several handlers; two Jobs with one shared handler would not be two
        # independent Jobs.
        authority.add_route_handler("impl", job["producer_participant"])
        authority.add_route_handler("rview", job["reviewer_participant"])
        granted = []
        for who, capability in ((receipts["verification"], "verify"),
                                (receipts["review"], "review"),
                                (receipts["approval"], "approve"),
                                (integrator, "integrate")):
            authority.grant_capability(who, capability, scope=scope)
            granted.append({"participant": who, "capability": capability})
        made.append({"job_id": job["job_id"], "work_id": job["work_id"],
                     "scope": scope, "granted": granted,
                     "route_handlers": {
                         "impl": job["producer_participant"],
                         "rview": job["reviewer_participant"]}})
    # THE REVIEW WORKER PASSES ITS ANSWERED ASSIGNMENT TO `integration`, so
    # that route needs a handler even though this gate submits no integration
    # stage and allocates no integration capacity.
    authority.add_route_handler("integration", integrator)
    authority.set_policy("canonical_target", base)
    return {"jobs": made, "canonical_target": base,
            "route_handlers": {"integration": integrator}}


def _composer(arguments):
    """The shipped composer, in a process bound to the PINNED source.

    One place builds this invocation, so the preflight and the composition
    cannot drift apart: `--check` and the real write run the same program with
    the same environment and the same working directory.
    """
    return subprocess.run(
        [sys.executable, "-B", str(HERE / "two_jobs.py"), *arguments],
        capture_output=True, text=True, timeout=600, cwd=os.sep,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                 PYTHONPATH=os.pathsep.join([SNAPSHOT, str(HERE)])))


def compose(document_path, into, *, stream):
    """The packet, through the SHIPPED composer rather than a second path."""
    answer = _composer(["--selections", document_path, "--into", into])
    print(answer.stdout, end="", file=stream)
    if answer.returncode != 0:
        _refuse(f"the composer refused this packet:\n{answer.stderr.strip()}")
    return {"into": into, "stdout": answer.stdout.strip().splitlines()}


def main(argv=None, *, stream=None, authority_opener=None):
    """Validate everything, then act. Never the other way round.

    Review 2026-09-23T20:34:15Z: the first version wrote both task documents
    and the resolved selections, then performed the Authority acts, and only
    then met the composer's refusal -- so a run that could never have composed
    still left files behind and still revisited the Authority. Every refusal
    below happens before the first byte is written, including the product's
    own validation of the whole proposed packet.
    """
    stream = sys.stdout if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="prepare_two_jobs",
        description="Prepare one FRESH two-Job instance: identities, routes, "
                    "capabilities, inputs, resolved selections and a composed "
                    "packet. Starts no container, reads no credential, runs "
                    "no provider, opens no Job or control store and performs "
                    "no Git operation.")
    parser.add_argument("--run-root", required=True,
                        help="the bootstrapped run root; it must name this "
                             "run and lie outside the checkout boundaries")
    parser.add_argument("--source", required=True,
                        help="the fixture repository, mounted read-only")
    parser.add_argument("--base", required=True,
                        help="that repository's HEAD, which is also the "
                             "declared base of both lines and the "
                             "Authority's canonical target")
    parser.add_argument("--authority-uuid", default=None,
                        help="optional cross-check against the bootstrap "
                             "record, which is the identity")
    parser.add_argument("--run-id", default=None,
                        help="defaults to the run root's own name")
    parser.add_argument("--operation-prefix", default=None,
                        help="defaults to w247941-<run id>")
    parser.add_argument("--emit-bootstrap-inputs", action="store_true",
                        help="derive and print the `tools.bootstrap --inputs` "
                             "document for this run root, and do nothing "
                             "else. This runs BEFORE the instance exists, so "
                             "it needs no bootstrap record and performs no "
                             "act of any kind.")
    taken = parser.parse_args(argv)

    if taken.emit_bootstrap_inputs:
        # THE ONE MODE THAT PRECEDES THE INSTANCE. It still refuses a root
        # inside a checkout boundary or under a consumed instance, because an
        # operator who bootstraps into one has already spent the effort.
        held = fresh(os.path.abspath(os.path.expanduser(taken.run_root)),
                     taken.run_id or os.path.basename(
                         os.path.abspath(taken.run_root).rstrip(os.sep)))
        print(json.dumps(bootstrap_inputs(held), indent=2, sort_keys=True),
              file=stream)
        return 0

    # ---- EVERY REFUSAL FIRST, and nothing written yet --------------------
    run_root = os.path.abspath(os.path.expanduser(taken.run_root))
    run_id = taken.run_id or os.path.basename(run_root.rstrip(os.sep))
    run_root = fresh(run_root, run_id)
    places = layout(run_root)
    if len(taken.base) != 40 or any(one not in "0123456789abcdef"
                                    for one in taken.base):
        _refuse(f"--base is one full lower-case object name; this is "
                f"{taken.base!r}")
    source = os.path.realpath(os.path.expanduser(taken.source))
    if not os.path.isdir(source):
        _refuse(f"the fixture source {source!r} is not a directory; creating "
                f"and committing it is an operator step, because this "
                f"performs no Git operation")
    authority_uuid = receipt_of(places, expected=taken.authority_uuid)

    tasks = {}
    for job_id in sorted(TASKS):
        document = task_document(job_id, run_id=run_id, base=taken.base)
        raw = json.dumps(document, sort_keys=True).encode("utf-8")
        tasks[job_id] = {"path": os.path.join(places["tasks"],
                                              f"{job_id}.json"),
                         "raw": raw, "touches": TASKS[job_id]["path"]}
    touched = disjoint(tasks)

    work_ids = {job_id: f"{authority_uuid[:8]}-W{number}"
                for number, job_id in enumerate(sorted(TASKS), start=1)}
    document = resolved(run_root=run_root, run_id=run_id, source=source,
                        base=taken.base, authority_uuid=authority_uuid,
                        work_ids=work_ids, tasks=tasks)
    raw_selections = (json.dumps(document, indent=2, sort_keys=True)
                      .encode("utf-8"))

    # A REPEAT IS AN EXACT REPLAY OR A REFUSAL THAT CHANGES NOTHING, and both
    # are decided here, before the first byte.
    changing = [one["path"] for one in tasks.values()
                if not unchanged(one["path"], one["raw"])]
    if not unchanged(places["selections"], raw_selections):
        changing.append(places["selections"])
    if changing:
        _refuse(f"these inputs already exist with DIFFERENT bytes and this "
                f"run would change them: {', '.join(sorted(changing))}. "
                f"A preparation that rewrites an earlier run's inputs is not "
                f"a replay. Select a fresh run root, or pass the same "
                f"operands.")
    # THE COMPOSER'S ACTUAL RULE, not a weaker reading of it. Review
    # 2026-09-23T20:52:13Z: this refused only when `deployment.json` or
    # `submission.json` was already there, so an EMPTY target passed the
    # preflight and the composer refused it afterwards -- after the task
    # documents, the selections and the Authority acts. `two_jobs.main` is
    # create-only about the path itself, and so is this.
    if os.path.lexists(places["run"]):
        _refuse(f"{places['run']!r} already exists; the composer is "
                f"create-only about the target path itself, so this would "
                f"refuse after the Authority had been acted on. Nothing was "
                f"written. Select a fresh run root.")

    # THE PACKET THIS STEP BUILDS IS BUILT WITH THE PINNED CONTRACTS. The
    # manifests and their `job_input_identity` are computed in THIS process,
    # so `baton_v12` here has to be the selected one. The VALIDATION does not
    # happen here at all any more -- see below.
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import two_jobs
    strayed = two_jobs.imported_from(SNAPSHOT)
    building = [one for one in strayed if one.startswith("baton_v12 ")]
    if building:
        _refuse(f"this preparation derives digests with contracts that are "
                f"not the pinned ones: {'; '.join(building)}. Bind PYTHONPATH "
                f"to {SNAPSHOT}.")

    # ---- THE ONE EFFECT VALIDATION REQUIRES ------------------------------
    # The validator OPENS the task document -- `held_configuration` reads the
    # configured task and refuses one it cannot -- so the two task files have
    # to exist before the packet can be checked. They are the only thing
    # written before validation, they are never written over differing bytes
    # (the refusal above), and a validation failure leaves exactly these two
    # files in a run root that was this run's own. Nothing else is touched:
    # no selections, no Authority act, no composed document.
    os.makedirs(places["tasks"], exist_ok=True)
    for one in tasks.values():
        with open(one["path"], "wb") as handle:
            handle.write(one["raw"])

    # THE WHOLE PREFLIGHT RUNS WHERE THE COMPOSITION RUNS. Review
    # 2026-09-23T21:06:44Z: validating in THIS process meant `held` imported
    # `tools` from wherever this process found it, and I had explicitly
    # tolerated that. `two_jobs.py --check` performs the digest pins, the
    # import provenance and the entire composition in a subprocess bound to
    # the pinned source, and writes nothing -- so the bytes that validate are
    # the bytes that compose, by construction rather than by argument, and
    # the pins are checked before any Authority act.
    #
    # The selections it reads are written to a TEMPORARY path, because the
    # real one is an effect this step has not earned yet.
    import tempfile
    handle, staged = tempfile.mkstemp(prefix="two-jobs-check-", suffix=".json")
    try:
        with os.fdopen(handle, "wb") as writing:
            writing.write(raw_selections)
        answer = _composer(["--selections", staged, "--check"])
    finally:
        os.unlink(staged)
    if answer.returncode != 0:
        _refuse(f"the pinned product refuses this packet, and nothing beyond "
                f"the two task documents under {places['tasks']!r} was "
                f"written:\n{(answer.stderr or answer.stdout).strip()}")

    with open(places["selections"], "wb") as handle:
        handle.write(raw_selections)

    from baton_v12.authority import Authority
    opener = authority_opener or (
        lambda: Authority.open(places["authority_store"],
                               expected_authority_uuid=authority_uuid))
    authority = opener()
    try:
        prepared = prepare(
            authority, document, base=taken.base,
            operation_prefix=taken.operation_prefix or f"w247941-{run_id}")
    finally:
        authority.dispose()

    composed = compose(places["selections"], places["run"], stream=stream)
    # AND THE OWNED ROOTS THE LIVE PREFLIGHT WILL LOOK FOR. Owner
    # 2026-09-23: the previous packet declared them and created none, so the
    # supervisor refused in `worker_preflight` before it submitted anything
    # and the operator had to `mkdir` by hand.
    provisioned = provision(places)
    # THE EXACT OPERANDS THE NEXT TWO STEPS TAKE, printed from the places this
    # run actually used rather than from a page that has to be kept in step.
    print(json.dumps({
        "run_id": run_id, "run_root": run_root,
        "authority_uuid": authority_uuid,
        "places": places, "tasks_touch": touched,
        "provisioned": provisioned,
        "provenance": {
            "pinned_source": SNAPSHOT,
            "this_process_resolved_elsewhere": strayed,
            "note": "the composer runs as a subprocess with PYTHONPATH bound "
                    "to the pinned source and runs this check itself; these "
                    "are this process's own imports, which validate the "
                    "packet but do not compose it"},
        "prepared": prepared, "composed": composed,
        "serve_command": [
            "--deployment", places["deployment"],
            "--submission", places["submission"],
            "--job-store", places["job_store"],
            "--control-store", places["control_store"],
            "--incarnation", f"two-jobs-{run_id}",
            "--outcome", places["outcome"],
            "--total-seconds", "600", "--cleanup-seconds", "60"],
        "status_command": [
            "--store", places["job_store"],
            "--incarnation", f"inspect-{run_id}",
            "--authority-uuid", authority_uuid,
            "status", "--control", places["control_store"]],
        "not_done_here": [
            "no container, credential, provider, engine or network reached",
            "no Job or control store opened",
            "no Git operation performed",
            "the run itself is a separate operator step",
        ],
    }, indent=2, sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    try:
        raise SystemExit(main())
    except PreparationRefusal as refusal:
        print(f"refused: {refusal}", file=sys.stderr)
        raise SystemExit(2)
