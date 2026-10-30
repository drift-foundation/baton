#!/usr/bin/env python3
"""The joined proof, from a clean start, needing nothing that is not here.

Review 2026-10-27T18-27-26Z [R3]: "The successful script reads
/tmp/distro.txt, an undeclared transient prerequisite. Replace it with
explicit verified runtime input or the retained archive's owned
materialization path. A reviewer should not have to patch the script to
reproduce its published command."

So this script MATERIALIZES THE RUNTIME ITSELF, through `capacity.materialize`
-- the same entrypoint an operator calls, which verifies both of the archive's
pins -- unless `--distro` names one. There is no hidden file, no environment
variable the caller has to know about and no step to perform by hand.

    python3 prove_capacity.py                      # materializes its own
    python3 prove_capacity.py --distro <folder>    # reuses a verified one
    python3 prove_capacity.py --scratch <root>     # disk-backed scratch root

WHAT IT RUNS, IN ORDER, ALL OF IT INERT:

    1  mint only -- `bootstrap --inputs` ALONE, state_root naming a private
       disposable destination this script created
    2  read the minted identity back from the instance's own record
    3  compose around that readback
    4  ONE destination install carrying both lanes
    5  `DeploymentDerivation` reads the configuration the installer emitted
    6  ordinary `manager create`
    7  the refusals, against THIS composition and not an old fixture:
       stale source, malformed authority identity, wrong retained artifact,
       occupied materialization target, and the manifest's own seal
    8  `preflight` writes nothing -- MEASURED, by digesting the whole child
       directory either side of the call
    9  a WELL-FORMED authority identity that is not this instance's, offered
       to the installer and to `create`
   10  the same chain again with the seven PROPOSED policy artifacts bound,
       READ-ONLY, in both variants -- the canonical default set and a
       format-selected variant published explicitly into a fresh directory
       -- plus the refusal when one set is bound to the other's task
   11  AND THE CUSTODY GUARD OVER THE WHOLE RUN: every file under the child
       directory is digested before anything happens and again at the very
       end, with the inventory compared as well as the bytes. Step 8 digests
       around one subcall; this one digests around the entire command, which
       is what review-2026-10-27T22-59-54Z found step 8 could not do.

NOTHING OPERATIONAL. The proposed destination is never touched, no engine or
provider is contacted, no repository is cloned, no build runs and nothing is
removed -- every path is created by this invocation under the scratch root and
RETAINED for inspection, which is the rule `INCIDENT-367234-scratch-deletion.md`
records.

THE ONE SUBSTITUTION, LABELLED IN THE ANSWER. Each worker names a nominated
source directory and the installer proves it with an lstat. An operator gets
those directories by passing `--repository-source <checkout>`, which CLONES,
and cloning is outside this preparation's boundary -- so here they are created
empty and reported under `test_substitutions`, never as an arrangement that
would serve.
"""
import argparse
import io
import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import capacity                                              # noqa: E402

sys.path[:0] = [str(capacity.DISTRIBUTION / "src"),
                str(capacity.DISTRIBUTION)]

PILOT_INSTALL_INPUTS = (capacity.REPOSITORY / "work/records/2026/10"
                        / "finding-v12-native-pilot-instance-packet"
                        / "fresh5-361402/install-inputs.json")


def _mint(destination, said):
    """Step 1: `bootstrap --inputs` ALONE. No destination, no distro."""
    from tools import bootstrap

    phase1 = json.loads(PILOT_INSTALL_INPUTS.read_text())
    phase1["state_root"] = destination
    phase1["integration_target"] = os.path.join(destination, "repo",
                                                "target.git")
    phase1["integration_workspace"] = os.path.join(destination, "repo",
                                                   "workspace")
    if phase1.get("workers") or phase1.get("jobs"):
        raise SystemExit("the pilot mint inputs are supposed to configure no "
                         "worker and no job")
    pathlib.Path(destination).mkdir(parents=True, exist_ok=False)
    # OUTSIDE THE DESTINATION, deliberately. `fresh.py:mint` writes the
    # installer input document at <destination>/install-inputs.json, and the
    # destination-form install in step 4 then refuses -- "there is already an
    # installer input document ... Nothing here replaces one". The mint form
    # takes any path, so the staged input lives BESIDE the destination and
    # step 4 writes the destination's own slot itself.
    staged = pathlib.Path(destination).parent / "phase1-install-inputs.json"
    staged.write_text(json.dumps(phase1, indent=1, sort_keys=True) + "\n")
    heard = io.StringIO()
    code = bootstrap.main(["--inputs", str(staged)], stream=heard)
    said["step1_mint"] = {"exit": code, "inputs": str(staged),
                          "said": heard.getvalue().strip().splitlines()[-4:]}
    return code == 0


