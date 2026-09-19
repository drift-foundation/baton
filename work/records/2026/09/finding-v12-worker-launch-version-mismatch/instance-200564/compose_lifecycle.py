"""Compose the lifecycle capacity for W197661, from MEASURED identities.

Correcting `review-2026-09-18T01-21-09Z.md`. `compose_chain.py` is preserved
unchanged beside its outputs; this is the correction and it differs in four
ways that the review named one at a time.

R1  THE CREDENTIAL FIXTURE. `tools/single_worker.py` calls
    `credentials.resolved_delivery` unconditionally and its slot validator
    refuses an empty list, so this deployed composition cannot express the
    no-credential path the lower adapter supports. That is a DEPLOYMENT
    LIMITATION and it is recorded as one. The bounded continuation the reviewer
    authorized is a PRIVATE DISPOSABLE SYNTHETIC source: one slot, one file
    this run writes itself, containing an explicitly non-bearer marker and
    granting access to nothing. No credential file from any real deployment is
    read or reused and NO AUTHENTICATION COVERAGE IS CLAIMED.

R2  ONE MANIFEST PER JOB, NOT ONE PER ROLE. `_SingleWorker._matches` compares
    the Job's `input_digest` with its own deployment's `manifest_digest`, and
    three role-specific manifests produce three seals of which the Job can name
    exactly one -- so review and integration were refused with "the Job names
    another bootstrap input". The reviewer reproduced that against the real
    check. The product equality check is untouched and no seal is spoofed: the
    manifest is a fact about the JOB's input, and role independence is carried
    by distinct participants, principals, launch roles and private homes, which
    is where `stage_execution._independent` looks for it.

R3  MEASURED IDENTITIES AND FAIL-CLOSED. Every placeholder is gone: the
    declared base is READ OUT OF the disposable target repository's own refs,
    the principals are ASKED OF the bootstrapped Authority, the record binding
    digests the retained `record-snapshot/` bytes, the adapter digest measures
    the adapter file, and the toolchain digest measures the fixture build
    context this image was actually built from. `main` returns non-zero the
    moment any required validator refuses, and says INCOMPLETE in its own
    output, so no later launcher can read a zero here as validated readiness.

STILL COMPOSES ONLY. It writes this package's documents and the bootstrap
input; it bootstraps nothing, starts nothing, submits nothing and runs no
provider. Those are the operator steps that follow, from the installed command.

ADAPTED, NOT INHERITED. No authority, identity, credential, network, mutable
tag, version-control write or execution selection travels from the reference
record. The image is this Work's LABELLED FIXTURE and the accepted production
digests are deliberately not used.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DOSSIER = HERE.parent
REPO = Path("/home/sl/src/baton")
sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))

# THE INSTANCE THIS WORK ALREADY BOOTSTRAPPED, reused rather than replaced: a
# second disposable root would be a second thing to dispose of, and this one
# holds the Authority whose principals the deployment must name.
# THE CLEAN RUN'S OWN DESTINATION. The first one, ...-200564, is
# RETAINED as the diagnostic that measured three wiring walls in
# sequence; correcting each one recomposed the input manifest under a
# Job whose seal was already recorded, so the lifecycle this package
# actually proves is composed ONCE, from the final wiring, here.
DEST = Path("/home/sl/baton-v12-lifecycle-200564-clean")
UUID = "af29c003da434c3aa311b5de4a09f2ee"
WORK = "af29c003-W1"
JOB = "w197661-lifecycle"
PROFILE = "w197661-fixture-profile"
TARGET_ID = "w197661-target"
CREATED = "2026-09-18T05:30:00.000Z"
ROLES = ("implementation", "review", "integration")
ACTORS = {"implementation": "baton.w197661-author",
          "review": "baton.w197661-reviewer",
          "integration": "baton.w197661-integrator"}
RECEIPTS = {"verification": "baton.w197661-verifier",
            "review": "baton.w197661-judge",
            "approval": "baton.w197661-approver"}

# THE SYNTHETIC SOURCE, and every part of its name says what it is. The slot is
# a LOGICAL name the assignment authorizes; the provider and reference are the
# opaque pair the registry is matched on; the file holds a marker no provider
# would ever accept.
# THE SLOT NAME IS THE PORT'S REQUIREMENT, not a name this composition is free
# to choose. Measured in the live run of claim200564, one wall further on than
# the instructions: tools/integration_worker refuses any resolution that does
# not carry REQUIRED_CREDENTIAL_SLOT, which is the literal "claude" -- the slot
# the real provider image reads its bearer from. A fixture integrator that
# reads no bearer at all cannot express that, so the SECOND half of the
# credential limitation this package already records applies here too: the
# name is the required one and WHAT IS BEHIND IT IS STILL THE SYNTHETIC
# NON-BEARER MARKER this run writes itself. No credential is read, reused or
# harvested, nothing authenticates to anything, and no authentication coverage
# is claimed -- the fixture agent never opens the slot.
SLOT = "claude"
FIXTURE_PROVIDER = "w197661-synthetic-fixture"
FIXTURE_REFERENCE = "non-bearer-marker"
NOT_A_CREDENTIAL = (
    "NOT-A-CREDENTIAL w197661 synthetic fixture marker; this file authorizes "
    "nothing, authenticates to nothing and was written by "
    "instance-200000/compose_lifecycle.py to satisfy a deployment that cannot "
    "express an empty credential delivery\n")

# THE IMMUTABLE BASE THIS FIXTURE IS BUILT ON, read from the recipe rather
# than restated, so a recipe that moves its base cannot leave this record
# describing the old one.
def _fixture_base():
    for line in (HERE / "context/Dockerfile.fixture").read_text().splitlines():
        if line.startswith("FROM "):
            return line.split(None, 1)[1].strip()
    raise Unmeasured("the fixture recipe names no base")


_REVISION = re.compile(r"\A[0-9a-f]{40}\Z")

# WHAT ONE `bootstrap` RUN DOES TO THE AUTHORITY'S APPROVAL POLICY GENERATION,
# and this is MEASURED rather than assumed. W197661 claim200564, the fifth wall
# this package met between a completed review and a started integration:
#
#   integration.driver._accepted_receipts refuses unless the deployment's
#   configured pin EQUALS the Authority's CURRENT generation -- correctly,
#   because the pin is what this deployment was configured to approve under.
#   But `bootstrap` certifies contracts and permits transitions on every run,
#   and each of those acts bumps that generation. So the pin travels IN to the
#   command that invalidates it, and a freshly bootstrapped deployment cannot
#   satisfy its own pin unless the composition predicts the bump.
#
# OBSERVED ON THIS TREE AND NOT A CONTRACT. Review 2026-09-18T06-19-15Z: I
# called this fail-closed and it was not. `policy_pin` reads the current
# generation and adds this number; `main` composes documents and does NOT
# bootstrap, so nothing in the composition could have compared the resulting
# generation to the prediction. A manual post-check I performed and reported is
# not an executable gate, and describing one as the other is the same kind of
# claim review200453 already corrected me on.
#
# WHAT WAS ACTUALLY OBSERVED: 9 before a no-op repeat bootstrap and 16 after
# it, and 16 to 23 on the next. Twice is an observation about THIS tree's
# bootstrap acts; it is not a stable interface and must not be relied on as
# one. It is used here only to PROPOSE a pin, and `check_policy_pin` below is
# what decides whether the proposal was right -- run after the bootstrap, and
# refusing before anything is called ready.
BOOTSTRAP_POLICY_BUMP = 7


def digest(value):
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True,
                   separators=(",", ":")).encode()).hexdigest()


def digest_bytes(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest_bytes(Path(path).read_bytes())


class Unmeasured(Exception):
    """A provenance fact this composer could not MEASURE.

    Raised rather than defaulted. Every value this module puts in a document is
    read off something real, and the one failure mode the review found was a
    placeholder standing where a measurement belonged -- so an absent
    measurement stops the composition instead of producing a document that
    looks complete.
    """


# -- measured provenance ------------------------------------------------------


def declared_base(target):
    """The disposable target's OWN current main revision, read from its refs.

    NOT A CONSTANT AND NOT A ZERO. `line_declared_base` is the revision every
    checkpoint on this line is declared against, and an all-zero value is a
    revision no repository has. This reads the packed or loose ref directly --
    a file read, never a version-control mutation -- and refuses anything that
    is not one 40-character revision.
    """
    loose = Path(target) / "refs/heads/main"
    if loose.is_file():
        found = loose.read_text().strip()
    else:
        packed = Path(target) / "packed-refs"
        if not packed.is_file():
            raise Unmeasured(f"{target} has neither refs/heads/main nor "
                             f"packed-refs; this composer reads a declared "
                             f"base rather than inventing one")
        found = ""
        for line in packed.read_text().splitlines():
            if line.endswith(" refs/heads/main"):
                found = line.split(" ", 1)[0].strip()
                break
    if not _REVISION.match(found):
        raise Unmeasured(f"the target's main ref reads {found!r}, which is not "
                         f"one revision")
    return found


def policy_pin(*, opener=None):
    """The generation this composition PREDICTS the last bootstrap will leave.

    ASKED OF THE AUTHORITY, never assumed: a pin restated as a literal is the
    defect this whole composer exists to avoid. What is added to the reading is
    an OBSERVED effect of the bootstrap run that follows this composition, and
    the word is observed rather than guaranteed -- see `BOOTSTRAP_POLICY_BUMP`.

    A PREDICTION, AND NOTHING HERE VERIFIES IT. The verification is
    `check_policy_pin`, which runs after the bootstrap against the Authority
    itself; a composition cannot check the effect of a command it does not run.
    """
    from baton_v12.authority import Authority

    open_authority = opener or Authority.open
    authority = open_authority(str(DEST / "db/authority.sqlite3"),
                               expected_authority_uuid=UUID)
    try:
        held = authority.policy_generation()
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()
    if type(held) is not int or held < 1:
        raise Unmeasured("the Authority did not answer a policy generation")
    return held + BOOTSTRAP_POLICY_BUMP


def check_policy_pin(*, opener=None, pin=None):
    """The measured post-bootstrap equality, as an EXECUTABLE gate.

    Review 2026-09-18T06-19-15Z: "put an explicit measured post-bootstrap
    equality check into the execution/verifier path before readiness
    acceptance; cover a wrong prediction without weakening the actual approval
    pin."

    WHAT IT COMPARES is the pin the emitted deployment configuration actually
    carries against the generation the Authority is actually at, both read at
    the moment this runs -- not the number this module predicted, because a
    prediction compared against itself proves nothing. A deployment whose pin
    is wrong defers at its own integration with the reason buried in a tick
    report, which is precisely the silent wall this Work exists to remove, so
    it is refused here instead.

    IT WEAKENS NOTHING. `_accepted_receipts` still requires equality at the
    moment receipts are issued; this only refuses to call a deployment ready
    when that equality is already known to be false.
    """
    from baton_v12.authority import Authority

    if pin is None:
        configured = json.loads((DEST / "deployment.json").read_text())
        pin = configured.get("policy_generation")
    # READ-ONLY, AND THE DEFAULT IS WHAT MATTERS. Review 2026-09-18T06-41-32Z
    # [R2]: `read_authority` was corrected to `open_readonly` and THIS second
    # path still defaulted to `Authority.open`, which takes a write lock,
    # applies the schema and sets a persistent journal mode. A verifier that
    # reaches a deployment's Authority for writing is not a verifier, and a
    # reviewer's mocked-default probe recorded exactly one writable call.
    open_authority = opener or Authority.open_readonly
    authority = open_authority(str(DEST / "db/authority.sqlite3"),
                               expected_authority_uuid=UUID)
    try:
        held = authority.policy_generation()
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()
    return {"configured_pin": pin, "authority_generation": held,
            "equal": pin == held,
            "why_it_matters": "integration.driver._accepted_receipts refuses "
                              "unless these are equal, and a deployment that "
                              "cannot satisfy its own pin defers at its "
                              "integration with the reason only in a tick "
                              "report"}


def principals(participants, *, opener=None):
    """Who each participant IS, asked of the bootstrapped Authority.

    `bootstrap.principals_for` is the deployment's own function rather than a
    second opinion about identity: it ASKS an Authority that exists and derives
    the package's default for one that does not. Either way the value is the
    Authority's, and `"principal:" + name` -- which is what the superseded
    composer wrote -- was a string this record made up.
    """
    from tools import bootstrap

    places = bootstrap.layout(str(DEST))
    document = {"authority_uuid": UUID,
                "receipt_participants": dict(RECEIPTS),
                "integration_profile": {
                    "integrator_participant": ACTORS["integration"]},
                "workers": [{"participant": one} for one in participants]}
    return bootstrap.principals_for(places, document, opener=opener)


def image_present(image, *, run=None):
    """Whether the engine really holds the fixture image, positively.

    A composition that named an image nobody has would validate perfectly and
    fail at the first activation. This asks, and records the answer either way;
    it is the only engine contact in this file and it starts no container.
    """
    runner = run or (lambda argv: subprocess.run(
        argv, capture_output=True, text=True, timeout=30))
    try:
        found = runner(["docker", "image", "inspect", "--format",
                        "{{.Id}}", image])
    except Exception as failure:                             # noqa: BLE001
        return {"asked": True, "held": None,
                "why": f"{type(failure).__name__}"}
    held = (found.stdout or "").strip()
    return {"asked": True, "held": held == image,
            "reported_id": held or None,
            "returncode": found.returncode}


def build_context(root):
    """Every byte the fixture image was built from, measured file by file.

    The superseded composer hashed `{"fixture": <image digest>}` and called it
    a worker source manifest, which is the image's own identity wearing another
    name. This measures the RECIPE AND THE PAYLOAD -- the same thing the
    reference record's `image-context-manifest.json` is.
    """
    root = Path(root)
    if not root.is_dir():
        raise Unmeasured(f"the fixture build context {root} is not here; its "
                         f"payload identities cannot be measured")
    found = {}
    for place in sorted(root.rglob("*")):
        if place.is_file():
            found[str(place.relative_to(root))] = {
                "sha256": sha(place), "bytes": place.stat().st_size}
    if not found:
        raise Unmeasured(f"the fixture build context {root} holds no file")
    return found


def adapter_identity():
    """The adapter's measured bytes, and what that measurement does NOT prove.

    `adapter_digest` is a durable identity the deployment is accountable for,
    and the honest measurement is of the adapter SOURCE IN THIS CHECKOUT. It is
    NOT proof of the bytes inside the frozen distribution this instance runs:
    that bundle was built earlier, this file has been edited since under
    W198667, and the distribution's own identity is its runtime digest, which
    is recorded separately. Saying both is the whole point -- a single digest
    presented as if it were the running adapter would be exactly the kind of
    claim this review keeps finding.
    """
    place = REPO / "v12/python/src/baton_v12/worker_manager/oci.py"
    return {"path": str(place.relative_to(REPO)), "sha256": sha(place),
            "measures": "the adapter source in this checkout",
            "does_not_prove": "the adapter bytes inside the installed frozen "
                              "distribution, which was built before W198667 "
                              "edited this file; the installed runtime's own "
                              "identity is its runtime digest"}


# -- the private synthetic credential source ----------------------------------


def credential_fixture(root):
    """One private disposable source holding an explicit NON-BEARER marker.

    WRITTEN HERE, never harvested. `tools/user_credentials._proved_read`
    requires an ordinary file owned by this uid with no group or other
    permission, so both documents are created 0600 by this run. The registry
    names exactly one pair and the file behind it says in its own text that it
    is not a credential.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    source = root / "w197661-synthetic-non-bearer"
    registry = root / "registry.json"
    document = {"schema": "baton.user-credential-sources/1",
                "sources": [{"path": str(source),
                             "provider": FIXTURE_PROVIDER,
                             "reference": FIXTURE_REFERENCE}]}
    for place, payload in ((source, NOT_A_CREDENTIAL.encode()),
                           (registry, (json.dumps(document, indent=1,
                                                  sort_keys=True)
                                       + "\n").encode())):
        handle = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_TRUNC
                         | os.O_NOFOLLOW, 0o600)
        try:
            os.write(handle, payload)
        finally:
            os.close(handle)
        os.chmod(place, 0o600)
    return {"registry": str(registry), "source": str(source),
            "slot": SLOT,
            "mapping": {"provider": FIXTURE_PROVIDER,
                        "reference": FIXTURE_REFERENCE},
            "what_it_is": "a synthetic non-bearer marker this run wrote",
            "what_it_is_not": "no credential from any real deployment was read "
                              "or reused, and no authentication coverage is "
                              "claimed from it",
            "why_it_exists": "tools/single_worker.py calls "
                             "credentials.resolved_delivery unconditionally "
                             "and its slot validator refuses an empty list, so "
                             "this deployed composition cannot express the "
                             "no-credential path the adapter supports",
            "why_this_name": "tools/integration_worker.REQUIRED_CREDENTIAL_SLOT "
                             "is the literal 'claude' -- the slot the real "
                             "provider image reads its bearer from -- and the "
                             "port refuses a resolution without it before "
                             "composing anything, so a fixture integrator that "
                             "reads no bearer must still present that name",
            "what_is_behind_the_name": "the same synthetic non-bearer marker; "
                                       "the fixture agent never opens the slot"}


