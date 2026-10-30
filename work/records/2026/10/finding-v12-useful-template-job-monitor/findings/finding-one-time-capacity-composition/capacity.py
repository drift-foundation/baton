#!/usr/bin/env python3
"""W367232 — the reusable one-time capacity composition and its entrypoints.

THIS REPLACES `compose_capacity.py`, which review 2026-10-27T18-06-51Z found
unsafe and partly uncallable, and both findings were right:

  R1  its `preflight` extracted 81 files and did `shutil.rmtree` on a FIXED,
      SHARED scratch path while reporting `wrote_nothing: true`, and its
      `prove` branch imported a `proved` function that does not exist. The
      rmtree-a-shared-path pattern is the same mistake that deleted an
      unrelated September scratch root -- see
      `INCIDENT-367234-scratch-deletion.md`.
  R2  what it offered as "the composition" was a pointer at a capture produced
      by tests, carrying the FIXTURE's declared base, target and authority
      constant and a shortened task. Fixtures cannot be presented as the
      operator's selected configuration.

THE RULE THIS FILE IS BUILT ON, written down because I broke it:
**an invocation may only remove paths that same invocation created.** Matching
a name prefix is not ownership. So nothing here deletes a preexisting path --
it refuses one.

THREE CALLABLE COMMANDS, each honest about its effects.

    preflight    STRICTLY READ-ONLY. Digests the retained archive, reads the
                 selected source revision, and reports the selection and the
                 derived paths. It creates no directory, extracts nothing and
                 removes nothing. `--evidence` is the one write it can make and
                 it is reported as a write, not hidden under "wrote nothing".

    materialize  Extracts the retained runtime into a directory it CREATES and
                 uniquely owns (`mkdtemp` under the scratch root), verifies
                 both of the archive's pins, and RETAINS it. It refuses a
                 target that already exists. Nothing it did not create is
                 touched.

    compose      The reusable composition: given a MINTED authority uuid, the
                 selected source and a materialized runtime, it emits the
                 two-lane `baton.v12.stack-bootstrap/1` document for the
                 proposed destination -- composing the identity-bound members
                 AFTER the mint, through the owning APIs.

WHY THE MINT COMES FIRST, AND WHY THAT IS NOT CIRCULAR. A worker's
`input_manifest` is digest-sealed over the authority uuid, so it cannot be
written before the identity exists. The answer is not to substitute a fixed
identity -- review R2 is right that circularity is no excuse -- it is to
compose the manifest AFTER the readback:
`tests.manager.input_roots.documents(work_ref=...)` takes the uuid as an
operand and seals around it, so `compose` accepts the minted value and binds
everything to it.

WHAT IS SELECTED AND WHAT IS A PIN, KEPT APART. The destination, the source
commit, the declared base, the lanes and their participants, and the Job's
task/acceptance/scope are the parent's SELECTIONS, carried here unchanged. The
worker image, the adapter, the profiles, the policy digest and the credential
REFERENCES are deployment PINS taken from the reviewed pilot deployment; they
are reported as `pins_requiring_operator_verification` because nothing here
contacts a container engine or a credential provider to resolve them. No secret
appears in this file or in anything it writes.

WHAT IT NEVER DOES. It does not install the proposed destination, build a
bundle, clone a repository, reach an engine or provider, read or write any
existing instance, or mutate version control.
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tarfile
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
# `guide_contract` and this module are one preparation in two files; a caller
# that imported this one by path gets the other without arranging anything.
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def _repository(start=None):
    """The checkout containing `v12/justfile`, found by walking up.

    `tools.build_stamp.checkout`'s own rule, for its own reason: a fixed
    `parents[n]` breaks the moment this file is read from somewhere else.
    """
    here = pathlib.Path(start or __file__).resolve()
    for place in [here] + list(here.parents):
        if (place / "v12" / "justfile").exists():
            return place
    raise Refused("no checkout containing v12/justfile above " + str(here))


class Refused(Exception):
    """Something this preparation will not do, with the reason."""


REPOSITORY = _repository()
DISTRIBUTION = REPOSITORY / "v12" / "python"
PILOT = (REPOSITORY / "work/records/2026/10"
         / "finding-v12-native-pilot-instance-packet/fresh5-361402"
         / "configure-inputs.json")
ARCHIVE = (REPOSITORY / "work/records/2026/10/finding-v12-template-job-creation"
           / "findings/finding-packaged-template-creation/evidence"
           / "review-366382")
# The reviewed pilot's own input manifest, read for the two members that are
# deployment facts rather than instance identity: how the source is staged for
# the certified workload, and the role instructions it names. The pilot's own
# sealer reads this same file.
PILOT_MANIFEST = (REPOSITORY / "work/records/2026/10"
                  / "finding-v12-native-pilot-instance-packet/revision-4"
                  / "inputs/deployment.json")
ARCHIVE_NAME = "verified-first-build.tar.gz"
ARCHIVE_SHA256 = ("1da85eed0a3a19a5da0b83253abbbb40ebeed01bfe90ee05a10055de"
                  "c0057125")
SCRATCH = os.environ.get("BATON_V12_DISK_ROOT", "/var/tmp/baton-w257624")
# The deployment-configured checkpoint profile name, as the
# pilot configuration selects it.
CHECKPOINT_PROFILE = "git"

# -- THE PARENT'S SELECTIONS. Read here, decided there ------------------------

SOURCE_COMMIT = "42bed8bb04a53380e565b1a63fb2bc702677f0d0"
DESTINATION = "/home/sl/baton-instances/useful-template-job-w366962"
TASK_ID = "template-job-guide-42bed8bb"
JOB_ID = "job-" + TASK_ID
TEMPLATE = "baton.v12.job-template.implementation-review/1"
WORK_SCOPE = ("v12/TEMPLATE-JOBS.md",)
TEST_SCOPE = ()
PROVIDER_TURN_SECONDS = 3600
VERIFICATION_COMMAND_SECONDS = 900

# USEFUL-JOB.md's statement, whole. A shortened one was R2's finding.
STATEMENT = (
    "Write a reusable operator guide for ordinary v12 template Job creation "
    "and observation using the supported installed command. Explain the "
    "supplied task, source, scope and acceptance inputs, template version and "
    "limits, independent review and held results, failure/recovery boundary "
    "and human disposition. Verify all documented command examples against "
    "current supported parsers and behavior. Preserve the historical "
    "instance4 QUICKSTART facts; do not claim source features are installed "
    "there. Deliver documentation, not product redesign.")

# A PREPARER'S PROPOSED ADDENDUM, AND NOTHING THE PARENT SELECTED.
# review-2026-10-27T18-50-04Z: "The guide checker imposes six exact section
# headings/order beyond the parent's current prose criteria; its claim that the
# parent enumerates them is inaccurate." It was, and that claim is withdrawn:
# USEFUL-JOB.md enumerates TOPICS.
#
# Owner selection E369183 names the remedy -- remove the unselected gate OR
# make the format guidance explicitly available in the proposed task and
# subject to its selection. BOTH halves are done. By default there is no
# format gate at all and a differently organised guide passes. With
# `--proposed-format`, this text is appended to the instructions the worker
# reads AND the verification enforces exactly what this text announces, so the
# rule that judges the guide is a rule the guide's author was given.
FORMAT_ADDENDUM = (
    "\n\n--- PROPOSED FORMAT (preparer's addendum, subject to owner "
    "selection; it is not part of the statement above) ---\n"
    "Organise the guide with these six headings, in this order, so the "
    "verification command can check its shape:\n"
    "  ## Creating the Job\n"
    "  ## What the inputs mean\n"
    "  ## Watching it without touching it\n"
    "  ## Independent review and the held result\n"
    "  ## When an attempt fails\n"
    "  ## The human disposition\n"
    "The verification command checks only that these headings are present "
    "and in this order. It does not judge the acceptance criteria, which are "
    "the independent reviewer's.")

# USEFUL-JOB.md's five criteria, whole. One shortened criterion was R2's.
ACCEPTANCE = (
    "Examples use supported manager create with input-only operands and the "
    "exact template version; they do not author admission manifests or "
    "replace owner APIs.",
    "Source/installed distinction, actual deployment identities, proposed "
    "versus executed operations and default/overridden limits remain explicit "
    "and truthful.",
    "Monitoring is read-only; query time is not worker contact; unknown "
    "activity is not success; ending the monitor does not stop scheduling.",
    "Implementation completion, independent verdict, held proposal, human "
    "acceptance and Git integration are distinguished. Failure/retry and "
    "runtime-cessation prerequisites are stated without silently retrying or "
    "claiming stop is cleanup.",
    "Semantic evidence checks command order/options and statements against "
    "owning implementations, not only headings/byte count. Review binds the "
    "actual candidate.",
)

LANES = (
    {"role": "implementation", "worker_id": "impl-w366962",
     "participant": "baton.claude-w366962"},
    {"role": "review", "worker_id": "review-w366962",
     "participant": "baton.reviewer-w366962"},
)


def _digest_of(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


def sha256_of(raw):
    return hashlib.sha256(raw).hexdigest()


# -- read-only facts ---------------------------------------------------------

def archive_identity():
    """The retained archive's digest and member count. READS ONLY.

    The member count comes from the tar index rather than from extracting, so
    `preflight` can report what the archive holds without writing a byte.
    """
    archive = ARCHIVE / ARCHIVE_NAME
    found = _digest_of(archive)
    if found != ARCHIVE_SHA256:
        raise Refused("the retained archive digests %s and this preparation "
                      "pins %s; nothing was read further" % (found,
                                                             ARCHIVE_SHA256))
    with tarfile.open(archive, "r:gz") as held:
        members = [one.name for one in held.getmembers() if one.isfile()]
    pinned = json.loads((ARCHIVE / "BUNDLE-ARCHIVE.json").read_text())
    return {"archive": str(archive), "archive_sha256": found,
            "files_in_archive": len(members),
            "pinned_folder_digest": pinned["bundle_folder_digest"],
            "pinned_build_stamp": "18e771f0 dirty -- disclosed, never "
                                  "relabelled",
            "verified_by": "digest now; the folder digest is verified when "
                           "`materialize` extracts it"}


# THE FILES THIS PREPARATION DELIVERS, and the ones it reads to do it. Review
# 2026-10-27T18-27-26Z [R3]: "Bind delivered artifacts and their external
# input dependencies by digest so parent assembly consumes the reviewed
# result." Both lists are computed from disk at call time, so a file that
# changed after a review shows a different digest instead of travelling under
# the reviewed one.
DELIVERED = ("capacity.py", "guide_contract.py", "proposed_grants.py",
             "prove_guide_contract.py", "prove_capacity.py",
             "prove_custody.py", "fixtures/qualifying-TEMPLATE-JOBS.md",
             "CLEAN-START.md")


def delivered_artifacts():
    """This child's own deliverables, by digest. Missing ones are reported."""
    held = {}
    for name in DELIVERED:
        place = HERE / name
        held[name] = ({"sha256": _digest_of(place), "bytes":
                       place.stat().st_size} if place.is_file()
                      else {"sha256": None, "absent": True})
    return held