def _readback(destination, said):
    """Step 2: the minted identity, from the instance's own record."""
    from tools import bootstrap

    places = bootstrap.layout(destination)
    minted = json.loads(
        pathlib.Path(places["identity"]).read_text())["authority_uuid"]
    configured = json.loads(pathlib.Path(places["configuration"]).read_text())
    said["step2_readback"] = {
        "authority_uuid": minted,
        "generated": minted != "0" * 31 + "a",
        "mint_configured_no_workers": (configured.get("workers") or []) == []}
    return minted


def _install(destination, distro, held, said):
    """Step 4: ONE destination install carrying both lanes."""
    from tools import bootstrap, instance

    said["test_substitutions"] = [{
        "what": "the two nominated source directories are created empty",
        "why": "the installer lstats them; an operator obtains them with "
               "--repository-source, which clones, and cloning is outside "
               "this preparation's boundary",
        "not_operational": True}]
    for lane in capacity.LANES:
        pathlib.Path(os.path.join(instance.layout(destination)["repository"],
                                  "source-" + lane["worker_id"])).mkdir(
            parents=True, exist_ok=True)
    # THE INSTALLED TASK DOCUMENT IS WRITTEN BEFORE THE INSTALL, which is
    # where `fresh.py:install_and_configure` writes it and for the same
    # reason: the installer opens it, and the manifest's `human_contract`
    # already digests exactly these bytes.
    place = pathlib.Path(held["installed_task"]["place"])
    place.parent.mkdir(parents=True, exist_ok=True)
    place.write_text(held["task_bytes"])
    said["installed_task_written"] = {
        "place": str(place), "bytes": len(held["task_bytes"].encode()),
        "content_digest": held["installed_task"]["content_digest"],
        "digest_agrees": ("sha256:" + capacity.sha256_of(
            held["task_bytes"].encode())
            == held["installed_task"]["content_digest"])}
    inputs = pathlib.Path(destination) / "phase2-inputs.json"
    inputs.write_text(json.dumps(held["document"], indent=1, sort_keys=True)
                      + "\n")
    heard = io.StringIO()
    code = bootstrap.main(["--inputs", str(inputs), "--destination",
                           destination, "--distro", distro,
                           "--no-repositories"], stream=heard)
    said["step4_install"] = {"exit": code, "inputs": str(inputs),
                             "said": heard.getvalue().strip().splitlines()[-4:]}
    return code == 0


def _derive(destination, minted, said):
    """Step 5: the product's own reader over the emitted configuration."""
    from tools import instance
    from tools.creation_ports import DeploymentDerivation

    emitted = json.loads(
        pathlib.Path(instance.layout(destination)["deployment"]).read_text())
    derived = DeploymentDerivation(destination).derived()
    said["step5_derivation"] = {
        "lanes": sorted((one["role"], one["deployment"]["participant"])
                        for one in emitted["workers"]),
        "every_worker_bound_to_the_mint": all(
            one["deployment"]["authority_uuid"] == minted
            for one in emitted["workers"]),
        "review_routes": {one["role"]: one["deployment"].get("review_route")
                          for one in emitted["workers"]},
        "work_id": derived["work_id"],
        "profiles": sorted(derived["profiles"]),
        "input_digest": derived["input_digest"]}
    return True