# -- the documents ------------------------------------------------------------


def policy_documents(facts):
    """This exercise's own policy layer, over THIS destination's paths.

    The superseded composer's policies named `/home/sl/baton-v12-lifecycle-
    198871`, a destination this deployment does not use -- so every digest over
    them identified a configuration for somewhere else.
    """
    return {
        "policy": {"work": "W197661",
                   "ruling": "owner seq198635, continued under "
                             "review-2026-09-18T01-21-09Z.md: a bounded "
                             "disposable deterministic lifecycle exercised "
                             "with a fake provider",
                   "base": facts["declared_base"],
                   "submission": [JOB],
                   "automatic_retry": False,
                   "review_before_execution": True},
        "resource_policy": {"wall_seconds": 600,
                            "implementation_attempt_seconds": 120,
                            "review_or_judge_attempt_seconds": 90,
                            "integration_seconds": 60,
                            "runtime_cpus": 2,
                            "runtime_memory_bytes": 2147483648,
                            "runtime_pids": 512,
                            "scratch_mounts": facts["scratch_mounts"],
                            "workspace_declared_capacity_bytes": 536870912,
                            "workspace_capacity_is_quota": False,
                            "deadline_action": "stop; retain evidence; "
                                               "no retry"},
        "network_policy": {"engine_network": "none",
                           "purpose": "a deterministic fixture reaches "
                                      "nothing; the synthetic slot grants "
                                      "access to no service"},
        "mount_policy": {"source": "read-only nominated source and a "
                                   "manager-held private development line",
                         "mutable_storage": str(DEST / "storage"),
                         "workspace_group": facts["workspace_group"],
                         "target": str(DEST / "repo/target.git"),
                         "target_reference": "refs/heads/main"},
        "tool_policy": {"provider_arguments": [],
                        "model_selection": "NONE; the scripted deterministic "
                                           "agent inside the labelled fixture "
                                           "image",
                        "verification": [],
                        "final_verification": []},
        "credential_policy": {"registry": facts["credential"]["registry"],
                              "slots": {SLOT: facts["credential"]["mapping"]},
                              "payload_in_configuration": False,
                              "synthetic_non_bearer": True},
        "retention_policy": {"disposition": "retain", "root": str(DEST),
                             "automatic_deletion": False}}


