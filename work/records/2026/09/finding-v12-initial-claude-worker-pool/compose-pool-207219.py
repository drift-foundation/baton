"""Compose the Claude worker pool for the selected v12 development instance.

W202663 step 7, under owner ruling 206702. ADAPTED from W197661's
`instance-201492/compose_lifecycle.py`, which is preserved unchanged beside its
own outputs; the structure that is reused is its discipline -- every identity
MEASURED rather than restated, fail-closed the moment a required validator
refuses, and composing only, never bootstrapping, starting or submitting.

WHAT IS DIFFERENT HERE, AND IT IS THE WHOLE POINT. W197661 put all three roles
on ONE image because it had to: a Job named one input identity and a worker's
manifest carried its own image, so a heterogeneous pool could not be expressed.
Owner ruling 206702 called that a gap, and W202663 corrected it. This
composition is the first to USE that correction -- three workers, each with its
own sealed runtime manifest naming its own image:

    implementation  baton.claude-coder      the provider image
    review          baton.claude-reviewer   the provider image
    integration     baton.merge             the INTEGRATION image

and all three projecting to the ONE Job input identity the submission names.
The provider and integration images are two different artefacts with two
different entrypoints -- `dogfood_entry.py` and `integration_entry.py` -- which
is exactly the pool that could not be configured before.

IT COMPOSES ONLY. It writes this package's documents and the bootstrap input;
it bootstraps nothing, starts nothing, submits nothing and runs no provider or
engine beyond one read-only `image inspect`. Those are operator steps, and the
commands for them are written into the dossier rather than performed here.

NO LIVE MODEL IS REACHED BY COMPOSING THIS, and composing it is not authority
to run one. The provider image contains a real provider; a Job that reaches it
makes a model turn, which owner ruling 206702 excludes from this Work. What
this package produces is a CONFIGURED pool and the exact commands to launch it,
which is what the owner asked for -- and the deterministic report-and-hold
verification is a separate step that must not use these two images.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("/home/sl/src/baton")
sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))

DEST = Path("/home/sl/baton-v12-instance-2026-09-18T10-38-52Z")
UUID = "a92e1d717fcc40fe9972df8b2497c055"
WORK = "a92e1d71-W1"
JOB = "w202663-first-development-job"
TARGET_ID = "w202663-target"
CREATED = "2026-09-18T23:30:00.000Z"
ROLES = ("implementation", "review", "integration")

# THE OWNER'S OWN WORDS, resolved to identities. "Configure distinct Claude
# coder and reviewer identities": two participants, never one, so
# `stage_execution._independent` is satisfied by construction rather than by
# convention. The integrator is `baton.merge`, which `AGENTS.md` names as the
# proposal-integration identity and which the instance's own
# `integration_profile` already carries.
ACTORS = {"implementation": "baton.claude-coder",
          "review": "baton.claude-reviewer",
          "integration": "baton.merge"}

# THE TWO ARTEFACTS W202663 BUILT, by digest. Not tags: a tag is a name
# somebody can move, and what a manager pins is a content digest.
#
# CLAIM225590 MOVES THE PROVIDER DIGEST, and the prior one
# (sha256:9ff3322f58f08275bfc4bb2cd511fb7a6b156e991449ee36f365d05e2133529d,
# tag e486652c) stays here as history: review225576's candidate-root
# demonstration found the frozen verification suite dies at COLLECTION
# inside that artefact -- `ModuleNotFoundError: jsonschema`, the product's
# one declared dependency, absent from the image that runs the product's
# tests. The candidate below is the same recipe plus `python3-jsonschema`
# (tag claim225590), in which the exact frozen argv ran 126 tests OK from a
# repository-root candidate at the accepted base, network-disabled. Per the
# recipe's own selection doctrine it is a CANDIDATE until the owner's
# launch authorization selects it.
# CLAIM227097 MOVES THE PROVIDER DIGEST AGAIN, and the prior candidate
# (sha256:448c98c937849e5c6dcdd03cc33936084f698d0175520b2a5cbe9a9af92e8559,
# tag claim225590) stays here as history: Job2's live episode measured its
# two defects -- PID 1 never reaped (the killed background suite's ~498
# zombies exhausted the 512-PID cgroup and broke the authoritative capture),
# and the fixed /run/baton/logs room was open to ANY importer, so nested
# adapter code declared failures into the real sidecars. The candidate below
# is the same recipe with `dogfood_entry.py` as a reaping PID-1 supervisor
# and the room gated on the entry-set BATON_ATTEMPT_LOG_ROOM
# (RECOVERY-IMAGE-227097.json: in-image byte identity, PID-1 reap proof and
# room-gating proof). Per the recipe's own selection doctrine it is a
# CANDIDATE until the owner's launch authorization selects it.
# CLAIM227424 MOVES IT ONCE MORE (owner 2026-09-21T05:54:40Z): the b44f5522
# candidate's marker still pointed at the legacy room spelling; this build's
# entry names the MOVED authoritative room `/run/baton/attempt-logs`, and the
# legacy `/run/baton/logs` is the composed disposable decoy old-byte nested
# writers land in (in-image proof in RECOVERY-EVIDENCE-227424.json).
#
# CLAIM229926 MOVES IT FOR D10 (owner 2026-09-21T12:41:22Z): the d1e2869e
# candidate's adapter walked the WHOLE line candidate as provider material,
# and job-4 measured what that refuses -- the real repository, 19,553
# entries / 652 MB / 102 committed links against a 2,000-entry / 64 MiB
# payload walk. The candidate below carries the delta inventory: the
# committed baseline (proven at the pinned entry head) passes as baseline,
# the provider answers for its CHANGES under every unchanged protection,
# and the corrected adapter answers the retained job-4 checkout's delta --
# exactly the two candidate files, at the reviewer's own recorded hashes --
# in under a second (D10-EVIDENCE-229926.json).
# CLAIM230107 NARROWS IT (owner 2026-09-21T12:47:17Z, review230027 R1):
# the d447cf38 candidate still inventoried and hashed the whole baseline
# and vetoed unrelated ignored additions. The candidate below collects the
# proposal from Git's own status listing -- no baseline walk at all, an
# unrelated ignored or special file is disclosed instead of refused, links
# among the CHANGES and delivered/verified set-and-byte equality remain the
# only vetoes -- and answers the retained job-4 checkout's delta in 0.066 s
# (D10-EVIDENCE-230107.json).
PROVIDER_IMAGE = ("sha256:5c2eb55d64a775cf939425941960289c3c98a49689f8"
                  "41a335bdf03f69afd5b6")
INTEGRATION_IMAGE = ("sha256:b9b75acc300170d99649d0497f9f93876ab5d8d73a91"
                     "57c9861c5763f17c9561")
IMAGES = {"implementation": PROVIDER_IMAGE,
          "review": PROVIDER_IMAGE,
          "integration": INTEGRATION_IMAGE}

# WHICH BUILD CONTEXT EACH IMAGE WAS MADE FROM, measured per image, because the
# two recipes copy different file sets and a toolchain digest that described
# the union would describe neither artefact.
RECIPES = {"implementation": "worker/Dockerfile.claude",
           "review": "worker/Dockerfile.claude",
           "integration": "worker/Dockerfile.integration"}

# THE CREDENTIAL SLOT, and what is behind it. `tools/integration_worker`
# requires the literal "claude" slot, and `tools/single_worker` refuses an
# empty slot list, so a deployment cannot express "this worker reads no
# bearer". W197661 recorded that as a deployment limitation and it is unchanged
# here.
#
# WHAT THIS COMPOSITION PUTS BEHIND THE SLOT IS THE OPERATOR'S OWN SOURCE,
# NAMED AND NOT READ. This package neither opens, copies, hashes nor stages any
# credential; it writes a registry LOCATOR into the deployment and the operator
# supplies what is behind it. Composing this grants no access to anything and
# claims no authentication coverage.
SLOT = "claude"
CREDENTIAL_SOURCES = str(Path.home() / ".baton/credential-sources.json")
CREDENTIAL_REFERENCE = {"provider": "operator-file",
                        "reference": "w202663-development"}

# WHAT ONE BOOTSTRAP RUN DOES TO THIS AUTHORITY'S APPROVAL POLICY GENERATION,
# MEASURED HERE rather than assumed. A first capacity bootstrap over a fresh
# install also creates the Work, its routes, its grants and the canonical
# target, so it moves further than a repeat does. Observations of THIS
# instance, not a contract: 1 -> 9 on the first (claim207219).
FIRST_BOOTSTRAP_BUMP = 8
REPEAT_BOOTSTRAP_BUMP = 7

_REVISION = re.compile(r"\A[0-9a-f]{40}\Z")


class Unmeasured(Exception):
    """A fact this composition refuses to invent."""


def digest(value):
    from baton_v12.contracts import canonical

    return canonical.digest(value)


def sha(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


# -- measured provenance ------------------------------------------------------


ACCEPTED_BASE = None


def select_base(reference):
    """Compose the Claude Job against an EXPLICIT accepted reference.

    Review222023 [R2], under owner 2026-09-20T14:57:48Z: the real Job's
    base is the human-accepted reference, an OPAQUE input carried verbatim
    into the task, binding and manifests -- never derived from the
    dedicated target. Without `--base`, `declared_base` keeps reading the
    target's refs exactly as the recorded historical runs did.
    """
    global ACCEPTED_BASE
    if not _REVISION.match(reference or ""):
        raise Unmeasured("--base carries a 40-lowercase-hex reference")
    ACCEPTED_BASE = reference
    return {"accepted_base": ACCEPTED_BASE}


def declared_base(target=None):
    """The instance target's own current main revision, read from its refs.

    A file read and never a version-control mutation, exactly as W197661's
    composer does it: `line_declared_base` is the revision every checkpoint on
    this line is declared against, and a constant would describe some other
    repository.

    THE DEFAULT RESOLVES AT CALL TIME. FINDING.md D5 (claim208777): binding
    `DEST / "repo/target.git"` in the signature froze the module-load DEST,
    which on the verification composer poisoned a fresh Authority's canonical
    target. This composer still carries only the superseded instance's
    constants and MUST gain instance selection before it composes for any
    other destination; the default-argument port is done now so the defect
    class cannot survive into that work.
    """
    if target is None:
        target = DEST / "repo/target.git"
    loose = Path(target) / "refs/heads/main"
    if loose.is_file():
        found = loose.read_text().strip()
    else:
        packed = Path(target) / "packed-refs"
        if not packed.is_file():
            raise Unmeasured(f"{target} has neither refs/heads/main nor "
                             f"packed-refs")
        found = ""
        for line in packed.read_text().splitlines():
            if line.endswith(" refs/heads/main"):
                found = line.split(" ", 1)[0].strip()
                break
    if not _REVISION.match(found):
        raise Unmeasured(f"the target's main ref reads {found!r}, which is not "
                         f"one revision")
    return found


def principals(*, opener=None):
    """Who each participant IS, asked of the instance's own Authority."""
    from tools import bootstrap

    places = bootstrap.layout(str(DEST))
    document = {
        "authority_uuid": UUID,
        "receipt_participants": dict(RECEIPTS),
        "integration_profile": {
            "integrator_participant": ACTORS["integration"]},
        # THE RETAINED WORKERS' PARTICIPANTS TRAVEL TOO (ported claim226458;
        # the verification composer measured the identical narrow-document
        # defect as `KeyError: 'baton.fixture-coder'`): a composer that
        # validates a narrower document than it writes is not validating
        # what it writes.
        "workers": [{"participant": one} for one in sorted(
            set(ACTORS.values())
            | {one["participant"] for one in prepared_workers()})]}
    return bootstrap.principals_for(places, document, opener=opener)