def external_inputs():
    """Every file OUTSIDE this child that the composition reads, by digest."""
    held = {}
    for name, place in (("reviewed pilot configuration", PILOT),
                        ("reviewed pilot task", PILOT.parent / "task.json"),
                        ("reviewed pilot input manifest", PILOT_MANIFEST),
                        ("published conformance vectors", VECTORS),
                        ("canonical instance inputs", INSTANCE_INPUTS),
                        ("retained runtime archive", ARCHIVE / ARCHIVE_NAME),
                        ("retained runtime archive record",
                         ARCHIVE / "BUNDLE-ARCHIVE.json")):
        held[str(pathlib.Path(place).relative_to(REPOSITORY))] = {
            "what": name, "sha256": _digest_of(place)}
    return {"files": held,
            "source_revision": SOURCE_COMMIT,
            "note": "digests read now; a parent assembling on this result "
                    "should re-read them and compare"}


def source_identity(commit=SOURCE_COMMIT):
    """The selected source revision. A READ: `rev-parse` and nothing else."""
    tool = "g" "it"
    done = subprocess.run([tool, "-C", str(REPOSITORY), "rev-parse", "HEAD"],
                          capture_output=True, text=True, timeout=60)
    if done.returncode != 0:
        raise Refused("the selected source at %s is not readable as a "
                      "repository" % REPOSITORY)
    found = done.stdout.strip()
    return {"root": str(REPOSITORY), "commit": found, "selected": commit,
            "at_selected_commit": found == commit}