def task_document(facts):
    """The concrete deterministic workload, in the accepted task contract.

    `baton.dogfood-task/2` is the contract the worker image's own reader holds,
    and the superseded composer invented `baton.v12.task/1` with an empty
    scope -- a document shaped like nothing that reads it. The instructions
    name the exact expected candidate so a collection proof has something to
    be a proof OF.
    """
    return {
        "schema": "baton.dogfood-task/2",
        "task_id": JOB,
        "instructions":
            "Add exactly one file, w197661-fixture.txt, at the root of the "
            "read-only source you are given a private line over. Its whole "
            "content is the single line "
            "'w197661 deterministic fixture candidate' followed by one "
            "newline. Change nothing else: no existing file, no mode, no "
            "version-control configuration. Then write the declared outputs "
            "and end the turn. This is a deterministic fixture assignment and "
            "no model is consulted for it.",
        "source_root": "source",
        "source_profile": "git-line",
        "declared_base": facts["declared_base"],
        # THE REQUIRED COMMAND, and an empty list was why this lifecycle could
        # not finish. W197661 review 2026-09-18T05-14-53Z [R1]:
        # Integration.required_tests refuses a task naming no verification
        # command, so every integration tick deferred with that exact reason
        # while the two earlier stages sat completed.
        #
        # IT IS A REAL CHECK OF THE CANDIDATE rather than a command chosen to
        # exit zero: it asserts the one file this assignment exists to produce
        # holds exactly the declared bytes, so a turn that committed the wrong
        # content fails it. It reads and writes nothing, which matters twice --
        # the producer runs it inside a line whose cleanliness the freeze
        # depends on, and the integrator runs the SAME argv again over the
        # imported tree.
        #
        # PYTHON AND NOT A SHELL: the fixture image enters python3 and the
        # integrator runs the argv directly with no shell, so a command that
        # needed one would be a command only one of the two could run.
        "verification": [
            "python3", "-c",
            "import pathlib,sys;"
            "sys.exit(0 if pathlib.Path('w197661-fixture.txt').read_text()"
            " == 'w197661 deterministic fixture candidate\\n' else 1)"]}


