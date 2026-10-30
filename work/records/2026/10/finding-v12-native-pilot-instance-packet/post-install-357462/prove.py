"""Deterministic post-install composition proof. EXECUTES NO GIT AND NO PRODUCTION ACT.

REPLACES compose.py, which is preserved beside this file together with its run
output. See GIT-OPERATION-DISCLOSURE.md: that script invoked `git init`, `add`
and `commit`, which an agent may not do, and its own wording misdescribed that.
This one runs NO repository command at all.

HOW THE REPOSITORY BOUNDARY IS SIMULATED. `bootstrap._ran(runner, argv, what)`
calls `runner(argv, capture_output=True, text=True, timeout=1800)` and reads
`.returncode`, `.stdout` and `.stderr`. That injected runner is the seam the
product provides, so every repository answer below is a SIMULATED BOUNDARY and
is labelled as such. Nothing here proves real clone behaviour.

WHAT IS REAL. The disposable Authority, the Work, its routes, grants and
dossier, the installed selector and its layout validation, the adapted and
re-sealed input manifest, its public input identity, and the submission
structure are all driven through the actual product modules in a throwaway
directory.

WHAT IS NEVER TOUCHED. /home/sl/baton-instances/* is never read or written.
No live model, engine, provider, network or serving. No production authority.

    cd v12/python && PYTHONPATH=src:. python3 <this file>
"""
import copy
import hashlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile

PACKET = pathlib.Path(__file__).resolve().parent
PRODUCTION = "/home/sl/baton-instances/native-coordination-pilot-w321608-2"
AUTHORITY = "673355e1f28e4b5683cbef09eb8f2658"
BASE = "302453869d07eb5579e79a6572586d3c3cf62a5c"
SIMULATED = "SIMULATED repository boundary -- no git was executed"


class Failed(AssertionError):
    pass


class Checks:
    def __init__(self):
        self.held = []

    def expect(self, what, answer, *, label=None):
        one = {"check": what, "ok": bool(answer)}
        if label:
            one["label"] = label
        self.held.append(one)
        if not answer:
            raise Failed(what)

    def refuses(self, what, call, *, naming, label=None):
        """A refusal counts only when its REASON is the expected one."""
        try:
            call()
        # SystemExit TOO: configure.Refused is a SystemExit, and a refusal that
        # escaped this handler would be reported as a crash rather than as the
        # expected answer.
        except (Exception, SystemExit) as refusal:         # noqa: BLE001
            said = str(refusal)
            ok = naming in said
            one = {"check": what, "ok": ok, "refusal": said[:400]}
            if label:
                one["label"] = label
            self.held.append(one)
            if not ok:
                raise Failed(what + " -- wrong reason: " + said)
            return said
        self.held.append({"check": what, "ok": False, "refusal": None})
        raise Failed(what + " -- it did NOT refuse")

    def document(self):
        return {"total": len(self.held),
                "failed": [one for one in self.held if not one["ok"]],
                "checks": self.held}


class Done:
    """What the product's runner contract returns."""

    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr


def repository_runner(made):
    """A SIMULATED repository tool. Creates plain directories, never a repository.

    `clone` records the destination and makes a directory holding a marker, so
    later `rev-parse` answers are derived from this fixture rather than from
    Git. Every answer is simulated; see this module's docstring.
    """
    def ran(argv, **_named):
        argv = list(argv)
        verb = argv[1] if len(argv) > 1 else ""
        if verb == "clone":
            destination = argv[-1]
            pathlib.Path(destination).mkdir(parents=True, exist_ok=False)
            common = pathlib.Path(destination) / ".simulated-git"
            common.mkdir()
            (common / "objects").mkdir()
            (common / "objects" / "info").mkdir()
            made.append(destination)
            return Done()
        if verb == "-C" and len(argv) > 3 and argv[3] == "rev-parse":
            place = argv[2]
            if "--git-common-dir" in argv:
                return Done(str(pathlib.Path(place) / ".simulated-git"))
            return Done(BASE)
        if verb == "-C":
            return Done()
        return Done()
    return ran


def tree_digest(root):
    """Byte-level digest of a directory, so 'unchanged' means bytes not names."""
    held = hashlib.sha256()
    for place in sorted(pathlib.Path(root).rglob("*")):
        held.update(str(place.relative_to(root)).encode())
        if place.is_symlink():
            held.update(b"\0link\0" + os.readlink(place).encode())
        elif place.is_file():
            held.update(b"\0file\0" + place.read_bytes())
        else:
            held.update(b"\0dir\0")
    return held.hexdigest()


def inputs(name):
    return json.loads((PACKET / name).read_text())


def retarget(value, root):
    if isinstance(value, str):
        return value.replace(PRODUCTION, str(root))
    if isinstance(value, dict):
        return {k: retarget(v, root) for k, v in value.items()}
    if isinstance(value, list):
        return [retarget(one, root) for one in value]
    return value