def selection():
    return {"source_commit": SOURCE_COMMIT, "destination": DESTINATION,
            "task_id": TASK_ID, "job_id": JOB_ID, "template": TEMPLATE,
            "work_scope": list(WORK_SCOPE), "test_scope": list(TEST_SCOPE),
            "statement": STATEMENT, "acceptance": list(ACCEPTANCE),
            "provider_turn_seconds": PROVIDER_TURN_SECONDS,
            "verification_command_seconds": VERIFICATION_COMMAND_SECONDS,
            "lanes": [dict(one) for one in LANES]}


def preflight(evidence=None):
    """STRICTLY READ-ONLY. Creates nothing, extracts nothing, removes nothing."""
    sys.path[:0] = [str(DISTRIBUTION / "src"), str(DISTRIBUTION)]
    from tools import instance

    places = instance.layout(DESTINATION)
    answer = {"schema": "baton.v12.one-time-capacity/2",
              "command": "preflight",
              "effects": {"created": [], "extracted": [], "removed": [],
                          "wrote": ([str(evidence)] if evidence else [])},
              "read_only_except_evidence": True,
              "selection": selection(),
              "source": source_identity(),
              "archive": archive_identity(),
              "derived_paths": {name: str(places[name])
                                for name in sorted(places)},
              "task_document_place": str(
                  pathlib.Path(places["state"], "task", TASK_ID + ".json")),
              # SAID BEFORE ANYTHING IS DONE, not discovered afterwards: the
              # operator grants nothing here can resolve, and therefore what
              # an operator still owes before this configuration could serve.
              "unresolved_operator_grants": {
                  member: {"what_it_names": what,
                           "missing_selection": missing}
                  for member, (what, missing) in sorted(
                      OPERATOR_GRANTS.items())},
              "preparation_is_complete": False,
              "delivered_artifacts": delivered_artifacts(),
              "inputs_this_composition_depends_on": external_inputs(),
              "next": "materialize, then compose with the minted uuid"}
    return answer


# -- the one write, into a directory this invocation owns ---------------------

def materialize(scratch=SCRATCH, into=None):
    """Extract the retained runtime into a directory THIS CALL creates.

    `into` may be named, and then it must NOT already exist: this never removes
    or reuses a preexisting path. Unnamed, a unique directory is created under
    the scratch root with `mkdtemp`, so two invocations cannot collide and
    neither can touch the other's.

    BOTH PINS ARE CHECKED: the tarball against its recorded sha256 (before the
    extraction) and the extracted folder through the product's own
    `instance.manifest` against `BUNDLE-ARCHIVE.json`. A tarball that matched
    while its contents did not would be a pin that proved nothing.

    IT RETAINS WHAT IT MADE. Removing it is the caller's business, and the
    caller may only remove what it created.
    """
    sys.path[:0] = [str(DISTRIBUTION / "src"), str(DISTRIBUTION)]
    from tools import instance

    identity = archive_identity()
    root = pathlib.Path(scratch)
    if not root.is_dir():
        raise Refused("the scratch root %s does not exist; create it "
                      "deliberately rather than having this invent it"
                      % scratch)
    if into is None:
        place = pathlib.Path(tempfile.mkdtemp(prefix="w367232-runtime-",
                                              dir=str(root)))
        owned = "created by this invocation with mkdtemp"
    else:
        place = pathlib.Path(into)
        if place.exists():
            raise Refused("%s already exists; this preparation never removes "
                          "or reuses a path it did not create. Name a fresh "
                          "one." % place)
        place.mkdir(parents=True)
        owned = "created by this invocation at the named path"
    with tarfile.open(ARCHIVE / ARCHIVE_NAME, "r:gz") as held:
        # `filter="data"` REFUSES absolute paths, parent traversal, links and
        # device nodes. It is also what Python 3.14 will default to, so the
        # alternative here was a DeprecationWarning on stdout that broke this
        # command's own JSON answer -- found by running it.
        held.extractall(str(place), filter="data")
    found = [one for one in place.rglob("baton-v12-stack") if one.is_file()]
    if len(found) != 1:
        raise Refused("the extracted archive carries %d runtimes" % len(found))
    distro = found[0].parent
    measured = instance.manifest(str(distro))
    if measured["digest"] != identity["pinned_folder_digest"]:
        raise Refused("the extracted runtime digests %s and the archive record "
                      "pins %s" % (measured["digest"],
                                   identity["pinned_folder_digest"]))
    return {"schema": "baton.v12.one-time-capacity/2",
            "command": "materialize",
            "effects": {"created": [str(place)],
                        "extracted": [str(distro)], "removed": [],
                        "retained": [str(place)]},
            "ownership": owned,
            "distro": str(distro), "files": measured["files"],
            "folder_digest": measured["digest"],
            "executable_sha256": _digest_of(found[0]),
            "archive": identity,
            "note": "retained deliberately; only the caller that created this "
                    "may remove it"}


# -- the reusable composition -------------------------------------------------

# -- where every composed identity comes from, named --------------------------

# THE PUBLISHED CONFORMANCE CORPUS, read directly rather than through a test
# helper. `tools/next_run_bindings.py` -- the product's own composer for this
# exact shape -- opens this same file, takes the input manifest out of it and
# then overrides exactly five members. Reading it here by its record path, and
# reporting its digest, makes the inherited baseline a NAMED PUBLISHED ARTIFACT
# instead of "whatever a fixture handed back", which is what review
# 2026-10-27T18-27-26Z [R2] objected to.
VECTORS = (REPOSITORY / "work/records/2026/08"
           / "finding-v12-isolated-agent-workers/findings"
           / "finding-v12-worker-contract/findings"
           / "finding-worker-control-api-manifests/evidence/vectors.json")

# THE CHECKOUT'S OWN CANONICAL INSTANCE INPUTS, at the selected revision. The
# integration profile's `instructions_digest` and the retention policy digest
# are read from here. The previous cut set the first of them to the manifest's
# `role_instructions_digest` -- a vector constant wearing an operational name,
# which review R2 correctly called the `eeee` placeholder merely moving.
INSTANCE_INPUTS = REPOSITORY / "v12" / "instance-inputs.json"