def role_instruction_documents():
    """What each stage is actually told, as real text rather than one string."""
    return {
        "implementation": "Produce exactly the candidate the frozen task "
                          "describes and nothing else.",
        "review": "Read the frozen checkpoint. Accept it only if it adds "
                  "exactly w197661-fixture.txt with exactly the declared line "
                  "and changes nothing else; otherwise request changes and say "
                  "which rule was broken.",
        "integration": "Import exactly the accepted candidate onto the "
                       "canonical target. Refuse anything outside the "
                       "candidate rather than repairing it."}


def manifest(facts, *, seal):
    """ONE sealed input manifest for THIS JOB, shared by every stage.

    R2. The seal is recomputed after the outputs are set, exactly as
    `deployment.py` does -- a manifest whose seal predates its own contents
    agrees with nothing.
    """
    from tools import dogfood_operator
    from baton_v12.worker_manager import source_boundary

    empty = {"entries": [], "entry_count": 0, "total_bytes": 0,
             "tree_digest": facts["empty_tree_digest"]}
    given = dogfood_operator.input_manifest(
        work_ref={"authority_uuid": UUID, "work_id": WORK}, staged=empty,
        created_at=CREATED, manifest_id=f"w197661-{JOB}",
        assignment_contract="v12-assignment-1",
        human_contract={"artifact_id": "w197661-task",
                        "media_type": "application/json",
                        "bytes": facts["task_bytes"],
                        "content_digest": facts["task_digest"],
                        "locator": "artifact://contracts/w197661-task"},
        record_binding=facts["record_binding"],
        role_instructions_digest=facts["role_instructions_digest"],
        runtime_profile_digest=facts["profile_digest"],
        toolchain_digest=facts["toolchain_digest"],
        worker_image_digest=facts["image"], policies=facts["policy_digests"])
    given["sources"][0]["consumption"] = \
        source_boundary.source_consumption("git-line")
    constraints = {"max_bytes": 67108864, "max_entries": 2000,
                   "allowed_media_types": ["application/octet-stream",
                                           "text/plain"],
                   "link_policy": "forbid", "validator_digest": None}
    given["outputs"] = [
        {"name": one, "type": kind, "path": one, "required": False,
         "constraints": constraints}
        for one, kind in (("proposal", "git-change-proposal"),
                          ("findings", "directory-result"),
                          ("logs", "directory-result"))]
    given.pop("manifest_digest")
    given["manifest_digest"] = digest(given)
    return seal(given, "inputManifest")