RECEIPTS = {"verification": "baton.codex",
            "review": "baton.codex",
            "approval": "baton.slaw"}


def policy_pin(*, opener=None):
    """The generation this composition predicts the bootstrap will leave.

    ASKED, then CHECKED afterwards by `check_policy_pin`. W197661 measured that
    `bootstrap` bumps the Authority's approval policy generation on every run
    while the pin travels IN to that same run, so a composition that restated a
    literal would emit a deployment which cannot satisfy its own pin and would
    defer at its first integration with the reason only in a tick report.

    THE NUMBERS ARE OBSERVATIONS OF THAT TREE, NOT A CONTRACT. W197661 measured
    1 -> 9 for a first capacity bootstrap over a fresh install and seven per
    repeat afterwards. They are used only to PROPOSE a pin.
    """
    from baton_v12.authority import Authority

    open_authority = opener or Authority.open_readonly
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
    # THE BUMPS ARE MEASURED ON THIS INSTANCE, not copied from W197661's tree.
    #
    # claim207219 ran the first capacity bootstrap here and the Authority moved
    # 1 -> 9: a bump of EIGHT, where W197661 observed 8 on its own first run and
    # 7 per repeat. My first prediction used 8 and `check_policy_pin` reported
    # configured 8 against generation 9 -- the prediction was of the generation
    # BEFORE the bootstrap plus the bump, and I had added the bump to a reading
    # taken when the generation was 1 while the pin has to equal what the
    # bootstrap LEAVES. The reading and the bump are both right; only which
    # bootstrap they describe was wrong.
    #
    # STILL A PREDICTION, AND STILL CHECKED. `check_policy_pin` runs after the
    # bootstrap against the Authority itself and is what decides whether this
    # was right; a number that agreed with itself would prove nothing.
    # PORTED FROM compose-verification-208217.py's banked measurements after
    # the gate refused THIS composer's first PR prediction (claim225533,
    # configured 9 against generation 8): PR MODE COSTS ONE LESS PER
    # PREPARATION (the absent integration stage certifies one transition
    # fewer, measured 1 -> 8 on two fresh PR instances now), and FIRST means
    # NO DEPLOYMENT RECORD, not no job store -- the job store is created by
    # the first START, so a root composed before any start would read every
    # compose as "first".
    pr = "integration" not in ROLES
    # FIRST means NO CONFIGURED CAPACITY, not no deployment file (claim225590,
    # gate-caught on the fresh 01-28-41Z instance: THIS installer writes an
    # EMPTY deployment.json at install, so a file-existence test read a fresh
    # root as prepared and predicted the repeat bump -- configured 7 against
    # the first apply's measured 1 -> 8).
    place = DEST / "deployment.json"
    prepared = (place.is_file()
                and bool(json.loads(place.read_text()).get("workers")))
    if not prepared:
        return held + FIRST_BOOTSTRAP_BUMP - (1 if pr else 0)
    # PREPARED APPLIES COST PER JOB (ported claim226458 with the two-Job
    # support; the verification composer measured PR repeats at exactly six
    # per job, claim222268, twice). The gate still checks every prediction.
    jobs = len(_all_jobs()) or 1
    return held + (REPEAT_BOOTSTRAP_BUMP - (1 if pr else 0)) * jobs