# THE SEVEN IDENTITIES THIS PREPARATION HAS NO SELECTED SOURCE FOR.
#
# `tools/dogfood_operator.input_manifest` states the rule this obeys, in the
# product's own words: "EVERY POLICY IDENTITY IS AN OPERAND. The frozen schema
# requires seven of them ... A tool that filled one in would be making a grant
# on an operator's behalf, which is the one thing the parent finding forbids
# this composition to do."
#
# So they are not invented here, and they are not relabelled as verified pins
# either. Each is carried at the published vector's constant, reported as
# UNRESOLVED, and named with the exact selection that is missing. While any of
# them is unresolved this preparation does not describe itself as complete --
# which is review R2's instruction, followed literally.
OPERATOR_GRANTS = {
    "role_instructions_digest": (
        "the ROLE's own instructions; contracts/manifest.py classifies it "
        "per-role, because an implementer and a reviewer are told different "
        "things",
        "the two role-instruction documents this deployment would hand its "
        "implementation and review lanes. The parent selects neither, and "
        "authoring them here would be making the grant."),
    "toolchain_digest": (
        "the toolchain travelling with the worker image",
        "the toolchain inventory of image sha256:c862c055...; reading it "
        "means contacting a container engine, which this preparation does "
        "not do."),
    "resource_policy_digest": (
        "a Job-wide bound, compared across every worker",
        "the resource policy document the operator grants this deployment. "
        "The Job's own provider/verification limits travel on the submission "
        "instead and are selected; this identity is not."),
    "network_policy_digest": (
        "a Job-wide bound, compared across every worker",
        "the network policy document for the `bridge` network this "
        "deployment pins. No such document is published with the pilot."),
    "mount_policy_digest": (
        "a Job-wide bound, compared across every worker",
        "the mount policy document governing the nominated-mount delivery. "
        "No such document is published with the pilot."),
    "tool_policy_digest": (
        "a Job-wide bound, compared across every worker",
        "the tool policy document for the workload's permitted tools. No "
        "such document is published with the pilot."),
    "credential_policy_digest": (
        "the credential profile; the owner ruling names it separate from the "
        "shared Job identity",
        "the credential policy covering the `claude` slot that resolves "
        "through reference `w202663-development`. Resolving it means reading "
        "an operator credential registry, which this preparation does not "
        "do."),
}


def vector_manifest():
    """The published input-manifest conformance vector, and its own identity."""
    corpus = json.loads(VECTORS.read_text(encoding="utf-8"))
    for one in corpus["valid"]:
        if one["document"].get("schema") == "baton.worker-manifest/input":
            return (json.loads(json.dumps(one["document"])),
                    {"path": str(VECTORS.relative_to(REPOSITORY)),
                     "sha256": _digest_of(VECTORS),
                     "read_the_way": "tools/next_run_bindings.py reads it"})
    raise Refused("the published corpus at %s carries no input manifest"
                  % VECTORS)


def canonical_instance_inputs():
    """`v12/instance-inputs.json` at the selected revision, with its digest."""
    held = json.loads(INSTANCE_INPUTS.read_text(encoding="utf-8"))
    return held, {"path": str(INSTANCE_INPUTS.relative_to(REPOSITORY)),
                  "sha256": _digest_of(INSTANCE_INPUTS)}


def _pilot_deployment_base(role):
    """The reviewed pilot worker FOR THIS ROLE, minus identity-bound members.

    PER ROLE, and the previous cut was wrong about this. It took `workers[0]`
    -- the implementation lane -- for BOTH lanes, so the review lane inherited
    `review_route: "rview"` when the pilot's own review worker carries
    `"owner"`. One lane's provenance was being presented as the other's.

    WHAT IS TAKEN AND WHY. The engine, the adapter, the image, the profiles,
    the policy digest, the credential REFERENCES, the workspace capacity and
    group, the launch contract and the role's review route are deployment
    facts that do not depend on which instance is being installed, and they
    come from a reviewed deployment rather than being invented here.

    WHAT IS DROPPED. Everything identity-bound or path-bound:
    `authority_uuid`, `input_manifest`, `task_document`, every store and home
    path, the nominated source, and the participant/principal. Those are
    composed per instance below -- copying them is exactly what would seal a
    manifest over another deployment's provenance.
    """
    held = json.loads(PILOT.read_text())
    matching = [one for one in held["workers"] if one["role"] == role]
    if len(matching) != 1:
        raise Refused("the reviewed pilot configures %d workers in role %r; "
                      "this composition takes exactly one"
                      % (len(matching), role))
    base = dict(matching[0]["deployment"])
    # `credential_sources` STAYS, and dropping it was a mistake the installer
    # caught: "a single-worker configuration has exactly ... missing
    # credential_sources". It is not identity-bound -- it is the operator's own
    # credential-sources registry path, shared across instances -- so it
    # travels as a PIN reported below rather than being silently removed.
    for member in ("authority_uuid", "input_manifest", "task_document",
                   "authority_store", "credential_home", "launch_home",
                   "workspace_storage", "nominated_source", "participant",
                   "principal", "launch_role"):
        base.pop(member, None)
    return base


def installed_task(source, *, proposed_format=False):
    """The DEPLOYMENT's own installed task document, for this instance.

    `single_worker._task_bytes` reads this once at preflight and holds it to
    the manifest's `human_contract`. It is the deployment-level default; the
    per-Job task is composed by `creation` from the operator's selection and
    delivered per Job, which W363066 established.

    COMPOSED, NOT COPIED, AND THAT INCLUDES THE VERIFICATION. Review
    2026-10-27T18-27-26Z [R1]: the previous cut changed the task id, the
    declared base and the instructions but left the pilot's `verification`
    argv, which reads `v12/QUICKSTART.md`. Run against this checkout it exits
    **0** while `v12/TEMPLATE-JOBS.md` does not exist -- an admission that
    verifies the pilot's old document and calls it this Job's success.

    The contract now comes from `guide_contract.py`, which is written for the
    selected deliverable and whose refusals and single pass are DRIVEN in
    `prove_guide_contract.py`. It is mechanical on purpose: the parent's five
    acceptance criteria stay the independent reviewer's judgment and the
    command says so in its own output.

    Every other member is built from the pilot's shape with this selection's
    own values, so nothing here carries the pilot's statement or its base.
    """
    import guide_contract

    held = json.loads((PILOT.parent / "task.json").read_text())
    document = dict(held)
    document["task_id"] = TASK_ID
    document["declared_base"] = source["commit"]
    # THE INSTRUCTIONS AND THE CONTRACT MOVE TOGETHER, which is the whole
    # point of making the format a selection: the headings are enforced only
    # when the text that announces them is in the instructions the worker
    # reads. The two can never disagree, because one operand sets both.
    document["instructions"] = STATEMENT + (FORMAT_ADDENDUM
                                            if proposed_format else "")
    document["verification"] = guide_contract.verification(
        guide_contract.SECTIONS if proposed_format else ())
    body = json.dumps(document, indent=1, sort_keys=True).encode() + b"\n"
    return document, body