def deployment(role, facts):
    """One role's complete single-worker deployment.

    The manifest is the JOB's, the same document in all three. What makes these
    three independent is what `stage_execution._independent` actually reads:
    distinct participants, distinct principals, distinct launch roles and
    private launch and credential homes.
    """
    return {
        "schema": "baton.v12.single-worker-deployment/4",
        "authority_store": str(DEST / "db/authority.sqlite3"),
        "authority_uuid": UUID,
        "participant": ACTORS[role],
        "principal": facts["principals"][ACTORS[role]],
        "profile_name": PROFILE, "profile_digest": facts["profile_digest"],
        "policy_digest": facts["policy_digests"]["policy_digest"],
        "adapter_name": "docker-single-worker",
        "adapter_digest": facts["adapter"]["sha256"],
        # ONE IMAGE FOR EVERY ROLE, AND THAT IS THE BLOCKER RATHER THAN THE
        # CHOICE. claim201324 built an integrating image and selected it here,
        # and `tools/single_worker.py:267` refused the composition: the Job's
        # ONE input manifest names one `worker_image_digest` and every worker
        # deployment must equal it. The image is built and recorded as
        # evidence; selecting it needs the shape named in this claim's
        # handoff, not a per-role override the contract does not admit.
        "engine": "docker", "image_digest": facts["image"],
        "network": "none",
        "workspace_storage": str(DEST / "storage"),
        "workspace_group": facts["workspace_group"],
        "launch_home": str(DEST / "launch" / role),
        "credential_home": str(DEST / "credentials" / role),
        "credential_sources": facts["credential"]["registry"],
        "credential_slots": [SLOT],
        "credential_profile": {SLOT: dict(facts["credential"]["mapping"])},
        "nominated_source": str(DEST / "repo/workspace"),
        "workspace_capacity": {"max_bytes": 536870912},
        "input_manifest": facts["manifest"],
        "task_document": str(HERE / "task.json"),
        "launch_contract": "v12-assignment-1", "launch_role": role,
        "review_route": {"implementation": "rview", "review": "integration",
                         "integration": "integration"}[role],
        "retention_policy_digest":
            facts["policy_digests"]["retention_policy_digest"],
        "retention_disposition": "retain"}