def check_policy_pin(*, opener=None, pin=None):
    """The post-bootstrap equality, as an executable gate rather than a note."""
    from baton_v12.authority import Authority

    if pin is None:
        configured = json.loads((DEST / "deployment.json").read_text())
        pin = configured.get("policy_generation")
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
            "equal": pin == held}


def image_present(image, *, run=None):
    """Whether the engine really holds this image. Starts no container."""
    runner = run or (lambda argv: subprocess.run(
        argv, capture_output=True, text=True, timeout=60))
    try:
        found = runner(["docker", "image", "inspect", "--format", "{{.Id}}",
                        image])
    except Exception as failure:                             # noqa: BLE001
        return {"asked": True, "held": None,
                "why": type(failure).__name__}
    held = (found.stdout or "").strip()
    return {"asked": True, "held": held == image, "reported_id": held or None}


def toolchain_of(recipe):
    """What ONE recipe was built from: its own bytes and every path it copies.

    Per recipe rather than per tree. `copied-inputs-207111.py` already
    establishes which paths each recipe carries; this digests that set plus the
    recipe itself, so the provider and integration images carry different
    toolchain digests because they ARE built from different inputs.
    """
    sys.path.insert(0, str(HERE))
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "copied_inputs", HERE / "copied-inputs-207111.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    place = REPO / "v12" / recipe
    entries = module.checkout_side(place)
    return digest({"recipe": recipe, "recipe_sha256": sha(place),
                   "copied": {where: one["sha256"]
                              for where, one in sorted(entries.items())}})


def adapter_identity():
    """The adapter's measured bytes, as a durable identity."""
    place = REPO / "v12/python/src/baton_v12/worker_manager/oci.py"
    return {"adapter_name": "docker-single-worker", "sha256": sha(place),
            "path": str(place.relative_to(REPO)),
            "what_it_does_not_prove": "a file digest identifies the adapter "
                                      "this deployment names; it is not "
                                      "evidence that the adapter ran"}


def record_binding():
    """This Work's own canonical dossier, digested where it actually lives."""
    finding = HERE / "FINDING.md"
    plan = HERE / "PLAN.md"
    for place in (finding, plan):
        if not place.is_file():
            raise Unmeasured(f"{place} is not here; a record binding names a "
                             f"record that exists")
    return {"root": "baton",
            "path": "work/records/2026/09/finding-v12-initial-claude-worker-pool",
            "finding_digest": sha(finding), "plan_digest": sha(plan)}


# -- the documents ------------------------------------------------------------