def _create(destination, minted, said):
    """Step 6: ordinary `manager create`, through the owning entrypoint."""
    from baton_v12.worker_manager import ControlStore
    from tools import instance, job_manager

    places = instance.layout(destination)
    with ControlStore.open(places["control_store"], incarnation="manager-1",
                           clock=lambda: "2026-09-02T00:00:00.000Z"):
        pass
    argv = ["--store", places["job_store"], "--incarnation", "operator-1",
            "--authority-uuid", minted, "create",
            "--instance", destination, "--control", places["control_store"],
            "--authority", places["authority_store"],
            "--task", capacity.TASK_ID, "--template", capacity.TEMPLATE,
            "--source", "installed", "--statement", capacity.STATEMENT,
            "--provider-turn-seconds", str(capacity.PROVIDER_TURN_SECONDS),
            "--verification-command-seconds",
            str(capacity.VERIFICATION_COMMAND_SECONDS)]
    for one in capacity.ACCEPTANCE:
        argv += ["--acceptance", one]
    for one in capacity.WORK_SCOPE:
        argv += ["--work-scope", one]
    heard = io.StringIO()
    try:
        code = job_manager.main(argv, stream=heard)
    except Exception as failure:                             # noqa: BLE001
        said["step6_create"] = {"raised": "%s: %s" % (type(failure).__name__,
                                                      str(failure)[:400])}
        return False
    answer = json.loads(heard.getvalue()) if code == 0 else None
    said["step6_create"] = {"exit": code}
    if answer is not None:
        said["step6_create"].update({
            "job_id": answer["job_id"], "work_id": answer["work_id"],
            "template": answer["template"]["version"],
            "servable": answer["servable"],
            "acceptance_count": len(answer["acceptance"]),
            "scope": answer["scope"],
            "statement_is_the_selected_one":
                answer["task"]["statement"] == capacity.STATEMENT,
            "acceptance_is_the_selected_one":
                list(answer["acceptance"]) == list(capacity.ACCEPTANCE)})
    return code == 0


def _refusals(minted, scratch, distro, said):
    """Step 7: the refusals, against THIS composition.

    Review R3: "retain specific stale-source, foreign-UUID, wrong-artifact and
    occupied-path failures against this new composition (old fixed-identity
    fixture cases do not establish them)". Each one RUNS and the message is
    recorded; none is asserted.
    """
    held = {}

    stale = dict(capacity.source_identity())
    stale.update({"commit": "0" * 40, "at_selected_commit": False})
    try:
        capacity.compose(minted, destination="/nowhere-this-never-reaches",
                         source=stale)
        held["stale_source"] = {"refused": False}
    except capacity.Refused as refusal:
        held["stale_source"] = {"refused": True, "said": str(refusal)}

    for name, bad in (("foreign_uuid_not_hex", "z" * 32),
                      ("foreign_uuid_wrong_length", minted[:31]),
                      ("foreign_uuid_absent", None)):
        try:
            capacity.compose(bad, destination="/nowhere-this-never-reaches")
            held[name] = {"refused": False}
        except capacity.Refused as refusal:
            held[name] = {"refused": True, "said": str(refusal)}

    # WRONG ARTIFACT: the archive pin, moved. The real archive is untouched --
    # the module constant is swapped for the length of the call and restored.
    pinned = capacity.ARCHIVE_SHA256
    try:
        capacity.ARCHIVE_SHA256 = "f" * 64
        capacity.archive_identity()
        held["wrong_artifact"] = {"refused": False}
    except capacity.Refused as refusal:
        held["wrong_artifact"] = {"refused": True, "said": str(refusal)}
    finally:
        capacity.ARCHIVE_SHA256 = pinned
    held["archive_pin_restored"] = capacity.ARCHIVE_SHA256 == pinned

    # OCCUPIED PATH: a directory this call created, with a sentinel in it, and
    # `materialize` pointed at it. It must refuse and leave the sentinel.
    occupied = pathlib.Path(tempfile.mkdtemp(prefix="w367232-occupied-",
                                             dir=str(scratch)))
    sentinel = occupied / "SENTINEL.txt"
    sentinel.write_text("planted by prove_capacity.py; must survive\n")
    before = capacity.sha256_of(sentinel.read_bytes())
    try:
        capacity.materialize(scratch=str(scratch), into=str(occupied))
        held["occupied_path"] = {"refused": False}
    except capacity.Refused as refusal:
        held["occupied_path"] = {
            "refused": True, "said": str(refusal), "path": str(occupied),
            "sentinel_unchanged": (sentinel.is_file()
                                   and capacity.sha256_of(
                                       sentinel.read_bytes()) == before),
            "nothing_else_appeared": sorted(
                one.name for one in occupied.iterdir()) == ["SENTINEL.txt"]}

    # THE SEAL: one member moved after sealing, and the owner's own digest
    # over the altered document no longer matches what it carries.
    from baton_v12.contracts import digest as seal

    composed, _sources = capacity.sealed_manifest(
        capacity._pilot_deployment_base(capacity.LANES[0]["role"]),
        minted_uuid=minted, work=minted[:8] + "-W1",
        task_bytes=b"{}", task_id=capacity.TASK_ID)
    moved = json.loads(json.dumps(composed))
    moved["work_ref"] = {"authority_uuid": "a" * 32, "work_id": "aaaaaaaa-W1"}
    carried = moved.pop("manifest_digest")
    held["seal_detects_a_moved_member"] = {
        "sealed_digest": composed["manifest_digest"],
        "reseal_of_the_altered_document": seal(moved),
        "differs": seal(moved) != carried}
    said["step7_refusals"] = held
    return (all(one.get("refused") for name, one in held.items()
                if isinstance(one, dict) and "refused" in one)
            and held["occupied_path"].get("sentinel_unchanged")
            and held["seal_detects_a_moved_member"]["differs"]
            and held["archive_pin_restored"])