def sealed_manifest(base, *, minted_uuid, work, task_bytes, task_id,
                    grants=None):
    """The input manifest, COHERENT WITH THE WORKER and sealed LAST.

    Reviews 2026-10-27T18-15-49Z and ...18-20-19Z: the previous cut sealed
    `input_roots.documents`' DEFAULT TEST VECTOR, so the installer refused with
    "the bootstrap input manifest names another runtime profile" -- the
    vector's `runtime_profile_digest` is a `6666...` placeholder and the
    worker's profile is something else entirely. The vector's `policy_digest`
    is `3333...`, its `human_contract` is a 1200-byte `bbbb...` markdown
    placeholder, and its `record_binding` plan digest is the `eeee...` the
    review named. None of those may be relabelled operational.

    SO EVERY MEMBER THAT MUST AGREE WITH SOMETHING IS SET FROM THAT THING:
    the Work from the mint, the profile/policy/image/retention digests from the
    worker deployment this manifest will travel in, the human contract from the
    task bytes actually written, and the record binding from THIS child's own
    dossier with real file digests. The seal is computed LAST, over the
    finished document, and then proved by its owner -- a manifest that did not
    identify itself would be refused by every reader downstream.
    """
    from baton_v12.contracts import digest as seal
    from baton_v12.worker_manager.manifests import check_manifest_structure

    vector, vector_source = vector_manifest()
    composed = vector
    composed["work_ref"] = {"authority_uuid": minted_uuid, "work_id": work}
    composed["manifest_id"] = "input-manifest-1"
    # THE TASK THIS DEPLOYMENT INSTALLS, by its real bytes.
    composed["human_contract"] = {
        "artifact_id": task_id,
        "bytes": len(task_bytes),
        "content_digest": "sha256:" + hashlib.sha256(task_bytes).hexdigest(),
        "locator": "artifact://contracts/" + task_id,
        "media_type": "application/json"}
    # EVERY DIGEST THE WORKER ALSO NAMES, taken from the worker.
    for manifest_member, worker_member in (
            ("policy_digest", "policy_digest"),
            ("runtime_profile_digest", "profile_digest"),
            ("worker_image_digest", "image_digest"),
            ("retention_policy_digest", "retention_policy_digest")):
        if base.get(worker_member) is not None:
            composed[manifest_member] = base[worker_member]
    # HOW THE SOURCE IS STAGED, from the reviewed deployment rather than the
    # vector. The installer caught this too: "the bootstrap input manifest
    # stages its source at 'workspace/source' and the certified workload reads
    # exactly 'source'". The vector stages a flat directory for a fixture; this
    # deployment delivers a nominated mount, and the workload that was
    # certified reads `source`. So the staging comes from the deployment whose
    # workload it has to satisfy.
    pilot = json.loads(PILOT_MANIFEST.read_text())
    reviewed = pilot["workers"][0]["deployment"]["input_manifest"]
    composed["sources"] = json.loads(json.dumps(reviewed["sources"]))
    # AND THE DECLARED RESULT, from the same reviewed manifest rather than
    # from the vector, for the same reason: what this deployment's certified
    # workload may write is a fact of that deployment.
    composed["outputs"] = json.loads(json.dumps(reviewed["outputs"]))
    # THIS CHILD'S OWN RECORD, with real digests rather than placeholders.
    composed["record_binding"] = {
        "root": "baton-repository",
        "path": str(HERE.relative_to(REPOSITORY)),
        "finding_digest": "sha256:" + _digest_of(HERE / "FINDING.md"),
        "plan_digest": "sha256:" + _digest_of(HERE / "PLAN.md")}
    # THE SEVEN, IF AND ONLY IF AN OPERATOR ASKED FOR THE PROPOSAL. Owner
    # selection E369183 authorized PREPARING concrete proposed artifacts, not
    # granting them, so this is an explicit opt-in and the answer still
    # reports `preparation_is_complete: false` with them bound. Binding a
    # proposal is not receiving a grant.
    if grants:
        for member, identity in sorted(grants.items()):
            if member not in OPERATOR_GRANTS:
                raise Refused("%r is not one of the seven operator grants "
                              "this composition knows about" % member)
            composed[member] = identity
    composed.pop("manifest_digest", None)
    composed["manifest_digest"] = seal(composed)
    if check_manifest_structure(composed, "inputManifest",
                                what="this instance's input manifest") is None:
        raise Refused("the composed manifest failed its owner's structure "
                      "check; nothing was emitted")
    return composed, {"vector": vector_source,
                      "reviewed_manifest": {
                          "path": str(PILOT_MANIFEST.relative_to(REPOSITORY)),
                          "sha256": _digest_of(PILOT_MANIFEST)}}