def policy_documents(facts):
    """This deployment's policy layer, over THIS destination's paths."""
    return {
        "policy": {"work": "W202663",
                   "ruling": "owner 206702: workers select their own immutable "
                             "images; provider image, credential profile, role "
                             "and participant remain separate",
                   "base": facts["declared_base"],
                   "submission": [JOB],
                   "automatic_retry": False,
                   "review_before_execution": True},
        "resource_policy": {"wall_seconds": 3600,
                            "implementation_attempt_seconds": 900,
                            "review_or_judge_attempt_seconds": 600,
                            "integration_seconds": 300,
                            "runtime_cpus": 2,
                            "runtime_memory_bytes": 4294967296,
                            "runtime_pids": 512,
                            "workspace_declared_capacity_bytes": 2147483648,
                            "workspace_capacity_is_quota": False,
                            "deadline_action": "stop; retain evidence; "
                                               "no retry"},
        "network_policy": {"engine_network": "bridge",
                           "purpose": "the provider image reaches its own "
                                      "service; the integration image inherits "
                                      "that posture and reaches the read-only "
                                      "mounted line"},
        "mount_policy": {"source": "read-only nominated source and a "
                                   "manager-held private development line",
                         "mutable_storage": str(DEST / "workers"),
                         "workspace_group": facts["workspace_group"],
                         "target": str(DEST / "repo/target.git"),
                         "target_reference": "refs/heads/main"},
        "tool_policy": {"provider_arguments": [],
                        "model_selection": "the provider image's own default; "
                                           "NO model is selected here and none "
                                           "is reached by composing this",
                        "verification": [],
                        "final_verification": []},
        "credential_policy": {"registry": CREDENTIAL_SOURCES,
                              "slots": {SLOT: dict(CREDENTIAL_REFERENCE)},
                              "payload_in_configuration": False,
                              "read_by_this_composition": False},
        "retention_policy": {"disposition": "retain", "root": str(DEST),
                             "automatic_deletion": False}}


def task_document(facts):
    """The first development task, in the contract the worker image reads.

    BOUNDED at claim220385 (review220364 [2]): the historical instruction
    asked for the whole user-managed pool-management outcome, which is not a
    reviewable single-Job execution package. This is the two-path cut
    REAL-JOB-PROPOSAL-220329.md proposed and the reviewer required the task
    bytes to actually request: ONE `add-worker` verb, TWO allowed paths, the
    verb's own tests plus the bootstrap family as the gate. The original
    broader objective stays recorded in that proposal as follow-on work.
    """
    return {
        "schema": "baton.dogfood-task/2",
        "task_id": JOB,
        "instructions":
            "Add exactly one new tool: a `add-worker` verb in a NEW file "
            "v12/python/tools/pool.py that admits ONE worker document into "
            "an existing instance's deployment configuration. It must "
            "validate exactly what tools/bootstrap.py validates for a worker "
            "(the worker's image_digest equal to its own input manifest's "
            "worker_image_digest; participant and principal resolution; "
            "profile shape), rewrite the instance's deployment.json with the "
            "worker added, and print the pool generation the scheduler will "
            "mint at the next activation. It must NOT prepare any Job, "
            "submit anything, create or touch any Work, or remove or modify "
            "any existing worker. Write its tests in a NEW file "
            "v12/python/tests/tools/test_pool.py covering: a valid worker "
            "admitted; an image digest disagreeing with its manifest "
            "refused; an existing worker id refused; nothing else in the "
            "configuration changed byte-for-byte. Change ONLY these two "
            "files. Do not change tools/bootstrap.py or any existing rule "
            "it enforces. Run tests in the FOREGROUND only, and only the "
            "task's own selected modules: do not launch background test "
            "runs or repository-wide test sweeps in this container -- its "
            "process budget is bounded and a killed background run "
            "previously destroyed the attempt's own verification evidence.",
        "source_root": "source",
        "source_profile": "git-line",
        "declared_base": facts["declared_base"],
        # REVIEW225576 [R1]: the argv runs WITH THE CANDIDATE ROOT AS ITS
        # WORKING DIRECTORY (claude_agent `_verify`, cwd=candidate) and the
        # candidate is the whole repository -- `tests.tools.*` does not
        # exist there; the selected modules live under `v12/python`. The
        # argv contract is a shell-less vector, so the interpreter itself
        # enters the subtree and sets the import path, exactly as the
        # repository's own test invocations do (`cd v12/python` +
        # `PYTHONPATH=src:.`). `unittest.main` exits nonzero on failure, so
        # the gate's verdict still travels in the exit status.
        #
        # REVIEW226905 [3], SUPERSEDED REMEDY (owner 2026-09-21T05:53:07Z,
        # "I approve spare mount", after review227324 R2): THE FIXTURE ROOT
        # IS A REAL DELIVERY NOW, AND THE GATE IS THE FULL REQUIRED SET.
        #
        # Claim227097 measured the ground truth: eleven ValidFixture-derived
        # test_bootstrap classes (75 of 125 tests) demand, through
        # `_disk_root_outside_the_checkout` (which refuses rather than
        # skips), a root at once DISK-BACKED, WRITABLE and OUTSIDE the
        # checkout -- and the container then offered no such place by mount
        # contract. Claim227097's remedy excluded those classes; review227324
        # correctly rejected that as changed acceptance scope, and the owner
        # selected the direct correction instead: the manager now delivers a
        # per-attempt disk-backed scratch directory at the constant
        # `/scratch` (oci.SCRATCH_TARGET; allocated in the attempt's own
        # assignment home by single_worker._attempt_scratch). The argv
        # selects it, the FULL test_pool + test_bootstrap families run --
        # no stub, no exclusions -- and the retained real pool tests
        # (AdmissionCase -> ValidFixture) are exactly what the in-container
        # demonstration runs.
        #
        # PRECEDENCE, unchanged from the operator rule tools/environment.py
        # states: an explicitly exported BATON_V12_STACK_TEST_ROOT is never
        # overridden. Otherwise /scratch when it is a writable directory
        # (the delivered mount), and a real-path mkdtemp on host reruns
        # where no /scratch exists -- realpath because the verifier's own
        # TMPDIR is a held /proc/self/fd object valid only in one process,
        # and the stack cases hand the root to children.
        "verification": [
            "python3", "-c",
            "import os, sys, tempfile, unittest\n"
            "# W202663 owner 2026-09-21T05:53:07Z: the delivered per-attempt\n"
            "# disk-backed scratch is the fixture root; an exported selection\n"
            "# wins; a host rerun without /scratch falls back to a real\n"
            "# temporary directory.\n"
            "if not os.environ.get('BATON_V12_STACK_TEST_ROOT'):\n"
            "    place = '/scratch'\n"
            "    if not (os.path.isdir(place) and os.access(place, os.W_OK)):\n"
            "        place = os.path.realpath(\n"
            "            tempfile.mkdtemp(prefix='stack-test-root-'))\n"
            "    os.environ['BATON_V12_STACK_TEST_ROOT'] = place\n"
            "os.chdir('v12/python')\n"
            "sys.path[:0] = [os.path.abspath('src'), os.path.abspath('.')]\n"
            "unittest.main(module=None, argv=['unittest', "
            "'tests.tools.test_pool', 'tests.tools.test_bootstrap'])\n"]}