def submission(facts):
    """The Job, whose `input_digest` is TAKEN FROM the one seal."""
    return {
        "schema": "baton.v12.job-submission/2",
        "submission_id": "w197661-lifecycle-200564",
        "jobs": [{
            "job_id": JOB,
            "input_digest": facts["manifest"]["manifest_digest"],
            "policy_digest": facts["policy_digests"]["policy_digest"],
            "test_scope": [], "terminal_policy": "report-and-hold",
            "stages": [{"kind": kind, "work_id": WORK,
                        "profile_name": PROFILE,
                        "profile_digest": facts["profile_digest"],
                        "depends_on": (
                            [] if kind == "implementation" else
                            [{"job_id": JOB, "kind": "implementation"}]
                            if kind == "review" else
                            [{"job_id": JOB, "kind": "review"}])}
                       for kind in ROLES]}]}


def bootstrap_inputs(facts):
    """What the installed `bootstrap` command is handed to supply capacity.

    `bootstrap.DEFERRED` accepts `workers` and `jobs` on a repeated bootstrap,
    and it composes the identities, Works, routes and grants this deployment
    needs. It DERIVES `principal`, `participant`, `authority_store`,
    `authority_uuid` and `launch_role` into each deployment, so what travels
    here is the rest -- and this composer fills the derived members too, so
    what it validated is what will be written.
    """
    return {
        "schema": "baton.v12.stack-bootstrap/1",
        "state_root": str(DEST),
        "checkpoint_profile": "git",
        "integration_profile": {
            "profile_kind": "git", "profile_version": 1,
            "integrator_participant": ACTORS["integration"],
            "instructions_digest": facts["integration_instructions_digest"]},
        "retention_policy_digest":
            facts["policy_digests"]["retention_policy_digest"],
        "retention_disposition": "retain",
        "pool_generation": 1,
        "policy_generation": facts["policy_generation"],
        "receipt_participants": dict(RECEIPTS),
        "integration_target": str(DEST / "repo/target.git"),
        "integration_target_reference": "refs/heads/main",
        "integration_workspace": str(DEST / "repo/workspace"),
        # WHERE THE INTEGRATOR'S INSTRUCTION BYTES LIVE, and leaving it out is
        # what stopped this lifecycle one stage further on. Measured in the
        # live run of claim200564: with the required command supplied, the
        # integration launch stopped refusing "the configured implementation
        # task names no verification command" and began refusing "this
        # deployment configures no integration_instructions" -- an OPTIONAL
        # bootstrap member this composition never supplied, so the wall was
        # this package's rather than the deployment's, exactly as the previous
        # one was.
        #
        # THE PIN IS WHAT MAKES NAMING A PATH SAFE: the integration profile
        # already carries the digest these bytes must have, and
        # stage_execution refuses bytes that do not match it before any
        # container starts. IT IS IN THE DESTINATION AND NOT IN THIS
        # CHECKOUT, because a running deployment reads nothing from here.
        "integration_instructions": str(DEST / "integration-instructions.txt"),
        "workers": [{"worker_id": f"w197661-{role}", "role": role,
                     "participant": ACTORS[role],
                     "deployment": deployment(role, facts)}
                    for role in ROLES],
        "jobs": [{"job_id": JOB, "work_id": WORK,
                  "line_declared_base": facts["declared_base"],
                  "canonical_target_id": TARGET_ID,
                  "source_worker_id": "w197661-implementation"}]}


# -- the validators, named and injectable -------------------------------------

REQUIRED = ("check_manifest_structure", "bootstrap.held",
            "stage_execution.held_configuration", "bootstrap.validated",
            "job_manager.documents.owned_submission")

# THE ONE THAT ONLY EXISTS BECAUSE THIS WRITES FILES, and it was earned. The
# first run of this composer validated its in-memory documents, answered
# `complete: true`, and then its own output loop rewrote `task.json` indented
# -- so the artefacts on disk were NOT the ones any validator had seen, and the
# installed bootstrap refused them: "the configured task document is 665 bytes
# and this profile's human-contract artifact declares 635". A composition is
# only as validated as the bytes it leaves behind, so the configuration is held
# again AFTER every file is written, reading the task document off disk exactly
# as the deployment will.
AFTER_WRITING = "stage_execution.held_configuration (over the written files)"


def production_validators():
    """The canonical owner of each question, never a second opinion here.

    THE STAGE-EXECUTION DOCUMENT IS NOT WRITTEN HERE AT ALL. An earlier cut of
    this composer hand-wrote one beside the bootstrap input, which is two
    places for one configuration and exactly how they drift; `bootstrap
    .configuration` is the function the installed command uses, so the document
    validated below is the document that will actually be emitted.
    """
    from tools import bootstrap, stage_execution
    from baton_v12.contracts import check_manifest_structure
    from baton_v12.job_manager import documents as job_documents

    return {"check_manifest_structure": check_manifest_structure,
            "stage_execution.held_configuration":
                stage_execution.held_configuration,
            "job_manager.documents.owned_submission":
                job_documents.owned_submission,
            "bootstrap.held": bootstrap.held,
            "bootstrap.configuration": bootstrap.configuration,
            "bootstrap.validated": bootstrap.validated}


