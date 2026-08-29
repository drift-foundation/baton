"""A composed `/input/` root, for the suites whose subject is not the root.

W19784 review [P0], 2026-08-27. `request_runtime_start` now refuses to start a
runtime over a directory this manager has not held against its own assignment,
and the requirement is DERIVED: it applies exactly when the attempt records the
input digest it was claimed against, which every real delivery does.

So the lifecycle suites -- intake, attempts, sessions -- need a real composed
root even though none of them is about the root. This builds one, and it builds
it THROUGH `compose_input_root` rather than by writing two files, so a suite
that got a root this way got one the production boundary would accept. A
fixture that wrote the documents directly would be a second composer, and the
first defect this Work found was two parties disagreeing about one delivery.

`tests/manager/test_workspaces.py` owns the root's own rules; nothing here
asserts anything.
"""

import json
import os
import pathlib
import shutil
import tempfile

from baton_v12.contracts import digest
from baton_v12.worker_manager.workspaces import (assignment_workspace,
                                                 compose_input_root)

VECTORS = (pathlib.Path(__file__).resolve().parents[3] / ".." / "work"
           / "records" / "2026" / "08" / "finding-v12-isolated-agent-workers"
           / "findings" / "finding-v12-worker-contract" / "findings"
           / "finding-worker-control-api-manifests" / "evidence"
           / "vectors.json").resolve()


def _sealed(document):
    document.pop("manifest_digest", None)
    document["manifest_digest"] = digest(document)
    return document


def documents(*, work_ref, participant, generation, runtime_attempt_id,
              given=None, policy_digest=None, profile_digest=None):
    """The record's own published input manifest, and an assignment minted for
    THIS attempt against it.

    The input side is the conformance vector rather than a hand-built document,
    for the reason the rest of this campaign gives: a manifest written to pass
    my own rules proves less than the one the contract finding published.
    """
    corpus = json.loads(VECTORS.read_text(encoding="utf-8"))
    by_schema = {one["document"].get("schema"): one["document"]
                 for one in corpus["valid"]}
    if given is None:
        given = dict(by_schema["baton.worker-manifest/input"],
                     work_ref=dict(work_ref))
        if policy_digest is not None:
            given["policy_digest"] = policy_digest
        if profile_digest is not None:
            given["runtime_profile_digest"] = profile_digest
        given = _sealed(given)
    # A SUPPLIED input manifest is used UNCHANGED and is never resealed. The
    # caller supplies one because the attempt was recorded against ITS digest,
    # and a fixture that edited it would move that digest and test
    # `authorize_input_root`'s refusal everywhere by accident.
    assignment = _sealed(dict(
        by_schema["baton.worker-manifest/assignment"],
        assignment_ref={"work_ref": dict(work_ref),
                        "participant": participant,
                        "generation": generation},
        runtime_attempt_id=runtime_attempt_id,
        input_manifest_digest=given["manifest_digest"],
        policy_digest=given["policy_digest"],
        runtime_profile_digest=given["runtime_profile_digest"]))
    return given, assignment


def composed(case, storage, *, work_ref, participant, generation,
             runtime_attempt_id, given=None, policy_digest=None,
             profile_digest=None):
    """A composed root for one attempt, cleaned up with the case.

    Answers `(inputs, input_manifest_digest)`. The digest is what the caller
    must record on the attempt: `authorize_input_root` compares the root's
    input manifest with the digest the attempt was claimed against, and a
    fixture that recorded a different one would be testing that refusal
    everywhere by accident.
    """
    given, assignment = documents(
        work_ref=work_ref, participant=participant, generation=generation,
        runtime_attempt_id=runtime_attempt_id, given=given,
        policy_digest=policy_digest, profile_digest=profile_digest)
    inputs = assignment_workspace(
        configured_group(case.store), storage, runtime_attempt_id)["inputs"]
    compose_input_root(inputs, given, assignment,
                       assignment=dict(assignment["assignment_ref"]),
                       runtime_attempt_id=runtime_attempt_id)
    case.addCleanup(_forcibly_remove, inputs)
    return inputs, given["manifest_digest"]


def storage_under(case):
    """A workspace storage root that goes away with the case."""
    home = tempfile.mkdtemp(prefix="v12-input-roots-")
    case.addCleanup(_forcibly_remove, home)
    place = os.path.join(home, "storage")
    os.makedirs(place)
    return place


def _forcibly_remove(place):
    # The component delivers READ-ONLY documents on purpose, so the fixture
    # has to be able to take them away again.
    for current, _directories, files in os.walk(place):
        os.chmod(current, 0o700)
        for name in files:
            os.chmod(os.path.join(current, name), 0o600)
    shutil.rmtree(place, ignore_errors=True)


def configured_group(store):
    """The deployment's configured workspace group, for a fixture.

    W33936 review [P1]: a fixture cannot mint a `WorkspaceGroup` any more than
    a caller can, and that is the correction. It has to CONFIGURE one -- the
    deployment's act -- and then read the manager's own record, which is
    exactly the sequence a real deployment performs.

    WHICH GID, AND WHY IT COMES FROM THE ENVIRONMENT. M34630 requires a
    DEDICATED non-authority group, which is a property of a DEPLOYMENT -- so
    the deployment is what names it here. `BATON_V12_WORKSPACE_GROUP` is the
    same operand a real deployment passes to `configure_workspace_group`, and
    a run that sets it to a provisioned dedicated group proves the ruled
    boundary rather than an approximation of it.

    THE FALLBACK IS NAMED RATHER THAN SILENT. Without it the fixture
    configures `os.getgid()`, the group this process can actually `chgrp` to,
    so every step stays real on a workstation that has no provisioned group.
    That fallback proves the MECHANISM and says nothing about whether a
    manager's own primary group is an acceptable production configuration.
    `evidence/w33936-dedicated-group-*.txt` is the run that sets the variable.
    """
    from baton_v12.worker_manager import (configure_workspace_group,
                                          configured_workspace_group)
    configure_workspace_group(store, deployment_workspace_group())
    return configured_workspace_group(store)


def deployment_workspace_group():
    """The gid the deployment configures, or this process's own group.

    A malformed value is a REFUSAL rather than a fallback: a run that meant to
    prove a dedicated group and quietly proved the login group instead is the
    exact substitution this Work exists to close.
    """
    named = os.environ.get("BATON_V12_WORKSPACE_GROUP")
    if named is None:
        return os.getgid()
    if not named.lstrip("-").isdigit():
        raise AssertionError(
            f"BATON_V12_WORKSPACE_GROUP is {named!r}; the deployment's "
            f"configured workspace group is a group id, and a fixture that "
            f"fell back to os.getgid() here would report a login-group run as "
            f"a dedicated-group one")
    return int(named)