def role_instruction_documents():
    """What each stage is told. Different text per role, deliberately.

    The ROLE INSTRUCTIONS ARE PER-WORKER under owner ruling 206702 and are
    projected out of the Job input identity for exactly that reason: an
    implementer and a reviewer are not told the same thing.
    """
    return {
        "implementation": "You are the Claude coder. Produce the candidate the "
                          "frozen task describes and the tests that go with "
                          "it. Change nothing outside the scope it names.",
        "review": "You are the Claude reviewer, and you did not write this "
                  "candidate. Read the frozen checkpoint and accept it only if "
                  "it delivers the task's outcome without weakening an "
                  "existing rule; otherwise request changes and say which rule "
                  "was broken.",
        "integration": "Import exactly the accepted candidate onto the "
                       "canonical target. Refuse anything outside the "
                       "candidate rather than repairing it."}


def manifest_for(role, facts, *, seal):
    """ONE sealed input manifest per WORKER, sharing one Job input identity.

    THIS IS THE FIRST COMPOSITION THAT CAN DO THIS. W197661 needed one manifest
    for all three roles because `_matches` compared a Job's single input digest
    against a worker's WHOLE manifest digest; W202663 corrected that to the
    Job-scoped projection, so each worker now carries its own manifest naming
    its own image, and all three project to one value.

    WHAT DIFFERS PER ROLE is exactly the worker-runtime axis the correction
    projects out -- image, toolchain, role instructions, manifest id and
    creation instant. Everything the JOB owns is identical by construction,
    because it is composed from the same `facts`.
    """
    from tools import dogfood_operator
    from baton_v12.worker_manager import source_boundary

    empty = {"entries": [], "entry_count": 0, "total_bytes": 0,
             "tree_digest": facts["empty_tree_digest"]}
    given = dogfood_operator.input_manifest(
        work_ref={"authority_uuid": UUID, "work_id": WORK}, staged=empty,
        created_at=CREATED, manifest_id=f"input-{JOB}-{role}",
        assignment_contract="v12-assignment-1",
        human_contract={"artifact_id": JOB,
                        "media_type": "application/json",
                        "bytes": facts["task_bytes"],
                        "content_digest": facts["task_digest"],
                        "locator": f"artifact://contracts/{JOB}"},
        record_binding=facts["record_binding"],
        role_instructions_digest=facts["role_instructions_digest"][role],
        runtime_profile_digest=facts["profile_digest"],
        toolchain_digest=facts["toolchain_digest"][role],
        worker_image_digest=IMAGES[role], policies=facts["policy_digests"])
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


def deployment_for(role, facts):
    """One role's complete single-worker deployment, on its OWN image."""
    return {
        "schema": "baton.v12.single-worker-deployment/4",
        "authority_store": str(DEST / "db/authority.sqlite3"),
        "authority_uuid": UUID,
        "participant": ACTORS[role],
        "principal": facts["principals"][ACTORS[role]],
        "profile_name": f"claude-{JOB}",
        "profile_digest": facts["profile_digest"],
        "policy_digest": facts["policy_digests"]["policy_digest"],
        "adapter_name": facts["adapter"]["adapter_name"],
        "adapter_digest": facts["adapter"]["sha256"],
        "engine": "docker",
        "image_digest": IMAGES[role],
        "network": "bridge",
        # ONE STORE, MANAGER-SCOPED (claim226109, measured at the owner's
        # first start and again at this claim's own: `configure_workspace_
        # storage` refuses a second store -- "a changed store is a fresh
        # store rather than a reconfiguration" -- because every attempt
        # already allocated under the first would become unfindable. What is
        # per-worker is the private launch and credential home below, which
        # is where `stage_execution._independent` actually looks for
        # separation; the verification composer and W197661's accepted
        # composition share one store for the same reason.
        "workspace_storage": str(DEST / "workers/implementation/storage"),
        "workspace_group": facts["workspace_group"],
        "launch_home": str(DEST / "workers" / role / "launch"),
        "credential_home": str(DEST / "workers" / role / "credentials"),
        "credential_sources": CREDENTIAL_SOURCES,
        "credential_slots": [SLOT],
        "credential_profile": {SLOT: dict(CREDENTIAL_REFERENCE)},
        "nominated_source": str(DEST / "repo/workspace"),
        "workspace_capacity": {"max_bytes": 2147483648},
        "input_manifest": facts["manifests"][role],
        "task_document": str(DEST / "jobs" / JOB / "task.json"),
        "launch_contract": "v12-assignment-1",
        "launch_role": role,
        "review_route": {"implementation": "rview", "review": "integration",
                         "integration": "integration"}[role],
        "retention_policy_digest":
            facts["policy_digests"]["retention_policy_digest"],
        "retention_disposition": "retain"}


def submission(facts):
    """The Job, naming the ONE Job input identity all three workers project to."""
    return {
        "schema": "baton.v12.job-submission/2",
        "submission_id": f"{JOB}-submission",
        "jobs": [{
            "job_id": JOB,
            "input_digest": facts["job_input_identity"],
            "policy_digest": facts["policy_digests"]["policy_digest"],
            "test_scope": [], "terminal_policy": "report-and-hold",
            "stages": [{"kind": kind, "work_id": WORK,
                        "profile_name": f"claude-{JOB}",
                        "profile_digest": facts["profile_digest"],
                        "depends_on": (
                            [] if kind == "implementation" else
                            [{"job_id": JOB, "kind": "implementation"}]
                            if kind == "review" else
                            [{"job_id": JOB, "kind": "review"}])}
                       for kind in ROLES]}]}