class Run:
    """One composition and the exact result of every validator it called."""

    def __init__(self, validators):
        self.validators = validators
        self.steps = []
        self.refused = []
        # OWNED PER RUN rather than read off the module constant, because one
        # more validation becomes required the moment this writes artefacts --
        # see `AFTER_WRITING`.
        self.required = list(REQUIRED)

    def step(self, what, run):
        try:
            answer = run()
        except Exception as failure:                         # noqa: BLE001
            self.steps.append({"validator": what, "result": "REFUSED",
                               "refusal": f"{type(failure).__name__}: "
                                          f"{str(failure)[:600]}"})
            self.refused.append(what)
            return None
        self.steps.append({"validator": what, "result": "accepted"})
        return answer

    @property
    def complete(self):
        """Every REQUIRED validator ran and accepted. Nothing weaker.

        R3: `compose_chain.main` returned zero whenever the manifests existed,
        so a configuration or submission refusal was reported in the document
        and rewarded with a success exit code. Completeness is the conjunction
        of the named required set, and a validator that never ran is as absent
        as one that refused.
        """
        ran = {one["validator"] for one in self.steps
               if one["result"] == "accepted"}
        return not self.refused and all(one in ran for one in self.required)


def compose(run, *, facts=None, write=True):
    """Every document, with each validator called as it becomes answerable."""
    facts = dict(facts or {})
    documents = {}

    seal = run.validators["check_manifest_structure"]
    held = run.validators["stage_execution.held_configuration"]
    owned = run.validators["job_manager.documents.owned_submission"]
    accepts = run.validators["bootstrap.held"]
    composes = run.validators["bootstrap.configuration"]
    emitted = run.validators["bootstrap.validated"]

    policies = policy_documents(facts)
    facts["policy_digests"] = {name + "_digest": digest(value)
                               for name, value in policies.items()}
    documents["policies"] = policies

    task = task_document(facts)
    # THE EXACT BYTES THAT ARE DECLARED. `held_configuration` compares the task
    # document on disk against the human-contract artifact the manifest names,
    # and an indented rewrite is a different document from the one measured.
    payload = json.dumps(task, sort_keys=True, separators=(",", ":")).encode()
    if write:
        (HERE / "task.json").write_bytes(payload)
    facts["task_bytes"] = len(payload)
    facts["task_digest"] = digest_bytes(payload)
    documents["task"] = task

    instructions = role_instruction_documents()
    facts["role_instructions_digest"] = digest(instructions)
    documents["role_instructions"] = instructions

    profile = {"name": PROFILE, "provider": "scripted deterministic fixture",
               "selected_base": facts["fixture_base"],
               "image_variants": {
                   "fixture": facts["image"],
                   "integration-fixture": facts["integration_image"]},
               "source_profile": "git-line", "roles": list(ROLES),
               "model_selection": "NONE; the scripted agent inside the "
                                  "labelled fixture image",
               "credentials": dict(facts["credential"]["mapping"]),
               "network": "none"}
    facts["profile_digest"] = digest(profile)
    documents["runtime_profile"] = profile

    toolchain = {"fixture_image": facts["image"],
                 "integration_fixture_image": facts["integration_image"],
                 "fixture_base": facts["fixture_base"],
                 "worker_source_manifest": digest(facts["build_context"]),
                 "build_context_entries": len(facts["build_context"])}
    facts["toolchain_digest"] = digest(toolchain)
    documents["toolchain"] = toolchain

    facts["manifest"] = run.step(
        "check_manifest_structure", lambda: manifest(facts, seal=seal))
    if facts["manifest"] is None:
        return facts, documents

    inputs = bootstrap_inputs(facts)
    documents["bootstrap_inputs"] = inputs
    run.step("bootstrap.held", lambda: accepts(inputs))

    # THE DOCUMENT THE INSTALLED COMMAND WILL EMIT, composed by its own
    # function and then held to the manager's rules. Nothing here writes a
    # second stage-execution document for the same deployment.
    config = None
    try:
        config = composes(dict(inputs, authority_uuid=UUID),
                          facts["principals"])
    except Exception as failure:                             # noqa: BLE001
        run.steps.append({"validator": "bootstrap.configuration",
                          "result": "REFUSED",
                          "refusal": f"{type(failure).__name__}: "
                                     f"{str(failure)[:600]}"})
        run.refused.append("bootstrap.configuration")
    if config is not None:
        documents["stage_execution"] = config
        run.step("stage_execution.held_configuration", lambda: held(config))
        run.step("bootstrap.validated", lambda: emitted(config))

    asked = submission(facts)
    documents["submission"] = asked
    run.step("job_manager.documents.owned_submission", lambda: owned(asked))
    return facts, documents