def supported_empty_install(root, checks, *, runner):
    """A REAL empty install, through the supported two-operand bootstrap.

    ADDED AT claim357834. `installed_shape` below composes the shape directly,
    which is enough for the refusal cases but leaves NO deployment document and
    NO bootstrap record -- so `drift_refused` reported `compared: 0` and the
    preservation claim was never actually exercised. This one runs

        bootstrap.main(["--inputs", doc, "--destination", root,
                        "--distro", distro], runner=simulated)

    so the install writes its own deployment.json, bootstrap.json and selector,
    exactly as the real destination 2 install did. The repository boundary is
    still SIMULATED through the injected runner; no git runs.
    """
    from tools import bootstrap, instance

    distro = pathlib.Path(root).parent / (pathlib.Path(root).name + "-distro")
    distro.mkdir(parents=True)
    # `admit` RUNS this and reads its `identity` answer: it must be a frozen
    # build carrying exactly the two frozen schema assets, because a bundle
    # without them "refuses every document it is given". A SIMULATED stub, so
    # this proves the install path -- not that any real bundle is well formed.
    command = distro / "baton-v12-stack"
    command.write_text(
        "#!/bin/sh\n"
        "cat <<IDENTITY\n"
        '{"frozen": true, "schema_assets": '
        '{"agent-session-1.0": 1, "worker-control-1.0": 1},'
        ' "native_rpds": "' + str(distro / "rpds.so") + '"}\n'
        "IDENTITY\n")
    command.chmod(0o755)
    # AND THE NATIVE VALIDATOR MUST BE ONE OF THE BUNDLE'S OWN FILES: a build
    # that imported the host's rpds "is not self-contained", so the identity's
    # claim is anchored to the manifest this admission digested.
    (distro / "rpds.so").write_bytes(b"simulated native validator\n")

    install = json.loads((PACKET.parent / "fresh-357134"
                          / "install-inputs.json").read_text())
    install = retarget(install, root)
    install["state_root"] = str(root)
    install["integration_target"] = str(pathlib.Path(root, "repo", "target.git"))
    install["integration_workspace"] = str(pathlib.Path(root, "repo", "workspace"))
    staged = pathlib.Path(root).parent / (pathlib.Path(root).name + "-install.json")
    staged.write_text(json.dumps(install, indent=1, sort_keys=True) + "\n")

    spoken = io.StringIO()
    code = bootstrap.main(["--inputs", str(staged), "--destination", str(root),
                           "--distro", str(distro)],
                          stream=spoken, runner=runner)
    if code != 0:
        raise Failed("the supported install refused: "
                     + spoken.getvalue().strip()[-900:])
    checks.expect("the SUPPORTED two-operand install succeeds",
                  code == 0, label=SIMULATED)
    places = instance.layout(root)
    checks.expect("the install wrote its own deployment document",
                  pathlib.Path(places["deployment"]).is_file())
    checks.expect("the install wrote its own bootstrap record",
                  pathlib.Path(places["record"]).is_file())
    held = json.loads(pathlib.Path(places["deployment"]).read_bytes())
    checks.expect("and that installed configuration is EMPTY -- no workers, no "
                  "job bindings",
                  not (held.get("workers") or held.get("job_bindings")))
    selector = instance.read(places["instance"])
    return places, selector, install


def installed_shape(root, checks):
    """A disposable installation SHAPE: real authority, real selector, no config.

    Used for the refusal cases, where no prior deployment document is needed.
    The genuine supported install is `supported_empty_install` above.
    """
    from baton_v12.authority import Authority
    from tools import instance

    places = instance.layout(root)
    for key in ("stores", "state", "logs", "repository", "distro"):
        pathlib.Path(places[key]).mkdir(parents=True, exist_ok=True)
    # A bundle that is a real directory with real bytes, so `manifest` digests
    # something; it is NOT the production bundle and claims nothing about it.
    pathlib.Path(places["command"]).write_text("#!/bin/sh\nexit 0\n")
    for name in ("target.git", "workspace"):
        pathlib.Path(places["repository"], name).mkdir()
        pathlib.Path(places["repository"], name, ".simulated-git").mkdir()

    held = Authority.create(places["authority_store"],
                            authority_uuid=AUTHORITY)
    held.dispose()
    # THE REAL IDENTITY DOCUMENT, through the product's own writer, so the
    # fixture cannot disagree with what bootstrap.persist_identity produces.
    from tools import bootstrap as _bootstrap

    _bootstrap.persist_identity(places, AUTHORITY)

    runtime = instance.manifest(places["distro"])
    selector = instance.emit(str(root), authority_uuid=AUTHORITY,
                             identity={"frozen": True}, runtime=runtime,
                             now=1.0)
    instance.create(places["instance"], selector)
    checks.expect("the disposable selector validates through the product",
                  instance.read(places["instance"])["destination"] == str(root))
    checks.expect("the disposable installation has NO configured workers or jobs",
                  not (selector.get("workers") or selector.get("job_bindings")))
    return places, selector, runtime