def bootstrap_inputs(facts):
    """What the installed `bootstrap` command is handed to supply capacity."""
    workers = prepared_workers() + [
        {"worker_id": f"{JOB}-{role}", "role": role,
         "participant": ACTORS[role],
         "deployment": deployment_for(role, facts)}
        for role in ROLES]
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
        "pool_generation": _pool_generation_prediction(DEST, workers),
        "policy_generation": facts["policy_generation"],
        "receipt_participants": dict(RECEIPTS),
        "integration_target": str(DEST / "repo/target.git"),
        "integration_target_reference": "refs/heads/main",
        "integration_workspace": str(DEST / "repo/workspace"),
        "integration_instructions": str(DEST / "integration-instructions.txt"),
        "workers": workers,
        "jobs": prepared_jobs() + [
            {"job_id": JOB, "work_id": WORK,
             "line_declared_base": facts["declared_base"],
             "canonical_target_id": TARGET_ID,
             "source_worker_id": f"{JOB}-implementation"}]}


# -- what is already prepared here, preserved verbatim (ported claim226458
#    from the verification composer's reviewed two-Job support) --------------
#
# A REPEATED BOOTSTRAP PRESERVES WHAT IS THERE: "a Job that stops being named
# is not thereby unconfigured", so a composition over a prepared root must
# name the retained Jobs and carry their workers AS RECORDED -- recomposing
# them would re-derive digests from today's facts and silently rewrite the
# deployment the failed attempt actually ran under, which is exactly the
# rewrite the preserved-evidence rule forbids.


def _prepared():
    place = DEST / "deployment.json"
    if not place.is_file():
        return None
    return json.loads(place.read_text())


def prepared_workers():
    """Every retained worker except the selected Job's own, verbatim."""
    held = _prepared()
    if held is None:
        return []
    return [{"worker_id": one["worker_id"], "role": one["role"],
             "participant": one["deployment"]["participant"],
             "deployment": one["deployment"]}
            for one in held.get("workers", [])
            if not one["worker_id"].startswith(JOB + "-")]


def prepared_jobs():
    """Every Job this destination already holds, in the input's own shape."""
    held = _prepared()
    if held is None:
        return []
    return [{"job_id": one["job_id"], "work_id": one["job_work_id"],
             "line_declared_base": one["line_declared_base"],
             "canonical_target_id": one["canonical_target_id"],
             "source_worker_id": one["source_worker_id"]}
            for one in (held.get("job_bindings") or [])
            if one["job_id"] != JOB]


def _all_jobs():
    """Every Job the next bootstrap will prepare: the held ones and this one."""
    return prepared_jobs() + [{"job_id": JOB, "work_id": WORK}]


def _pool_generation_prediction(dest, workers):
    """The generation the NEXT activation will answer -- read, not restated.

    The scheduler's own rule (ported with the verification composer's
    claim219702/220080 correction): an absent pool mints 1, an identical
    membership re-answers the current generation, a changed one mints the
    next. The whole composed membership is compared, not one worker.

    THROUGH THE PUBLIC READERS ONLY (review226502 [R2]): the durable pool is
    asked via `JobStore.open_readonly` and the scheduler's own
    `active_generation`/`pool_workers`, never raw SQL -- the raw form this
    replaced was a policy violation even read-only, because a helper that
    reaches past the store's owned crossings is a second schema consumer the
    product never promised to keep working.
    """
    place = dest / "db/jobs.sqlite3"
    if not place.is_file():
        return 1
    import datetime

    from baton_v12.job_manager.store import JobStore
    from baton_v12.job_manager import scheduler

    def _clock():
        return datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    store = JobStore.open_readonly(
        str(place), authority_uuid=UUID,
        incarnation="compose-pool-prediction", clock=_clock)
    try:
        active = scheduler.active_generation(store)
        if active is None:
            return 1
        current = active["generation"]
        rows = {(one["worker_id"], one["lane"], one["participant"])
                for one in scheduler.pool_workers(store, current)}
    finally:
        close = getattr(store, "close", None) or getattr(store, "dispose",
                                                         None)
        if close is not None:
            close()
    composed = {(one["worker_id"],
                 "implementation" if one["role"] == "integration"
                 else one["role"],
                 one["participant"]) for one in workers}
    return current if composed == rows else current + 1


# -- the validators, and the fail-closed run ----------------------------------

REQUIRED = ("check_manifest_structure", "bootstrap.held",
            "bootstrap.configuration", "stage_execution.held_configuration",
            "bootstrap.validated", "job_manager.documents.owned_submission")

AFTER_WRITING = "stage_execution.held_configuration (over the written files)"


def production_validators():
    """The canonical owner of each question, never a second opinion here."""
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
        self.required = list(REQUIRED)

    def step(self, what, run):
        try:
            answer = run()
        except Exception as failure:                         # noqa: BLE001
            self.steps.append({"validator": what, "result": "REFUSED",
                               "refusal": f"{type(failure).__name__}: "
                                          f"{str(failure)[:800]}"})
            self.refused.append(what)
            return None
        self.steps.append({"validator": what, "result": "accepted"})
        return answer

    @property
    def complete(self):
        ran = {one["validator"] for one in self.steps
               if one["result"] == "accepted"}
        return not self.refused and all(one in ran for one in self.required)