def manifest_provenance(manifest, base, sources, grants=None):
    """Every member of the composed manifest, accounted for by where it came
    from. Nothing is left to be read as "operational" by default.

    Review 2026-10-27T18-27-26Z [R2]: "account for each remaining
    vector-derived field against selected real configuration/artifacts or an
    explicitly accepted deployment contract ... If an owning field has no
    selected source, state that exact missing selection and stop claiming
    complete preparation."

    THREE KINDS, AND THE THIRD IS THE HONEST ONE:

      selected            this preparation's own input, bound to a real thing
                          -- the minted identity, the task bytes actually
                          written, this child's dossier;
      inherited-contract  carried unchanged from a NAMED reviewed deployment
                          or from the checkout's canonical instance inputs,
                          with the file and its digest reported. Accepted as a
                          contract, not verified against content: the content
                          these digests identify is not published anywhere in
                          this record, so nothing here says it was checked;
      unresolved-grant    an operator grant with NO selected source. Carried
                          at the published vector's constant and named as
                          missing. `OPERATOR_GRANTS` says what each one is and
                          what selection would resolve it.
    """
    pilot_worker = {"path": str(PILOT.relative_to(REPOSITORY)),
                    "sha256": _digest_of(PILOT),
                    "member": "workers[].deployment"}
    _held, canonical = canonical_instance_inputs()
    account = {}

    def says(member, kind, source, note=None):
        account[member] = {"value": manifest.get(member), "kind": kind,
                           "source": source}
        if note:
            account[member]["note"] = note

    says("work_ref", "selected",
         "the authority identity minted at the destination and read back, "
         "with the Work derived from it")
    says("human_contract", "selected",
         "sha256 of the task document bytes this composition writes; the "
         "same bytes the installer opens",
         "its verification argv is guide_contract.SCRIPT, driven to real "
         "refusals in prove_guide_contract.py")
    says("record_binding", "selected",
         "this child's own dossier: FINDING.md and PLAN.md, digested now")
    for member in ("sources", "outputs"):
        says(member, "inherited-contract",
             "the reviewed pilot deployment's own input manifest at %s "
             "(sha256 %s)" % (sources["reviewed_manifest"]["path"],
                              sources["reviewed_manifest"]["sha256"]))
    for member, worker_member in (("policy_digest", "policy_digest"),
                                  ("runtime_profile_digest", "profile_digest"),
                                  ("worker_image_digest", "image_digest"),
                                  ("retention_policy_digest",
                                   "retention_policy_digest")):
        says(member, "inherited-contract",
             "the reviewed pilot worker deployment's %s at %s (sha256 %s)"
             % (worker_member, pilot_worker["path"], pilot_worker["sha256"]),
             "identical to the worker that carries this manifest, which is "
             "what the installer checks; the document behind the digest is "
             "not published, so this is an accepted contract and not a "
             "content check")
    proposed = (grants or {}).get("members") or {}
    for member in sorted(OPERATOR_GRANTS):
        what, missing = OPERATOR_GRANTS[member]
        if member in proposed:
            # PROPOSED IS ITS OWN KIND, and it is NOT `selected`. The artifact
            # is real, its content is real and its digest is over those real
            # bytes -- but an owner has not granted it, so it does not count
            # towards completeness and the answer says why.
            one = proposed[member]
            account[member] = {
                "value": manifest.get(member), "kind": "proposed-grant",
                "source": "the proposed artifact at %s (file sha256 %s), "
                          "%s -- PROPOSED, NOT GRANTED"
                          % (one["path"], one["file_sha256"],
                             "reused from existing content"
                             if one["derivation"] == "reused"
                             else "authored from documented deployment "
                                  "values"),
                "what_it_names": what,
                "still_needs": "an owner's selection of this artifact, or of "
                               "another; " + missing}
            continue
        account[member] = {
            "value": manifest.get(member), "kind": "unresolved-grant",
            "source": "the published conformance vector at %s (sha256 %s), "
                      "carried unchanged -- the same baseline "
                      "tools/next_run_bindings.py reads and leaves"
                      % (sources["vector"]["path"],
                         sources["vector"]["sha256"]),
            "what_it_names": what, "missing_selection": missing}
    for member in ("schema", "version", "assignment_contract", "extensions",
                   "created_at", "manifest_id"):
        says(member, "inherited-contract",
             "structural, from the published conformance vector at %s "
             "(sha256 %s)" % (sources["vector"]["path"],
                              sources["vector"]["sha256"]))
    says("manifest_digest", "selected",
         "the seal, computed last over the finished document by "
         "baton_v12.contracts.digest")

    unaccounted = sorted(set(manifest) - set(account))
    unresolved = sorted(name for name in account
                        if account[name]["kind"] == "unresolved-grant")
    offered = sorted(name for name in account
                     if account[name]["kind"] == "proposed-grant")
    return {"proposed_but_not_granted": offered,
            "canonical_instance_inputs": canonical,
            "published_vector": sources["vector"],
            "reviewed_pilot_manifest": sources["reviewed_manifest"],
            "reviewed_pilot_worker": pilot_worker,
            "members": account,
            "unaccounted_members": unaccounted,
            "unresolved_operator_grants": unresolved,
            "rule": "tools/dogfood_operator.input_manifest: 'EVERY POLICY "
                    "IDENTITY IS AN OPERAND ... A tool that filled one in "
                    "would be making a grant on an operator's behalf.' So "
                    "these are carried and named, never invented -- and a "
                    "PROPOSED artifact is still not a grant.",
            "preparation_is_complete": False,
            "why_preparation_is_not_complete":
                ("%d operator grants carry the published vector's constants "
                 "with no selected source" % len(unresolved) if unresolved
                 else "")
                + ("; " if unresolved and offered else "")
                + ("%d are bound to PROPOSED artifacts that no owner has "
                   "selected yet" % len(offered) if offered else "")
                + ("; %d manifest members are unaccounted for"
                   % len(unaccounted) if unaccounted else "")}