def _tree(place):
    """Every ordinary file under a directory, by digest. `__pycache__` out."""
    held = {}
    for one in sorted(pathlib.Path(place).rglob("*")):
        if one.is_file() and "__pycache__" not in one.parts:
            held[str(one.relative_to(place))] = capacity.sha256_of(
                one.read_bytes())
    return held


def _preflight_writes_nothing(said):
    """Step 8: `preflight` is read-only, MEASURED rather than declared.

    review-2026-10-27T18-50-04Z: "Final connected tests should include …
    actual preflight no-mutation check." So the whole child directory is
    digested, `preflight` runs, and it is digested again. The proposed
    destination's existence is checked on both sides too, because the one
    path `preflight` derives paths *for* is the one it must not create.
    """
    before, existed = _tree(HERE), os.path.exists(capacity.DESTINATION)
    answer = capacity.preflight()
    after, exists = _tree(HERE), os.path.exists(capacity.DESTINATION)
    changed = sorted(set(before) ^ set(after)) + sorted(
        name for name in set(before) & set(after)
        if before[name] != after[name])
    said["step8_preflight_no_mutation"] = {
        "files_digested": len(before),
        "changed": changed,
        "destination_existed_before": existed,
        "destination_exists_after": exists,
        "reported_effects": answer["effects"],
        "reported_effects_are_empty": not any(answer["effects"].values()),
        "measured": "every ordinary file under the child directory, digested "
                    "either side of the call"}
    return (not changed and existed == exists
            and not any(answer["effects"].values()))