def measured(*, run=None, opener=None):
    """Every fact this composition refuses to invent, asked of its owner."""
    from baton_v12.worker_manager import workspaces
    from tools import single_worker

    facts = {"declared_base": (ACCEPTED_BASE if ACCEPTED_BASE is not None
                               else declared_base()),
             "record_binding": record_binding(),
             "adapter": adapter_identity(),
             "empty_tree_digest": single_worker.EMPTY_TREE_DIGEST,
             "workspace_group": workspaces.__dict__.get("DEFAULT_GROUP")
             or __import__("os").getgid()}
    facts["principals"] = principals(opener=opener)
    facts["policy_generation"] = policy_pin(opener=opener)
    facts["image_in_engine"] = {
        role: image_present(IMAGES[role], run=run) for role in ROLES}
    facts["toolchain_digest"] = {role: toolchain_of(RECIPES[role])
                                 for role in ROLES}

    instructions = role_instruction_documents()
    facts["role_instructions"] = instructions
    facts["role_instructions_digest"] = {role: digest(instructions[role])
                                         for role in ROLES}

    policies = policy_documents(facts)
    facts["policies"] = policies
    facts["policy_digests"] = {
        f"{name}_digest": digest(body) for name, body in policies.items()}
    facts["profile_digest"] = digest({
        "profile": f"claude-{JOB}", "images": dict(IMAGES),
        "adapter": facts["adapter"]["sha256"]})

    task = task_document(facts)
    facts["task"] = task
    payload = json.dumps(task, sort_keys=True).encode("utf-8")
    facts["task_bytes"] = len(payload)
    facts["task_digest"] = "sha256:" + hashlib.sha256(payload).hexdigest()
    facts["task_payload"] = payload

    text = ("Import exactly the accepted candidate onto the canonical target. "
            "Refuse anything outside it.\n")
    facts["integration_instructions"] = text
    facts["integration_instructions_digest"] = (
        "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest())
    return facts


def compose(run, *, facts):
    """Every document, with each validator called as it becomes answerable."""
    from baton_v12.contracts import job_input_identity

    seal = run.validators["check_manifest_structure"]
    documents = {}

    facts["manifests"] = {}
    for role in ROLES:
        held = run.step(
            "check_manifest_structure",
            lambda role=role: manifest_for(role, facts, seal=seal))
        if held is None:
            return facts, documents
        facts["manifests"][role] = held

    # THE ONE JOB INPUT IDENTITY, PROVED RATHER THAN ASSUMED. Three workers on
    # two different images must project to one value; if they do not, this
    # composition is wrong and says so here rather than at a launch.
    identities = {role: job_input_identity(facts["manifests"][role])
                  for role in ROLES}
    if len(set(identities.values())) != 1:
        run.steps.append({"validator": "one Job input identity",
                          "result": "REFUSED", "refusal": repr(identities)})
        run.refused.append("one Job input identity")
        return facts, documents
    facts["job_input_identity"] = identities["implementation"]
    run.steps.append({"validator": "one Job input identity",
                      "result": "accepted"})

    inputs = bootstrap_inputs(facts)
    documents["bootstrap_inputs"] = inputs
    documents["submission"] = submission(facts)

    # THE INPUT DOCUMENT DOES NOT NAME THE AUTHORITY, and `held` refuses one
    # that does: an instance generates its identity once at install and
    # persists it at the destination, so a document naming one would be a
    # second place for a fact this instance already owns. The identity is
    # supplied to `configuration`, which DERIVES it into each worker, exactly
    # as the installed command does.
    held = run.step("bootstrap.held",
                    lambda: run.validators["bootstrap.held"](inputs))
    if held is not None:
        configuration = run.step(
            "bootstrap.configuration",
            lambda: run.validators["bootstrap.configuration"](
                dict(held, authority_uuid=UUID), facts["principals"]))
        if configuration is not None:
            documents["stage_execution"] = configuration
            run.step("stage_execution.held_configuration",
                     lambda: run.validators[
                         "stage_execution.held_configuration"](configuration))
            # `validated` HOLDS THE EMITTED CONFIGURATION, not the input: it
            # exists because an earlier cut of this helper validated what it
            # read and not what it wrote.
            run.step("bootstrap.validated",
                     lambda: run.validators["bootstrap.validated"](
                         configuration))
    run.step("job_manager.documents.owned_submission",
             lambda: run.validators["job_manager.documents.owned_submission"](
                 documents["submission"]))
    return facts, documents


def stage_inputs(facts):
    """The two files the DEPLOYMENT itself names, written at the destination.

    A deployment reads its task document and its integrator instructions from
    its own directory -- a running instance reads nothing out of this checkout
    -- so these are the one thing this package writes outside itself.

    THIS IS NOT A BOOTSTRAP AND TOUCHES NO STORE. It creates
    `jobs/<job>/task.json` and `integration-instructions.txt` under the
    destination the owner selected, whose pool is empty and whose Job bindings
    are none. No database is opened for writing, no Authority is composed, no
    prior instance is reached.

    THE BYTES ARE THE MEASURED ONES. `task_bytes` and `task_digest` were taken
    over exactly this payload before any manifest was sealed, so what the
    human contract declares is what the deployment will actually open --
    W197661 paid two rounds for writing an indented copy over a measured one.
    """
    place = DEST / "jobs" / JOB
    place.mkdir(parents=True, exist_ok=True)
    (place / "task.json").write_bytes(facts["task_payload"])
    (DEST / "integration-instructions.txt").write_text(
        facts["integration_instructions"])
    # THE DEPLOYMENT'S OWN DIRECTORIES, created here because the manager
    # refuses to invent them: `check_workspace_storage` demands an EXISTING
    # directory owned by this uid. The verification composer has carried
    # this block since start-208777.log measured the refusal; THIS composer
    # named the same paths in `deployment_for` without making them, and the
    # owner's first authorized start of the live pool refused at
    # configure_workspace_storage before any submission (owner FINDING,
    # 2026-09-21). Naming a store is a deployment act, so the deployment's
    # composer is where the named directories are made — per selected role:
    # launch home, credential home, and (unlike the verification pool,
    # whose manager scopes ONE workspace store) each role's OWN workspace
    # storage, because that is what `deployment_for` names.
    for role in ROLES:
        for home in ("launch", "credentials"):
            (DEST / "workers" / role / home).mkdir(parents=True,
                                                   exist_ok=True)
    (DEST / "workers/implementation/storage").mkdir(parents=True,
                                                    exist_ok=True)


def select_instance(destination):
    """Point this composer at another installed instance, by path.

    Review220364 [2]: the proposal's launch recipe named `--instance` while
    `__main__` ignored argv and the historical claim207219 constants stayed
    in force -- so the recipe could not select anything. Ported from the
    verification composer's reviewed selection (review208507 [R2]): the
    historical constants remain the record of that run; `--instance`
    overrides them by reading the destination's OWN persisted identity.
    """
    global DEST, UUID, WORK

    place = Path(destination)
    identity = place / "authority-identity.json"
    if not identity.is_file():
        raise Unmeasured(f"{identity} is not here; --instance names an "
                         f"installed destination")
    held = json.loads(identity.read_text())
    DEST = place
    UUID = held["authority_uuid"]
    WORK = UUID[:8] + "-W1"
    return {"instance": str(DEST), "authority_uuid": UUID, "work": WORK}


def select_pr():
    """Compose the owner-selected PR shape: coder and reviewer only.

    OWNER-HANDOFF-PR-JOBS (claim220385): the Job's deliverable is the
    durable reviewed candidate; integration is a human act or a separately
    submitted ordinary Job, so no `baton.merge` worker and no integration
    stage compose here. The reviewed candidate's proposal tree and the
    reviewer's verdict are the handback.
    """
    global ROLES
    ROLES = ("implementation", "review")
    return {"pr": True, "roles": list(ROLES),
            "actors": {role: ACTORS[role] for role in ROLES}}


def select_job(job_id, work_number=None):
    """Compose a FRESH Job -- its participants AND ITS OWN WORK -- by id.

    Ported claim226458 from the verification composer's reviewed
    `select_job` (claim208777 cadence): a Job whose launch durably failed is
    PRESERVED EVIDENCE, its released allocation is not re-reservable and its
    live episode's ending is not in the replaceable set -- so the correction
    is a NEW Job under fresh identities beside it, exactly as review208349
    required for the first wrong task document. One participant per worker
    across the whole pool is the measured rule, so the fresh actors carry
    the job's own numeric suffix. The Work is selected WITH the Job
    (review209459): a fresh authority-qualified Work id, minted by
    `bootstrap._compose` on the implementation route, existing Works left
    alone.
    """
    global JOB, ACTORS, WORK

    suffix = job_id.rsplit("-", 1)[-1]
    if not suffix.isdigit():
        raise Unmeasured(f"--job {job_id!r} does not end in -<number>; the "
                         f"numeric suffix names the fresh participants")
    JOB = job_id
    ACTORS = {"implementation": f"baton.claude-coder-{suffix}",
              "review": f"baton.claude-reviewer-{suffix}",
              "integration": ACTORS["integration"]}
    number = suffix if work_number is None else str(work_number)
    if not number.isdigit() or int(number) < 1:
        raise Unmeasured(f"--work {number!r} is not a positive Work number")
    WORK = UUID[:8] + "-W" + number
    return {"job": JOB, "actors": dict(ACTORS), "work": WORK}


def main(argv=None, *, validators=None, write=True, run=None, opener=None):
    import argparse

    parser = argparse.ArgumentParser(prog="compose-pool-207219")
    parser.add_argument("--instance", default=None,
                        help="compose for this installed destination, "
                             "reading its own persisted identity")
    parser.add_argument("--base", default=None,
                        help="compose against this explicit accepted "
                             "reference (opaque; owner 2026-09-20T14:57:48Z)")
    parser.add_argument("--pr", action="store_true",
                        help="compose the owner-selected PR shape: coder "
                             "and reviewer only, no integration worker or "
                             "stage")
    parser.add_argument("--job", default=None,
                        help="compose a FRESH Job by id (must end in "
                             "-<number>; names the fresh participants and "
                             "the fresh Work) beside the destination's "
                             "preserved Jobs")
    parser.add_argument("--work", type=int, default=None,
                        help="an explicit Work number for --job, overriding "
                             "the job suffix")
    taken = parser.parse_args([] if argv is None else list(argv))
    if taken.instance is not None:
        print(json.dumps(select_instance(taken.instance)))
    if taken.pr:
        print(json.dumps(select_pr()))
    if taken.job is not None:
        print(json.dumps(select_job(taken.job, taken.work)))
    if taken.base is not None:
        print(json.dumps(select_base(taken.base)))
    state = Run(validators or production_validators())
    try:
        facts = measured(run=run, opener=opener)
    except Unmeasured as failure:
        print(json.dumps({"complete": False, "unmeasured": str(failure)},
                         indent=1))
        return 2
    if write:
        stage_inputs(facts)
    facts, documents = compose(state, facts=facts)
    if write and documents:
        (HERE / "pool-task.json").write_bytes(facts["task_payload"])
        (HERE / "pool-integration-instructions.txt").write_text(
            facts["integration_instructions"])
        for name, document in documents.items():
            (HERE / f"pool-{name.replace('_', '-')}.json").write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n")
    found = {
        "schema": "baton.w202663.pool-composition/1",
        "claim": 207219,
        "complete": state.complete,
        "composes_only": "writes documents; bootstraps nothing, starts "
                         "nothing, submits nothing, runs no provider",
        "validator_calls": state.steps,
        "required": list(state.required),
        "refused": state.refused,
        "instance": str(DEST),
        "authority_uuid": UUID,
        "declared_base": facts["declared_base"],
        "actors": dict(ACTORS),
        "images": dict(IMAGES),
        "heterogeneous": len(set(IMAGES.values())) > 1,
        "job_input_identity": facts.get("job_input_identity"),
        "runtime_manifest_digests": {
            role: one["manifest_digest"]
            for role, one in facts.get("manifests", {}).items()},
        "principals": facts["principals"],
        "policy_generation_predicted": facts["policy_generation"],
        "image_in_engine": facts["image_in_engine"],
        "adapter": facts["adapter"],
        "record_binding": facts["record_binding"],
        "no_live_model": "composing this reaches no provider and no model. The "
                         "provider image contains a real provider, so a Job "
                         "that reaches it makes a model turn -- which owner "
                         "206702 excludes from this Work. This package "
                         "configures and does not run.",
        "no_credential_read": "the credential registry and reference are "
                              "LOCATORS written into the deployment. Nothing "
                              "here opened, copied, hashed or staged a bearer.",
    }
    if write:
        (HERE / "POOL-COMPOSITION-207219.json").write_text(
            json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"complete": found["complete"],
                      "refused": state.refused,
                      "job_input_identity": found["job_input_identity"],
                      "runtime_manifest_digests":
                          found["runtime_manifest_digests"]}, indent=1))
    if not found["complete"]:
        print("INCOMPLETE: a required validator did not accept; this "
              "composition is NOT validated readiness", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