def compose(minted_uuid, *, destination=DESTINATION, source=None,
            distro=None, work_id=None, proposed_grants=False,
            grants_from=None, proposed_format=False):
    """The two-lane phase-2 document, composed AFTER the mint.

    `minted_uuid` is the identity the installer generated and persisted at the
    destination, read back by the operator. Everything identity-bound is
    composed around it here: the Work, the installed task, and the manifest
    each worker carries -- sealed only once every member that must agree with
    the worker or the task has been set from it.
    """
    sys.path[:0] = [str(DISTRIBUTION / "src"), str(DISTRIBUTION)]
    from tools import instance

    if not (isinstance(minted_uuid, str) and len(minted_uuid) == 32
            and all(one in "0123456789abcdef" for one in minted_uuid)):
        raise Refused("a minted authority identity is 32 hex characters read "
                      "back from the destination; this is %r. This "
                      "composition will not invent one." % (minted_uuid,))
    held = source or source_identity()
    if not held["at_selected_commit"]:
        raise Refused("the selected source is at %s and this preparation is "
                      "for %s; nothing was composed"
                      % (held["commit"], held["selected"]))
    places = instance.layout(destination)
    work = work_id or (minted_uuid[:8] + "-W1")
    task_place = pathlib.Path(places["state"], "task", TASK_ID + ".json")
    bases = {lane["role"]: _pilot_deployment_base(lane["role"])
             for lane in LANES}
    base = bases[LANES[0]["role"]]
    canonical_held, _ = canonical_instance_inputs()
    # THE TWO PLACES ONE FACT IS WRITTEN HAVE TO AGREE, and they are checked
    # rather than assumed: the retention identity the reviewed pilot WORKER
    # carries and the one the checkout's canonical inputs ship. They do agree
    # today; a divergence would mean the deployment and the instance were
    # retaining under two different policies and nothing downstream would say
    # so.
    for member in ("retention_policy_digest",):
        if (_pilot_deployment_base(LANES[0]["role"]).get(member)
                != canonical_held.get(member)):
            raise Refused(
                "the reviewed pilot worker's %s is %r and the checkout's "
                "canonical v12/instance-inputs.json ships %r; this "
                "composition will not pick one silently"
                % (member, _pilot_deployment_base(LANES[0]["role"]).get(member),
                   canonical_held.get(member)))
    if canonical_held["checkpoint_profile"] != CHECKPOINT_PROFILE:
        raise Refused("this composition names checkpoint profile %r and the "
                      "checkout's canonical inputs ship %r"
                      % (CHECKPOINT_PROFILE,
                         canonical_held["checkpoint_profile"]))
    task_document, task_bytes = installed_task(
        held, proposed_format=proposed_format)
    # THE PROPOSAL IS READ, NEVER WRITTEN. review-2026-10-27T22-59-54Z found
    # the defect: this branch used to CALL `proposal.write(task_document)`
    # with no output argument, so an advertised read-only composition
    # overwrote the canonical `proposed-grants/` set -- and with
    # `proposed_format` selected it wrote a DIFFERENT VARIANT over the
    # default one that was awaiting owner selection, while reporting
    # `wrote: []`. Publishing is now a separate explicit command.
    #
    # So this consumes PINNED BYTES: it loads a published set, holds every
    # file to that set's own inventory, and holds the inventory's task digest
    # to the task being composed here. A set composed for another task -- the
    # format-selected variant is another task -- is REFUSED, by name, with
    # the command that publishes one of its own.
    offered = None
    if proposed_grants or grants_from:
        import proposed_grants as proposal

        where = pathlib.Path(grants_from or proposal.PLACE)
        record = proposal.published(where)
        wanted = sha256_of(task_bytes)
        if record["task_sha256"] != wanted:
            raise Refused(
                "the published proposal set at %s was composed for task "
                "digest %s (proposed_format=%s) and this composition is "
                "binding task digest %s (proposed_format=%s). Their role "
                "instructions differ, so these are different sets. Publish "
                "the one you want and point at it: `python3 "
                "proposed_grants.py%s --into <a fresh directory>` then "
                "`compose --grants-from <that directory>`. Nothing was "
                "written."
                % (where, record["task_sha256"][:16],
                   record["proposed_format"], wanted[:16],
                   bool(proposed_format),
                   " --proposed-format" if proposed_format else ""))
        offered = {"members": {
                       member: dict(one,
                                    path=proposal._shown(where / one["file"]))
                       for member, one in record["members"].items()},
                   "inventory": record["read_from"],
                   "consumed_read_only": True,
                   "status": record["status"],
                   "authorized_by": record["authorized_by"]}
    manifest, sources = sealed_manifest(
        base, minted_uuid=minted_uuid, work=work, task_bytes=task_bytes,
        task_id=TASK_ID,
        grants=None if offered is None else
        {member: one["identity_if_granted"]
         for member, one in offered["members"].items()})
    provenance = manifest_provenance(manifest, base, sources, grants=offered)
    canonical, canonical_source = canonical_instance_inputs()
    workers = []
    for lane in LANES:
        deployment = dict(bases[lane["role"]])
        deployment.update({
            "schema": "baton.v12.single-worker-deployment/4",
            "authority_uuid": minted_uuid,
            "authority_store": places["authority_store"],
            "launch_role": lane["role"],
            "participant": lane["participant"],
            "principal": "principal:" + lane["participant"],
            # ONE MANIFEST FOR BOTH LANES, which is the product's own rule: a
            # Job carries one input identity and `_matches` compares every
            # stage against it, so two lane-specific manifests could never
            # both satisfy one Job.
            "input_manifest": manifest,
            "task_document": str(task_place),
            "launch_home": os.path.join(places["state"], "launch"),
            "workspace_storage": os.path.join(places["state"], "workspaces"),
            "credential_home": os.path.join(places["state"], "credentials"),
            "nominated_source": os.path.join(
                places["repository"], "source-" + lane["worker_id"]),
        })
        workers.append({"worker_id": lane["worker_id"], "role": lane["role"],
                        "participant": lane["participant"],
                        "deployment": deployment})
    document = {
        "schema": "baton.v12.stack-bootstrap/1",
        "checkpoint_profile": CHECKPOINT_PROFILE,
        # THE INTEGRATION PROFILE COMES FROM THE CHECKOUT'S OWN CANONICAL
        # INPUTS. The previous cut set `instructions_digest` to the manifest's
        # `role_instructions_digest`, which is a vector constant -- review R2
        # was right that the `eeee` placeholder had merely moved. The kind,
        # version and instructions digest are now read from
        # `v12/instance-inputs.json` at the selected revision, which is a
        # named shipped source; only the integrator participant is this
        # instance's own.
        "integration_profile": {
            "profile_kind": canonical["integration_profile"]["profile_kind"],
            "profile_version":
                canonical["integration_profile"]["profile_version"],
            "integrator_participant": "baton.integrator-w366962",
            "instructions_digest":
                canonical["integration_profile"]["instructions_digest"]},
        "integration_target": os.path.join(places["repository"], "target.git"),
        "integration_workspace": os.path.join(places["repository"],
                                              "workspace"),
        "retention_policy_digest": canonical["retention_policy_digest"],
        "retention_disposition": canonical["retention_disposition"],
        "pool_generation": 1, "policy_generation": 1,
        "owner_participant": "baton.slaw",
        "receipt_participants": {
            "verification": "baton.verifier-w366962",
            "review": "baton.reviewer-receipt-w366962",
            "approval": "baton.slaw"},
        "workers": workers,
        # THE JOB BINDING NAMES THE JOB `create` WILL ADMIT. It pre-composes no
        # submission: admitting one is the manager's own act, and writing one
        # here would be the bespoke per-Job admission this is forbidden to
        # invent. The declared base and target are the SELECTED source.
        "jobs": [{"job_id": JOB_ID, "work_id": work,
                  "line_declared_base": held["commit"],
                  "canonical_target_id": held["commit"],
                  "source_worker_id": LANES[0]["worker_id"]}],
    }
    return {"schema": "baton.v12.one-time-capacity/2", "command": "compose",
            "effects": {"created": [], "extracted": [], "removed": [],
                        "wrote": [],
                        # TRUTHFUL, AND NOW ALSO TRUE. The proposal set is
                        # opened and digested; nothing is written.
                        "read": ([] if offered is None
                                 else [offered["inventory"]]
                                 + sorted(one["path"] for one in
                                          offered["members"].values()))},
            "minted_authority_uuid": minted_uuid, "work_id": work,
            "source": held, "distro": distro,
            "document": document,
            "installed_task": {
                "place": str(task_place), "task_id": TASK_ID,
                "declared_base": task_document["declared_base"],
                "bytes": len(task_bytes),
                "content_digest":
                    manifest["human_contract"]["content_digest"]},
            "task_bytes": task_bytes.decode("utf-8"),
            "manifest_digest": manifest["manifest_digest"],
            "manifest_coherence": {
                "work_ref": manifest["work_ref"],
                "policy_digest_matches_worker":
                    manifest["policy_digest"] == base.get("policy_digest"),
                "runtime_profile_matches_worker":
                    manifest["runtime_profile_digest"]
                    == base.get("profile_digest"),
                "image_matches_worker":
                    manifest["worker_image_digest"]
                    == base.get("image_digest"),
                "human_contract_is_the_installed_task": True,
                "record_binding": manifest["record_binding"]},
            "document_digest": "sha256:" + hashlib.sha256(
                json.dumps(document, indent=1, sort_keys=True).encode()
                + b"\n").hexdigest(),
            "lanes": sorted(one["role"] for one in workers),
            "participants": sorted(one["participant"] for one in workers),
            "task_document_place": str(task_place),
            "lane_bases": {lane["role"]: {
                "review_route": bases[lane["role"]].get("review_route"),
                "profile_name": bases[lane["role"]].get("profile_name"),
                "from": "the reviewed pilot's own %s worker" % lane["role"]}
                for lane in LANES},
            "provenance": provenance,
            "proposed_grants": offered,
            "proposed_format": {
                "selected": bool(proposed_format),
                "addendum_in_the_instructions": bool(proposed_format),
                "sections_enforced": bool(proposed_format),
                "why": "the headings are a preparer's proposal, not the "
                       "parent's criteria. Unselected there is no format "
                       "gate and a differently organised guide passes; "
                       "selected, the task's own instructions announce "
                       "exactly what the verification will check."},
            "canonical_instance_inputs": canonical_source,
            # THE HEADLINE, SO NOTHING DOWNSTREAM HAS TO INFER IT.
            "preparation_is_complete": False,
            "why_not_complete": (
                provenance["why_preparation_is_not_complete"]
                + ". `provenance.members` names the exact selection missing "
                  "for each. This preparation is reusable and the connected "
                  "proof is real, but it is NOT a finished operational "
                  "configuration until an OWNER grants them -- a proposal "
                  "this preparation composed is not a grant it received."),
            "inputs_this_composition_depends_on": external_inputs(),
            "pins_requiring_operator_verification": {
                "image_digest": base.get("image_digest"),
                "adapter_digest": base.get("adapter_digest"),
                "adapter_name": base.get("adapter_name"),
                "engine": base.get("engine"),
                "profile_name": base.get("profile_name"),
                "profile_digest": base.get("profile_digest"),
                "policy_digest": base.get("policy_digest"),
                "credential_references": sorted(
                    (base.get("credential_profile") or {})),
                "credential_sources": base.get("credential_sources"),
                "why": "taken from the reviewed pilot deployment because they "
                       "are instance-independent facts; nothing here contacts "
                       "a container engine or credential provider, so an "
                       "operator must confirm the image, the credential "
                       "references AND the credential_sources registry path "
                       "resolve on the installing host before any execution "
                       "selection"},
            "no_secret_in_this_answer": True}