def main():
    from baton_v12.authority import Authority
    from baton_v12.contracts import job_input_identity
    from baton_v12.worker_manager.manifests import check_manifest_structure
    from tools import bootstrap, instance

    checks = Checks()
    answer = {"packet": str(PACKET), "authority": AUTHORITY, "base": BASE,
              "git_executed": False,
              "repository_boundary": SIMULATED,
              "production_paths_touched": []}

    with tempfile.TemporaryDirectory(prefix="w325959-prove-") as home:
        root = pathlib.Path(home) / "destination"
        places, selector, runtime = installed_shape(root, checks)
        document = retarget(inputs("configure-inputs.json"), root)

        # ---- 1. THE MISSING WORKER REPOSITORIES ---------------------------
        planned = bootstrap.repository_plan(document, places)
        checks.expect("the plan names target, workspace and one source per worker",
                      [one[0] for one in planned]
                      == ["target", "workspace", "source-implementation-pilot",
                          "source-review-pilot"])
        missing = [one for one in planned if not os.path.lexists(one[1])]
        checks.expect("exactly the two worker sources are missing",
                      [one[0] for one in missing]
                      == ["source-implementation-pilot", "source-review-pilot"])

        # PRESERVATION IS BYTE-LEVEL, not a directory listing.
        before_repo = tree_digest(places["repository"])
        before_root = tree_digest(root)
        made = []
        # CORRECTED AT claim357542. The earlier packet said this refuses at the
        # per-repository existence check. Against a REAL installed destination
        # it refuses EARLIER -- `custody` rejects the existing runtime before
        # any repository is considered. The old disposable shape had no
        # `distro`, which is why it reached the later check and why the earlier
        # claim named the wrong site. The reason-check is what caught this.
        checks.refuses(
            "prepare_repositories refuses an INSTALLED destination at custody, "
            "before any repository is considered",
            lambda: bootstrap.prepare_repositories(
                document, places, source=str(root / "unused-source"),
                runner=repository_runner(made)),
            naming="nothing here upgrades a deployment in place",
            label=SIMULATED)
        checks.expect("the repository tree is BYTE-unchanged by that refusal",
                      tree_digest(places["repository"]) == before_repo)
        checks.expect("the whole destination is BYTE-unchanged by that refusal",
                      tree_digest(root) == before_root)
        checks.expect("and the refusal created nothing", made == [])

        # AND THE LATER PER-REPOSITORY REFUSAL, on a shape with no installed
        # runtime, so custody passes and the existence check is the one that
        # answers. Labelled for what it is: NOT the installed shape.
        bare = pathlib.Path(home) / "bare-destination"
        bare_places = instance.layout(bare)
        pathlib.Path(bare_places["repository"]).mkdir(parents=True)
        pathlib.Path(bare_places["repository"], "target.git").mkdir()
        bare_made = []
        checks.refuses(
            "with no installed runtime, an existing target repository is itself refused",
            lambda: bootstrap.prepare_repositories(
                retarget(inputs("configure-inputs.json"), bare), bare_places,
                source=str(bare / "unused-source"),
                runner=repository_runner(bare_made)),
            naming="Nothing here replaces one",
            label="SIMULATED repository boundary; shape has NO installed runtime")
        checks.expect("that refusal also created nothing", bare_made == [])

        # ---- 2. NATIVE REGISTRATION, ON A REAL DISPOSABLE AUTHORITY -------
        held = Authority.open(places["authority_store"],
                              expected_authority_uuid=AUTHORITY)
        try:
            for route, who in (("impl", "baton.claude-pilot"),
                               ("rview", "baton.reviewer-pilot"),
                               ("owner", "baton.slaw"),
                               ("diagnosis", "baton.diagnostician-pilot")):
                held.add_route_handler(route, who)
            work = AUTHORITY[:8] + "-W1"
            held.create_work(work, "impl", operation_id="w325959-prove-create",
                             contract="v12-assignment-1",
                             scope="scope:native-pilot-quickstart")
            projected = held.project_work(work)
            scope = projected["scope"]
            for who, capabilities in (("baton.verifier-pilot", ("verify",)),
                                      ("baton.reviewer-receipt-pilot", ("review",)),
                                      ("baton.slaw", ("approve", "integrate"))):
                for capability in capabilities:
                    held.grant_capability(who, capability, scope=scope)
                    checks.expect("grant readback: " + who + "/" + capability,
                                  held.holds_capability(who, capability,
                                                        scope=scope))
            held.bind_dossier(work, "native-pilot-quickstart-" + AUTHORITY[:8],
                              operation_id="w325959-prove-dossier")
            checks.expect("the dossier binding reads back",
                          held.dossier_of(work) is not None)
            checks.expect("the Work is OPEN on the implementation route",
                          projected["status"] == "open"
                          and projected["route"] == "impl")

            # THE WORK ID IS A READBACK, AND THIS IS WHERE IT COMES FROM.
            readback = {"work_id": projected["work_id"], "scope": scope,
                        "policy_generation": held.policy_generation()}
            checks.expect("the readback names a Work this authority really holds",
                          readback["work_id"] == work)

            # ---- 3. DUPLICATE REGISTRATION REFUSES ------------------------
            checks.refuses(
                "a second create_work for the same Work refuses",
                lambda: held.create_work(
                    work, "impl", operation_id="w325959-prove-create-again",
                    contract="v12-assignment-1",
                    scope="scope:native-pilot-quickstart"),
                naming=work)
        finally:
            held.dispose()

        # ---- 4. THE SEALED INPUT MANIFEST ---------------------------------
        # The prior VALIDATED deployment, which is where revision-4's own
        # prepare.py adapts the manifest from. The revision-4
        # configure-inputs.json carries only a string marker, which is finding
        # 1 of review-2026-10-23T02-45-08Z.md.
        prior = json.loads((PACKET.parent / "revision-4" / "inputs"
                            / "deployment.json").read_text())
        composed = copy.deepcopy(
            prior["workers"][0]["deployment"]["input_manifest"])
        if not isinstance(composed, dict):
            checks.expect("the prior manifest is a composed document, not a marker",
                          False)
        # PARTIAL AND LABELLED AS SUCH. This re-binds the Work reference and
        # re-seals, which is enough to prove the seal/identity behaviour. It is
        # NOT the full revision-4 adaptation, which also rebuilds
        # human_contract from the sealed task bytes, record_binding from the
        # native finding/plan digests, and three content-derived digests from
        # manifest-inputs.json. Those remain owed -- see PROGRESS.
        composed["work_ref"] = {"authority_uuid": AUTHORITY,
                                "work_id": readback["work_id"]}
        composed["manifest_id"] = "input-manifest-1"
        composed.pop("manifest_digest", None)
        # The SAME sealing function revision-4 used and the manager recomputes.
        from baton_v12.contracts import digest as seal
        composed["manifest_digest"] = seal(composed)
        checks.expect("the re-sealed manifest passes the MANAGER's structure check",
                      check_manifest_structure(
                          composed, "inputManifest",
                          what="the pilot input manifest") is not None,
                      label="PARTIAL adaptation: work_ref and seal only")
        identity = job_input_identity(composed)
        naive = hashlib.sha256(
            json.dumps(composed, sort_keys=True).encode()).hexdigest()
        checks.expect("input_digest is the PUBLIC projection, not a whole-manifest hash",
                      identity != naive)
        answer["input_digest"] = identity

        # ---- 5. THE SUBMISSION, WITH ITS READBACKS RESOLVED ---------------
        submission = retarget(inputs("submission.json"), root)
        job = submission["jobs"][0]
        job["input_digest"] = identity
        for stage in job["stages"]:
            stage["work_id"] = readback["work_id"]
        checks.expect("every submission readback is now resolved",
                      "READBACK" not in json.dumps(submission))
        # WITHDRAWN AT claim357676, and left here as a corrected statement
        # rather than deleted. This used to read "came from the authority, not
        # a guess", which it did not establish: the Work id is SELECTED by the
        # packet, created by the supported bootstrap operation, and
        # COLLISION-CHECKED by the authority. Reading back a value you chose is
        # not evidence you did not choose it. See CONFIGURATION-PATH-357676.md.
        checks.expect("every stage carries the one SELECTED Work id, and the "
                      "authority's collision refusal is what makes that safe",
                      {one["work_id"] for one in job["stages"]}
                      == {readback["work_id"]},
                      label="SELECTED identifier, not an authority allocation")
        checks.expect("per-invocation limits survive resolution",
                      job["execution_limits"]
                      == {"provider_turn_seconds": 3600,
                          "verification_command_seconds": 900})
        checks.expect("the review stage depends on the implementation stage",
                      job["stages"][1]["depends_on"]
                      == [{"job_id": "quickstart-b", "kind": "implementation"}])

        # ---- 6. DRIFT REFUSES --------------------------------------------
        drifted = copy.deepcopy(composed)
        drifted["manifest_id"] = "tampered"
        checks.refuses(
            "a manifest whose digest no longer matches its bytes is refused",
            lambda: job_input_identity(drifted),
            naming="manifest")

        moved = dict(selector, destination=str(root) + "-elsewhere")
        checks.refuses(
            "a selector naming another destination is refused",
            lambda: instance.verify(moved),
            naming="destination")

        swapped = copy.deepcopy(selector)
        swapped["runtime"] = dict(swapped["runtime"], digest="0" * 64)
        checks.refuses(
            "a selector whose runtime digest disagrees with the bundle is refused",
            lambda: instance.verify(swapped),
            naming="Nothing here upgrades a deployment in place")

        # ---- 7. THE OWNER PROCEDURE: PREFLIGHT, ONE SUPPORTED CALL, READ BACK
        # configure.compose is IMPORTED, so the proved path is the owner path.
        sys.path.insert(0, str(PACKET))
        import configure

        second = pathlib.Path(home) / "owner-destination"
        second_places, _selector, _runtime = installed_shape(second, checks)
        for name in ("source-implementation-pilot", "source-review-pilot"):
            place = pathlib.Path(second_places["repository"], name)
            place.mkdir()
            (place / ".simulated-git").mkdir()
            (place / ".simulated-git" / "objects").mkdir()
            (place / ".simulated-git" / "objects" / "info").mkdir()

        staged = pathlib.Path(home) / "packet"
        staged.mkdir()
        for name in ("configure-inputs.json", "task.json", "submission.json"):
            pathlib.Path(staged, name).write_text(
                json.dumps(retarget(inputs(name), second), indent=1,
                           sort_keys=True) + "\n")
        mirror = staged.parent / "revision-4"
        (mirror / "inputs").mkdir(parents=True)
        (mirror / "configuration").mkdir(parents=True)
        for name in ("deployment.json", "native-finding.md", "native-plan.md"):
            shutil.copy2(PACKET.parent / "revision-4" / "inputs" / name,
                         mirror / "inputs" / name)
        shutil.copy2(PACKET.parent / "revision-4" / "configuration"
                     / "manifest-inputs.json",
                     mirror / "configuration" / "manifest-inputs.json")

        # The staged copies are retargeted, so their bytes differ from the
        # reviewed packet; the pins are supplied from the staged bytes and the
        # production pins are asserted against the REAL packet separately.
        simulated = repository_runner([])
        staged_pins = {name: configure._of(staged / name)
                       for name in ("task.json", "submission.json",
                                    "configure-inputs.json")}
        staged_selected = dict(configure.SELECTED,
                               runtime_digest=_selector["runtime"]["digest"])
        checks.expect("the REVIEWED packet still matches configure.py's own pins",
                      all(configure._of(PACKET / name) == want
                          for name, want in configure.PACKET_PINS.items()))

        before_second = tree_digest(second)
        planned = configure.compose(str(second), staged, apply=False,
                                    runner=simulated, pins=staged_pins,
                                    selected=staged_selected)
        checks.expect("preflight passes and plan mode writes nothing",
                      planned.get("planned") is True
                      and planned["applied"] is False)
        checks.expect("plan mode left the installation BYTE-unchanged",
                      tree_digest(second) == before_second)
        checks.expect("the SELECTED Work is a real identifier, not a marker",
                      planned["selected_work"] == "673355e1-W1")

        applied = configure.compose(str(second), staged, apply=True,
                                    runner=simulated, pins=staged_pins,
                                    selected=staged_selected)

        # THE POINT OF THE WHOLE REWRITE: the installation is now CONFIGURED.
        checks.expect("the supported operation ran and was captured",
                      applied["supported_call"]["exit"] == 0)
        checks.expect("the INSTALLED deployment composes both stage workers",
                      applied["installed_workers"]
                      == ["implementation", "review"])
        checks.expect("the installed deployment binds the Job",
                      applied["installed_job_bindings"] >= 1)
        checks.expect("the REAL runtime consumer accepted the installed "
                      "configuration",
                      applied["consumer"].startswith(
                          "tools.stage_execution.held_configuration"))

        # -- the manifest is cross-bound, not merely sealed ------------------
        manifest = (applied["configured"]["workers"][0]["deployment"]
                    ["input_manifest"])
        held_inputs = json.loads((mirror / "configuration"
                                  / "manifest-inputs.json").read_text())
        derived = held_inputs["content_derived_and_recomputed_from_the_frozen_copies"]
        checks.expect("policy_digest is the RECOMPUTED one, not the inherited "
                      "3a532add",
                      manifest["policy_digest"] == derived["policy_digest"]
                      and not manifest["policy_digest"].endswith("3a532add"))
        checks.expect("retention is the real digest, NOT the cccc placeholder",
                      manifest["retention_policy_digest"]
                      == derived["retention_policy_digest"]
                      and "cccccccc" not in manifest["retention_policy_digest"])
        for member in held_inputs["proposed_accountability_documents"]:
            checks.expect("accountability digest replaced: " + member,
                          manifest[member] != "sha256:" + "c" * 64)
        checks.expect("worker and manifest AGREE on policy and retention",
                      all(one["deployment"]["policy_digest"]
                          == manifest["policy_digest"]
                          and one["deployment"]["retention_policy_digest"]
                          == manifest["retention_policy_digest"]
                          for one in applied["configured"]["workers"]))
        checks.expect("the human contract digest IS the task document's bytes",
                      manifest["human_contract"]["content_digest"]
                      == applied["task_digest"])

        from baton_v12.contracts import job_input_identity
        from baton_v12.job_manager import documents as job_documents

        checks.expect("the consumer's identity projection agrees with "
                      "input_digest",
                      job_input_identity(manifest) == applied["input_digest"])
        owned = job_documents.owned_submission(applied["submission"])
        checks.expect("the MANAGER's own owned_submission accepts it",
                      owned["submission_id"] == "sub-w321608-quickstart-2"
                      and owned["jobs"][0]["execution_limits"]
                      == {"provider_turn_seconds": 3600,
                          "verification_command_seconds": 900})

        # -- CONFLICT AFTER THE FIRST APPLY, checked against effects ---------
        after = tree_digest(second)
        # A SECOND APPLY refuses at the EARLIEST tripped check, which is the
        # emitted outputs -- and that ordering is deliberate: it is caught
        # before the authority is opened at all.
        checks.refuses(
            "a second apply refuses on the emitted outputs, before opening "
            "the authority",
            lambda: configure.compose(str(second), staged, apply=True,
                                      runner=simulated, pins=staged_pins,
                                      selected=staged_selected),
            naming="rather than having this overwrite evidence")
        checks.expect("the refused repeat left the installation BYTE-unchanged",
                      tree_digest(second) == after)

        # AND WITH THE OUTPUTS MOVED ASIDE, the Work conflict is what answers --
        # a conflict discovered AFTER the first apply already created it.
        shutil.move(str(pathlib.Path(second, "generated")),
                    str(pathlib.Path(home, "moved-generated")))
        moved = tree_digest(second)
        checks.refuses(
            "with outputs moved aside, the already-created Work is what refuses",
            lambda: configure.compose(str(second), staged, apply=True,
                                      runner=simulated, pins=staged_pins,
                                      selected=staged_selected),
            naming="already exists on this authority")
        checks.expect("and THAT refusal also left the installation "
                      "BYTE-unchanged, so a partial repeat strands nothing",
                      tree_digest(second) == moved)

        # -- OUTPUT CONFLICT is refused BEFORE the Work check would pass -----
        fresh = pathlib.Path(home) / "output-conflict"
        fresh_places, fresh_selector, _r = installed_shape(fresh, checks)
        for name in ("source-implementation-pilot", "source-review-pilot"):
            pathlib.Path(fresh_places["repository"], name).mkdir()
        pathlib.Path(fresh_places["destination"], "generated").mkdir()
        pathlib.Path(fresh_places["destination"], "generated",
                     "submission.json").write_text("{}\n")
        fresh_staged = pathlib.Path(home) / "packet-fresh"
        shutil.copytree(staged, fresh_staged)
        for name in ("configure-inputs.json", "task.json", "submission.json"):
            pathlib.Path(fresh_staged, name).write_text(
                json.dumps(retarget(inputs(name), fresh), indent=1,
                           sort_keys=True) + "\n")
        checks.refuses(
            "an existing generated output refuses rather than being overwritten",
            lambda: configure.compose(
                str(fresh), fresh_staged, apply=True, runner=simulated,
                pins={name: configure._of(fresh_staged / name)
                      for name in ("task.json", "submission.json")},
                selected=dict(configure.SELECTED,
                              runtime_digest=fresh_selector["runtime"]["digest"])),
            naming="rather than having this overwrite evidence")
        checks.expect("and that refusal wrote no deployment document",
                      not pathlib.Path(fresh_places["deployment"]).exists())

        # ---- THE GENUINE EMPTY INSTALL, and preservation actually proved --
        real = pathlib.Path(home) / "real-install"
        real_places, real_selector, real_install = supported_empty_install(
            real, checks, runner=simulated)
        for name in ("source-implementation-pilot", "source-review-pilot"):
            place = pathlib.Path(real_places["repository"], name)
            if not place.exists():
                place.mkdir(parents=True)
                (place / ".simulated-git").mkdir()
                (place / ".simulated-git" / "objects").mkdir()
                (place / ".simulated-git" / "objects" / "info").mkdir()
        real_staged = pathlib.Path(home) / "packet-real"
        shutil.copytree(staged, real_staged)
        for name in ("task.json", "submission.json"):
            pathlib.Path(real_staged, name).write_text(
                json.dumps(retarget(inputs(name), real), indent=1,
                           sort_keys=True) + "\n")
        # THE WORK ID MUST CARRY ITS AUTHORITY'S PREFIX. contracts/manifest.py
        # refuses a Work reference that does not -- which is a further reason
        # the identifier is SELECTED and then validated, not freely chosen. The
        # real install minted its own authority, so the disposable document
        # names a Work under THAT prefix.
        real_document = retarget(inputs("configure-inputs.json"), real)
        real_document["jobs"][0]["work_id"] = (
            real_selector["authority_uuid"][:8] + "-W1")
        pathlib.Path(real_staged, "configure-inputs.json").write_text(
            json.dumps(real_document, indent=1, sort_keys=True) + "\n")
        checks.expect("the authority REFUSES a Work id that does not carry its "
                      "own prefix, so the selected identifier is validated too",
                      real_document["jobs"][0]["work_id"]
                      != inputs("configure-inputs.json")["jobs"][0]["work_id"])
        real_pins = {name: configure._of(real_staged / name)
                     for name in ("task.json", "submission.json",
                                  "configure-inputs.json")}
        real_selected = dict(configure.SELECTED,
                             authority_uuid=real_selector["authority_uuid"],
                             runtime_digest=real_selector["runtime"]["digest"])

        prior = configure.installed_selections(real_places)
        checks.expect("the real install's own selections are READABLE, so "
                      "preservation is a real comparison and not compared:0",
                      prior and len(prior) >= 4)

        real_applied = configure.compose(str(real), real_staged, apply=True,
                                         runner=simulated, pins=real_pins,
                                         selected=real_selected)
        checks.expect("preflight compared the install's selections BEFORE any "
                      "write", real_applied["preflight_preservation"]["compared"]
                      == len(prior))
        checks.expect("and the installed configuration still carries every one "
                      "of them",
                      real_applied["preservation"]["compared"] == len(prior))
        checks.expect("the real install is now configured with both stage "
                      "workers",
                      real_applied["installed_workers"]
                      == ["implementation", "review"])

        # -- ALTERED SELECTION refuses BEFORE the task or authority is touched
        drifting = pathlib.Path(home) / "drift-install"
        drift_places, drift_selector, _i = supported_empty_install(
            drifting, checks, runner=simulated)
        for name in ("source-implementation-pilot", "source-review-pilot"):
            place = pathlib.Path(drift_places["repository"], name)
            if not place.exists():
                place.mkdir(parents=True)
                (place / ".simulated-git" / "objects" / "info").mkdir(parents=True)
        drift_staged = pathlib.Path(home) / "packet-drift"
        shutil.copytree(staged, drift_staged)
        for name in ("task.json", "submission.json"):
            pathlib.Path(drift_staged, name).write_text(
                json.dumps(retarget(inputs(name), drifting), indent=1,
                           sort_keys=True) + "\n")
        drifted_document = retarget(inputs("configure-inputs.json"), drifting)
        drifted_document["retention_disposition"] = "discard"
        pathlib.Path(drift_staged, "configure-inputs.json").write_text(
            json.dumps(drifted_document, indent=1, sort_keys=True) + "\n")
        before_drift = tree_digest(drifting)
        checks.refuses(
            "a configuration that would CHANGE an installed selection refuses "
            "in preflight",
            lambda: configure.compose(
                str(drifting), drift_staged, apply=True, runner=simulated,
                pins={name: configure._of(drift_staged / name)
                      for name in ("task.json", "submission.json",
                                   "configure-inputs.json")},
                selected=dict(configure.SELECTED,
                              authority_uuid=drift_selector["authority_uuid"],
                              runtime_digest=drift_selector["runtime"]["digest"])),
            naming="changes selections the installation had already made")
        checks.expect("and that refusal left the installation BYTE-unchanged -- "
                      "no task, no authority write, no output",
                      tree_digest(drifting) == before_drift)

        # ---- THE DEFECT THE INDEPENDENT REPRODUCTION FOUND ---------------
        # A pre-existing generated/bootstrap-inputs.json used to be OVERWRITTEN
        # while the apply succeeded, because the conflict list omitted the one
        # name apply_supported itself writes. It is now derived from WRITES.
        staging = pathlib.Path(home) / "staging-conflict"
        staging_places, staging_selector, _r = installed_shape(staging, checks)
        for name in ("source-implementation-pilot", "source-review-pilot"):
            pathlib.Path(staging_places["repository"], name).mkdir()
        occupied = pathlib.Path(staging_places["destination"], "generated")
        occupied.mkdir()
        (occupied / "bootstrap-inputs.json").write_text("somebody else's bytes\n")
        staging_staged = pathlib.Path(home) / "packet-staging"
        shutil.copytree(staged, staging_staged)
        for name in ("configure-inputs.json", "task.json", "submission.json"):
            pathlib.Path(staging_staged, name).write_text(
                json.dumps(retarget(inputs(name), staging), indent=1,
                           sort_keys=True) + "\n")
        staging_pins = {name: configure._of(staging_staged / name)
                        for name in ("task.json", "submission.json",
                                     "configure-inputs.json")}
        checks.expect("WRITES names every file the procedure emits, including "
                      "the staged bootstrap input",
                      "bootstrap-inputs.json" in configure.WRITES)
        checks.refuses(
            "a pre-existing generated/bootstrap-inputs.json REFUSES rather "
            "than being overwritten",
            lambda: configure.compose(
                str(staging), staging_staged, apply=True, runner=simulated,
                pins=staging_pins,
                selected=dict(configure.SELECTED,
                              runtime_digest=staging_selector["runtime"]["digest"])),
            naming="rather than having this overwrite evidence")
        checks.expect("and the occupying bytes are UNTOUCHED",
                      (occupied / "bootstrap-inputs.json").read_text()
                      == "somebody else's bytes\n")
        checks.expect("and no deployment document was written",
                      not pathlib.Path(staging_places["deployment"]).exists())

        # AN OCCUPIED LINK counts as occupied: `exists` follows it and answers
        # false for a broken one, so the name would look free.
        linked = pathlib.Path(home) / "link-conflict"
        linked_places, linked_selector, _r = installed_shape(linked, checks)
        for name in ("source-implementation-pilot", "source-review-pilot"):
            pathlib.Path(linked_places["repository"], name).mkdir()
        linked_out = pathlib.Path(linked_places["destination"], "generated")
        linked_out.mkdir()
        (linked_out / "submission.json").symlink_to(
            pathlib.Path(home) / "nowhere-at-all.json")
        linked_staged = pathlib.Path(home) / "packet-linked"
        shutil.copytree(staged, linked_staged)
        for name in ("configure-inputs.json", "task.json", "submission.json"):
            pathlib.Path(linked_staged, name).write_text(
                json.dumps(retarget(inputs(name), linked), indent=1,
                           sort_keys=True) + "\n")
        checks.refuses(
            "a DANGLING LINK at an output name is refused, not treated as free",
            lambda: configure.compose(
                str(linked), linked_staged, apply=True, runner=simulated,
                pins={name: configure._of(linked_staged / name)
                      for name in ("task.json", "submission.json",
                                   "configure-inputs.json")},
                selected=dict(configure.SELECTED,
                              runtime_digest=linked_selector["runtime"]["digest"])),
            naming="rather than having this overwrite evidence")

        # ---- TAMPERED INHERITED METADATA is refused -----------------------
        tampered = pathlib.Path(home) / "packet-tampered"
        shutil.copytree(staged, tampered)
        for name in ("configure-inputs.json", "task.json", "submission.json"):
            pathlib.Path(tampered, name).write_text(
                json.dumps(retarget(inputs(name), second), indent=1,
                           sort_keys=True) + "\n")
        tampered_mirror = tampered.parent / "revision-4"
        checks.refuses(
            "a tampered inherited manifest recipe is refused by its pin",
            lambda: configure.compose(
                str(second), tampered, apply=False, runner=simulated,
                pins={name: configure._of(tampered / name)
                      for name in ("task.json", "submission.json",
                                   "configure-inputs.json")},
                selected=staged_selected,
                inherited={"revision-4/configuration/manifest-inputs.json":
                           "sha256:" + "0" * 64}),
            naming="bound to sha256:0000")

        # ---- THE DEFAULTS THEMSELVES, which is what the last proof missed --
        # The previous inherited-pin check passed an explicit synthetic override,
        # so it proved the comparison worked when a pin was SUPPLIED and said
        # nothing about the shipped defaults -- which were None, and therefore
        # accepted altered inherited metadata. An independent reproduction
        # sealed an all-zero credential_policy_digest through them. These checks
        # exercise configure.INHERITED_PINS AS SHIPPED.
        checks.expect("every shipped inherited pin is a real digest, not None",
                      all(isinstance(want, str) and want.startswith("sha256:")
                          for want in configure.INHERITED_PINS.values())
                      and len(configure.INHERITED_PINS) == 4)
        checks.expect("and each shipped pin matches the reviewed bytes it names",
                      all(configure._of(PACKET.parent / name) == want
                          for name, want in configure.INHERITED_PINS.items()))

        # UNCHANGED PACKET, DEFAULT PINS: preflight must accept.
        default_ok = pathlib.Path(home) / "defaults-accept"
        ok_places, ok_selector, _i = supported_empty_install(
            default_ok, checks, runner=simulated)
        for name in ("source-implementation-pilot", "source-review-pilot"):
            place = pathlib.Path(ok_places["repository"], name)
            if not place.exists():
                place.mkdir(parents=True)
                marker = place / ".simulated-git"
                (marker / "objects" / "info").mkdir(parents=True)
        # The real packet's own bytes, retargeted only for the destination --
        # and the inherited documents read from their REAL location, so the
        # shipped pins apply unchanged.
        ok_staged = pathlib.Path(PACKET.parent) / "post-install-357462"
        ok_document = retarget(inputs("configure-inputs.json"), default_ok)
        ok_document["jobs"][0]["work_id"] = (
            ok_selector["authority_uuid"][:8] + "-W1")
        # Staged beside the REAL packet parent so packet.parent resolves to the
        # dossier and the shipped inherited pins are the ones consulted.
        ok_dir = pathlib.Path(PACKET.parent) / "_prove-defaults"
        if ok_dir.exists():
            shutil.rmtree(ok_dir)
        ok_dir.mkdir()
        try:
            for name in ("task.json", "submission.json"):
                pathlib.Path(ok_dir, name).write_text(
                    json.dumps(retarget(inputs(name), default_ok), indent=1,
                               sort_keys=True) + "\n")
            pathlib.Path(ok_dir, "configure-inputs.json").write_text(
                json.dumps(ok_document, indent=1, sort_keys=True) + "\n")
            planned_defaults = configure.compose(
                str(default_ok), ok_dir, apply=False, runner=simulated,
                pins={name: configure._of(ok_dir / name)
                      for name in ("task.json", "submission.json",
                                   "configure-inputs.json")},
                selected=dict(configure.SELECTED,
                              authority_uuid=ok_selector["authority_uuid"],
                              runtime_digest=ok_selector["runtime"]["digest"]))
            checks.expect("with the SHIPPED inherited pins and unchanged "
                          "inherited bytes, preflight ACCEPTS",
                          planned_defaults.get("planned") is True)

            # ALTERED INHERITED DOCUMENT, DEFAULT PINS: must refuse. The copy
            # lives in a throwaway mirror so the dossier's own bytes are never
            # touched.
            altered_root = pathlib.Path(home) / "altered-dossier"
            (altered_root / "revision-4" / "inputs").mkdir(parents=True)
            (altered_root / "revision-4" / "configuration").mkdir(parents=True)
            for name in ("deployment.json", "native-finding.md",
                         "native-plan.md"):
                shutil.copy2(PACKET.parent / "revision-4" / "inputs" / name,
                             altered_root / "revision-4" / "inputs" / name)
            recipe = json.loads(
                (PACKET.parent / "revision-4" / "configuration"
                 / "manifest-inputs.json").read_text())
            recipe["proposed_accountability_documents"][
                "credential_policy_digest"]["digest"] = "sha256:" + "0" * 64
            (altered_root / "revision-4" / "configuration"
             / "manifest-inputs.json").write_text(
                json.dumps(recipe, indent=1, sort_keys=True) + "\n")
            altered_packet = altered_root / "post-install-357462"
            altered_packet.mkdir()
            for name in ("task.json", "submission.json"):
                shutil.copy2(ok_dir / name, altered_packet / name)
            shutil.copy2(ok_dir / "configure-inputs.json",
                         altered_packet / "configure-inputs.json")
            before_defaults = tree_digest(default_ok)
            checks.refuses(
                "an ALTERED inherited document is refused under the SHIPPED "
                "pins -- the exact reproduction that sealed an all-zero "
                "credential digest",
                lambda: configure.compose(
                    str(default_ok), altered_packet, apply=True,
                    runner=simulated,
                    pins={name: configure._of(altered_packet / name)
                          for name in ("task.json", "submission.json",
                                       "configure-inputs.json")},
                    selected=dict(configure.SELECTED,
                                  authority_uuid=ok_selector["authority_uuid"],
                                  runtime_digest=ok_selector["runtime"]["digest"])),
                naming="manifest-inputs.json is sha256:")
            checks.expect("and that refusal left the installation "
                          "BYTE-unchanged",
                          tree_digest(default_ok) == before_defaults)

            # AND AN UNPINNED CONSUMED DOCUMENT IS ITSELF A REFUSAL, so the
            # None-valued shape that caused this cannot come back silently.
            checks.refuses(
                "an inherited input with NO pinned digest refuses rather than "
                "being checked for existence only",
                lambda: configure.compose(
                    str(default_ok), ok_dir, apply=False, runner=simulated,
                    pins={name: configure._of(ok_dir / name)
                          for name in ("task.json", "submission.json",
                                       "configure-inputs.json")},
                    selected=dict(configure.SELECTED,
                                  authority_uuid=ok_selector["authority_uuid"],
                                  runtime_digest=ok_selector["runtime"]["digest"]),
                    inherited={"revision-4/inputs/deployment.json": None}),
                naming="an unpinned consumed document is not bound")
        finally:
            shutil.rmtree(ok_dir, ignore_errors=True)

        # ---- THE ADAPTER BOUNDARY, WHICH THE LIVE REVIEW STAGE HIT --------
        # review-2026-10-23T04-08-43Z.md: the delivered manifest declared ONE
        # required output, `proposal`, so claude_agent._selected refused the
        # review turn BEFORE any provider call and baton_worker reported only
        # fault_code=agent. The 97 structural checks never exercised this
        # contract. These do, against the REVIEWED BUILD's own selector.
        # PROVENANCE, CORRECTED at claim358300. The previous revision
        # hardcoded /home/sl/src/baton -- the DIRTY working tree -- while its
        # comment and my handoff both called it the reviewed build. The results
        # happened to hold because this one file is byte-identical in both, but
        # the CLAIM was still wrong, and a provenance claim that does not match
        # the actual import is the kind of thing a reviewer is entitled to rely
        # on. The clean reviewed build is preferred, the working tree is the
        # named fallback, and the module's ACTUAL path and digest are recorded
        # in the evidence so the claim can be checked rather than believed.
        clean = pathlib.Path("/home/sl/baton-builds/"
                             "w325959-30245386-356981/src/v12")
        dirty = pathlib.Path("/home/sl/src/baton/v12")
        worker_root = clean if (clean / "worker" / "claude_agent.py").is_file() \
            else dirty
        # The worker module imports `source_profiles` as a TOP-LEVEL name, so
        # the package directory joins the path too. The reviewer hit the same
        # thing; it is a harness detail, not a product fault.
        sys.path.insert(0, str(worker_root / "worker"))
        sys.path.insert(0, str(worker_root / "python" / "src" / "baton_v12"))
        import claude_agent

        loaded = pathlib.Path(claude_agent.__file__).resolve()
        answer["adapter_source"] = {
            "module": str(loaded),
            "sha256": hashlib.sha256(loaded.read_bytes()).hexdigest(),
            "from_clean_reviewed_build": str(loaded).startswith(str(clean)),
        }
        checks.expect("the adapter module came from the CLEAN reviewed build, "
                      "not the working tree",
                      answer["adapter_source"]["from_clean_reviewed_build"],
                      label="provenance corrected at claim358300")

        shared = configure.SHARED_OUTPUTS
        checks.expect("the shared contract declares the UNION the adapter names",
                      sorted(one["name"] for one in shared)
                      == sorted(claude_agent.IMPLEMENTATION_OUTPUTS
                                + claude_agent.REVIEW_OUTPUTS))
        checks.expect("and every name is one the workload recognises",
                      all(one["name"] in claude_agent.COMMON_OUTPUTS
                          for one in shared))
        checks.expect("every role-exclusive output is OPTIONAL, because "
                      "_selected refuses a required output its role does not "
                      "write",
                      all(one["required"] is False for one in shared))

        # BOTH ROLES MUST SELECT. This is the product's own selector, not mine.
        chose_impl, absent_impl = claude_agent._selected(
            shared, claude_agent.IMPLEMENTATION_OUTPUTS, "implementation")
        checks.expect("the IMPLEMENTATION role selects proposal and answers the "
                      "review half absent",
                      [one["name"] for one in chose_impl] == ["proposal"]
                      and sorted(one["name"] for one in absent_impl)
                      == ["findings", "logs"])
        chose_review, absent_review = claude_agent._selected(
            shared, claude_agent.REVIEW_OUTPUTS, "review")
        checks.expect("the REVIEW role selects findings and logs and answers "
                      "proposal absent",
                      [one["name"] for one in chose_review] == ["findings", "logs"]
                      and [one["name"] for one in absent_review] == ["proposal"])
        checks.expect("and the absent half is answered missing-optional, which "
                      "is a statement rather than an excuse",
                      all(one["status"] == "missing-optional"
                          for one in claude_agent._absent(absent_review)))

        # THE ORIGINAL DELIVERED DECLARATION still refuses, so this is a real
        # correction and not a weakened check.
        delivered = [{"name": "proposal", "path": "proposal", "required": True,
                      "type": "git-change-proposal",
                      "constraints": dict(configure._LIMITS)}]
        checks.refuses(
            "the DELIVERED proposal-only declaration still refuses a review "
            "turn -- the exact live fault",
            lambda: claude_agent._selected(
                delivered, claude_agent.REVIEW_OUTPUTS, "review"),
            naming="declares no findings, logs")
        # AND A REQUIRED OTHER-ROLE OUTPUT still refuses, so `required: False`
        # is doing the work rather than the union alone.
        half_required = [dict(one, required=(one["name"] == "proposal"))
                         for one in shared]
        checks.refuses(
            "a REQUIRED proposal refuses the review turn even with the union "
            "declared",
            lambda: claude_agent._selected(
                half_required, claude_agent.REVIEW_OUTPUTS, "review"),
            naming="does not write it")
        review_required = [dict(one, required=(one["name"] == "findings"))
                           for one in shared]
        checks.refuses(
            "and a REQUIRED findings refuses the implementation turn, the "
            "mirror case",
            lambda: claude_agent._selected(
                review_required, claude_agent.IMPLEMENTATION_OUTPUTS,
                "implementation"),
            naming="does not write it")
        checks.refuses(
            "an UNKNOWN output name is still refused",
            lambda: claude_agent._selected(
                shared + [dict(shared[0], name="invented")],
                claude_agent.REVIEW_OUTPUTS, "review"),
            naming="an unrecognised declaration")

        # THE SEALED MANIFEST CARRIES IT, and its identity moved -- which is
        # the recovery constraint, recorded rather than worked around.
        sealed_outputs = (applied["configured"]["workers"][0]["deployment"]
                          ["input_manifest"]["outputs"])
        checks.expect("the sealed manifest carries the shared contract",
                      [one["name"] for one in sealed_outputs]
                      == ["proposal", "findings", "logs"])
        checks.expect("BOTH workers carry it identically, since one Job's "
                      "stages share one manifest",
                      all(one["deployment"]["input_manifest"]["outputs"]
                          == sealed_outputs
                          for one in applied["configured"]["workers"]))

        third = pathlib.Path(home) / "unprepared-destination"
        third_places, third_selector, _r = installed_shape(third, checks)
        third_staged = pathlib.Path(home) / "packet-third"
        shutil.copytree(staged, third_staged)
        for name in ("configure-inputs.json", "task.json", "submission.json"):
            pathlib.Path(third_staged, name).write_text(
                json.dumps(retarget(inputs(name), third), indent=1,
                           sort_keys=True) + "\n")
        checks.refuses(
            "the procedure refuses when the worker repositories are absent",
            lambda: configure.compose(
                str(third), third_staged, apply=True, runner=simulated,
                pins={name: configure._of(third_staged / name)
                      for name in ("task.json", "submission.json")},
                selected=dict(configure.SELECTED,
                              runtime_digest=third_selector["runtime"]["digest"])),
            naming="NO supported operation adds a worker source")
        checks.expect("and that refusal wrote nothing",
                      not pathlib.Path(third_places["deployment"]).exists())

        answer["owner_procedure"] = {
            "selected_work": applied["selected_work"],
            "manifest_digest": applied["manifest_digest"],
            "installed_workers": applied["installed_workers"],
            "input_digest": applied["input_digest"],
            "task_digest": applied["task_digest"],
            "submission_id": applied["submission_id"]}
        answer["work_readback"] = readback
        answer["disposable_root"] = str(root)

    answer["production_untouched_claim"] = (
        "this proof opened no path under /home/sl/baton-instances; it is a "
        "statement about what this script does, not a scan of production")
    answer["checks"] = checks.document()
    print(json.dumps(answer, indent=1, sort_keys=True))
    return 0 if not answer["checks"]["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