def _valid_foreign_identity(destination, minted, distro, said):
    """Step 9: a well-formed uuid that is NOT this instance's identity.

    review-2026-10-27T18-50-04Z: "The UUID cases are malformed values, not a
    valid foreign-authority admission test; do not expand that evidence
    claim." Correct, so here is the missing one. The uuid below is 32 hex
    characters — `compose` has nothing to object to — and it is simply a
    DIFFERENT instance's identity. What refuses it is the product, and
    whatever the product actually does is what gets recorded.
    """
    from baton_v12.worker_manager import ControlStore
    from tools import bootstrap, instance, job_manager

    foreign = "f" * 8 + minted[8:]
    if foreign == minted:                                    # pragma: no cover
        foreign = "e" * 8 + minted[8:]
    held = {"foreign_uuid": foreign, "instance_uuid": minted,
            "well_formed": len(foreign) == 32 and all(
                one in "0123456789abcdef" for one in foreign),
            "composed_without_objection": None}
    document = capacity.compose(foreign, destination=destination,
                                distro=distro)
    held["composed_without_objection"] = True
    held["note"] = ("compose accepts it, correctly: a well-formed identity is "
                    "not something a composer can tell is the wrong one. The "
                    "instance is what knows.")

    # A FRESH DESTINATION FOR THE INSTALL ARM, and the first cut of this case
    # did not have one. Offering the foreign document to the ALREADY-INSTALLED
    # instance got a refusal -- "there is already a runtime … nothing here
    # upgrades a deployment in place" -- which is a custody refusal and says
    # nothing whatever about the identity. So this arm mints its own
    # destination, composes for THAT destination under the FOREIGN uuid, and
    # offers it to an installer that has no other reason to object.
    fresh = str(pathlib.Path(tempfile.mkdtemp(
        prefix="w367232-foreign-", dir=str(pathlib.Path(destination).parents[1]
                                           ))) / "instance")
    inner = {}
    if _mint(fresh, inner):
        its_own = json.loads(pathlib.Path(
            bootstrap.layout(fresh)["identity"]).read_text())["authority_uuid"]
        elsewhere = capacity.compose(foreign, destination=fresh,
                                     distro=distro)
        for lane in capacity.LANES:
            pathlib.Path(os.path.join(
                instance.layout(fresh)["repository"],
                "source-" + lane["worker_id"])).mkdir(parents=True,
                                                      exist_ok=True)
        task = pathlib.Path(elsewhere["installed_task"]["place"])
        task.parent.mkdir(parents=True, exist_ok=True)
        task.write_text(elsewhere["task_bytes"])
        inputs = pathlib.Path(fresh) / "foreign-inputs.json"
        inputs.write_text(json.dumps(elsewhere["document"], indent=1,
                                     sort_keys=True) + "\n")
        heard = io.StringIO()
        code = bootstrap.main(["--inputs", str(inputs), "--destination",
                               fresh, "--distro", distro,
                               "--no-repositories"], stream=heard)
        held["install_into_a_fresh_instance"] = {
            "destination": fresh,
            "its_own_minted_uuid": its_own,
            "document_names": foreign,
            "exit": code, "refused": code != 0,
            "said": " ".join(heard.getvalue().split())[-400:]}

    places = instance.layout(destination)
    with ControlStore.open(places["control_store"], incarnation="manager-1",
                           clock=lambda: "2026-09-02T00:00:00.000Z"):
        pass
    argv = ["--store", places["job_store"], "--incarnation", "operator-1",
            "--authority-uuid", foreign, "create",
            "--instance", destination, "--control", places["control_store"],
            "--authority", places["authority_store"],
            "--task", capacity.TASK_ID, "--template", capacity.TEMPLATE,
            "--source", "installed", "--statement", capacity.STATEMENT,
            "--work-scope", capacity.WORK_SCOPE[0]]
    for one in capacity.ACCEPTANCE:
        argv += ["--acceptance", one]
    heard = io.StringIO()
    try:
        code = job_manager.main(argv, stream=heard)
        held["create_with_the_foreign_identity"] = {
            "exit": code, "refused": code != 0,
            "said": " ".join(heard.getvalue().split())[-400:]}
    except Exception as failure:                             # noqa: BLE001
        held["create_with_the_foreign_identity"] = {
            "refused": True,
            "raised": "%s: %s" % (type(failure).__name__, str(failure)[:400])}
    said["step9_valid_foreign_identity"] = held
    return (held.get("install_into_a_fresh_instance", {}).get("refused")
            and held["create_with_the_foreign_identity"]["refused"])