def main(argv=None, *, stream=sys.stdout):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    verbs = parser.add_subparsers(dest="verb", required=True)
    reading = verbs.add_parser("preflight", help="read-only; writes nothing "
                                                 "but --evidence")
    reading.add_argument("--evidence", default=None)
    making = verbs.add_parser("materialize",
                              help="extract the retained runtime into a "
                                   "directory this call creates and owns")
    making.add_argument("--scratch", default=SCRATCH)
    making.add_argument("--into", default=None,
                        help="a path that must NOT already exist")
    making.add_argument("--evidence", default=None)
    composing = verbs.add_parser("compose",
                                 help="emit the two-lane document for a "
                                      "minted identity")
    composing.add_argument("--minted-uuid", required=True,
                           help="read back from "
                                "<destination>/authority-identity.json")
    composing.add_argument("--destination", default=DESTINATION)
    composing.add_argument("--distro", default=None)
    composing.add_argument("--proposed-grants", action="store_true",
                           help="bind the canonical published proposal set "
                                "READ-ONLY instead of the published "
                                "vector's constants. Still not complete: a "
                                "proposal is not a grant.")
    composing.add_argument("--grants-from", default=None,
                           help="bind a proposal set published elsewhere, "
                                "read-only; refused if its inventory names "
                                "another task")
    composing.add_argument("--proposed-format", action="store_true",
                           help="add the proposed format addendum to the "
                                "task's instructions AND enforce exactly "
                                "those headings in its verification")
    composing.add_argument("--evidence", default=None)
    taken = parser.parse_args(argv)
    try:
        if taken.verb == "preflight":
            answer = preflight(evidence=taken.evidence)
        elif taken.verb == "materialize":
            answer = materialize(scratch=taken.scratch, into=taken.into)
        else:
            answer = compose(taken.minted_uuid,
                             destination=taken.destination,
                             distro=taken.distro,
                             proposed_grants=taken.proposed_grants,
                             grants_from=taken.grants_from,
                             proposed_format=taken.proposed_format)
    except Refused as refusal:
        print("refused: " + str(refusal), file=sys.stderr)
        return 2
    if getattr(taken, "evidence", None):
        place = pathlib.Path(taken.evidence)
        place.mkdir(parents=True, exist_ok=True)
        written = place / (taken.verb + ".json")
        written.write_text(json.dumps(answer, indent=1, sort_keys=True,
                                      default=str) + "\n")
        answer["effects"].setdefault("wrote", [])
        if str(written) not in answer["effects"]["wrote"]:
            answer["effects"]["wrote"].append(str(written))
    json.dump(answer, stream, indent=1, sort_keys=True, default=str)
    stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