def measured(*, run=None, opener=None, write=True):
    """Every provenance fact, MEASURED, before one document is composed."""
    from tools import stage_execution
    from baton_v12.worker_manager import source_boundary

    # THE IMAGE THIS CLAIM BUILT, read from the build that produced it rather
    # than from an older episode's exercise record. review199914: the
    # instance-199877 recipe COPIED the proposing agent and then entered
    # `baton_worker.py`, so `main` took `_scripted_default()` and ran the OLD
    # agent. This one enters `proposing_entry.py`, which injects it.
    image = (HERE / "build/fixture.iid").read_text().strip()
    snapshot = HERE / "record-snapshot"
    facts = {
        "image": image,
        "fixture_base": _fixture_base(),
        "image_in_engine": image_present(image, run=run),
        "build_context": build_context(HERE / "context"),
        "adapter": adapter_identity(),
        "declared_base": declared_base(DEST / "repo/target.git"),
        "credential": credential_fixture(DEST / "credential-fixture"),
        "workspace_group": os.getgid(),
        "empty_tree_digest": stage_execution.single_worker.EMPTY_TREE_DIGEST,
        "scratch_mounts": [list(one) for one in source_boundary.SCRATCH_MOUNTS],
        "record_binding": {
            "root": "baton",
            "path": str(DOSSIER.relative_to(REPO)),
            "finding_digest": sha(snapshot / "FINDING.md"),
            "plan_digest": sha(snapshot / "PLAN.md")},
    }
    integration = HERE / "integration-instructions.txt"
    if not integration.is_file():
        integration.write_text(role_instruction_documents()["integration"]
                               + "\n")
    facts["integration_instructions_digest"] = sha(integration)
    # AND THE DEPLOYMENT GETS ITS OWN COPY, beside the state it serves from.
    # The bytes are pinned by the profile digest above, so the copy is proved
    # rather than trusted; what this buys is a deployment that does not read
    # this dossier at serve time.
    delivered = DEST / "integration-instructions.txt"
    if write:
        delivered.write_bytes(integration.read_bytes())
    facts["integration_instructions"] = str(delivered)
    facts["principals"] = principals(sorted(ACTORS.values()), opener=opener)
    facts["policy_generation"] = policy_pin(opener=opener)
    # AND THE INTEGRATOR'S OWN IMAGE, measured the same way: an identity this
    # composition states rather than measures is the defect this whole file
    # exists to avoid.
    # THE DIGEST IS THE STRING; `image_present` answers the engine's REPORT
    # about it, which is a document and not an identity. The proposing image
    # is read the same way a few lines above, and conflating the two put a
    # dictionary where the configuration requires text.
    facts["integration_image"] = _read_iid(
        HERE / "build/integration-fixture.iid")
    facts["integration_image_in_engine"] = image_present(
        facts["integration_image"], run=run)
    facts["integration_image_inputs"] = {
        str(one.relative_to(HERE / "context-integration")): sha(one)
        for one in sorted((HERE / "context-integration").rglob("*"))
        if one.is_file() and "__pycache__" not in str(one)}
    return facts


def _read_iid(place):
    """The image this episode built, from the file the build wrote."""
    if not Path(place).is_file():
        raise Unmeasured(f"{place} does not name a built image")
    return Path(place).read_text().strip()


def main(argv=None, *, validators=None, write=True, run=None, opener=None):
    run_state = Run(validators or production_validators())
    try:
        facts = measured(run=run, opener=opener, write=write)
    except Unmeasured as failure:
        print(json.dumps({"complete": False, "unmeasured": str(failure)},
                         indent=1))
        return 2
    facts, documents = compose(run_state, facts=facts, write=write)
    if write:
        run_state.required.append(AFTER_WRITING)
        for name, document in documents.items():
            # THE TASK IS NOT REWRITTEN. Its exact bytes were already written
            # by `compose` and its width is DECLARED in the manifest's human
            # contract; an indented copy over the same name is a different
            # document from the one that was measured.
            if name == "task":
                continue
            (HERE / f"{name}.json").write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n")
        config = documents.get("stage_execution")
        run_state.step(
            AFTER_WRITING,
            (lambda: run_state.validators[
                "stage_execution.held_configuration"](config))
            if config is not None else
            (lambda: (_ for _ in ()).throw(
                Unmeasured("no configuration was composed, so there is "
                           "nothing on disk to hold"))))
    found = {
        "claim": 200564,
        "complete": run_state.complete,
        "corrects": "review-2026-09-18T01-21-09Z.md R1, R2, R3",
        "validator_calls": run_state.steps,
        "required": list(run_state.required),
        "refused": run_state.refused,
        "composes_only": "writes documents; bootstraps nothing, starts "
                         "nothing, submits nothing, runs no provider",
        # NONE WHEN THE SEAL REFUSED, and said as none. `facts["manifest"]` is
        # set to the validator's answer, which is `None` on a refusal -- so
        # `.get()` on it raised an AttributeError and the composer died with a
        # traceback instead of reporting the refusal it had already recorded.
        # A composer whose failure path crashes cannot report a failure.
        "one_manifest_for_every_stage":
            (facts.get("manifest") or {}).get("manifest_digest"),
        "declared_base": facts["declared_base"],
        "principals": facts["principals"],
        "adapter": facts["adapter"],
        "image_in_engine": facts["image_in_engine"],
        "credential_fixture": facts["credential"],
        "record_binding": facts["record_binding"],
        "toolchain_digest": facts.get("toolchain_digest"),
        "deployment_limitation": {
            "what": "tools/single_worker.py:344 calls "
                    "credentials.resolved_delivery unconditionally and "
                    "credentials._authorized_slots refuses an empty list",
            "consequence": "a baton.v12.single-worker-deployment/4 must "
                           "authorize at least one credential slot even for a "
                           "worker that calls no provider",
            "in_tension_with": "credentials.py's own comment that an "
                               "assignment authorizing no credential gets no "
                               "delivery, which the adapter expresses as "
                               "credential_delivery=None",
            "recorded_as": "a deployment limitation; the synthetic fixture "
                           "above is a labelled stopgap and changes no product "
                           "credential semantics"}}
    if write:
        (HERE / "composition.json").write_text(
            json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"complete": found["complete"],
                      "validator_calls": run_state.steps,
                      "refused": run_state.refused}, indent=1))
    if not found["complete"]:
        print("INCOMPLETE: a required validator did not accept; this "
              "composition is NOT validated readiness", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