def _under_the_proposal(scratch, distro, said):
    """Step 10: the proposal bound READ-ONLY, in both of its variants.

    review-2026-10-27T22-59-54Z found the defect this now avoids: the first
    cut called `proposal.write(...)` from inside `compose`, so proving the
    FORMAT-SELECTED variant silently overwrote the DEFAULT proposal that was
    awaiting owner selection -- while `compose` reported `wrote: []`.

    So there are now two arms and they consume two SEPARATE published sets:

      a  the canonical set, bound to the default task. Read-only.
      b  the format-selected variant, published by an explicit command into
         a FRESH directory this run created, and bound from there.

    And between them, the refusal: binding the canonical set to the
    format-selected task is refused by name, because their role instructions
    differ and they are not the same set.
    """
    import proposed_grants as proposal

    held = {}
    for name, grants_from, formatted in (
            ("default", str(proposal.PLACE), False),
            ("format_selected", None, True)):
        if formatted:
            # PUBLISHED EXPLICITLY, INTO A PLACE THIS RUN OWNS. `mkdtemp`
            # under the scratch root, never over the canonical set.
            grants_from = str(pathlib.Path(tempfile.mkdtemp(
                prefix="w367232-variant-", dir=str(scratch))) / "proposal")
            said["effects"]["created"].append(
                str(pathlib.Path(grants_from).parent))
            source = capacity.source_identity()
            document, raw = capacity.installed_task(source,
                                                    proposed_format=True)
            wrote = proposal.write(document, raw, into=grants_from,
                                   proposed_format=True)
            inner = {"published_to": grants_from,
                     "inventory_sha256": wrote["inventory_sha256"],
                     "published_by": "an explicit proposed_grants.write, "
                                     "not by compose"}
        else:
            inner = {"consumed_from": grants_from,
                     "published_by": "nothing in this run -- the canonical "
                                     "set is read, not written"}

        destination = str(pathlib.Path(tempfile.mkdtemp(
            prefix="w367232-proposal-", dir=str(scratch))) / "instance")
        said["effects"]["created"].append(str(pathlib.Path(destination).parent))
        inner["destination"] = destination
        if not _mint(destination, inner):
            held[name] = dict(inner, reached=False)
            continue
        minted = _readback(destination, inner)
        composed = capacity.compose(minted, destination=destination,
                                    distro=distro, grants_from=grants_from,
                                    proposed_format=formatted)
        manifest = composed["document"]["workers"][0]["deployment"][
            "input_manifest"]
        inner["compose_effects"] = composed["effects"]
        inner["compose_wrote_nothing"] = not composed["effects"]["wrote"]
        inner["grants"] = {
            member: {"bound": manifest[member],
                     "derivation": one["derivation"],
                     "status": one["status"]}
            for member, one in sorted(
                composed["proposed_grants"]["members"].items())}
        inner["consumed_read_only"] = composed["proposed_grants"][
            "consumed_read_only"]
        inner["no_vector_constants_left"] = not [
            member for member, one in composed["provenance"]["members"].items()
            if one["kind"] == "unresolved-grant"]
        inner["still_not_complete"] = (
            composed["preparation_is_complete"] is False)
        inner["format_addendum_in_the_task"] = (
            ("PROPOSED FORMAT" in composed["task_bytes"]) == formatted)
        reached = _install(destination, distro, composed, inner)
        if reached:
            _derive(destination, minted, inner)
            reached = _create(destination, minted, inner)
        inner["reached"] = reached
        held[name] = inner

    # AND THE REFUSAL BETWEEN THEM, driven rather than described.
    destination = str(pathlib.Path(tempfile.mkdtemp(
        prefix="w367232-mismatch-", dir=str(scratch))) / "instance")
    said["effects"]["created"].append(str(pathlib.Path(destination).parent))
    inner = {}
    if _mint(destination, inner):
        minted = _readback(destination, inner)
        try:
            capacity.compose(minted, destination=destination, distro=distro,
                             grants_from=str(proposal.PLACE),
                             proposed_format=True)
            held["canonical_set_bound_to_the_format_task"] = {
                "refused": False}
        except capacity.Refused as refusal:
            held["canonical_set_bound_to_the_format_task"] = {
                "refused": True, "said": str(refusal)}
    said["step10_under_the_proposal"] = held
    return (held.get("default", {}).get("reached")
            and held.get("format_selected", {}).get("reached")
            and held["default"]["compose_wrote_nothing"]
            and held["format_selected"]["compose_wrote_nothing"]
            and held["canonical_set_bound_to_the_format_task"]["refused"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scratch", default=capacity.SCRATCH)
    parser.add_argument("--distro", default=None,
                        help="a runtime folder already verified by "
                             "`capacity.py materialize`; omitted, this "
                             "script materializes its own")
    parser.add_argument("--evidence", default=None)
    taken = parser.parse_args(argv)

    scratch = pathlib.Path(taken.scratch)
    if not scratch.is_dir():
        print("refused: no scratch root at " + str(scratch), file=sys.stderr)
        return 2
    said = {"schema": "baton.v12.capacity-proof/2",
            "scratch_root": str(scratch), "effects": {"created": [],
                                                      "removed": []}}
    # THE CUSTODY GUARD OPENS HERE, before a single step runs.
    opening = _tree(HERE)

    if taken.distro:
        # PINNED HERE, NOT BY THE INSTALLER. review-2026-10-27T18-50-04Z: "The
        # current --distro branch relies on bootstrap runtime admission rather
        # than independently pinning the named folder to the retained
        # archive." So the named folder is now measured by the product's own
        # `instance.manifest` and held to the archive record's folder digest
        # before anything else happens, exactly as `materialize` holds the one
        # it extracts. A folder that does not match is refused here.
        from tools import instance

        identity = capacity.archive_identity()
        measured = instance.manifest(taken.distro)
        if measured["digest"] != identity["pinned_folder_digest"]:
            print("refused: the runtime at %s digests %s and the retained "
                  "archive record pins %s"
                  % (taken.distro, measured["digest"],
                     identity["pinned_folder_digest"]), file=sys.stderr)
            return 2
        said["runtime"] = {
            "distro": taken.distro, "obtained": "named by --distro",
            "folder_digest": measured["digest"],
            "files": measured["files"],
            "pinned_independently": "measured by instance.manifest and held "
                                    "to the archive record BEFORE the "
                                    "installer sees it"}
    else:
        made = capacity.materialize(scratch=str(scratch))
        said["runtime"] = {"distro": made["distro"],
                           "obtained": "materialized by this run from the "
                                       "retained archive, both pins verified",
                           "folder_digest": made["folder_digest"],
                           "archive_sha256": made["archive"]["archive_sha256"]}
        said["effects"]["created"] += made["effects"]["created"]
    distro = said["runtime"]["distro"]

    destination = str(pathlib.Path(tempfile.mkdtemp(
        prefix="w367232-proof-", dir=str(scratch))) / "instance")
    said["effects"]["created"].append(str(pathlib.Path(destination).parent))
    said["destination"] = destination
    said["proposed_destination_untouched"] = {
        "proposed": capacity.DESTINATION,
        "exists": os.path.exists(capacity.DESTINATION)}

    reached = _mint(destination, said)
    if reached:
        minted = _readback(destination, said)
        held = capacity.compose(minted, destination=destination,
                                distro=distro)
        said["step3_compose"] = {
            "work_id": held["work_id"], "lanes": held["lanes"],
            "participants": held["participants"],
            "declared_base": held["document"]["jobs"][0]["line_declared_base"],
            "manifest_digest": held["manifest_digest"],
            "document_digest": held["document_digest"],
            "integration_instructions_digest":
                held["document"]["integration_profile"]["instructions_digest"],
            "lane_bases": held["lane_bases"],
            "preparation_is_complete": held["preparation_is_complete"],
            "why_not_complete": held["why_not_complete"],
            "unresolved_operator_grants":
                held["provenance"]["unresolved_operator_grants"],
            "unaccounted_manifest_members":
                held["provenance"]["unaccounted_members"]}
        said["provenance"] = held["provenance"]
        reached = _install(destination, distro, held, said)
        if reached:
            _derive(destination, minted, said)
            reached = _create(destination, minted, said)
        said["step7_ok"] = _refusals(minted, scratch, distro, said)
        said["step8_ok"] = _preflight_writes_nothing(said)
        said["step9_ok"] = _valid_foreign_identity(destination, minted,
                                                   distro, said)
        said["step10_ok"] = _under_the_proposal(scratch, distro, said)

    # ...AND CLOSES HERE, after everything including both proposal variants.
    closing = _tree(HERE)
    appeared = sorted(set(closing) - set(opening))
    vanished = sorted(set(opening) - set(closing))
    rewritten = sorted(name for name in set(opening) & set(closing)
                       if opening[name] != closing[name])
    said["step11_custody_over_the_whole_run"] = {
        "files_digested": len(opening),
        "appeared": appeared, "vanished": vanished, "rewritten": rewritten,
        "proposal_set_unchanged": not [
            name for name in appeared + vanished + rewritten
            if name.startswith("proposed-grants/")],
        "why_this_and_not_step_8": "step 8 digests around ONE subcall. The "
                                   "defect review-2026-10-27T22-59-54Z found "
                                   "happened in step 10, after step 8 had "
                                   "already passed, so only a guard around "
                                   "the WHOLE command can see it.",
        "note": "`appeared` is expected to be non-empty only when --evidence "
                "names a directory inside this one; those writes are "
                "reported, not hidden."}
    said["step11_ok"] = not vanished and not rewritten
    said["delivered_artifacts"] = capacity.delivered_artifacts()
    said["inputs_this_composition_depends_on"] = capacity.external_inputs()
    said["not_established"] = [
        "no provider authentication, container start, model output or live "
        "latency: nothing here contacts an engine or a provider",
        "no repository was cloned and no build ran",
        "the emitted deployment.json is a verification artifact, not an "
        "operational installation",
        "the input manifest's seven operator grants remain unresolved, so "
        "this is a reusable preparation and not a finished configuration"]
    said["ok"] = bool(reached and said.get("step6_create", {}).get("exit") == 0
                      and said.get("step7_ok") and said.get("step8_ok")
                      and said.get("step9_ok") and said.get("step10_ok")
                      and said.get("step11_ok"))
    if taken.evidence:
        place = pathlib.Path(taken.evidence)
        place.mkdir(parents=True, exist_ok=True)
        (place / "PROOF.json").write_text(
            json.dumps(said, indent=1, sort_keys=True, default=str) + "\n")
        said.setdefault("wrote", []).append(str(place / "PROOF.json"))
    json.dump(said, sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0 if said["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
